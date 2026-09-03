'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { CheckCircle2, XCircle, Loader2, AlertTriangle } from 'lucide-react'
import { fetchQC } from '@/lib/api'
import { useErpToken } from '@/hooks/useErpToken'

interface Props {
  erpToken: string
  erpTenantId: string
  onNeedsToken: () => void
  onClearToken: () => void
}

interface CheckRow {
  field: string
  formula: string
  expected: number
  actual: number
  ok: boolean
}

function round(v: number, dp = 4) {
  return Math.round(v * 10 ** dp) / 10 ** dp
}

function validateQCLine(line: any): CheckRow[] {
  const grn_qty = parseFloat(line.grn_qty ?? 0)
  const base_rate = parseFloat(line.base_rate ?? 0)
  const empty_bag_weight = parseFloat(line.empty_bag_weight ?? 0)
  const deduction_percent = parseFloat(line.deduction_percent ?? 0)
  const discount_rate = parseFloat(line.discount_rate ?? 0)

  const total_amount = round(base_rate * grn_qty, 6)
  const empty_bags_txn_amount = round(empty_bag_weight * base_rate, 6)
  const accepted_qty = round(grn_qty - empty_bag_weight, 6)
  const net_of_empty_bag_amount = round(total_amount - empty_bags_txn_amount, 6)
  const qc_deduction_rate = round(base_rate * deduction_percent / 100, 6)
  const deduction_weight = round(accepted_qty * deduction_percent / 100, 6)
  const qc_deduction_amount = round(deduction_weight * base_rate, 6)
  const subtotal = round(net_of_empty_bag_amount - qc_deduction_amount, 6)
  const cash_discount_amount = round(subtotal * discount_rate / 100, 6)
  const txn_currency_amount = round(subtotal - cash_discount_amount, 6)

  const TOLERANCE = 0.02

  function chk(field: string, formula: string, expected: number, actual: number): CheckRow {
    return { field, formula, expected, actual, ok: Math.abs(expected - actual) <= TOLERANCE }
  }

  return [
    chk('total_amount', 'grn_qty × base_rate', total_amount, parseFloat(line.total_amount ?? 0)),
    chk('empty_bags_txn_amount', 'empty_bag_weight × base_rate', empty_bags_txn_amount, parseFloat(line.empty_bags_txn_amount ?? 0)),
    chk('alternate_accepted_qty', 'grn_qty − empty_bag_weight', accepted_qty, parseFloat(line.alternate_accepted_qty ?? 0)),
    chk('net_of_empty_bag_amount', 'total_amount − empty_bags_txn_amount', net_of_empty_bag_amount, parseFloat(line.net_of_empty_bag_amount ?? 0)),
    chk('qc_deduction_rate', 'base_rate × ded% / 100', qc_deduction_rate, parseFloat(line.qc_deduction_rate ?? 0)),
    chk('deduction_weight', 'accepted_qty × ded% / 100', deduction_weight, parseFloat(line.deduction_weight ?? 0)),
    chk('qc_deduction_amount', 'deduction_weight × base_rate', qc_deduction_amount, parseFloat(line.qc_deduction_amount ?? 0)),
    chk('transaction_amount_without_discount', 'net_of_empty_bag − qc_deduction', subtotal, parseFloat(line.transaction_amount_without_discount ?? 0)),
    chk('cash_discount_deduction_amount', 'subtotal × discount% / 100', cash_discount_amount, parseFloat(line.cash_discount_deduction_amount ?? 0)),
    chk('txn_currency_amount', 'subtotal − cash_discount', txn_currency_amount, parseFloat(line.txn_currency_amount ?? 0)),
  ]
}

function validateBags(line: any): CheckRow[] {
  const empty_bag_weight = parseFloat(line.empty_bag_weight ?? 0)
  const bags = (line.qc_bags_details ?? [])[0] ?? {}
  const weight_of_bags = parseFloat(bags.weight_of_bags ?? 0)
  const total_weight_of_bags = parseFloat(bags.total_weight_of_bags ?? 0)
  const TOLERANCE = 0.02

  function chk(field: string, formula: string, expected: number, actual: number): CheckRow {
    return { field, formula, expected, actual, ok: Math.abs(expected - actual) <= TOLERANCE }
  }

  return [
    chk('weight_of_bags', 'empty_bag_weight (per-bag weight)', empty_bag_weight, weight_of_bags),
    chk('total_weight_of_bags', 'empty_bag_weight (1 bag row)', empty_bag_weight, total_weight_of_bags),
  ]
}

