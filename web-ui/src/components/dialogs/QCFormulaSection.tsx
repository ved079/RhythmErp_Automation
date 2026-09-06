'use client'

import React, { useState, useCallback, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { CheckCircle2, XCircle, Loader2, AlertTriangle, RefreshCw, Key, CheckSquare, Square, ListChecks, X, Eye, Info } from 'lucide-react'
import { fetchQCList, fetchQC, fetchCQPMasters, type QCListItem, type CQPRange } from '@/lib/api'
import { useErpToken } from '@/hooks/useErpToken'
import LoadingCard from '@/components/ui/LoadingCard'

interface Props {
  erpToken: string
  erpTenantId: string
  onNeedsToken: () => void
  onClearToken: () => void
}

interface CheckRow {
  field: string
  formula: string
  calc?: string       // substituted values string shown after "=" in formula col
  expected: number
  actual: number
  ok: boolean
  note?: string
  tooltip?: React.ReactNode
}

const TOLERANCE = 0.05

function r(v: number, dp = 6) { return Math.round(v * 10 ** dp) / 10 ** dp }
function ind(n: number) { return Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 }) }
function fmtVal(v: number): string {
  if (isNaN(v)) return '…'
  const a = Math.abs(v)
  if (a >= 10000) return v.toLocaleString('en-IN', { maximumFractionDigits: 2 })
  if (a >= 1 || a === 0) return v.toFixed(4)
  return v.toFixed(6)
}

function chk(field: string, formula: string, calc: string | undefined, expected: number, actual: number, note?: string): CheckRow {
  // NaN expected = CQP not yet loaded; treat as pending (ok=true so it doesn't inflate fail count)
  return { field, formula, calc, expected, actual, ok: isNaN(expected) || Math.abs(expected - actual) <= TOLERANCE, note }
}

function validateQCLine(line: any): CheckRow[] {
  const grn_qty = parseFloat(line.grn_qty ?? 0)
  const base_rate = parseFloat(line.base_rate ?? 0)
  const empty_bag_weight = parseFloat(line.empty_bag_weight ?? 0)
  const deduction_percent = parseFloat(line.deduction_percent ?? 0)
  const discount_rate = parseFloat(line.discount_rate ?? 0)

  const total_amount = r(base_rate * grn_qty)
  const empty_bags_txn_amount = r(empty_bag_weight * base_rate)
  const accepted_qty = r(grn_qty - empty_bag_weight)
  const net_of_empty_bag_amount = r(total_amount - empty_bags_txn_amount)
  const qc_deduction_rate = r(base_rate * deduction_percent / 100)
  const isRateWeight: boolean = !!line.is_rate_weight_deduction
  const stored_qc_deduction_rate = parseFloat(line.qc_deduction_rate ?? qc_deduction_rate)
  const stored_deduction_weight = parseFloat(line.deduction_weight ?? 0)

  // is_rate_weight_deduction=false → rate path: qc_deduction_amount = stored_rate × accepted_qty
  // is_rate_weight_deduction=true  → weight path: qc_deduction_amount = stored_deduction_weight × base_rate
  // deduction_weight formula is inconsistent across records — not checked
  const exp_qc_deduction_amount = isRateWeight
    ? r(stored_deduction_weight * base_rate)
    : r(stored_qc_deduction_rate * accepted_qty)

  const stored_qc_deduction_amount = parseFloat(line.qc_deduction_amount ?? 0)
  const exp_txn_without_discount = r(net_of_empty_bag_amount - stored_qc_deduction_amount)

  // CD Deduction Qty formula splits by mode:
  //   weight-based: accepted_qty × discount%          (cash discount on gross accepted weight)
  //   rate-based:   (accepted_qty - ded_wt) × discount%  (cash discount on net qty after quality)
  const exp_cd_deduction_qty = isRateWeight
    ? r(accepted_qty * discount_rate / 100)
    : r((accepted_qty - stored_deduction_weight) * discount_rate / 100)
  const stored_cd_deduction_qty = parseFloat(line.c_d_deduction ?? 0)
  // Rate-based: ERP computes cash discount as txn_without_discount × discount% (higher precision)
  // Weight-based: ERP rounds c_d_deduction to 3dp first, then × rate — use stored value to match
  const cash_discount_amount = isRateWeight
    ? r(stored_cd_deduction_qty * base_rate)
    : r(exp_txn_without_discount * discount_rate / 100)

  // txn_currency_amount = net − stored_ded_wt×rate − cash_discount (always weight-path for ded component)
  const txn_currency_amount = r(net_of_empty_bag_amount - r(stored_deduction_weight * base_rate) - cash_discount_amount)

  const dedAmtFormula = isRateWeight ? 'stored_ded_wt × base_rate' : 'stored_rate × accepted_qty'

  const stored_net_purchase_rate = parseFloat(line.rate ?? 0)
  const exp_net_purchase_rate = accepted_qty > 0 ? r(txn_currency_amount / accepted_qty) : 0

  return [
    chk('total_amount', 'grn_qty × base_rate', `${grn_qty} kg × ₹${ind(base_rate)}`, total_amount, parseFloat(line.total_amount ?? 0)),
    chk('empty_bags_txn_amount', 'empty_bag_weight × base_rate', `${empty_bag_weight} kg × ₹${ind(base_rate)}`, empty_bags_txn_amount, parseFloat(line.empty_bags_txn_amount ?? 0)),
    chk('alternate_accepted_qty', 'grn_qty − empty_bag_weight', `${grn_qty} − ${empty_bag_weight} kg`, accepted_qty, parseFloat(line.alternate_accepted_qty ?? 0)),
    chk('net_of_empty_bag_amount', 'total_amount − empty_bags_txn_amount', `₹${ind(total_amount)} − ₹${ind(empty_bags_txn_amount)}`, net_of_empty_bag_amount, parseFloat(line.net_of_empty_bag_amount ?? 0)),
    chk('deduction_weight', 'accepted_qty × ded% / 100', `${accepted_qty} × ${deduction_percent} / 100`, r(accepted_qty * deduction_percent / 100), stored_deduction_weight),
    chk('qc_deduction_rate', 'base_rate × ded% / 100', `₹${ind(base_rate)} × ${deduction_percent} / 100`, qc_deduction_rate, parseFloat(line.qc_deduction_rate ?? 0), 'ERP stores rounded to 4dp'),
    chk('qc_deduction_amount', dedAmtFormula,
      isRateWeight ? `${stored_deduction_weight} × ₹${ind(base_rate)}` : `₹${ind(stored_qc_deduction_rate)} × ${accepted_qty} kg`,
      exp_qc_deduction_amount, stored_qc_deduction_amount),
    chk('transaction_amount_without_discount', 'net_of_empty_bag − qc_deduction', `₹${ind(net_of_empty_bag_amount)} − ₹${ind(stored_qc_deduction_amount)}`, exp_txn_without_discount, parseFloat(line.transaction_amount_without_discount ?? 0)),
    ...(discount_rate > 0 ? [
      chk('c_d_deduction',
        isRateWeight ? 'accepted_qty × discount% / 100' : '(accepted_qty − ded_wt) × discount% / 100',
        isRateWeight ? `${accepted_qty} × ${discount_rate} / 100` : `(${accepted_qty} − ${stored_deduction_weight}) × ${discount_rate} / 100`,
        exp_cd_deduction_qty, stored_cd_deduction_qty),
      chk('cash_discount_deduction_amount',
        isRateWeight ? 'stored_c_d_deduction × base_rate' : 'txn_without_discount × discount%',
        isRateWeight ? `${stored_cd_deduction_qty.toFixed(3)} × ₹${ind(base_rate)}` : `₹${ind(exp_txn_without_discount)} × ${discount_rate}%`,
        cash_discount_amount, parseFloat(line.cash_discount_deduction_amount ?? 0)),
    ] : []),
    chk('txn_currency_amount', 'purchase_before_CD − cash_discount',
      `₹${ind(net_of_empty_bag_amount)} − ₹${ind(r(stored_deduction_weight * base_rate))} − ₹${ind(cash_discount_amount)}`,
      txn_currency_amount, parseFloat(line.txn_currency_amount ?? 0), 'ERP stores rounded to 2dp'),
    ...(accepted_qty > 0 ? [
      chk('net_purchase_rate', 'txn_amount / accepted_qty', `₹${ind(txn_currency_amount)} / ${accepted_qty} kg`, exp_net_purchase_rate, stored_net_purchase_rate),
    ] : []),
  ]
}

