'use client'

import React, { useState, useCallback, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { CheckCircle2, XCircle, Loader2, AlertTriangle, RefreshCw, Key, CheckSquare, Square, ListChecks, X } from 'lucide-react'
import { fetchQCList, fetchQC, type QCListItem } from '@/lib/api'
import { fetchPBByQC } from '@/lib/api'
import { useErpToken } from '@/hooks/useErpToken'
import LoadingCard from '@/components/ui/LoadingCard'

interface Props {
  erpToken: string
  erpTenantId: string
  onNeedsToken: () => void
  onClearToken: () => void
}

interface CrossRow {
  field: string
  qcPath: string   // human-readable path in QC JSON
  pbPath: string   // human-readable path in PB JSON
  qcVal: number | string
  pbVal: number | string
  ok: boolean
  note?: string
}

interface CheckRow {
  field: string
  formula: string
  calc?: string
  expected: number
  actual: number
  ok: boolean
  note?: string
}

const TOLERANCE = 0.05
function r(v: number, dp = 6) { return Math.round(v * 10 ** dp) / 10 ** dp }
function ind(n: number | string) { return Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 }) }
function fmtVal(v: number | string): string {
  const n = Number(v)
  if (isNaN(n)) return String(v)
  const a = Math.abs(n)
  if (a >= 10000) return n.toLocaleString('en-IN', { maximumFractionDigits: 2 })
  if (a >= 1 || a === 0) return n.toFixed(4)
  return n.toFixed(6)
}

function numClose(a: number | string, b: number | string): boolean {
  return Math.abs(Number(a) - Number(b)) <= TOLERANCE
}

// ── Build cross-check rows from QC + PB line pairs ───────────────────────────
function buildCrossRows(qcLine: any, pbLine: any): CrossRow[] {
  function row(
    field: string, qcPath: string, pbPath: string,
    qcRaw: any, pbRaw: any, note?: string
  ): CrossRow {
    const qcVal = qcRaw ?? '—'
    const pbVal = pbRaw ?? '—'
    const ok = qcRaw == null || pbRaw == null ? false : numClose(qcRaw, pbRaw)
    return { field, qcPath, pbPath, qcVal, pbVal, ok, note }
  }

  return [
    row('base_rate',          'base_rate',                   'base_rate',                      qcLine.base_rate,                       pbLine.base_rate),
    row('grn_qty',            'grn_qty',                     'alternate_gate_pass_quantity',    qcLine.grn_qty,                         pbLine.alternate_gate_pass_quantity),
    row('empty_bag_weight',   'empty_bag_weight',            'empty_bag_weight',                qcLine.empty_bag_weight,                pbLine.empty_bag_weight),
    row('accepted_qty',       'alternate_accepted_qty',      'alternate_net_qty',               qcLine.alternate_accepted_qty,          pbLine.alternate_net_qty),
    row('empty_bags_amount',  'empty_bags_txn_amount',       'empty_bags_txn_amount',           qcLine.empty_bags_txn_amount,           pbLine.empty_bags_txn_amount),
    row('net_of_empty_bag',   'net_of_empty_bag_amount',     'net_of_empty_bag_amount',         qcLine.net_of_empty_bag_amount,         pbLine.net_of_empty_bag_amount),
    row('deduction_weight',   'deduction_weight',            'alternate_deduction_weight',      qcLine.deduction_weight,                pbLine.alternate_deduction_weight),
    row('qc_deduction_amount','qc_deduction_amount',         'qc_deduction_amount',             qcLine.qc_deduction_amount,             pbLine.qc_deduction_amount),
    row('txn_without_discount','transaction_amount_without_discount','transaction_amount_without_discount', qcLine.transaction_amount_without_discount, pbLine.transaction_amount_without_discount),
    row('net_txn_amount',     'txn_currency_amount',         'txn_currency_amount_detail',      qcLine.txn_currency_amount,             pbLine.txn_currency_amount_detail, 'PB stores 3dp'),
    row('net_purchase_rate',  'rate',                        'rate',                            qcLine.rate,                            pbLine.rate),
  ]
}