function ResultTable({ rows }: { rows: CheckRow[] }) {
  const allOk = rows.every(r => r.ok)
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className={`px-4 py-2 text-sm font-semibold flex items-center gap-2 ${allOk ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'}`}>
        {allOk ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
        {allOk ? 'All checks passed' : `${rows.filter(r => !r.ok).length} check(s) failed`}
      </div>
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400">
            <th className="text-left px-3 py-2 font-medium">Field</th>
            <th className="text-left px-3 py-2 font-medium">Formula</th>
            <th className="text-right px-3 py-2 font-medium">Expected</th>
            <th className="text-right px-3 py-2 font-medium">Actual</th>
            <th className="text-center px-3 py-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className={`border-t border-gray-100 dark:border-gray-700 ${r.ok ? '' : 'bg-red-50 dark:bg-red-900/10'}`}>
              <td className="px-3 py-2 font-mono text-gray-700 dark:text-gray-300">{r.field}</td>
              <td className="px-3 py-2 text-gray-500 dark:text-gray-400">{r.formula}</td>
              <td className="px-3 py-2 text-right font-mono">{r.expected.toFixed(4)}</td>
              <td className="px-3 py-2 text-right font-mono">{r.actual.toFixed(4)}</td>
              <td className="px-3 py-2 text-center">
                {r.ok
                  ? <CheckCircle2 className="w-4 h-4 text-green-500 mx-auto" />
                  : <XCircle className="w-4 h-4 text-red-500 mx-auto" />}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function QCFormulaSection({ erpToken, erpTenantId, onNeedsToken }: Props) {
  const { token, tenantId } = useErpToken(erpToken, erpTenantId)
  const [qcId, setQcId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [qcData, setQcData] = useState<any>(null)

  async function handleFetch() {
    if (!qcId.trim()) return
    if (!token) { onNeedsToken(); return }
    setLoading(true)
    setError('')
    setQcData(null)
    try {
      const data = await fetchQC(token, tenantId, qcId.trim())
      if (data.error) throw new Error(data.error)
      setQcData(data)
    } catch (e: any) {
      setError(e.message ?? 'Failed to fetch QC')
    } finally {
      setLoading(false)
    }
  }

  const lines: any[] = qcData?.qc_details ?? []

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h2 className="text-base font-semibold text-gray-800 dark:text-white">QC Formula Validator</h2>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Enter a QC record ID to validate all calculated fields against the formula.</p>
      </div>

      {/* Input */}
      <div className="flex gap-2 items-center">
        <Input
          placeholder="QC record ID (e.g. 2548)"
          value={qcId}
          onChange={e => setQcId(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleFetch()}
          className="w-56 text-sm"
        />
        <Button onClick={handleFetch} disabled={loading || !qcId.trim()} size="sm">
          {loading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
          {loading ? 'Fetching…' : 'Check'}
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {qcData && (
        <div className="space-y-5">
          {/* Record header */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-3 bg-gray-50 dark:bg-gray-800/50 text-xs space-y-1">
            <div className="font-semibold text-gray-700 dark:text-gray-200 text-sm">{qcData.transaction_ref_no}</div>
            <div className="text-gray-500 dark:text-gray-400">Date: {qcData.transaction_date} · Supplier ID: {qcData.supplier_ref_id} · Status: {qcData.workflow_status}</div>
            <div className="text-gray-500 dark:text-gray-400">Total: {qcData.total_txn_currency_amount}</div>
          </div>

          {lines.map((line, idx) => {
            const formulaRows = validateQCLine(line)
            const bagsRows = validateBags(line)
            return (
              <div key={idx} className="space-y-3">
                <div className="text-sm font-medium text-gray-700 dark:text-gray-200">
                  Line {idx + 1} — Item #{line.item_ref_id} · Rate {line.base_rate} · GRN qty {line.grn_qty} · Bags {line.no_of_bags} · Empty bag wt {line.empty_bag_weight} · Ded% {line.deduction_percent} · Discount% {line.discount_rate ?? 0}
                </div>
                <ResultTable rows={formulaRows} />
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mt-1">Bags detail</div>
                <ResultTable rows={bagsRows} />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
