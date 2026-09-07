'use client'

import React, { useState, useCallback, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { CheckCircle2, XCircle, Loader2, AlertTriangle, RefreshCw, Key, CheckSquare, Square, ListChecks, X, Eye } from 'lucide-react'
import { fetchQC } from '@/lib/api'
import { fetchPBList, fetchPBById, resolveRefs, type PBCrossListItem, type ResolvedRefs } from '@/lib/api'

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

// Match PB lines to QC lines by item_ref_id; fall back to positional if no match found
function matchPBLine(pbLines: any[], qcLine: any, fallbackIdx: number): any {
  const match = pbLines.find(pb => String(pb.item_ref_id) === String(qcLine.item_ref_id))
  return match ?? pbLines[fallbackIdx] ?? {}
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
function LineSection({ idx, qcLine, pbLine, crossRows, pbCheckRows, crossStart, pbCheckStart, revealedCount, isFirst, itemName }: {
  idx: number; qcLine: any; pbLine: any; crossRows: CrossRow[]; pbCheckRows: CheckRow[]
  crossStart: number; pbCheckStart: number; revealedCount: number; isFirst: boolean; itemName?: string
}) {
  const allOk = [...crossRows, ...pbCheckRows].every(r => r.ok)
  const failCount = [...crossRows, ...pbCheckRows].filter(r => !r.ok).length
  const [open, setOpen] = useState(isFirst || !allOk)
  useEffect(() => { if (!allOk) setOpen(true) }, [allOk])

  const specs = [
    { label: 'Item', value: itemName ? `#${qcLine.item_ref_id} · ${itemName}` : `#${qcLine.item_ref_id}` },
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
        <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200 flex-1 text-left">
          Item <span className="font-mono font-normal text-gray-500 dark:text-gray-400">#{qcLine.item_ref_id}</span>
          {itemName && <span className="ml-1.5 font-normal text-gray-500 dark:text-gray-400 text-[11px]">· {itemName}</span>}
        </span>
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
function HeaderCrossTable({ qcData, pbData, refs }: { qcData: any; pbData: any; refs: ResolvedRefs }) {
  const rows = [
    { field: 'supplier', qcVal: qcData.supplier_ref_id, pbVal: pbData.supplier_ref_id, resolvedName: refs.supplier },
    { field: 'grn_ref',  qcVal: qcData.grn_ref_id_id,  pbVal: pbData.grn_ref_id_id,   resolvedName: refs.grn_ref },
    { field: 'po_ref',   qcVal: qcData.po_ref_id_id,   pbVal: pbData.po_ref_id_id,    resolvedName: refs.po_ref },
  ].map(r => ({ ...r, ok: String(r.qcVal) === String(r.pbVal) }))

  const allOk = rows.every(r => r.ok)
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* Table header */}
      <div className="grid grid-cols-[6rem_1fr_1fr_1.5rem] gap-0 px-3 py-1.5 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
        <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-gray-400 dark:text-gray-500 self-center">Header links</span>
        <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-blue-400 dark:text-blue-500 px-2">QC</span>
        <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-purple-400 dark:text-purple-500 px-2">PB</span>
        <span className={`text-[10px] font-semibold self-center text-right ${allOk ? 'text-emerald-500' : 'text-red-500'}`}>
          {allOk ? '✓' : '✗'}
        </span>
      </div>
      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        {rows.map((row, i) => (
          <div key={i} className={`grid grid-cols-[6rem_1fr_1fr_1.5rem] gap-0 px-3 py-2 ${row.ok ? '' : 'bg-red-50/50 dark:bg-red-900/10'}`}>
            <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 self-start pt-0.5">{row.field}</span>
            <div className="px-2 min-w-0">
              <div className="text-[11px] font-medium text-gray-700 dark:text-gray-200 truncate">
                {row.resolvedName || <span className="font-mono text-blue-600 dark:text-blue-400">{String(row.qcVal)}</span>}
              </div>
            </div>
            <div className="px-2 min-w-0">
              <div className="text-[11px] font-medium text-gray-700 dark:text-gray-200 truncate">
                {row.resolvedName || <span className="font-mono text-purple-600 dark:text-purple-400">{String(row.pbVal)}</span>}
              </div>
            </div>
            <div className="self-start pt-0.5">
              {row.ok ? <CheckCircle2 className="size-3.5 text-emerald-500" /> : <XCircle className="size-3.5 text-red-500" />}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

type BulkCrossResult = {
  pb: PBCrossListItem
  ok: boolean
  error?: string
  failCount?: number
  done: boolean
  qcData?: any
  pbData?: any
}

function countCrossCheckFails(qcData: any, pbData: any): number {
  const headerRows = [
    { qcVal: qcData.supplier_ref_id, pbVal: pbData.supplier_ref_id },
    { qcVal: qcData.grn_ref_id_id,   pbVal: pbData.grn_ref_id_id },
    { qcVal: qcData.po_ref_id_id,    pbVal: pbData.po_ref_id_id },
  ]
  let fails = headerRows.filter(r => String(r.qcVal) !== String(r.pbVal)).length
  const qcLines: any[] = qcData.qc_details ?? []
  const pbLines: any[] = pbData.purchase_booking_details ?? []
  for (let i = 0; i < qcLines.length; i++) {
    const pbLine = matchPBLine(pbLines, qcLines[i], i)
    const crossRows = buildCrossRows(qcLines[i], pbLine)
    const pbCheckRows = buildPBChecks(pbData, pbLine)
    fails += [...crossRows, ...pbCheckRows].filter(r => !r.ok).length
  }
  return fails
}

// ── Main component ────────────────────────────────────────────────────────────
export function QCPBCrossCheck({ erpToken, erpTenantId, onNeedsToken, onClearToken }: Props) {
  const { token, tenantId, localToken, setLocalToken, localTenantId, setLocalTenantId, handleAuthError } = useErpToken(erpToken, erpTenantId)

  const [showTokenInput, setShowTokenInput] = useState(false)
  const [pbList, setPbList] = useState<PBCrossListItem[]>([])
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError] = useState('')
  const [search, setSearch] = useState('')

  const [selectedPB, setSelectedPB] = useState<PBCrossListItem | null>(null)
  const [showList, setShowList] = useState(true)
  const [qcData, setQcData] = useState<any>(null)
  const [pbData, setPbData] = useState<any>(null)
  const [refs, setRefs] = useState<ResolvedRefs>({})
  const [refsLoading, setRefsLoading] = useState(false)
  const [fetching, setFetching] = useState(false)
  const [fetchError, setFetchError] = useState('')

  const [revealedCount, setRevealedCount] = useState(0)

  // Multi-select / bulk run state
  const [multiSelect, setMultiSelect] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set())
  const [bulkResults, setBulkResults] = useState<BulkCrossResult[]>([])
  const [bulkRunning, setBulkRunning] = useState(false)
  const [bulkProgress, setBulkProgress] = useState(0)
  const [bulkOpen, setBulkOpen] = useState(false)

  const bulkResultsRef = useRef<HTMLDivElement>(null)
  const bulkRowRefs = useRef<(HTMLDivElement | null)[]>([])
  const bulkRunBtnRef = useRef<HTMLDivElement>(null)
  const bulkAbort = useRef(false)
  const bulkFromView = useRef(false)
  const bulkViewIndex = useRef(0)

  const loadList = useCallback(async () => {
    if (!token || !tenantId) return
    setListLoading(true); setListError('')
    try {
      setPbList(await fetchPBList(token, tenantId))
    } catch (err) {
      if (!handleAuthError(err)) setListError(err instanceof Error ? err.message : String(err))
    } finally { setListLoading(false) }
  }, [token, tenantId, handleAuthError])

  const loadListRef = useRef(loadList)
  useEffect(() => { loadListRef.current = loadList }, [loadList])
  const hasToken = !!token && !!tenantId
  useEffect(() => { if (!hasToken) return; loadListRef.current() }, [hasToken])

  // Fetch both PB detail and QC detail for a selected PB listing row
  const handleSelect = async (pb: PBCrossListItem) => {
    setSelectedPB(pb); setShowList(false)
    setFetching(true); setFetchError(''); setQcData(null); setPbData(null); setRefs({})
    try {
      const pbDetail = await fetchPBById(token!, tenantId, String(pb.id))
      if (pbDetail.error) throw new Error(pbDetail.error)
      setPbData(pbDetail)
      const qcNumericId = pbDetail.qc_ref_id_id
      if (!qcNumericId) throw new Error('PB has no linked QC id')
      const qcDetail = await fetchQC(token!, tenantId, String(qcNumericId))
      if (qcDetail.error) throw new Error(qcDetail.error)
      setQcData(qcDetail)
      // Resolve IDs to display names — gate the header table render until done
      const itemIds = (qcDetail.qc_details ?? []).map((l: any) => l.item_ref_id).filter(Boolean)
      setRefsLoading(true)
      resolveRefs(token!, tenantId, {
        supplier_id: qcDetail.supplier_ref_id ?? null,
        grn_id: qcDetail.grn_ref_id_id ?? null,
        po_id: qcDetail.po_ref_id_id ?? null,
        item_ids: itemIds,
      }).then(r => setRefs(r)).catch(() => {}).finally(() => setRefsLoading(false))
    } catch (err) {
      if (!handleAuthError(err)) setFetchError(err instanceof Error ? err.message : String(err))
    } finally { setFetching(false) }
  }

  const handleBulkRun = async () => {
    if (!token || !tenantId || selectedIds.size === 0) return
    const selected = pbList.filter(pb => selectedIds.has(pb.id ?? pb.ref_no))
    bulkAbort.current = false
    bulkRowRefs.current = []
    setBulkRunning(true)
    setBulkProgress(0)
    setBulkOpen(true)
    const results: BulkCrossResult[] = selected.map(pb => ({ pb, ok: false, done: false }))
    setBulkResults([...results])
    setTimeout(() => bulkResultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 80)
    for (let i = 0; i < selected.length; i++) {
      if (bulkAbort.current) break
      setTimeout(() => bulkRowRefs.current[i]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50)
      const pb = selected[i]
      try {
        const pbDetail = await fetchPBById(token!, tenantId, String(pb.id))
        if (pbDetail.error) throw new Error(pbDetail.error)
        const qcNumericId = pbDetail.qc_ref_id_id
        if (!qcNumericId) throw new Error('No QC linked')
        const qcDetail = await fetchQC(token!, tenantId, String(qcNumericId))
        if (qcDetail.error) throw new Error(qcDetail.error)
        const failCount = countCrossCheckFails(qcDetail, pbDetail)
        results[i] = { pb, ok: failCount === 0, failCount, done: true, qcData: qcDetail, pbData: pbDetail }
      } catch (err) {
        results[i] = { pb, ok: false, error: err instanceof Error ? err.message : String(err), done: true }
      }
      setBulkResults([...results])
      setBulkProgress(i + 1)
    }
    setBulkRunning(false)
  }

  const filtered = pbList.filter(pb => {
    const q = search.toLowerCase()
    return !q || pb.ref_no.toLowerCase().includes(q) || pb.supplier.toLowerCase().includes(q) || pb.qc_ref.toLowerCase().includes(q)
  })

  const sortedBulkResults = [...bulkResults].sort((a, b) => {
    if (!a.done && b.done) return 1
    if (a.done && !b.done) return -1
    if (a.ok && !b.ok) return 1
    if (!a.ok && b.ok) return -1
    return 0
  })

  // Build all rows for reveal animation
  const qcLines: any[] = qcData?.qc_details ?? []
  const pbLines: any[] = pbData?.purchase_booking_details ?? []

  const allSections = qcLines.map((qcLine, i) => {
    const pbLine = matchPBLine(pbLines, qcLine, i)
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
                <Input type="text" value={localToken} onChange={e => setLocalToken(e.target.value)}
                  placeholder="Paste your Bearer token here..."
                  autoComplete="off"
                  style={{ WebkitTextSecurity: 'disc' } as React.CSSProperties}
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
                <Input type="text" value={localTenantId} onChange={e => setLocalTenantId(e.target.value)} placeholder="Tenant ID" autoComplete="off" className="h-9 text-[12px] w-36" />
                <Button onClick={() => { setShowTokenInput(false); loadList() }} variant="ghost" size="sm" className="h-9 text-[12px] cursor-pointer">Done</Button>
              </div>
            </div>
          </div>
        )}

        {/* Main content */}
        {!showTokenInput && (
          <div className="p-4 overflow-y-auto flex-1 min-h-0 space-y-3">
            {listError && <p className="text-[11px] text-red-500">{listError}</p>}
            {listLoading && pbList.length === 0 && (
              <LoadingCard message="FETCHING" steps={[{ label: 'Fetching purchase bookings with linked QC', done: false }]} />
            )}
            {!listLoading && pbList.length === 0 && !listError && (
              <p className="text-[12px] text-gray-400 py-2">No Purchase Bookings with a linked QC found. Click Refresh or check your token.</p>
            )}

            {/* PB list */}
            {pbList.length > 0 && showList && (
              <>
                <div className="flex items-center justify-between">
                  <Label className="text-[11px] text-gray-700 dark:text-gray-300">Select Purchase Booking to cross-check</Label>
                  <button
                    onClick={() => { setMultiSelect(v => !v); setSelectedIds(new Set()); setBulkResults([]); setBulkOpen(false) }}
                    className={`text-[11px] flex items-center gap-1 px-2 py-0.5 rounded border transition-colors cursor-pointer ${multiSelect ? 'border-[#3F51B5] text-[#3F51B5] bg-[#3F51B5]/5' : 'border-gray-200 dark:border-gray-700 text-gray-500 hover:border-[#3F51B5] hover:text-[#3F51B5]'}`}>
                    <ListChecks className="size-3" /> Multi-select
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by PB ref, QC ref or supplier…" className="h-8 text-[12px] flex-1" />
                  {multiSelect && (() => {
                    const allSel = filtered.length > 0 && filtered.every(pb => selectedIds.has(pb.id ?? pb.ref_no))
                    return (
                      <button onClick={() => allSel ? setSelectedIds(new Set()) : setSelectedIds(new Set(filtered.map(pb => pb.id ?? pb.ref_no)))}
                        className="text-[11px] flex items-center gap-1 px-2 py-1 rounded border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:border-[#3F51B5] transition-colors cursor-pointer shrink-0">
                        {allSel ? <CheckSquare className="size-3.5 text-[#3F51B5]" /> : <Square className="size-3.5" />}
                        {allSel ? 'Deselect all' : 'Select all'}
                      </button>
                    )
                  })()}
                </div>
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden max-h-64 overflow-y-auto">
                  {filtered.map((pb, i) => {
                    const pbKey = pb.id ?? pb.ref_no
                    const checked = selectedIds.has(pbKey)
                    return (
                      <div key={pb.id ?? i}
                        onClick={multiSelect ? () => setSelectedIds(prev => { const n = new Set(prev); n.has(pbKey) ? n.delete(pbKey) : n.add(pbKey); return n }) : undefined}
                        className={`flex items-start gap-2 px-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 hover:bg-[#3F51B5]/5 dark:hover:bg-[#3F51B5]/10 transition-colors ${multiSelect ? 'cursor-pointer' : ''} ${checked ? 'bg-[#3F51B5]/5 dark:bg-[#3F51B5]/10' : ''}`}>
                        {multiSelect && (
                          <button onClick={e => { e.stopPropagation(); setSelectedIds(prev => { const n = new Set(prev); n.has(pbKey) ? n.delete(pbKey) : n.add(pbKey); return n }) }}
                            className="mt-0.5 shrink-0 cursor-pointer text-[#3F51B5]">
                            {checked ? <CheckSquare className="size-3.5" /> : <Square className="size-3.5 text-gray-300 dark:text-gray-600" />}
                          </button>
                        )}
                        <button onClick={() => handleSelect(pb)} className="flex-1 text-left cursor-pointer">
                          <div className="flex items-center justify-between gap-3">
                            <span className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100 shrink-0">{pb.ref_no}</span>
                            {pb.amount && <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0 font-medium">₹{Number(pb.amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>}
                          </div>
                          <div className="mt-0.5 flex items-center justify-between gap-2">
                            <span className="text-[11px] text-gray-600 dark:text-gray-300 truncate font-medium">{pb.supplier}</span>
                            <span className="text-[10px] text-purple-400 dark:text-purple-500 shrink-0 font-mono">{pb.qc_ref}</span>
                          </div>
                          {pb.date && <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{pb.date}</div>}
                        </button>
                      </div>
                    )
                  })}
                </div>

                {/* Bulk action bar */}
                {multiSelect && selectedIds.size > 0 && (
                  <div ref={bulkRunBtnRef} className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-[#3F51B5]/5 border border-[#3F51B5]/20">
                    <span className="text-[12px] text-[#3F51B5] dark:text-[#7986CB] font-semibold">{selectedIds.size} PB{selectedIds.size > 1 ? 's' : ''} selected</span>
                    <div className="flex items-center gap-2">
                      {bulkRunning ? (
                        <div className="flex items-center gap-2">
                          <Loader2 className="size-3.5 animate-spin text-[#3F51B5]" />
                          <span className="text-[11px] text-gray-500">{bulkProgress} / {selectedIds.size}</span>
                          <button onClick={() => { bulkAbort.current = true }} className="text-[11px] text-red-500 hover:underline cursor-pointer">Stop</button>
                        </div>
                      ) : (
                        <Button onClick={handleBulkRun} size="sm" className="h-7 text-[11px] gap-1.5 cursor-pointer bg-[#3F51B5] hover:bg-[#303f9f]">
                          <ListChecks className="size-3" />Run All
                        </Button>
                      )}
                    </div>
                  </div>
                )}
                {/* Progress bar */}
                {bulkRunning && (
                  <div className="h-1 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
                    <div className="h-full bg-[#3F51B5] transition-all duration-300 rounded-full" style={{ width: `${(bulkProgress / selectedIds.size) * 100}%` }} />
                  </div>
                )}
                {/* Bulk results */}
                {bulkOpen && bulkResults.length > 0 && (
                  <div ref={bulkResultsRef} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                      <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">Bulk Results</span>
                      <div className="flex items-center gap-3 text-[10px] text-gray-500">
                        <span>{sortedBulkResults.filter(r => r.done && r.ok).length} passed · {sortedBulkResults.filter(r => r.done && !r.ok).length} failed</span>
                        {!bulkRunning && <button onClick={() => setBulkOpen(false)} className="text-gray-400 hover:text-gray-600 cursor-pointer ml-1"><X className="size-3" /></button>}
                      </div>
                    </div>
                    <div className="divide-y divide-gray-100 dark:divide-gray-800 max-h-72 overflow-y-auto">
                      {sortedBulkResults.map((r, i) => (
                        <div key={i} ref={el => { bulkRowRefs.current[i] = el }}
                          className={`flex items-center gap-2.5 px-3 py-2 ${!r.done ? 'opacity-50' : r.ok ? '' : 'bg-red-50/40 dark:bg-red-900/10'}`}>
                          <div className="shrink-0">
                            {!r.done ? <Loader2 className="size-3.5 animate-spin text-[#3F51B5]" /> : r.ok ? <CheckCircle2 className="size-3.5 text-emerald-500" /> : <XCircle className="size-3.5 text-red-500" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100">{r.pb.ref_no}</span>
                              <span className="text-[10px] text-purple-400 dark:text-purple-500 font-mono truncate">{r.pb.qc_ref}</span>
                            </div>
                            {r.done && !r.ok && (
                              <div className="text-[10px] text-red-500 dark:text-red-400 mt-0.5 truncate">
                                {r.error || (r.failCount != null ? `${r.failCount} field${r.failCount !== 1 ? 's' : ''} mismatched` : 'Cross-check failed')}
                              </div>
                            )}
                          </div>
                          {r.done && r.qcData && r.pbData && (
                            <button onClick={() => {
                              bulkFromView.current = true
                              bulkViewIndex.current = i
                              setSelectedPB(r.pb)
                              setShowList(false)
                              setQcData(r.qcData)
                              setPbData(r.pbData)
                              setFetchError('')
                            }} className="text-[10px] text-[#3F51B5] hover:underline shrink-0 cursor-pointer flex items-center gap-0.5">
                              <Eye className="size-3" />View
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Results */}
            {!showList && selectedPB && (
              <div className="space-y-4">
                {/* Nav */}
                <div className="flex items-center gap-2">
                  {bulkFromView.current ? (
                    <button onClick={() => {
                      const idx = bulkViewIndex.current
                      bulkFromView.current = false
                      setShowList(true); setQcData(null); setPbData(null); setSelectedPB(null); setFetchError(''); setRefs({}); setRefsLoading(false)
                      setTimeout(() => {
                        bulkResultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
                        setTimeout(() => bulkRowRefs.current[idx]?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 200)
                      }, 50)
                    }} className="flex items-center gap-1 text-[11px] h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 hover:text-[#3F51B5] hover:border-[#3F51B5]/50 transition-colors cursor-pointer">
                      ← Back to results
                    </button>
                  ) : (
                    <button onClick={() => { setShowList(true); setQcData(null); setPbData(null); setSelectedPB(null); setFetchError(''); setRefs({}); setRefsLoading(false) }}
                      className="flex items-center gap-1 text-[11px] h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 hover:text-[#3F51B5] hover:border-[#3F51B5]/50 transition-colors cursor-pointer">
                      <RefreshCw className="size-3" /> Change
                    </button>
                  )}
                  {!fetching && qcData && pbData && (
                    <span className={`flex items-center gap-1 text-[11px] font-medium ${allOk ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {allOk ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      {allOk ? 'QC ↔ PB fully consistent' : 'Discrepancies found'}
                    </span>
                  )}
                </div>

                {/* QC + PB header cards */}
                <div className="grid grid-cols-2 gap-3">
                  <div className={`rounded-lg border p-3 ${qcData ? 'border-blue-200 dark:border-blue-800/50 bg-blue-50/40 dark:bg-blue-900/10' : 'border-gray-200 dark:border-gray-700 bg-gray-50/40 dark:bg-gray-800/20'}`}>
                    <div className="text-[9px] font-bold uppercase tracking-widest text-blue-400 mb-1">QC</div>
                    {fetching && <div className="flex items-center gap-1.5 text-[11px] text-gray-400"><Loader2 className="size-3 animate-spin" />Fetching…</div>}
                    {qcData && <>
                      <div className="font-mono font-bold text-[13px] text-gray-800 dark:text-gray-100">{qcData.transaction_ref_no}</div>
                      <div className="text-[11px] text-gray-500 mt-0.5">{qcData.transaction_date}</div>
                      <div className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 mt-1">₹{Number(qcData.total_txn_currency_amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>
                    </>}
                  </div>
                  <div className="rounded-lg border border-purple-200 dark:border-purple-800/50 p-3 bg-purple-50/40 dark:bg-purple-900/10">
                    <div className="text-[9px] font-bold uppercase tracking-widest text-purple-400 mb-1">PB</div>
                    <div className="font-mono font-bold text-[13px] text-gray-800 dark:text-gray-100">{selectedPB.ref_no}</div>
                    <div className="text-[11px] text-gray-500 mt-0.5">{selectedPB.date}</div>
                    {pbData && <div className="text-[11px] font-semibold text-purple-600 dark:text-purple-400 mt-1">₹{Number(pbData.txn_currency_total_amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>}
                  </div>
                </div>

                {fetching && <LoadingCard message="FETCHING" steps={[{ label: 'Fetching PB and linked QC', done: false }]} />}
                {fetchError && <div className="flex items-center gap-2 text-[12px] text-red-600"><AlertTriangle className="w-4 h-4 shrink-0" />{fetchError}</div>}

                {qcData && pbData && (
                  <>
                    {refsLoading
                      ? <div className="flex items-center gap-2 px-3 py-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                          <Loader2 className="size-3.5 animate-spin text-gray-400" />
                          <span className="text-[11px] text-gray-400">Resolving IDs…</span>
                        </div>
                      : <HeaderCrossTable qcData={qcData} pbData={pbData} refs={refs} />
                    }
                    {allSections.map((sec, idx) => {
                      let offset = 0
                      for (let j = 0; j < idx; j++) offset += allSections[j].crossRows.length + allSections[j].pbCheckRows.length
                      return (
                        <LineSection key={idx} idx={idx}
                          qcLine={sec.qcLine} pbLine={sec.pbLine}
                          crossRows={sec.crossRows} pbCheckRows={sec.pbCheckRows}
                          crossStart={offset} pbCheckStart={offset + sec.crossRows.length}
                          revealedCount={revealedCount} isFirst={idx === 0}
                          itemName={refs.items?.[String(sec.qcLine.item_ref_id)]} />
                      )
                    })}
                  </>
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