// ── Build PB internal arithmetic checks ──────────────────────────────────────
function buildPBChecks(pb: any, pbLine: any): CheckRow[] {
  function chk(field: string, formula: string, calc: string | undefined, expected: number, actual: number, note?: string): CheckRow {
    return { field, formula, calc, expected, actual, ok: Math.abs(expected - actual) <= TOLERANCE, note }
  }

  const txnAmt   = parseFloat(pbLine.txn_currency_amount_detail ?? 0)
  const igstRate = parseFloat(pbLine.txn_currency_igst_rate ?? 0)
  const cgstRate = parseFloat(pbLine.txn_currency_cgst_rate ?? 0)
  const sgstRate = parseFloat(pbLine.txn_currency_sgst_rate ?? 0)
  const igstAmt  = parseFloat(pbLine.txn_currency_igst_amount ?? 0)
  const cgstAmt  = parseFloat(pbLine.txn_currency_cgst_amount ?? 0)
  const sgstAmt  = parseFloat(pbLine.txn_currency_sgst_amount ?? 0)
  const taxAmt   = parseFloat(pbLine.txn_currency_tax_amount ?? 0)
  const labour   = parseFloat(pbLine.labour_charges ?? 0)
  const transport= parseFloat(pbLine.transport ?? 0)
  const lineTotal= parseFloat(pbLine.txn_currency_total_txn_amount ?? 0)

  const gstType  = pbLine.gst_type || ''
  const rows: CheckRow[] = []

  if (igstRate > 0) {
    const expIgst = r(txnAmt * igstRate / 100)
    rows.push(chk('igst_amount', `net_txn × igst% / 100`, `₹${ind(txnAmt)} × ${igstRate}%`, expIgst, igstAmt))
  }
  if (cgstRate > 0) {
    const expCgst = r(txnAmt * cgstRate / 100)
    rows.push(chk('cgst_amount', `net_txn × cgst% / 100`, `₹${ind(txnAmt)} × ${cgstRate}%`, expCgst, cgstAmt))
  }
  if (sgstRate > 0) {
    const expSgst = r(txnAmt * sgstRate / 100)
    rows.push(chk('sgst_amount', `net_txn × sgst% / 100`, `₹${ind(txnAmt)} × ${sgstRate}%`, expSgst, sgstAmt))
  }

  const expTax = r(igstAmt + cgstAmt + sgstAmt)
  rows.push(chk('tax_total', 'igst + cgst + sgst', `₹${ind(igstAmt)} + ₹${ind(cgstAmt)} + ₹${ind(sgstAmt)}`, expTax, taxAmt))

  const expTotal = r(txnAmt + taxAmt + labour + transport)
  rows.push(chk('net_payable', 'net_txn + tax + labour + transport',
    `₹${ind(txnAmt)} + ₹${ind(taxAmt)} + ${labour} + ${transport}`, expTotal, lineTotal))

  return rows
}

// ── Column layouts ────────────────────────────────────────────────────────────
const CROSS_COLS = '1fr 1fr 1fr 1fr 28px'
const CHECK_COLS = '1fr 2fr 1fr 1fr 28px'