function calcTieredDeduction(actualVal: number, allowable: number, ranges: CQPRange[], qualityType: number): { deduction: number; formulaStr: string } {
  // Each range above the allowable contributes independently (tiered stacking).
  // The lower bound of each tier's contribution is max(allowable, prev_range_max).
  const tiers = ranges
    .filter(rng => rng.quality_type === qualityType)
    .sort((a, b) => a.min - b.min)

  let deduction = 0
  let prevMax = 0
  const tierParts: string[] = []

  for (const tier of tiers) {
    if (tier.multiplier === 0) { prevMax = tier.max; continue }
    const low = Math.max(allowable, prevMax)
    const high = Math.min(actualVal, tier.max)
    if (high > low) {
      const contrib = r((high - low) * tier.multiplier)
      deduction = r(deduction + contrib)
      tierParts.push(`(${high}−${low})×${tier.multiplier}`)
    }
    prevMax = tier.max
    if (actualVal <= tier.max) break
  }

  return {
    deduction,
    formulaStr: tierParts.length > 0 ? tierParts.join(' + ') : `excess(${actualVal}−${allowable}) × mult(0)`,
  }
}

// Returns null if all actual_values are zero (readings not entered — skip CQP check)
function allReadingsZero(line: any): boolean {
  const params: any[] = line.qc_parameter_details ?? []
  return params.length > 0 && params.every(p => parseFloat(p.actual_value ?? 0) === 0)
}

function validateQCParams(line: any, cqpRanges: CQPRange[] | undefined): CheckRow[] {
  const params: any[] = line.qc_parameter_details ?? []
  return params.map((p, i) => {
    const qualityType = p.item_quality_parameter_ref_id
    const actualVal = parseFloat(p.actual_value ?? 0)
    const allowable = parseFloat(p.allowable_percent ?? 0)
    const storedDed = parseFloat(p.quantity_deduction ?? 0)
    const tieredTooltip = (
      <div className="space-y-3">
        <div>
          <div className="font-semibold text-white text-[12px] mb-1">How is this calculated?</div>
          <div className="text-gray-400 text-[11px] leading-relaxed">
            Works like tax slabs — the excess above the allowable limit is split into ranges, and each range has its own penalty rate.
          </div>
        </div>
        <div className="bg-gray-800 rounded-md p-2.5 space-y-1.5">
          <div className="flex items-baseline gap-2">
            <span className="text-blue-400 font-semibold text-[11px] w-20 shrink-0">Actual</span>
            <span className="text-gray-300 text-[11px]">Measured quality value <span className="text-white font-semibold">({actualVal})</span></span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-blue-400 font-semibold text-[11px] w-20 shrink-0">Allowable</span>
            <span className="text-gray-300 text-[11px]">Max limit set in the contract <span className="text-white font-semibold">({allowable})</span></span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-blue-400 font-semibold text-[11px] w-20 shrink-0">Mult</span>
            <span className="text-gray-300 text-[11px]">Penalty rate per unit of excess, from CQP master</span>
          </div>
        </div>
        <div>
          <div className="text-gray-400 text-[10px] uppercase tracking-wide font-semibold mb-1.5">Step by step</div>
          <div className="space-y-1 text-[11px] text-gray-300">
            <div className="flex gap-2"><span className="text-gray-600 font-mono">1.</span>Find how much actual exceeds allowable</div>
            <div className="flex gap-2"><span className="text-gray-600 font-mono">2.</span>Split that excess across CQP ranges</div>
            <div className="flex gap-2"><span className="text-gray-600 font-mono">3.</span>Multiply each slice by its range's penalty rate</div>
            <div className="flex gap-2"><span className="text-gray-600 font-mono">4.</span>Add them all up → quantity deduction %</div>
          </div>
        </div>
      </div>
    )
    if (!cqpRanges) return { ...chk(`param_${i + 1} (type ${qualityType})`, 'tiered(actual − allowable) × mult', '…', NaN, storedDed), tooltip: tieredTooltip }
    const { deduction: expDed, formulaStr } = calcTieredDeduction(actualVal, allowable, cqpRanges, qualityType)
    return { ...chk(`param_${i + 1} (type ${qualityType})`, 'tiered(actual − allowable) × mult', formulaStr, expDed, storedDed), tooltip: tieredTooltip }
  })
}

function validateBags(line: any): CheckRow[] {
  const empty_bag_weight = parseFloat(line.empty_bag_weight ?? 0)
  const bagDetails: any[] = line.qc_bags_details ?? []
  // When uom_conversion_kg > 0 use qty × wt × conv; when 0 trust stored total_weight_of_bags
  const computedBagWeight = bagDetails.reduce((s: number, b: any) => {
    const qty = parseFloat(b.quantity_of_bags ?? 0)
    const wt = parseFloat(b.weight_of_bags ?? 0)
    const conv = parseFloat(b.uom_conversion_kg ?? 0)
    const stored = parseFloat(b.total_weight_of_bags ?? 0)
    // conv > 0: weight_of_bags is in a sub-unit, convert to kg
    // conv = 0: weight_of_bags is already in kg; use stored total as fallback if non-zero
    const contrib = conv > 0 ? qty * wt * conv : (stored > 0 ? stored : qty * wt)
    return s + contrib
  }, 0)
  const bagCalc = bagDetails.length === 1
    ? (() => {
        const b = bagDetails[0]
        const qty = parseFloat(b.quantity_of_bags ?? 0)
        const wt = parseFloat(b.weight_of_bags ?? 0)
        const conv = parseFloat(b.uom_conversion_kg ?? 0)
        const stored = parseFloat(b.total_weight_of_bags ?? 0)
        if (conv > 0) return `${qty} × ${wt} kg × ${conv}`
        if (stored > 0) return `${stored} kg (stored)`
        return `${qty} × ${wt} kg`
      })()
    : `${bagDetails.length} bag types`
  return [
    chk('total_weight_of_bags', 'Σ(bag_qty × wt_per_bag × uom_conv)', bagCalc, r(computedBagWeight), r(empty_bag_weight)),
  ]
}

// ── Formula info popover ──────────────────────────────────
function FormulaInfoButton({ tooltip }: { tooltip: React.ReactNode }) {
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null)
  const btnRef = useRef<HTMLButtonElement>(null)
  const popRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!pos) return
    function onMouseDown(e: MouseEvent) {
      if (popRef.current && !popRef.current.contains(e.target as Node) &&
          btnRef.current && !btnRef.current.contains(e.target as Node)) {
        setPos(null)
      }
    }
    function onScroll() { setPos(null) }
    document.addEventListener('mousedown', onMouseDown)
    window.addEventListener('scroll', onScroll, true)
    return () => {
      document.removeEventListener('mousedown', onMouseDown)
      window.removeEventListener('scroll', onScroll, true)
    }
  }, [pos])

  function handleClick(e: React.MouseEvent) {
    e.stopPropagation()
    if (pos) { setPos(null); return }
    const r = btnRef.current!.getBoundingClientRect()
    const popW = 320
    const popH = 380 // approximate height
    const left = Math.min(r.right + 8, window.innerWidth - popW - 12)
    const top = r.top + popH > window.innerHeight - 16
      ? Math.max(8, window.innerHeight - popH - 16)
      : r.top
    setPos({ top, left })
  }

  return (
    <>
      <button
        ref={btnRef}
        onClick={handleClick}
        className="flex items-center justify-center w-4 h-4 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-500 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-800/60 transition-colors shrink-0"
      >
        <Info className="w-2.5 h-2.5" />
      </button>
      {pos && (
        <div
          ref={popRef}
          style={{ position: 'fixed', top: pos.top, left: pos.left, width: 320, zIndex: 9999 }}
          className="rounded-xl bg-gray-900 border border-gray-700 shadow-2xl p-4"
          onClick={e => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400">Formula explained</span>
            <button onClick={() => setPos(null)} className="text-gray-500 hover:text-gray-300 transition-colors">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          {tooltip}
        </div>
      )}
    </>
  )
}