function CrossTable({ rows, revealStart, revealedCount }: { rows: CrossRow[], revealStart: number, revealedCount: number }) {
  const failCount = rows.filter(r => !r.ok).length
  const allOk = failCount === 0
  return (
    <div className="overflow-hidden">
      <div className="grid border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/40"
        style={{ gridTemplateColumns: CROSS_COLS }}>
        {['Field', 'QC path', 'QC value', 'PB value', ''].map((h, i) => (
          <span key={i} className={`text-[8px] font-bold uppercase tracking-[0.14em] text-gray-500 dark:text-gray-400 px-3 py-[7px] ${i >= 2 && i < 4 ? 'text-right' : ''} ${i > 0 ? 'border-l border-gray-200 dark:border-gray-700' : ''}`}>{h}</span>
        ))}
      </div>
      {rows.map((row, i) => {
        const revealed = (revealStart + i) < revealedCount
        const isFail = !row.ok
        const diff = Math.abs(Number(row.qcVal) - Number(row.pbVal))
        const isAmber = row.ok && diff > 0.000001
        return (
          <div key={i} className={`grid border-b border-gray-100 dark:border-gray-800 last:border-0 ${isAmber ? 'bg-amber-50/60 dark:bg-amber-900/10' : isFail ? 'bg-red-50/50 dark:bg-red-900/10' : ''}`}
            style={{ gridTemplateColumns: CROSS_COLS }}>
            <div className="px-3 py-[11px] flex items-center border-r border-gray-100 dark:border-gray-800 min-w-0">
              <span className={`text-[11px] font-semibold truncate ${isFail ? 'text-red-600 dark:text-red-400' : isAmber ? 'text-amber-600 dark:text-amber-400' : 'text-gray-700 dark:text-gray-200'}`}>{row.field}</span>
            </div>
            <div className="px-3 py-[11px] flex flex-col gap-[2px] border-r border-gray-100 dark:border-gray-800 min-w-0">
              <span className="text-[10px] text-blue-500 dark:text-blue-400 font-mono truncate">{row.qcPath}</span>
              <span className="text-[10px] text-purple-500 dark:text-purple-400 font-mono truncate">{row.pbPath}</span>
              {isAmber && <span className="font-mono text-[9px] text-amber-600 dark:text-amber-400">Δ {diff.toFixed(6)} · {row.note ?? 'rounding'}</span>}
            </div>
            <div className="px-3 py-[11px] flex items-center justify-end border-r border-gray-100 dark:border-gray-800">
              <span className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 font-mono">{fmtVal(row.qcVal)}</span>
            </div>
            <div className="px-3 py-[11px] flex items-center justify-end">
              <span className={`text-[11px] font-semibold font-mono ${isFail ? 'text-red-600 dark:text-red-400' : isAmber ? 'text-amber-600 dark:text-amber-400' : 'text-purple-600 dark:text-purple-400'}`}>{fmtVal(row.pbVal)}</span>
            </div>
            <div className="flex items-center justify-center">
              {revealed
                ? (row.ok ? <CheckCircle2 className={`size-3.5 ${isAmber ? 'text-amber-500' : 'text-emerald-500'}`} /> : <XCircle className="size-3.5 text-red-500" />)
                : <Loader2 className="size-3 animate-spin text-gray-300 dark:text-gray-600" />}
            </div>
          </div>
        )
      })}
      <div className={`flex items-center justify-between border-t border-gray-200 dark:border-gray-700 px-3 py-[7px] ${allOk ? 'bg-emerald-50/50 dark:bg-emerald-900/10' : 'bg-red-50/50 dark:bg-red-900/10'}`}>
        <div className={`flex items-center gap-[5px] text-[11px] font-semibold ${allOk ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
          {allOk ? <CheckCircle2 className="size-3.5" /> : <XCircle className="size-3.5" />}
          {allOk ? 'All fields match' : `${failCount} mismatch${failCount > 1 ? 'es' : ''}`}
        </div>
        <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-gray-400 dark:text-gray-500">{rows.length} checks</span>
      </div>
    </div>
  )
}

function PBChecksTable({ rows, revealStart, revealedCount }: { rows: CheckRow[], revealStart: number, revealedCount: number }) {
  const failCount = rows.filter(r => !r.ok).length
  const allOk = failCount === 0
  return (
    <div className="overflow-hidden">
      <div className="grid border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/40"
        style={{ gridTemplateColumns: CHECK_COLS }}>
        {['Field', 'Formula = Calculation', 'Computed', 'PB Stored', ''].map((h, i) => (
          <span key={i} className={`text-[8px] font-bold uppercase tracking-[0.14em] text-gray-500 dark:text-gray-400 px-3 py-[7px] ${i >= 2 && i < 4 ? 'text-right' : ''} ${i > 0 ? 'border-l border-gray-200 dark:border-gray-700' : ''}`}>{h}</span>
        ))}
      </div>
      {rows.map((row, i) => {
        const revealed = (revealStart + i) < revealedCount
        const diff = Math.abs(row.expected - row.actual)
        const isAmber = row.ok && diff > 0.000001
        const isFail = !row.ok
        return (
          <div key={i} className={`grid border-b border-gray-100 dark:border-gray-800 last:border-0 ${isAmber ? 'bg-amber-50/60 dark:bg-amber-900/10' : isFail ? 'bg-red-50/50 dark:bg-red-900/10' : ''}`}
            style={{ gridTemplateColumns: CHECK_COLS }}>
            <div className="px-3 py-[11px] flex items-center border-r border-gray-100 dark:border-gray-800">
              <span className={`text-[11px] font-semibold truncate ${isFail ? 'text-red-600 dark:text-red-400' : isAmber ? 'text-amber-600 dark:text-amber-400' : 'text-gray-700 dark:text-gray-200'}`}>{row.field}</span>
            </div>
            <div className="px-3 py-[11px] flex flex-col gap-[3px] border-r border-gray-100 dark:border-gray-800">
              <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-200 leading-snug">{row.formula}</span>
              {row.calc && <span className="text-[11px] text-gray-500 dark:text-gray-400 leading-snug">= {row.calc}</span>}
              {isAmber && <span className="font-mono text-[9px] text-amber-600 dark:text-amber-400">Δ {diff.toFixed(6)} · {row.note ?? 'rounding'}</span>}
            </div>
            <div className="px-3 py-[11px] flex items-center justify-end border-r border-gray-100 dark:border-gray-800">
              <span className={`text-[11px] font-semibold ${isAmber ? 'text-amber-600 dark:text-amber-400' : isFail ? 'text-red-500 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`}>{fmtVal(row.expected)}</span>
            </div>
            <div className="px-3 py-[11px] flex items-center justify-end">
              <span className={`text-[11px] font-semibold ${isFail ? 'text-red-600 dark:text-red-400' : isAmber ? 'text-amber-600 dark:text-amber-400' : 'text-gray-700 dark:text-gray-200'}`}>{fmtVal(row.actual)}</span>
            </div>
            <div className="flex items-center justify-center">
              {revealed
                ? (row.ok ? <CheckCircle2 className={`size-3.5 ${isAmber ? 'text-amber-500' : 'text-emerald-500'}`} /> : <XCircle className="size-3.5 text-red-500" />)
                : <Loader2 className="size-3 animate-spin text-gray-300 dark:text-gray-600" />}
            </div>
          </div>
        )
      })}
      <div className={`flex items-center justify-between border-t border-gray-200 dark:border-gray-700 px-3 py-[7px] ${allOk ? 'bg-emerald-50/50 dark:bg-emerald-900/10' : 'bg-red-50/50 dark:bg-red-900/10'}`}>
        <div className={`flex items-center gap-[5px] text-[11px] font-semibold ${allOk ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
          {allOk ? <CheckCircle2 className="size-3.5" /> : <XCircle className="size-3.5" />}
          {allOk ? 'All checks passed' : `${failCount} check${failCount > 1 ? 's' : ''} failed`}
        </div>
        <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-gray-400 dark:text-gray-500">{rows.length} checks</span>
      </div>
    </div>
  )
}

// ── Line section — QC line paired with PB line ────────────────────────────────
function LineSection({ idx, qcLine, pbLine, crossRows, pbCheckRows, crossStart, pbCheckStart, revealedCount, isFirst }: {
  idx: number; qcLine: any; pbLine: any; crossRows: CrossRow[]; pbCheckRows: CheckRow[]
  crossStart: number; pbCheckStart: number; revealedCount: number; isFirst: boolean
}) {
  const allOk = [...crossRows, ...pbCheckRows].every(r => r.ok)
  const failCount = [...crossRows, ...pbCheckRows].filter(r => !r.ok).length
  const [open, setOpen] = useState(isFirst || !allOk)
  useEffect(() => { if (!allOk) setOpen(true) }, [allOk])

  const specs = [
    { label: 'Item', value: `#${qcLine.item_ref_id}` },
    { label: 'Rate', value: `₹${Number(qcLine.base_rate).toLocaleString('en-IN')}` },
    { label: 'GRN qty', value: String(qcLine.grn_qty) },
    { label: 'GST type', value: pbLine.gst_type || '—' },
    { label: 'GST rate', value: pbLine.tax_rate != null ? `${pbLine.tax_rate}%` : '—' },
    { label: 'Deduction', value: `${qcLine.deduction_percent}%` },
  ]

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <button onClick={() => setOpen(v => !v)} className="w-full flex items-center gap-2 px-3 py-2.5 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer">
        <span className="text-[9px] font-bold uppercase tracking-[0.13em] text-gray-400 dark:text-gray-500 border border-gray-200 dark:border-gray-700 rounded px-1.5 py-0.5 bg-white dark:bg-gray-800 shrink-0">Line {idx + 1}</span>
        <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200 flex-1 text-left">Item <span className="font-mono font-normal text-gray-500 dark:text-gray-400">#{qcLine.item_ref_id}</span></span>
        <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${allOk ? 'text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/50 bg-emerald-50 dark:bg-emerald-900/10' : 'text-red-600 dark:text-red-400 border-red-200 dark:border-red-800/50 bg-red-50/50 dark:bg-red-900/10'}`}>
          {allOk ? <CheckCircle2 className="size-3" /> : <XCircle className="size-3" />}
          {allOk ? 'All passed' : `${failCount} failed`}
        </span>
        <span className="text-[9px] text-gray-400 dark:text-gray-600 shrink-0">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-px bg-gray-100 dark:bg-gray-700/40 border-b border-gray-200 dark:border-gray-700">
            {specs.map(({ label, value }) => (
              <div key={label} className="bg-white dark:bg-gray-800/40 px-2.5 py-2.5">
                <div className="text-[9px] font-bold uppercase tracking-[0.12em] text-gray-400 dark:text-gray-500 mb-1">{label}</div>
                <div className="font-mono text-[12px] font-semibold text-gray-800 dark:text-gray-100">{value}</div>
              </div>
            ))}
          </div>
          {/* QC → PB cross-checks */}
          <div className="flex items-center gap-2 px-3 pt-2 pb-1">
            <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-blue-500 dark:text-blue-400">QC → PB field match</span>
            <div className="flex-1 h-px bg-gray-100 dark:bg-gray-800" />
          </div>
          <CrossTable rows={crossRows} revealStart={crossStart} revealedCount={revealedCount} />
          {/* PB internal checks */}
          <div className="border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 px-3 pt-2 pb-1">
              <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-purple-500 dark:text-purple-400">PB internal (GST + payable)</span>
              <div className="flex-1 h-px bg-gray-100 dark:bg-gray-800" />
            </div>
            <PBChecksTable rows={pbCheckRows} revealStart={pbCheckStart} revealedCount={revealedCount} />
          </div>
        </div>
      )}
    </div>
  )
}

// ── Header cross-checks ───────────────────────────────────────────────────────
function HeaderCrossTable({ qcData, pbData }: { qcData: any; pbData: any }) {
  const rows = [
    { field: 'supplier', qcPath: 'supplier_ref_id', pbPath: 'supplier_ref_id', qcVal: qcData.supplier_ref_id, pbVal: pbData.supplier_ref_id },
    { field: 'grn_ref',  qcPath: 'grn_ref_id_id',  pbPath: 'grn_ref_id_id',  qcVal: qcData.grn_ref_id_id,  pbVal: pbData.grn_ref_id_id },
    { field: 'po_ref',   qcPath: 'po_ref_id_id',   pbPath: 'po_ref_id_id',   qcVal: qcData.po_ref_id_id,   pbVal: pbData.po_ref_id_id },
  ].map(r => ({ ...r, ok: String(r.qcVal) === String(r.pbVal) }))

  const allOk = rows.every(r => r.ok)
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
        <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-gray-400 dark:text-gray-500">Header links</span>
        <div className="flex-1 h-px bg-gray-100 dark:bg-gray-800" />
        <span className={`text-[10px] font-semibold ${allOk ? 'text-emerald-500' : 'text-red-500'}`}>{allOk ? 'Linked correctly' : 'Link mismatch'}</span>
      </div>
      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        {rows.map((row, i) => (
          <div key={i} className={`flex items-center gap-3 px-3 py-2.5 ${row.ok ? '' : 'bg-red-50/50 dark:bg-red-900/10'}`}>
            <span className="text-[11px] font-semibold text-gray-600 dark:text-gray-300 w-20 shrink-0">{row.field}</span>
            <span className="text-[11px] font-mono text-blue-600 dark:text-blue-400 flex-1">QC: {String(row.qcVal)}</span>
            <span className="text-[11px] font-mono text-purple-600 dark:text-purple-400 flex-1">PB: {String(row.pbVal)}</span>
            {row.ok ? <CheckCircle2 className="size-3.5 text-emerald-500 shrink-0" /> : <XCircle className="size-3.5 text-red-500 shrink-0" />}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export function QCPBCrossCheck({ erpToken, erpTenantId, onNeedsToken, onClearToken }: Props) {
  const { token, tenantId, localToken, setLocalToken, localTenantId, setLocalTenantId, handleAuthError } = useErpToken(erpToken, erpTenantId)

  const [showTokenInput, setShowTokenInput] = useState(false)
  const [qcList, setQcList] = useState<QCListItem[]>([])
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError] = useState('')
  const [search, setSearch] = useState('')

  const [selectedQC, setSelectedQC] = useState<QCListItem | null>(null)
  const [showList, setShowList] = useState(true)
  const [qcData, setQcData] = useState<any>(null)
  const [pbData, setPbData] = useState<any>(null)
  const [fetching, setFetching] = useState(false)
  const [fetchError, setFetchError] = useState('')
  const [pbLoading, setPbLoading] = useState(false)
  const [pbError, setPbError] = useState('')

  const [revealedCount, setRevealedCount] = useState(0)

  const loadList = useCallback(async () => {
    if (!token || !tenantId) return
    setListLoading(true); setListError('')
    try {
      setQcList(await fetchQCList(token, tenantId))
    } catch (err) {
      if (!handleAuthError(err)) setListError(err instanceof Error ? err.message : String(err))
    } finally { setListLoading(false) }
  }, [token, tenantId, handleAuthError])

  const loadListRef = useRef(loadList)
  useEffect(() => { loadListRef.current = loadList }, [loadList])
  const hasToken = !!token && !!tenantId
  useEffect(() => { if (!hasToken) return; loadListRef.current() }, [hasToken])

  const handleSelect = async (qc: QCListItem) => {
    setSelectedQC(qc); setShowList(false)
    setFetching(true); setFetchError(''); setQcData(null); setPbData(null); setPbError('')
    try {
      const data = await fetchQC(token!, tenantId, String(qc.id))
      if (data.error) throw new Error(data.error)
      setQcData(data)
      setPbLoading(true)
      fetchPBByQC(token!, tenantId, String(qc.id))
        .then(pb => {
          if (!pb) setPbError('No Purchase Booking found for this QC')
          else if (pb.error) setPbError(pb.error)
          else setPbData(pb)
        })
        .catch(err => setPbError(err instanceof Error ? err.message : String(err)))
        .finally(() => setPbLoading(false))
    } catch (err) {
      if (!handleAuthError(err)) setFetchError(err instanceof Error ? err.message : String(err))
    } finally { setFetching(false) }
  }

  const filtered = qcList.filter(qc => {
    const q = search.toLowerCase()
    return !q || qc.ref_no.toLowerCase().includes(q) || qc.supplier.toLowerCase().includes(q)
  })

  // Build all rows for reveal animation
  const qcLines: any[] = qcData?.qc_details ?? []
  const pbLines: any[] = pbData?.purchase_booking_details ?? []

  const allSections = qcLines.map((qcLine, i) => {
    const pbLine = pbLines[i] ?? {}
    const crossRows = buildCrossRows(qcLine, pbLine)
    const pbCheckRows = buildPBChecks(pbData ?? {}, pbLine)
    return { qcLine, pbLine, crossRows, pbCheckRows }
  })

  const totalRows = allSections.reduce((s, sec) => s + sec.crossRows.length + sec.pbCheckRows.length, 0)

  useEffect(() => {
    if (!qcData || !pbData) { setRevealedCount(0); return }
    setRevealedCount(0)
    let count = 0
    const iv = setInterval(() => {
      count++; setRevealedCount(count)
      if (count >= totalRows) clearInterval(iv)
    }, 60)
    return () => clearInterval(iv)
  }, [qcData, pbData])

  const allOk = allSections.length > 0 && allSections.every(s => [...s.crossRows, ...s.pbCheckRows].every(r => r.ok))

  return (
    <div className="relative flex flex-col h-full min-h-0">
      <div className="bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col min-h-0 flex-1 overflow-hidden">

        {/* Token panel */}
        {showTokenInput && (
          <div className="p-4 overflow-y-auto flex-1 min-h-0 space-y-3">
            <div className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
              <Label className="text-[11px] text-orange-600 dark:text-orange-400 mb-1.5 block font-medium">ERP Credentials</Label>
              <div className="flex items-center gap-2 mb-2">
                <Input type="password" value={localToken} onChange={e => setLocalToken(e.target.value)}
                  placeholder="Paste your Bearer token here..."
                  className={`h-9 text-[12px] flex-1 ${localToken && localToken.length > 100 ? 'border-green-400' : localToken ? 'border-red-400' : ''}`} />
              </div>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {[{ id: '795', name: 'Jalpan Builders' }, { id: '666', name: 'Jay Kisan Ltd' }, { id: '686', name: 'Agristack Company' }, { id: '903', name: 'Tenant 903' }].map(t => (
                  <button key={t.id} onClick={() => setLocalTenantId(t.id)}
                    className={`px-2 py-0.5 rounded-full text-[11px] font-medium border transition-colors cursor-pointer ${localTenantId === t.id ? 'bg-orange-500 text-white border-orange-500' : 'bg-white dark:bg-gray-800 text-orange-600 dark:text-orange-400 border-orange-300 dark:border-orange-700 hover:bg-orange-50'}`}>
                    {t.id} · {t.name}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <Input type="text" value={localTenantId} onChange={e => setLocalTenantId(e.target.value)} placeholder="Tenant ID" className="h-9 text-[12px] w-36" />
                <Button onClick={() => { setShowTokenInput(false); loadList() }} variant="ghost" size="sm" className="h-9 text-[12px] cursor-pointer">Done</Button>
              </div>
            </div>
          </div>
        )}

        {/* Main content */}
        {!showTokenInput && (
          <div className="p-4 overflow-y-auto flex-1 min-h-0 space-y-3">
            {listError && <p className="text-[11px] text-red-500">{listError}</p>}
            {listLoading && qcList.length === 0 && (
              <LoadingCard message="FETCHING" steps={[{ label: 'Fetching quality checks', done: false }]} />
            )}
            {!listLoading && qcList.length === 0 && !listError && (
              <p className="text-[12px] text-gray-400 py-2">No QC records found.</p>
            )}

            {/* QC list */}
            {qcList.length > 0 && showList && (
              <>
                <Label className="text-[11px] text-gray-700 dark:text-gray-300">Select Quality Check to cross-check with PB</Label>
                <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by ref no or supplier…" className="h-8 text-[12px]" />
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden max-h-64 overflow-y-auto">
                  {filtered.map((qc, i) => (
                    <button key={qc.id ?? i} onClick={() => handleSelect(qc)}
                      className="w-full flex items-start gap-2 px-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 hover:bg-[#3F51B5]/5 dark:hover:bg-[#3F51B5]/10 transition-colors text-left cursor-pointer">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100 shrink-0">{qc.ref_no}</span>
                          {qc.amount && <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0 font-medium">₹{Number(qc.amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>}
                        </div>
                        {qc.supplier && (
                          <div className="mt-0.5 flex items-center justify-between gap-2">
                            <span className="text-[11px] text-gray-600 dark:text-gray-300 truncate font-medium">{qc.supplier}</span>
                            {qc.date && <span className="text-[10px] text-gray-400 dark:text-gray-500 shrink-0">{qc.date}</span>}
                          </div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </>
            )}

            {/* Results */}
            {!showList && selectedQC && (
              <div className="space-y-4">
                {/* Nav */}
                <div className="flex items-center gap-2">
                  <button onClick={() => { setShowList(true); setQcData(null); setPbData(null); setSelectedQC(null); setFetchError(''); setPbError('') }}
                    className="flex items-center gap-1 text-[11px] h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 hover:text-[#3F51B5] hover:border-[#3F51B5]/50 transition-colors cursor-pointer">
                    <RefreshCw className="size-3" /> Change
                  </button>
                  {!fetching && !pbLoading && qcData && pbData && (
                    <span className={`flex items-center gap-1 text-[11px] font-medium ${allOk ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {allOk ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      {allOk ? 'QC ↔ PB fully consistent' : 'Discrepancies found'}
                    </span>
                  )}
                </div>

                {/* QC + PB header */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg border border-blue-200 dark:border-blue-800/50 p-3 bg-blue-50/40 dark:bg-blue-900/10">
                    <div className="text-[9px] font-bold uppercase tracking-widest text-blue-400 mb-1">QC</div>
                    <div className="font-mono font-bold text-[13px] text-gray-800 dark:text-gray-100">{selectedQC.ref_no}</div>
                    <div className="text-[11px] text-gray-500 mt-0.5">{selectedQC.date} · {selectedQC.supplier}</div>
                    {qcData && <div className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 mt-1">₹{Number(qcData.total_txn_currency_amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>}
                  </div>
                  <div className={`rounded-lg border p-3 ${pbData ? 'border-purple-200 dark:border-purple-800/50 bg-purple-50/40 dark:bg-purple-900/10' : 'border-gray-200 dark:border-gray-700 bg-gray-50/40 dark:bg-gray-800/20'}`}>
                    <div className="text-[9px] font-bold uppercase tracking-widest text-purple-400 mb-1">PB</div>
                    {pbLoading && <div className="flex items-center gap-1.5 text-[11px] text-gray-400"><Loader2 className="size-3 animate-spin" />Finding linked PB…</div>}
                    {pbError && <div className="flex items-center gap-1.5 text-[11px] text-amber-600 dark:text-amber-400"><AlertTriangle className="size-3" />{pbError}</div>}
                    {pbData && <>
                      <div className="font-mono font-bold text-[13px] text-gray-800 dark:text-gray-100">{pbData.transaction_ref_no}</div>
                      <div className="text-[11px] text-gray-500 mt-0.5">{pbData.transaction_date}</div>
                      <div className="text-[11px] font-semibold text-purple-600 dark:text-purple-400 mt-1">₹{Number(pbData.txn_currency_total_amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>
                    </>}
                  </div>
                </div>

                {fetching && <LoadingCard message="FETCHING" steps={[{ label: 'Fetching QC detail', done: false }]} />}
                {fetchError && <div className="flex items-center gap-2 text-[12px] text-red-600"><AlertTriangle className="w-4 h-4 shrink-0" />{fetchError}</div>}

                {qcData && pbData && (
                  <>
                    <HeaderCrossTable qcData={qcData} pbData={pbData} />
                    {allSections.map((sec, idx) => {
                      let offset = 0
                      for (let j = 0; j < idx; j++) offset += allSections[j].crossRows.length + allSections[j].pbCheckRows.length
                      return (
                        <LineSection key={idx} idx={idx}
                          qcLine={sec.qcLine} pbLine={sec.pbLine}
                          crossRows={sec.crossRows} pbCheckRows={sec.pbCheckRows}
                          crossStart={offset} pbCheckStart={offset + sec.crossRows.length}
                          revealedCount={revealedCount} isFirst={idx === 0} />
                      )
                    })}
                  </>
                )}

                {qcData && !pbLoading && !pbData && !pbError && (
                  <div className="text-[12px] text-gray-400 py-2">No PB linked to this QC yet.</div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Bottom bar */}
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 shrink-0 flex items-center gap-3">
          {!token ? (
            <Button onClick={() => setShowTokenInput(true)} variant="outline" size="sm" className="h-8 text-[12px] gap-1.5 cursor-pointer">
              <Key className="size-3" /> Set Token
            </Button>
          ) : (
            <>
              <button onClick={loadList} disabled={listLoading}
                className="text-[11px] text-[#3F51B5] dark:text-[#7986CB] flex items-center gap-1 hover:underline cursor-pointer disabled:opacity-50">
                <RefreshCw className={`size-3 ${listLoading ? 'animate-spin' : ''}`} /> Refresh
              </button>
              <button onClick={() => setShowTokenInput(true)}
                className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 hover:text-red-500 transition-colors cursor-pointer">
                <CheckCircle2 className="size-3" /> Token set · Change
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