// ── Checks table ─────────────────────────────────────────
// 5-col receipt grid: Field | Formula = Calculation | Computed | ERP Stored | Icon
const COLS = '1fr 2fr 1fr 1fr 28px'
function ChecksTable({ rows, revealStart, revealedCount }: { rows: CheckRow[], revealStart: number, revealedCount: number }) {
  const failCount = rows.filter(r => !r.ok).length
  const allOk = failCount === 0
  const headers = ['Field', 'Formula = Calculation', 'Computed', 'ERP Stored', '']
  return (
    <div className="overflow-hidden">
      {/* Column headers */}
      <div className="grid border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/40"
        style={{ gridTemplateColumns: COLS }}>
        {headers.map((h, i) => (
          <span key={i} className={`text-[8px] font-bold uppercase tracking-[0.14em] text-gray-500 dark:text-gray-400 px-3 py-[7px] ${i >= 2 && i < 4 ? 'text-right' : ''} ${i === 1 ? 'border-l border-gray-200 dark:border-gray-700' : ''} ${i === 2 ? 'border-l border-gray-200 dark:border-gray-700' : ''} ${i === 3 ? 'border-l border-gray-200 dark:border-gray-700' : ''}`}>{h}</span>
        ))}
      </div>

      {/* Rows */}
      {rows.map((row, i) => {
        const revealed = (revealStart + i) < revealedCount
        const diff = Math.abs(row.expected - row.actual)
        const isAmber = row.ok && diff > 0.000001
        const isPending = isNaN(row.expected)
        const isFail = !row.ok && !isPending
        const isExact = row.ok && !isPending && diff < 5e-7
        return (
          <div key={i}
            className={`grid border-b border-gray-100 dark:border-gray-800 last:border-0 ${isAmber ? 'bg-amber-50/60 dark:bg-amber-900/10' : isFail ? 'bg-red-50/50 dark:bg-red-900/10' : ''}`}
            style={{ gridTemplateColumns: COLS }}>

            {/* Field name */}
            <div className={`px-3 py-[11px] flex items-center border-r border-gray-100 dark:border-gray-800 min-w-0`}>
              <span className={`text-[11px] font-semibold truncate ${isFail ? 'text-red-600 dark:text-red-400' : isAmber ? 'text-amber-600 dark:text-amber-400' : 'text-gray-700 dark:text-gray-200'}`}>
                {row.field}
              </span>
            </div>

            {/* Formula = Calculation */}
            <div className="px-3 py-[11px] flex flex-col gap-[3px] border-r border-gray-100 dark:border-gray-800 min-w-0">
              <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-200 leading-snug flex items-center gap-1.5">
                {row.formula}
                {row.tooltip && <FormulaInfoButton tooltip={row.tooltip} />}
              </span>
              {row.calc && row.calc !== '…' && (
                <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 leading-snug">= {row.calc}</span>
              )}
              {isPending && <span className="text-[11px] font-semibold text-gray-400 dark:text-gray-600">= …</span>}
              {isAmber && <span className="font-mono text-[9px] text-amber-600 dark:text-amber-400">Δ {diff.toFixed(6)} · {row.note ?? 'rounding'}</span>}
              {isFail && row.note && <span className="font-mono text-[9px] text-red-500 dark:text-red-400">{row.note}</span>}
            </div>

            {/* Computed (expected) */}
            <div className={`px-3 py-[11px] flex items-center justify-end border-r border-gray-100 dark:border-gray-800`}>
              {isPending
                ? <span className="font-mono text-[11px] text-gray-300 dark:text-gray-600">…</span>
                : isExact
                  ? <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400">{fmtVal(row.expected)}</span>
                  : <span className={`text-[11px] font-semibold ${isAmber ? 'text-amber-600 dark:text-amber-400' : isFail ? 'text-red-500 dark:text-red-400' : 'text-gray-600 dark:text-gray-300'}`}>{fmtVal(row.expected)}</span>
              }
            </div>

            {/* ERP Stored (actual) */}
            <div className="px-3 py-[11px] flex items-center justify-end">
              <span className={`text-[11px] font-semibold ${isExact ? 'text-gray-400 dark:text-gray-500' : isFail ? 'text-red-600 dark:text-red-400' : isAmber ? 'text-amber-600 dark:text-amber-400' : 'text-gray-700 dark:text-gray-200'}`}>
                {fmtVal(row.actual)}
              </span>
            </div>

            {/* Icon */}
            <div className="flex items-center justify-center">
              {isPending
                ? <Loader2 className="size-3 animate-spin text-gray-300 dark:text-gray-600" />
                : revealed
                  ? (row.ok ? <CheckCircle2 className={`size-3.5 ${isAmber ? 'text-amber-500' : 'text-emerald-500'}`} /> : <XCircle className="size-3.5 text-red-500" />)
                  : <Loader2 className="size-3 animate-spin text-gray-300 dark:text-gray-600" />}
            </div>
          </div>
        )
      })}

      {/* Footer */}
      <div className={`flex items-center justify-between border-t border-gray-200 dark:border-gray-700 px-3 py-[7px] ${allOk ? 'bg-emerald-50/50 dark:bg-emerald-900/10' : 'bg-red-50/50 dark:bg-red-900/10'}`}>
        <div className={`flex items-center gap-[5px] text-[11px] font-semibold ${allOk ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
          {allOk ? <CheckCircle2 className="size-3.5" /> : <XCircle className="size-3.5" />}
          {allOk ? 'All checks passed' : `${failCount} check${failCount > 1 ? 's' : ''} failed`}
        </div>
        <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-gray-400 dark:text-gray-500">{rows.length} check{rows.length !== 1 ? 's' : ''}</span>
      </div>
    </div>
  )
}

function LineSection({ idx, line, qcRows, bagRows, paramRows, qcStart, bagStart, paramStart, revealedCount, isFirst }: {
  idx: number; line: any; qcRows: CheckRow[]; bagRows: CheckRow[]; paramRows: CheckRow[]
  qcStart: number; bagStart: number; paramStart: number; revealedCount: number; isFirst: boolean
}) {
  const activeParamRows = allReadingsZero(line) ? [] : paramRows
  const lineAllOk = [...qcRows, ...bagRows, ...activeParamRows].every(r => r.ok)
  const [open, setOpen] = useState(isFirst || !lineAllOk)

  useEffect(() => { if (!lineAllOk) setOpen(true) }, [lineAllOk])

  const failCount = [...qcRows, ...bagRows, ...activeParamRows].filter(r => !r.ok).length
  const specs = [
    { label: 'Item', value: `#${line.item_ref_id}` },
    { label: 'Rate', value: `₹${Number(line.base_rate).toLocaleString('en-IN')}` },
    { label: 'GRN qty', value: String(line.grn_qty) },
    { label: 'Empty bag wt', value: `${line.empty_bag_weight} kg` },
    { label: 'Deduction', value: `${line.deduction_percent}%` },
    { label: 'Discount', value: `${line.discount_rate ?? 0}%` },
  ]

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* Card header */}
      <button onClick={() => setOpen(v => !v)} className="w-full flex items-center gap-2 px-3 py-2.5 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer">
        <span className="text-[9px] font-bold uppercase tracking-[0.13em] text-gray-400 dark:text-gray-500 border border-gray-200 dark:border-gray-700 rounded px-1.5 py-0.5 bg-white dark:bg-gray-800 shrink-0">
          Line {idx + 1}
        </span>
        <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200 flex-1 text-left">
          Item <span className="font-mono font-normal text-gray-500 dark:text-gray-400">#{line.item_ref_id}</span>
        </span>
        <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${lineAllOk ? 'text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/50 bg-emerald-50 dark:bg-emerald-900/10' : 'text-red-600 dark:text-red-400 border-red-200 dark:border-red-800/50 bg-red-50/50 dark:bg-red-900/10'}`}>
          {lineAllOk ? <CheckCircle2 className="size-3" /> : <XCircle className="size-3" />}
          {lineAllOk ? 'All passed' : `${failCount} failed`}
        </span>
        <span className="text-[9px] text-gray-400 dark:text-gray-600 shrink-0">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          {/* Specs grid */}
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-px bg-gray-100 dark:bg-gray-700/40 border-b border-gray-200 dark:border-gray-700">
            {specs.map(({ label, value }) => (
              <div key={label} className="bg-white dark:bg-gray-800/40 px-2.5 py-2.5">
                <div className="text-[9px] font-bold uppercase tracking-[0.12em] text-gray-400 dark:text-gray-500 mb-1">{label}</div>
                <div className="font-mono text-[12px] font-semibold text-gray-800 dark:text-gray-100">{value}</div>
              </div>
            ))}
          </div>
          {/* Line checks label */}
          <div className="flex items-center gap-2 px-3 pt-2 pb-1">
            <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-gray-400 dark:text-gray-500">Line checks</span>
            <div className="flex-1 h-px bg-gray-100 dark:bg-gray-800" />
          </div>
          <ChecksTable rows={qcRows} revealStart={qcStart} revealedCount={revealedCount} />
          {/* Bags */}
          <div className="border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 px-3 pt-2 pb-1">
              <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-gray-400 dark:text-gray-500">Bags detail</span>
              <div className="flex-1 h-px bg-gray-100 dark:bg-gray-800" />
            </div>
            <ChecksTable rows={bagRows} revealStart={bagStart} revealedCount={revealedCount} />
          </div>
          {/* Quality parameters */}
          {paramRows.length > 0 && (
            <div className="border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 px-3 pt-2 pb-1">
                <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-gray-400 dark:text-gray-500">Quality parameters</span>
                <div className="flex-1 h-px bg-gray-100 dark:bg-gray-800" />
              </div>
              {allReadingsZero(line) ? (
                <div className="flex items-center gap-2 px-3 py-3 text-[11px] text-amber-600 dark:text-amber-400 bg-amber-50/50 dark:bg-amber-900/10">
                  <AlertTriangle className="size-3.5 shrink-0" />
                  Readings not entered in ERP — CQP formula check skipped
                </div>
              ) : (
                <ChecksTable rows={paramRows} revealStart={paramStart} revealedCount={revealedCount} />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function QCFormulaSection({ erpToken, erpTenantId, onNeedsToken, onClearToken }: Props) {
  const { token, tenantId, localToken, setLocalToken, localTenantId, setLocalTenantId, handleAuthError } = useErpToken(erpToken, erpTenantId)

  const [showTokenInput, setShowTokenInput] = useState(false)
  const [qcList, setQcList] = useState<QCListItem[]>([])
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError] = useState('')
  const [search, setSearch] = useState('')
  const [selectedQC, setSelectedQC] = useState<QCListItem | null>(null)
  const [showList, setShowList] = useState(true)
  const [qcData, setQcData] = useState<any>(null)
  const [fetching, setFetching] = useState(false)
  const [fetchError, setFetchError] = useState('')
  const [cqpMasters, setCqpMasters] = useState<Record<string, CQPRange[]>>({})
  const [cqpLoading, setCqpLoading] = useState(false)
  const [cqpError, setCqpError] = useState('')

  const bulkResultsRef = useRef<HTMLDivElement>(null)
  const bulkRowRefs = useRef<(HTMLDivElement | null)[]>([])
  const bulkRunBtnRef = useRef<HTMLDivElement>(null)
  const bulkAbort = useRef(false)
  const bulkFromView = useRef(false)
  const bulkViewIndex = useRef(0)
  const firstLineSectionRef = useRef<HTMLDivElement>(null)

  // Multi-select bulk validate state
  const [multiSelectQC, setMultiSelectQC] = useState(false)
  const [selectedQCIds, setSelectedQCIds] = useState<Set<string | number>>(new Set())
  const [bulkResults, setBulkResults] = useState<{ qc: QCListItem; ok: boolean; error?: string; failCount?: number; done: boolean; data?: any }[]>([])
  const [bulkRunning, setBulkRunning] = useState(false)
  const [bulkProgress, setBulkProgress] = useState(0)
  const [bulkOpen, setBulkOpen] = useState(false)
  const [revealedCount, setRevealedCount] = useState(0)

  const loadList = useCallback(async () => {
    if (!token || !tenantId) return
    setListLoading(true)
    setListError('')
    try {
      const list = await fetchQCList(token, tenantId)
      setQcList(list)
    } catch (err) {
      if (!handleAuthError(err)) setListError(err instanceof Error ? err.message : String(err))
    } finally {
      setListLoading(false)
    }
  }, [token, tenantId, handleAuthError])

  const loadListRef = useRef(loadList)
  useEffect(() => { loadListRef.current = loadList }, [loadList])

  const hasToken = !!token && !!tenantId
  useEffect(() => {
    if (!hasToken) return
    loadListRef.current()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasToken])

  const handleSelect = async (qc: QCListItem) => {
    setSelectedQC(qc)
    setShowList(false)
    setFetching(true)
    setFetchError('')
    setQcData(null)
    setCqpMasters({})
    try {
      const data = await fetchQC(token!, tenantId, String(qc.id))
      if (data.error) throw new Error(data.error)
      setQcData(data)
      // Fetch CQP masters only if any line has quality params
      const hasParams = (data.qc_details ?? []).some((l: any) => (l.qc_parameter_details ?? []).length > 0)
      const itemIds: number[] = [...new Set<number>((data.qc_details ?? []).map((l: any) => l.item_ref_id).filter(Boolean))]
      if (hasParams && itemIds.length > 0) {
        setCqpLoading(true)
        setCqpError('')
        fetchCQPMasters(token!, tenantId, itemIds)
          .then(masters => setCqpMasters(masters))
          .catch(err => setCqpError(err instanceof Error ? err.message : String(err)))
          .finally(() => setCqpLoading(false))
      }
    } catch (err) {
      if (!handleAuthError(err)) setFetchError(err instanceof Error ? err.message : String(err))
    } finally {
      setFetching(false)
    }
  }

  const handleBulkValidate = async () => {
    if (!token || !tenantId || selectedQCIds.size === 0) return
    const selected = qcList.filter(qc => selectedQCIds.has(qc.id ?? qc.ref_no))
    bulkAbort.current = false
    bulkRowRefs.current = []
    setBulkRunning(true)
    setBulkProgress(0)
    setBulkOpen(true)
    const results: typeof bulkResults = selected.map(qc => ({ qc, ok: false, done: false }))
    setBulkResults([...results])
    setTimeout(() => bulkResultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 80)
    for (let i = 0; i < selected.length; i++) {
      if (bulkAbort.current) break
      setTimeout(() => bulkRowRefs.current[i]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50)
      const qc = selected[i]
      try {
        const data = await fetchQC(token!, tenantId, String(qc.id))
        if (data.error) throw new Error(data.error)
        const lines: any[] = data.qc_details ?? []
        let failCount = 0
        for (const line of lines) {
          const rows = [...validateQCLine(line), ...validateBags(line)]
          failCount += rows.filter(r => !r.ok).length
        }
        results[i] = { qc, ok: failCount === 0, failCount, done: true, data }
      } catch (err) {
        results[i] = { qc, ok: false, error: err instanceof Error ? err.message : String(err), done: true }
      }
      setBulkResults([...results])
      setBulkProgress(i + 1)
    }
    setBulkRunning(false)
  }

  const filtered = qcList.filter(qc => {
    const q = search.toLowerCase()
    return !q || qc.ref_no.toLowerCase().includes(q) || qc.supplier.toLowerCase().includes(q)
  })

  const sortedBulkResults = [...bulkResults].sort((a, b) => {
    if (!a.done && b.done) return 1
    if (a.done && !b.done) return -1
    if (a.ok && !b.ok) return 1
    if (!a.ok && b.ok) return -1
    return 0
  })

  const lines: any[] = qcData?.qc_details ?? []

  // Sequential reveal animation — resets and replays every time qcData changes
  useEffect(() => {
    if (!qcData) { setRevealedCount(0); return }
    const totalRows = lines.reduce((sum: number, line: any) => sum + validateQCLine(line).length + validateBags(line).length, 0)
    setRevealedCount(0)
    let count = 0
    const iv = setInterval(() => {
      count++
      setRevealedCount(count)
      if (count >= totalRows) clearInterval(iv)
    }, 60)
    return () => clearInterval(iv)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qcData])

  // Auto-scroll first line section to center when results load (only for multi-line)
  useEffect(() => {
    if (!qcData || lines.length <= 1) return
    const t = setTimeout(() => firstLineSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300)
    return () => clearTimeout(t)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qcData])

  const allOk = lines.length > 0 && lines.every(line => {
    const paramRows = allReadingsZero(line) ? [] : validateQCParams(line, cqpMasters[String(line.item_ref_id)])
    const rows = [...validateQCLine(line), ...validateBags(line), ...paramRows]
    return rows.every(r => r.ok)
  })

  return (
    <div className="relative flex flex-col h-full min-h-0">
      <div className="bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col min-h-0 flex-1 overflow-hidden">

        {/* Token panel */}
        {showTokenInput && (
          <div className="p-4 overflow-y-auto flex-1 min-h-0 space-y-3">
            <div className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
              <Label className="text-[11px] text-orange-600 dark:text-orange-400 mb-1.5 block font-medium">ERP Credentials</Label>
              <div className="flex items-center gap-2 mb-2">
                <Input
                  type="password"
                  value={localToken}
                  onChange={e => setLocalToken(e.target.value)}
                  placeholder="Paste your Bearer token here..."
                  className={`h-9 text-[12px] flex-1 ${localToken && localToken.length > 100 ? 'border-green-400' : localToken ? 'border-red-400' : ''}`}
                />
              </div>
              {localToken && localToken.length > 100 && (
                <p className="text-[11px] text-green-600 dark:text-green-400 flex items-center gap-1 mb-2">
                  <span className="inline-block size-2 rounded-full bg-green-500" /> Token looks valid
                </p>
              )}
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
              <p className="text-[11px] text-orange-500 dark:text-orange-400 mt-1.5">Credentials stay in your browser session. Clear below to reset.</p>
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
              <p className="text-[12px] text-gray-400 py-2">No QC records found. Click Refresh or check your token.</p>
            )}

            {/* QC list */}
            {qcList.length > 0 && showList && (
              <>
                <div className="flex items-center justify-between">
                  <Label className="text-[11px] text-gray-700 dark:text-gray-300">Select Quality Check</Label>
                  <button
                    onClick={() => { setMultiSelectQC(v => !v); setSelectedQCIds(new Set()); setBulkResults([]); setBulkOpen(false) }}
                    className={`text-[11px] flex items-center gap-1 px-2 py-0.5 rounded border transition-colors cursor-pointer ${multiSelectQC ? 'border-[#3F51B5] text-[#3F51B5] bg-[#3F51B5]/5' : 'border-gray-200 dark:border-gray-700 text-gray-500 hover:border-[#3F51B5] hover:text-[#3F51B5]'}`}>
                    <ListChecks className="size-3" /> Multi-select
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by ref no or supplier…" className="h-8 text-[12px] flex-1" />
                  {multiSelectQC && (() => {
                    const allSel = filtered.length > 0 && filtered.every(qc => selectedQCIds.has(qc.id ?? qc.ref_no))
                    return (
                      <button onClick={() => allSel ? setSelectedQCIds(new Set()) : setSelectedQCIds(new Set(filtered.map(qc => qc.id ?? qc.ref_no)))}
                        className="text-[11px] flex items-center gap-1 px-2 py-1 rounded border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:border-[#3F51B5] transition-colors cursor-pointer shrink-0">
                        {allSel ? <CheckSquare className="size-3.5 text-[#3F51B5]" /> : <Square className="size-3.5" />}
                        {allSel ? 'Deselect all' : 'Select all'}
                      </button>
                    )
                  })()}
                </div>
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden max-h-64 overflow-y-auto">
                  {filtered.map((qc, i) => {
                    const qcKey = qc.id ?? qc.ref_no
                    const checked = selectedQCIds.has(qcKey)
                    return (
                      <div key={qc.id ?? i}
                        onClick={multiSelectQC ? () => setSelectedQCIds(prev => { const n = new Set(prev); n.has(qcKey) ? n.delete(qcKey) : n.add(qcKey); return n }) : undefined}
                        className={`flex items-start gap-2 px-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 hover:bg-[#3F51B5]/5 dark:hover:bg-[#3F51B5]/10 transition-colors ${multiSelectQC ? 'cursor-pointer' : ''} ${checked ? 'bg-[#3F51B5]/5 dark:bg-[#3F51B5]/10' : ''}`}>
                        {multiSelectQC && (
                          <button onClick={(e) => { e.stopPropagation(); setSelectedQCIds(prev => { const n = new Set(prev); n.has(qcKey) ? n.delete(qcKey) : n.add(qcKey); return n }) }}
                            className="mt-0.5 shrink-0 cursor-pointer text-[#3F51B5]">
                            {checked ? <CheckSquare className="size-3.5" /> : <Square className="size-3.5 text-gray-300 dark:text-gray-600" />}
                          </button>
                        )}
                        <button onClick={() => handleSelect(qc)} className="flex-1 text-left cursor-pointer">
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
                        </button>
                      </div>
                    )
                  })}
                </div>

                {/* Bulk action bar */}
                {multiSelectQC && selectedQCIds.size > 0 && (
                  <div ref={bulkRunBtnRef} className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-[#3F51B5]/5 border border-[#3F51B5]/20">
                    <span className="text-[12px] text-[#3F51B5] dark:text-[#7986CB] font-semibold">{selectedQCIds.size} QC{selectedQCIds.size > 1 ? 's' : ''} selected</span>
                    <div className="flex items-center gap-2">
                      {bulkRunning ? (
                        <div className="flex items-center gap-2">
                          <Loader2 className="size-3.5 animate-spin text-[#3F51B5]" />
                          <span className="text-[11px] text-gray-500">{bulkProgress} / {selectedQCIds.size}</span>
                          <button onClick={() => { bulkAbort.current = true }} className="text-[11px] text-red-500 hover:underline cursor-pointer">Stop</button>
                        </div>
                      ) : (
                        <Button onClick={handleBulkValidate} size="sm" className="h-7 text-[11px] gap-1.5 cursor-pointer bg-[#3F51B5] hover:bg-[#303f9f]">
                          <ListChecks className="size-3" />Validate All
                        </Button>
                      )}
                    </div>
                  </div>
                )}
                {/* Progress bar */}
                {bulkRunning && (
                  <div className="h-1 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
                    <div className="h-full bg-[#3F51B5] transition-all duration-300 rounded-full" style={{ width: `${(bulkProgress / selectedQCIds.size) * 100}%` }} />
                  </div>
                )}
                {/* Bulk validate results */}
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
                              <span className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100">{r.qc.ref_no}</span>
                              <span className="text-[10px] text-gray-400 dark:text-gray-500 truncate">{r.qc.supplier}</span>
                            </div>
                            {r.done && !r.ok && (
                              <div className="text-[10px] text-red-500 dark:text-red-400 mt-0.5 truncate">
                                {r.error || (r.failCount != null ? `${r.failCount} field${r.failCount !== 1 ? 's' : ''} failed` : 'Check failed')}
                              </div>
                            )}
                          </div>
                          {r.done && r.data && (
                            <button onClick={() => {
                              bulkFromView.current = true
                              bulkViewIndex.current = i
                              setSelectedQC(r.qc)
                              setShowList(false)
                              setQcData(r.data)
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

            {/* Results view */}
            {!showList && selectedQC && (
              <div className="space-y-4">
                {/* Header row */}
                <div className="flex items-center gap-2">
                  {bulkFromView.current ? (
                    <button onClick={() => {
                      const idx = bulkViewIndex.current
                      bulkFromView.current = false
                      setShowList(true); setQcData(null); setSelectedQC(null); setFetchError('')
                      setTimeout(() => {
                        bulkResultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
                        setTimeout(() => bulkRowRefs.current[idx]?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 200)
                      }, 50)
                    }}
                      className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-[#3F51B5]/40 bg-[#3F51B5]/5 text-[#3F51B5] dark:text-[#7986CB] hover:bg-[#3F51B5]/10 transition-colors cursor-pointer">
                      ← Back to results
                    </button>
                  ) : (
                    <button onClick={() => { setShowList(true); setQcData(null); setSelectedQC(null); setFetchError('') }}
                      className="flex items-center gap-1 text-[11px] h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-[#3F51B5] dark:hover:text-[#7986CB] hover:border-[#3F51B5]/50 transition-colors cursor-pointer">
                      <RefreshCw className="size-3" /> Change
                    </button>
                  )}
                  {!fetching && qcData && (
                    <span className={`flex items-center gap-1 text-[11px] font-medium ${allOk ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {allOk ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      {allOk ? 'All formulas pass' : 'Formula mismatch detected'}
                    </span>
                  )}
                </div>

                {/* Record header */}
                <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 bg-gray-50 dark:bg-gray-800/40 flex items-start justify-between gap-3 flex-wrap">
                  <div className="min-w-0">
                    <div className="font-mono font-bold text-[13px] text-gray-800 dark:text-gray-100 truncate">{selectedQC.ref_no}</div>
                    <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">{selectedQC.date} · {selectedQC.supplier}</div>
                  </div>
                  {qcData && (
                    <div className="flex items-center gap-2 shrink-0 flex-wrap">
                      <span className="inline-flex items-center gap-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md px-2.5 py-1 text-[11px]">
                        <span className="text-gray-400">Total</span>
                        <span className="font-semibold text-gray-700 dark:text-gray-200 font-mono">₹{Number(qcData.total_txn_currency_amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                      </span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${qcData.workflow_status === 'Created' ? 'bg-blue-50 dark:bg-blue-900/10 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-800/40' : 'bg-gray-100 dark:bg-gray-800 text-gray-500 border-gray-200 dark:border-gray-700'}`}>
                        {qcData.workflow_status}
                      </span>
                    </div>
                  )}
                </div>

                {fetching && (
                  <LoadingCard message="VALIDATING" steps={[{ label: 'Fetching QC detail', done: false }, { label: 'Running formula checks', done: false }]} />
                )}

                {fetchError && (
                  <div className="flex items-center gap-2 text-[12px] text-red-600">
                    <AlertTriangle className="w-4 h-4 shrink-0" /> {fetchError}
                  </div>
                )}

                {cqpError && (
                  <div className="flex items-center gap-2 text-[11px] text-amber-600 dark:text-amber-400 px-1">
                    <AlertTriangle className="w-3 h-3 shrink-0" /> CQP master: {cqpError}
                  </div>
                )}

                {cqpLoading && !cqpError && (
                  <LoadingCard message="LOADING" steps={[
                    { label: 'Fetching quality parameter master', done: false },
                    { label: 'Running formula checks', done: false },
                  ]} />
                )}

                {qcData && !cqpLoading && (() => {
                  let offset = 0
                  return (
                    <>
                      {lines.map((line, idx) => {
                        const qcRows = validateQCLine(line)
                        const bagRows = validateBags(line)
                        const itemRanges = cqpMasters[String(line.item_ref_id)]
                        const paramRows = validateQCParams(line, itemRanges)
                        const qcStart = offset
                        const bagStart = offset + qcRows.length
                        const paramStart = bagStart + bagRows.length
                        offset += qcRows.length + bagRows.length + paramRows.length
                        return (
                          <div key={idx} ref={idx === 0 ? firstLineSectionRef : undefined}>
                            <LineSection idx={idx} line={line}
                              qcRows={qcRows} bagRows={bagRows} paramRows={paramRows}
                              qcStart={qcStart} bagStart={bagStart} paramStart={paramStart}
                              revealedCount={revealedCount} isFirst={idx === 0} />
                          </div>
                        )
                      })}
                    </>
                  )
                })()}
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
                className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 hover:text-red-500 dark:hover:text-red-400 transition-colors cursor-pointer">
                <CheckCircle2 className="size-3" /> Token set · Change
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
