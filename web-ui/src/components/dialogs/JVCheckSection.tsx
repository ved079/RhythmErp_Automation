'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { CheckCircle2, XCircle, Key, RefreshCw, Loader2, AlertTriangle, Search, Download, FileText, FileSpreadsheet, ChevronDown, FileBarChart2, Maximize2, X, GitCompare } from 'lucide-react'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import Spinner from '@/components/ui/Spinner'
import LoadingCard from '@/components/ui/LoadingCard'
import { verifyJV, verifyInvJV, fetchPBList, fetchPBItems, fetchAccountingDef, crossCheckJV, type JVVerifyStep, type PBListItem, type PBItemLine, type AccountingDefDetail, type InvCommodityRow, type PurbMeta, type CrossCheckResponse } from '@/lib/api'
import { useErpToken } from '@/hooks/useErpToken'

interface Props {
  erpToken: string
  erpTenantId: string
  onNeedsToken: () => void
  onClearToken: () => void
}

const XL_BORDER = '<Borders><Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D6D6D6"/><Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D6D6D6"/><Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D6D6D6"/><Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D6D6D6"/></Borders>'

function escXml(v: string | number | null | undefined): string {
  return String(v ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export function JVCheckSection({ erpToken, erpTenantId, onNeedsToken, onClearToken }: Props) {
  const { token, tenantId, localToken, setLocalToken, localTenantId, setLocalTenantId, handleAuthError } = useErpToken(erpToken, erpTenantId)

  const [showTokenInput, setShowTokenInput] = useState(false)
  const tokenSectionRef = useRef<HTMLDivElement>(null)
  const tokenErrorRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // JV check mode state
  const [pbRefNo, setPbRefNo] = useState('')
  const [selectedPB, setSelectedPB] = useState<PBListItem | null>(null)
  const [jvSteps, setJvSteps] = useState<JVVerifyStep[]>([])
  const [verifying, setVerifying] = useState(false)
  const [jvError, setJvError] = useState('')
  const [pbList, setPbList] = useState<PBListItem[]>([])
  const [pbListLoading, setPbListLoading] = useState(false)
  const [pbListError, setPbListError] = useState('')
  const [pbSearch, setPbSearch] = useState('')
  const [pbListOpen, setPbListOpen] = useState(true)
  const [pbItems, setPbItems] = useState<PBItemLine[]>([])
  const [pbTaxableAmount, setPbTaxableAmount] = useState<number | null>(null)
  const [pbDiscountAmount, setPbDiscountAmount] = useState<number | null>(null)
  const [pbItemsLoading, setPbItemsLoading] = useState(false)
  const [jvAccountRows, setJvAccountRows] = useState<{ account_name: string; dr_cr: string; commodity: string; amount: number | null }[]>([])
  const [accountingDef, setAccountingDef] = useState<AccountingDefDetail[]>([])
  const [accountingDefLoading, setAccountingDefLoading] = useState(false)
  const [notAppliedOpen, setNotAppliedOpen] = useState(false)
  const [purbMeta, setPurbMeta] = useState<PurbMeta | null>(null)
  const [purbFullViewOpen, setPurbFullViewOpen] = useState(false)

  useEffect(() => {
    if (showTokenInput) {
      tokenSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [showTokenInput])

  // Scroll the token error banner into view within the scrollable container
  useEffect(() => {
    if (!localToken) return
    const t = localToken.startsWith('Bearer ') ? localToken.slice(7) : localToken
    const isInvalid = !(t.startsWith('eyJ') && t.split('.').length === 3 && t.length > 100)
    if (isInvalid) {
      requestAnimationFrame(() => {
        if (!tokenErrorRef.current || !scrollContainerRef.current) return
        const container = scrollContainerRef.current
        const el = tokenErrorRef.current
        const containerRect = container.getBoundingClientRect()
        const elRect = el.getBoundingClientRect()
        const offset = elRect.top - containerRect.top + container.scrollTop - container.clientHeight / 2 + el.offsetHeight / 2
        container.scrollTo({ top: offset, behavior: 'smooth' })
      })
    }
  }, [localToken])

  const loadPBList = useCallback(async () => {
    if (!token || !tenantId) return
    setPbListLoading(true)
    setPbListError('')
    try {
      const list = await fetchPBList(token, tenantId)
      setPbList(list)
    } catch (err) {
      if (!handleAuthError(err)) setPbListError(err instanceof Error ? err.message : String(err))
    } finally {
      setPbListLoading(false)
    }
  }, [token, tenantId, handleAuthError])

  // Stable ref — always points to latest callback so effects don't go stale
  const loadPBListRef = useRef(loadPBList)
  useEffect(() => { loadPBListRef.current = loadPBList }, [loadPBList])

  const hasToken = !!token && !!tenantId

  // Auto-load PB list on mount
  useEffect(() => {
    if (!hasToken) return
    loadPBListRef.current()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasToken])

  const handleVerify = async (refOverride?: string) => {
    const ref = (refOverride ?? pbRefNo).trim()
    if (!token || !tenantId || !ref) return
    setVerifying(true)
    setJvSteps([])
    setJvError('')
    setJvAccountRows([])
    setAccountingDef([])
    try {
      const [jvRes] = await Promise.all([
        verifyJV(token, tenantId, ref),
        // Fetch accounting definition in parallel
        (async () => {
          setAccountingDefLoading(true)
          try {
            const def = await fetchAccountingDef(token, tenantId, '5')
            setAccountingDef(def.details)
          } catch { /* silently skip */ }
          finally { setAccountingDefLoading(false) }
        })(),
      ])
      setJvSteps(jvRes.steps)
      setJvAccountRows(jvRes.account_rows ?? [])
      setPurbMeta(jvRes.purb_meta ?? null)
    } catch (err) {
      if (!handleAuthError(err)) setJvError(err instanceof Error ? err.message : String(err))
    } finally {
      setVerifying(false)
    }
  }

  // PB vs JV comparison rows — shared by the on-screen sheet and the export.
  const jvCompRows = React.useMemo<{ label: string; pb: string; jv: string; indent?: boolean }[] | null>(() => {
    const fieldsStep = jvSteps.find(s => s.fields)
    if (!selectedPB || !fieldsStep) return null
    const jvCommodity = fieldsStep.fields?.find(f => f.field === 'Commodity')?.value || '—'
    const uniqueItems = [...new Set(pbItems.map(i => i.name))]
    // jvCommodity may be comma-joined list for multi-item PBs
    const jvCommodityList = jvCommodity !== '—' ? jvCommodity.split(',').map(s => s.trim().toLowerCase()) : []
    const commodityRows: { label: string; pb: string; jv: string }[] =
      pbItems.length > 0
        ? uniqueItems.map((name, idx) => {
            const nameL = name.trim().toLowerCase()
            const matchedJv = jvCommodityList.find(c => c === nameL || c.includes(nameL) || nameL.includes(c))
            return { label: idx === 0 ? 'Commodity' : '', pb: name, jv: matchedJv ? name : '—' }
          })
        : [{ label: 'Commodity', pb: pbItemsLoading ? 'Loading…' : '—', jv: jvCommodity }]
    const fmtAmt = (n: number) => n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    const pbAmtStr = selectedPB.amount != null ? fmtAmt(Number(selectedPB.amount)) : '—'
    // Use the Payable (Credit) row as JV transaction amount — it equals the actual
    // supplier liability and excludes discount contra-entries that inflate the DR total.
    // Fallback to the largest single credit row if "payable" isn't found by name.
    const creditRows = jvAccountRows.filter(r => r.dr_cr === 'Credit')
    const payableRow = creditRows.find(r => r.account_name.toLowerCase().includes('payable'))
      ?? creditRows.reduce<typeof creditRows[0] | null>((best, r) => (r.amount ?? 0) > (best?.amount ?? 0) ? r : best, null)
    const jvAmtStr = payableRow?.amount != null ? fmtAmt(payableRow.amount) : jvAccountRows.length > 0 ? '—' : '—'
    // Per-item tax rows interleaved after each commodity row
    // Match JV tax row by amount (exact). Track used rows by absolute index into jvAccountRows
    // so IGST and CGST/SGST lookups don't corrupt each other's "used" state.
    const usedJvRowIndices = new Set<number>()
    const jvTaxRow = (keyword: string, pbAmt: number) => {
      const candidates = jvAccountRows
        .map((r, i) => ({ r, i }))
        .filter(({ r, i }) => r.dr_cr === 'Debit' && r.account_name.toLowerCase().includes(keyword) && !usedJvRowIndices.has(i))
      const match = candidates.find(({ r }) => r.amount != null && Math.abs((r.amount ?? 0) - pbAmt) < 0.02)
        ?? candidates[0]
      if (match) usedJvRowIndices.add(match.i)
      return match?.r?.amount != null ? fmtAmt(match.r.amount) : jvAccountRows.length > 0 ? '—' : '—'
    }
    const commodityWithTax: { label: string; pb: string; jv: string; indent?: boolean }[] = []
    for (const item of pbItems.length > 0 ? pbItems : []) {
      const nameL = item.name.trim().toLowerCase()
      const jvCommodityList = jvCommodity !== '—' ? jvCommodity.split(',').map(s => s.trim().toLowerCase()) : []
      const matchedJv = jvCommodityList.find(c => c === nameL || c.includes(nameL) || nameL.includes(c))
      commodityWithTax.push({ label: 'Commodity', pb: item.name, jv: matchedJv ? item.name : '—' })
      if (item.igst_amount != null && item.igst_amount > 0) {
        commodityWithTax.push({ label: 'IGST Amount', pb: fmtAmt(item.igst_amount), jv: jvTaxRow('igst', item.igst_amount), indent: true })
      } else {
        if (item.cgst_amount != null && item.cgst_amount > 0)
          commodityWithTax.push({ label: 'CGST Amount', pb: fmtAmt(item.cgst_amount), jv: jvTaxRow('cgst', item.cgst_amount), indent: true })
        if (item.sgst_amount != null && item.sgst_amount > 0)
          commodityWithTax.push({ label: 'SGST Amount', pb: fmtAmt(item.sgst_amount), jv: jvTaxRow('sgst', item.sgst_amount), indent: true })
      }
    }
    const finalCommodityRows = commodityWithTax.length > 0 ? commodityWithTax : commodityRows
    // Purchase Base: DR row named "purchase" but NOT a tax or discount row
    const purchaseDebitRow = jvAccountRows.find(r => {
      const n = r.account_name.toLowerCase()
      return r.dr_cr === 'Debit' && n.includes('purchase') && !n.includes('igst') && !n.includes('cgst') && !n.includes('sgst') && !n.includes('discount')
    })
    const pbBaseStr = pbTaxableAmount != null ? fmtAmt(pbTaxableAmount) : '—'
    const jvBaseStr = purchaseDebitRow?.amount != null ? fmtAmt(purchaseDebitRow.amount) : jvAccountRows.length > 0 ? '—' : '—'
    // Discount: DR row named "discount" — only shown when PB has a discount
    const discountDebitRow = jvAccountRows.find(r => r.dr_cr === 'Debit' && r.account_name.toLowerCase().includes('discount'))
    const discountRows: { label: string; pb: string; jv: string; indent?: boolean }[] =
      pbDiscountAmount != null && pbDiscountAmount > 0
        ? [{ label: 'Discount Amount', pb: fmtAmt(pbDiscountAmount), jv: discountDebitRow?.amount != null ? fmtAmt(discountDebitRow.amount) : jvAccountRows.length > 0 ? '—' : '—' }]
        : []
    return [
      { label: 'Division',            pb: selectedPB.division    || '—', jv: fieldsStep.fields?.find(f => f.field === 'Division')?.value    || '—' },
      { label: 'Department',          pb: selectedPB.department  || '—', jv: fieldsStep.fields?.find(f => f.field === 'Department')?.value  || '—' },
      { label: 'Type of Sale',        pb: selectedPB.type_of_sale || '—', jv: fieldsStep.fields?.find(f => f.field === 'Type of Sale')?.value || '—' },
      { label: 'Location',            pb: selectedPB.location    || '—', jv: fieldsStep.fields?.find(f => f.field === 'Location')?.value    || '—' },
      { label: 'Purchase Base',       pb: pbBaseStr, jv: jvBaseStr },
      ...finalCommodityRows,
      ...discountRows,
      { label: 'Transaction Amount',  pb: pbAmtStr,  jv: jvAmtStr },
    ]
  }, [jvSteps, selectedPB, pbItems, pbItemsLoading, jvAccountRows, pbTaxableAmount, pbDiscountAmount])

  // Export the JV verification report as a formatted Excel workbook using
  // SpreadsheetML (XML Spreadsheet 2003) — supports fonts, fills, borders and
  // number formats without any extra dependency.
  const exportJvReport = useCallback(() => {
    const found = jvSteps.find(s => s.n === 1)
    const fieldsStep = jvSteps.find(s => s.fields)
    const balanceStep = jvSteps.find(s => s.detail && !s.fields)
    if (!selectedPB || (!found && !fieldsStep)) return
    const fieldMismatch = (jvCompRows ?? []).some(r => r.pb !== '—' && r.jv !== '—' && r.pb.trim().toLowerCase() !== r.jv.trim().toLowerCase())
    const _defMap = new Map<string, typeof accountingDef[0]>()
    for (const d of accountingDef) { const k = d.account_name.trim().toLowerCase()+'|'+(d.dr_cr||'').toLowerCase(); if (!_defMap.has(k)) _defMap.set(k,d) }
    const accountRowFail = jvAccountRows.some(r => !_defMap.has(r.account_name.trim().toLowerCase()+'|'+(r.dr_cr||'').toLowerCase()))
    const _xlCr = jvAccountRows.filter(r => r.dr_cr === 'Credit')
    const _xlPayRow = _xlCr.find(r => r.account_name.toLowerCase().includes('payable')) ?? _xlCr.reduce<typeof _xlCr[0]|null>((b,r)=>(r.amount??0)>(b?.amount??0)?r:b,null)
    const amountMismatch = selectedPB.amount != null && _xlPayRow?.amount != null && Math.abs(Number(selectedPB.amount) - _xlPayRow.amount) > 0.02
    const ok = jvSteps.length > 0 && jvSteps.every(s => s.ok) && !fieldMismatch && !accountRowFail && !amountMismatch
    const balMatch = balanceStep?.detail?.match(/DR\s*=\s*([\d,]+\.?\d*)\s+\|CR\|\s*=\s*([\d,]+\.?\d*)/)
    const amountNum = selectedPB.amount != null ? Number(selectedPB.amount) : null

    // 5 columns: Account/Label(140) | Value/DrCr(145) | Amount(95) | Condition/Value(165) | Status(90)
    const cell = (style: string, value: string | number, mergeAcross?: number) => {
      const type = typeof value === 'number' ? 'Number' : 'String'
      return `<Cell${mergeAcross != null ? ` ss:MergeAcross="${mergeAcross}"` : ''}${style ? ` ss:StyleID="${style}"` : ''}><Data ss:Type="${type}">${escXml(value)}</Data></Cell>`
    }
    const emptyCell = (style = 'sVal') => `<Cell ss:StyleID="${style}"><Data ss:Type="String"></Data></Cell>`

    const rows: string[] = []

    // Title banner (spans all 5 cols via mergeAcross=4)
    rows.push(`<Row ss:Height="28">${cell('sTitle', 'JV VERIFICATION REPORT', 3)}${cell(ok ? 'sPass' : 'sFail', ok ? '✓ PASSED' : '✕ FAILED')}</Row>`)
    rows.push(`<Row ss:Height="16">${cell('sMeta', `Document: ${pbRefNo}`, 2)}${cell('sMeta', `Generated: ${new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}`, 2)}</Row>`)
    rows.push('<Row ss:Height="8"/>')

    // Document Details
    rows.push(`<Row ss:Height="19">${cell('sSection', 'DOCUMENT DETAILS', 4)}</Row>`)
    rows.push(`<Row>${cell('sLabel', 'Supplier')}${cell('sVal', selectedPB.supplier ?? '—', 3)}</Row>`)
    rows.push(`<Row>${cell('sLabel', 'Amount')}${amountNum != null ? cell('sMoney', amountNum) : cell('sVal', '—')}${cell('sLabel', 'Date')}${cell('sVal', selectedPB.date ?? '—')}${emptyCell()}</Row>`)
    rows.push('<Row ss:Height="8"/>')

    // Journal Voucher
    rows.push(`<Row ss:Height="19">${cell('sSection', 'JOURNAL VOUCHER', 4)}</Row>`)
    rows.push(`<Row>${cell('sLabel', 'JV Entry')}${cell(found ? (found.ok ? 'sPassText' : 'sFailText') : 'sDim', found ? (found.ok ? 'Entry found in JV report' : `Not found — ${found.detail ?? ''}`) : 'Not checked', 3)}</Row>`)
    if (balMatch) {
      const drNum = Number(balMatch[1].replace(/,/g, ''))
      const crNum = Number(balMatch[2].replace(/,/g, ''))
      rows.push(`<Row>${cell('sLabel', 'Balance Check')}${cell('sDr', drNum)}${cell('sCr', crNum)}${cell(balanceStep?.ok ? 'sPass' : 'sFail', balanceStep?.ok ? 'BALANCED ✓' : 'UNBALANCED ✕')}${emptyCell()}</Row>`)
    }
    rows.push('<Row ss:Height="8"/>')

    // Field Cross-Check
    const xrows: { label: string; pb: string; jv: string; indent?: boolean }[] = jvCompRows ?? fieldsStep?.fields?.map(f => ({ label: f.field, pb: '—', jv: f.value })) ?? []
    if (xrows.length > 0) {
      rows.push(`<Row ss:Height="19">${cell('sSection', 'ACCOUNTING FIELD CROSS-CHECK', 4)}</Row>`)
      rows.push(`<Row>${cell('sHead', 'Field')}${cell('sHead', 'Purchase Booking')}${cell('sHeadC', '↔')}${cell('sHead', 'Journal Voucher')}${cell('sHeadC', 'Match')}</Row>`)
      for (const r of xrows) {
        const match = r.pb !== '—' && r.jv !== '—' && r.pb.trim().toLowerCase() === r.jv.trim().toLowerCase()
        const unknown = r.pb === '—' || r.jv === '—'
        const labelCell = r.indent
          ? cell('sDim', `  · ${r.label}`)
          : cell(r.label ? 'sLabel' : 'sDim', r.label || '')
        rows.push(`<Row${r.indent ? ' ss:Height="15"' : ''}>${labelCell}${cell(unknown ? 'sDim' : match ? 'sVal' : 'sFail', r.pb)}${emptyCell('sDimC')}${cell(unknown ? 'sDim' : match ? 'sVal' : 'sFail', r.jv)}${cell(unknown ? 'sDimC' : match ? 'sPass' : 'sFail', unknown ? '—' : match ? 'PASS' : 'FAIL')}</Row>`)
      }
      rows.push('<Row ss:Height="8"/>')
    }

    // Accounting Definition — Applied Rules
    if (jvAccountRows.length > 0 && accountingDef.length > 0) {
      const normName = (s: string) => s.trim().toLowerCase()
      const defByName = new Map<string, typeof accountingDef[0]>()
      for (const d of accountingDef) {
        const k = normName(d.account_name) + '|' + (d.dr_cr || '').toLowerCase()
        if (!defByName.has(k)) defByName.set(k, d)
      }
      const groups = new Map<string, typeof jvAccountRows>()
      for (const row of jvAccountRows) {
        const key = row.commodity || ''
        if (!groups.has(key)) groups.set(key, [])
        groups.get(key)!.push(row)
      }
      const sortedKeys = [...groups.keys()].sort((a, b) =>
        a === '' ? 1 : b === '' ? -1 : a.localeCompare(b),
      )
      const jvAccountNameSet = new Set(jvAccountRows.map(r => normName(r.account_name)))
      const notApplied = accountingDef.filter((d, i, arr) => {
        const k = normName(d.account_name)
        const firstIdx = arr.findIndex(x => normName(x.account_name) === k && x.dr_cr === d.dr_cr)
        return firstIdx === i && !jvAccountNameSet.has(k)
      })

      rows.push(`<Row ss:Height="19">${cell('sSection', 'ACCOUNTING DEFINITION — APPLIED RULES', 4)}</Row>`)
      rows.push(`<Row>${cell('sHead', 'Account')}${cell('sHeadC', 'Dr/Cr')}${cell('sHeadR', 'Amount')}${cell('sHead', 'Rule / Condition')}${cell('sHeadC', 'Status')}</Row>`)

      for (const commodity of sortedKeys) {
        rows.push(`<Row ss:Height="15">${cell('sGroup', commodity ? commodity.toUpperCase() : 'SHARED — all items', 4)}</Row>`)
        const groupRows = groups.get(commodity)!
        let groupDr = 0, groupCr = 0
        for (const row of groupRows) {
          const def = defByName.get(normName(row.account_name) + '|' + (row.dr_cr || '').toLowerCase())
          const drCrMatch = !!def && def.dr_cr === row.dr_cr
          const status = !def ? 'EXTRA' : drCrMatch ? 'PASS' : 'WRONG TYPE'
          const condText = def?.condition_text || (def ? 'Always applies' : '—')
          const amtStyle = row.dr_cr === 'Debit' ? 'sDr' : 'sCr'
          if (row.amount != null) { row.dr_cr === 'Debit' ? (groupDr += row.amount) : (groupCr += row.amount) }
          const amtCell = row.amount != null ? cell(amtStyle, row.amount) : emptyCell('sValR')
          rows.push(`<Row>${cell('sVal', row.account_name)}${cell('sDrCrBadge', row.dr_cr)}${amtCell}${cell('sCond', condText)}${cell(status === 'PASS' ? 'sPass' : status === 'EXTRA' ? 'sFail' : 'sWarn', status)}</Row>`)
        }
        if (groupRows.length > 1) {
          rows.push(`<Row ss:Height="15">${emptyCell('sSubtotalL')}${cell('sSubtotalL', 'Subtotal')}${cell('sSubtotalR', groupDr || '')}${cell('sSubtotalR', groupCr || '')}${emptyCell('sSubtotalL')}</Row>`)
        }
      }

      // Grand totals row
      const totalDr = jvAccountRows.filter(r => r.dr_cr === 'Debit' && r.amount != null).reduce((s, r) => s + r.amount!, 0)
      const totalCr = jvAccountRows.filter(r => r.dr_cr === 'Credit' && r.amount != null).reduce((s, r) => s + r.amount!, 0)
      const balanced = Math.abs(totalDr - totalCr) < 0.01
      rows.push(`<Row ss:Height="18">${cell('sTotalL', 'TOTALS', 1)}${cell('sTotalDr', totalDr)}${cell('sTotalCr', totalCr)}${cell(balanced ? 'sPass' : 'sFail', balanced ? 'DR = CR ✓' : 'DR ≠ CR ✕')}</Row>`)

      if (notApplied.length > 0) {
        rows.push('<Row ss:Height="8"/>')
        rows.push(`<Row ss:Height="15">${cell('sGroupMuted', 'NOT APPLIED THIS TRANSACTION', 4)}</Row>`)
        rows.push(`<Row>${cell('sHeadMuted', 'Account')}${cell('sHeadMuted', 'Dr/Cr')}${cell('sHeadMuted', '—')}${cell('sHeadMuted', 'Why not applied (condition)')}${cell('sHeadMuted', '—')}</Row>`)
        for (const def of notApplied) {
          rows.push(`<Row>${cell('sDim', def.account_name)}${cell('sDimC', def.dr_cr)}${emptyCell('sDim')}${cell('sDim', def.condition_text || '—')}${cell('sDimC', 'n/a')}</Row>`)
        }
      }
    }
    rows.push('<Row ss:Height="12"/>')
    rows.push(`<Row ss:Height="14">${cell('sMeta', 'Generated by Pacs Automation — JV Verification Report', 4)}</Row>`)

    const XL_BORDER_DARK = '<Borders><Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/><Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/><Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/><Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/></Borders>'
    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
<Styles>
<Style ss:ID="Default" ss:Name="Normal"><Font ss:FontName="Calibri" ss:Size="10" ss:Color="#212121"/><Alignment ss:Vertical="Center"/></Style>
<Style ss:ID="sTitle"><Font ss:Bold="1" ss:Size="15" ss:Color="#FFFFFF"/><Interior ss:Color="#283593" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="2"/></Style>
<Style ss:ID="sMeta"><Font ss:Italic="1" ss:Size="9" ss:Color="#546E7A"/><Alignment ss:Vertical="Center" ss:Indent="1"/></Style>
<Style ss:ID="sSection"><Font ss:Bold="1" ss:Size="10" ss:Color="#1A237E"/><Interior ss:Color="#C5CAE9" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sLabel"><Font ss:Bold="1" ss:Size="10" ss:Color="#37474F"/><Interior ss:Color="#ECEFF1" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sVal"><Font ss:Color="#212121"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sValR"><Font ss:Color="#212121"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sMoney"><Font ss:Color="#212121"/><NumberFormat ss:Format="#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDr"><Font ss:Bold="1" ss:Color="#0D47A1"/><NumberFormat ss:Format="&quot;DR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sCr"><Font ss:Bold="1" ss:Color="#4A148C"/><NumberFormat ss:Format="&quot;CR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHead"><Font ss:Bold="1" ss:Size="10" ss:Color="#FFFFFF"/><Interior ss:Color="#3949AB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Left" ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHeadC"><Font ss:Bold="1" ss:Size="10" ss:Color="#FFFFFF"/><Interior ss:Color="#3949AB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHeadR"><Font ss:Bold="1" ss:Size="10" ss:Color="#FFFFFF"/><Interior ss:Color="#3949AB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Right" ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHeadMuted"><Font ss:Bold="1" ss:Size="9" ss:Color="#ECEFF1"/><Interior ss:Color="#607D8B" ss:Pattern="Solid"/><Alignment ss:Horizontal="Left" ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sPass"><Font ss:Bold="1" ss:Size="10" ss:Color="#1B5E20"/><Interior ss:Color="#A5D6A7" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sFail"><Font ss:Bold="1" ss:Size="10" ss:Color="#B71C1C"/><Interior ss:Color="#EF9A9A" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sWarn"><Font ss:Bold="1" ss:Size="10" ss:Color="#BF360C"/><Interior ss:Color="#FFCC80" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sPassText"><Font ss:Bold="1" ss:Color="#2E7D32"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sFailText"><Font ss:Bold="1" ss:Color="#C62828"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDim"><Font ss:Color="#78909C"/><Interior ss:Color="#F9FAFB" ss:Pattern="Solid"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDimC"><Font ss:Color="#78909C"/><Interior ss:Color="#F9FAFB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sGroup"><Font ss:Bold="1" ss:Italic="1" ss:Size="9" ss:Color="#1A237E"/><Interior ss:Color="#E8EAF6" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sGroupMuted"><Font ss:Bold="1" ss:Italic="1" ss:Size="9" ss:Color="#546E7A"/><Interior ss:Color="#ECEFF1" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDrCrBadge"><Font ss:Bold="1" ss:Size="9" ss:Color="#37474F"/><Interior ss:Color="#ECEFF1" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sCond"><Font ss:FontName="Consolas" ss:Size="9" ss:Color="#37474F"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sTotalL"><Font ss:Bold="1" ss:Size="10" ss:Color="#212121"/><Interior ss:Color="#CFD8DC" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sTotalDr"><Font ss:Bold="1" ss:Color="#0D47A1"/><Interior ss:Color="#BBDEFB" ss:Pattern="Solid"/><NumberFormat ss:Format="&quot;DR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sTotalCr"><Font ss:Bold="1" ss:Color="#4A148C"/><Interior ss:Color="#E1BEE7" ss:Pattern="Solid"/><NumberFormat ss:Format="&quot;CR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sSubtotalL"><Font ss:Italic="1" ss:Color="#546E7A"/><Interior ss:Color="#F5F5F5" ss:Pattern="Solid"/><Alignment ss:Horizontal="Right" ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sSubtotalR"><Font ss:Italic="1" ss:Color="#546E7A"/><Interior ss:Color="#F5F5F5" ss:Pattern="Solid"/><NumberFormat ss:Format="#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
</Styles>
<Worksheet ss:Name="JV Report">
<Table ss:DefaultRowHeight="18">
<Column ss:Width="140"/>
<Column ss:Width="145"/>
<Column ss:Width="95"/>
<Column ss:Width="165"/>
<Column ss:Width="90"/>
${rows.join('\n')}
</Table>
</Worksheet>
</Workbook>`

    const blob = new Blob([xml], { type: 'application/vnd.ms-excel;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${pbRefNo.replace(/[\\/]/g, '-')}_JV_Report.xls`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }, [selectedPB, jvSteps, jvCompRows, jvAccountRows, accountingDef, pbRefNo])

  // PDF export — same content as the .xls export but laid out as a styled A4
  // report (jsPDF) that opens in a new browser tab instead of downloading.
  const exportJvPdf = useCallback(async () => {
    const found = jvSteps.find(s => s.n === 1)
    const fieldsStep = jvSteps.find(s => s.fields)
    const balanceStep = jvSteps.find(s => s.detail && !s.fields)
    if (!selectedPB || (!found && !fieldsStep)) return
    const fieldMismatch = (jvCompRows ?? []).some(r => r.pb !== '—' && r.jv !== '—' && r.pb.trim().toLowerCase() !== r.jv.trim().toLowerCase())
    const _defMap = new Map<string, typeof accountingDef[0]>()
    for (const d of accountingDef) { const k = d.account_name.trim().toLowerCase()+'|'+(d.dr_cr||'').toLowerCase(); if (!_defMap.has(k)) _defMap.set(k,d) }
    const accountRowFail = jvAccountRows.some(r => !_defMap.has(r.account_name.trim().toLowerCase()+'|'+(r.dr_cr||'').toLowerCase()))
    const _pdfCr = jvAccountRows.filter(r => r.dr_cr === 'Credit')
    const _pdfPayRow = _pdfCr.find(r => r.account_name.toLowerCase().includes('payable')) ?? _pdfCr.reduce<typeof _pdfCr[0]|null>((b,r)=>(r.amount??0)>(b?.amount??0)?r:b,null)
    const amountMismatch = selectedPB.amount != null && _pdfPayRow?.amount != null && Math.abs(Number(selectedPB.amount) - _pdfPayRow.amount) > 0.02
    const ok = jvSteps.length > 0 && jvSteps.every(s => s.ok) && !fieldMismatch && !accountRowFail && !amountMismatch
    const balMatch = balanceStep?.detail?.match(/DR\s*=\s*([\d,]+\.?\d*)\s+\|CR\|\s*=\s*([\d,]+\.?\d*)/)
    const amountNum = selectedPB.amount != null ? Number(selectedPB.amount) : null

    const { jsPDF } = await import('jspdf')
    const doc = new jsPDF({ unit: 'mm', format: 'a4' })
    const PW = 210, PH = 297, M = 14, CW = PW - M * 2 // 182mm content width

    const safe = (v: string | number | null | undefined) =>
      String(v ?? '')
        .replace(/₹/g, 'Rs. ').replace(/[—–]/g, '-').replace(/[‘’]/g, "'")
        .replace(/[“”]/g, '"').replace(/·/g, '|').replace(/≥/g, '>=')
        .replace(/≤/g, '<=').replace(/×/g, 'x').replace(/ /g, ' ')
        .replace(/↔/g, '<->').replace(/≠/g, '!=').replace(/✓/g, 'OK').replace(/✕/g, 'X')

    const fmt = (n: number) => n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    // ── Palette ──
    const NAVY: [number,number,number]    = [40, 53, 147]
    const NAVY_D: [number,number,number]  = [26, 35, 126]
    const HEAD_BG: [number,number,number] = [57, 73, 171]
    const SEC_BG: [number,number,number]  = [197, 202, 233]
    const LBL_BG: [number,number,number]  = [236, 239, 241]
    const BDR: [number,number,number]     = [176, 176, 176]
    const TXT: [number,number,number]     = [33, 33, 33]
    const TXT_MED: [number,number,number] = [33, 33, 33] // used for condition/rule text — same as body so small mono stays readable
    const TXT_DIM: [number,number,number] = [84, 100, 114] // ~5.5:1 on white — muted but AA-readable
    const DR_T: [number,number,number]    = [13, 71, 161]
    const CR_T: [number,number,number]    = [74, 20, 140]
    const GRN_F: [number,number,number]   = [165, 214, 167], GRN_T: [number,number,number] = [27, 94, 32]
    const RED_F: [number,number,number]   = [239, 154, 154], RED_T: [number,number,number] = [183, 28, 28]
    const AMB_F: [number,number,number]   = [255, 204, 128], AMB_T: [number,number,number] = [191, 54, 12]
    const DR_F: [number,number,number]    = [187, 222, 251]
    const CR_F: [number,number,number]    = [225, 190, 231]
    const TOT_F: [number,number,number]   = [207, 216, 220]
    const STATUS_S: Record<string,{fill:[number,number,number];text:[number,number,number]}|undefined> = {
      PASS:{fill:GRN_F,text:GRN_T}, MATCHED:{fill:GRN_F,text:GRN_T}, PASSED:{fill:GRN_F,text:GRN_T},
      FAIL:{fill:RED_F,text:RED_T}, EXTRA:{fill:RED_F,text:RED_T}, MISMATCHED:{fill:RED_F,text:RED_T}, FAILED:{fill:RED_F,text:RED_T},
      'WRONG TYPE':{fill:AMB_F,text:AMB_T},
    }

    let y = M
    const need = (h: number) => { if (y + h > PH - M - 8) { doc.addPage(); y = M } }

    type CS = {
      t: string; span?: number; align?: 'L'|'C'|'R'
      color?: [number,number,number]; fill?: [number,number,number]|null
      bold?: boolean; italic?: boolean; size?: number; mono?: boolean; lbl?: boolean
    }

    // Factory — builds a row renderer for a given column-width array (mm).
    const makeRow = (cols: number[]) => (cells: CS[], h = 6.5) => {
      const PAD = 2.5
      const MAX_LINES = 5
      let colIdx = 0
      const measured = cells.map((c) => {
        const span = c.span ?? 1
        const cw = cols.slice(colIdx, colIdx + span).reduce((a, b) => a + b, 0)
        const fs = c.size ?? (c.lbl ? 8 : 9)
        doc.setFont(c.mono ? 'courier' : 'helvetica', (c.bold || c.lbl) && c.italic ? 'bolditalic' : c.bold || c.lbl ? 'bold' : c.italic ? 'italic' : 'normal')
        doc.setFontSize(fs)
        let lines: string[] = doc.splitTextToSize(safe(c.t), cw - PAD * 2)
        if (lines.length > MAX_LINES) {
          lines = lines.slice(0, MAX_LINES)
          lines[MAX_LINES - 1] = lines[MAX_LINES - 1].replace(/.{3}$/, '') + '...'
        }
        colIdx += span
        return { c, cw, fs, lines }
      })
      const rh = Math.max(h, ...measured.map(m => m.lines.length * m.fs * 0.353 * 1.25 + 2.4))
      need(rh)

      doc.setDrawColor(...BDR)
      let cx = M
      for (const { c, cw, fs, lines } of measured) {
        if (c.fill !== null) {
          const bg = c.fill ?? (c.lbl ? LBL_BG : null)
          if (bg) { doc.setFillColor(...bg); doc.rect(cx, y, cw, rh, 'FD') }
          else doc.rect(cx, y, cw, rh, 'S')
        }
        doc.setFont(c.mono ? 'courier' : 'helvetica', (c.bold || c.lbl) && c.italic ? 'bolditalic' : c.bold || c.lbl ? 'bold' : c.italic ? 'italic' : 'normal')
        doc.setFontSize(fs)
        doc.setTextColor(...(c.color ?? (c.lbl ? TXT_MED : TXT)))
        const tx = c.align==='C' ? cx+cw/2 : c.align==='R' ? cx+cw-PAD : cx+PAD
        const alignOpt = c.align==='C' ? 'center' as const : c.align==='R' ? 'right' as const : 'left' as const
        const lineStep = fs * 0.353 * 1.25
        let ly = y + (rh - lines.length * lineStep) / 2 + fs * 0.353 * 0.9
        for (const ln of lines) {
          doc.text(ln, tx, ly, { align: alignOpt })
          ly += lineStep
        }
        cx += cw
      }
      y += rh
    }

    // 4-col layout for cross-check [Field | PB | JV | Match]
    const COLS4: number[] = [42, 58, 58, 24]
    const row4 = makeRow(COLS4)
    // 5-col layout for AD section [Account | Dr/Cr | Amount | Condition | Status]
    const COLS5: number[] = [40, 16, 34, 70, 22]
    const row5 = makeRow(COLS5)

    const sectionHeader = (title: string) => {
      need(14); y += 4
      doc.setFillColor(...SEC_BG); doc.rect(M, y, CW, 7.5, 'F')
      doc.setDrawColor(...BDR); doc.rect(M, y, CW, 7.5, 'S')
      doc.setFont('helvetica', 'bold'); doc.setFontSize(9); doc.setTextColor(...NAVY_D)
      doc.text(title.toUpperCase(), M+3, y+5)
      y += 7.5
    }

    const groupBand = (title: string, muted = false) => {
      need(7)
      const bg: [number,number,number] = muted ? [236,239,241] : [232,234,246]
      const tc: [number,number,number] = muted ? TXT_DIM : NAVY_D
      doc.setFillColor(...bg); doc.rect(M, y, CW, 6, 'F')
      doc.setDrawColor(...BDR); doc.rect(M, y, CW, 6, 'S')
      doc.setFont('helvetica', 'bolditalic'); doc.setFontSize(8); doc.setTextColor(...tc)
      doc.text(safe(title), M+3, y+4)
      y += 6
    }

    // ── Title banner ──
    doc.setFillColor(...NAVY); doc.rect(M, y, CW, 16, 'F')
    doc.setFont('helvetica','bold'); doc.setFontSize(15); doc.setTextColor(255,255,255)
    doc.text('JV VERIFICATION REPORT', M+4, y+10.5)
    const chipText = ok ? 'PASSED' : 'FAILED'
    const st = STATUS_S[chipText]!
    doc.setFontSize(10)
    const chipW = doc.getTextWidth(chipText)+7
    doc.setFillColor(...st.fill); doc.roundedRect(PW-M-chipW-2, y+4.5, chipW, 7.5, 1.5, 1.5, 'F')
    doc.setTextColor(...st.text); doc.text(chipText, PW-M-chipW+1, y+9.5)
    y += 16

    // meta line
    doc.setFont('helvetica','italic'); doc.setFontSize(8); doc.setTextColor(...TXT_DIM)
    y += 5
    doc.text(safe(`Document: ${pbRefNo}   |   Generated: ${new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}`), M+1, y)
    y += 3

    // ── Document Details ──
    sectionHeader('Document Details')
    row4([{ t:'Supplier', lbl:true }, { t:safe(selectedPB.supplier??'-'), span:3 }])
    row4([
      { t:'Amount', lbl:true },
      amountNum!=null ? { t:`Rs. ${fmt(amountNum)}`, align:'R', bold:true, color:TXT } : { t:'-', color:TXT_DIM },
      { t:'Date', lbl:true },
      { t:safe(selectedPB.date??'-') },
    ])

    // ── Journal Voucher ──
    sectionHeader('Journal Voucher')
    row4([
      { t:'JV Entry', lbl:true },
      found
        ? { t: found.ok ? 'Entry found in JV report' : `Not found - ${found.detail??''}`, span:3, bold:true, color:found.ok?GRN_T:RED_T }
        : { t:'Not checked', span:3, color:TXT_DIM },
    ])
    if (balMatch) {
      const drNum = Number(balMatch[1].replace(/,/g,''))
      const crNum = Number(balMatch[2].replace(/,/g,''))
      const bOk = !!balanceStep?.ok
      row4([
        { t:'Balance Check', lbl:true },
        { t:`DR  ${fmt(drNum)}`, mono:true, color:DR_T, size:8 },
        { t:`CR  ${fmt(crNum)}`, mono:true, color:CR_T, size:8 },
        { t:bOk?'BALANCED':'UNBALANCED', align:'C', bold:true, size:8, fill:bOk?GRN_F:RED_F, color:bOk?GRN_T:RED_T },
      ])
    }

    // ── Accounting Field Cross-check ──
    const xrows: { label: string; pb: string; jv: string; indent?: boolean }[] = jvCompRows ?? fieldsStep?.fields?.map(f => ({ label:f.field, pb:'—', jv:f.value })) ?? []
    if (xrows.length > 0) {
      sectionHeader('Accounting Field Cross-check')
      row4([
        { t:'Field',            fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Purchase Booking', fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Journal Voucher',  fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Match',            fill:HEAD_BG, color:[255,255,255], size:8, align:'C' },
      ], 7)
      for (const r of xrows) {
        const match = r.pb!=='—' && r.jv!=='—' && r.pb.trim().toLowerCase()===r.jv.trim().toLowerCase()
        const unk = r.pb==='—' || r.jv==='—'
        const fail = !unk && !match
        row4([
          r.indent
            ? { t:`  · ${r.label}`, color:fail?RED_T:TXT_DIM, size:7.5 }
            : { t:r.label||'', lbl:!!r.label, color:r.label?undefined:TXT_DIM },
          { t:safe(r.pb), color:unk?TXT_DIM:fail?RED_T:TXT, size:r.indent?7.5:undefined },
          { t:safe(r.jv), color:unk?TXT_DIM:fail?RED_T:TXT, size:r.indent?7.5:undefined },
          unk
            ? { t:'-', align:'C', color:TXT_DIM }
            : { t:match?'PASS':'FAIL', align:'C', bold:true, size:8, fill:match?GRN_F:RED_F, color:match?GRN_T:RED_T },
        ], r.indent ? 5 : undefined)
      }
    }

    // ── Accounting Definition — Applied Rules ──
    if (jvAccountRows.length > 0 && accountingDef.length > 0) {
      const normName = (s: string) => s.trim().toLowerCase()
      const defByName = new Map<string, typeof accountingDef[0]>()
      for (const d of accountingDef) { const k=normName(d.account_name)+'|'+(d.dr_cr||'').toLowerCase(); if(!defByName.has(k)) defByName.set(k,d) }
      const groups = new Map<string, typeof jvAccountRows>()
      for (const ar of jvAccountRows) { const key=ar.commodity||''; if(!groups.has(key)) groups.set(key,[]); groups.get(key)!.push(ar) }
      const sortedKeys = [...groups.keys()].sort((a,b) => a===''?1:b===''?-1:a.localeCompare(b))
      const jvNameSet = new Set(jvAccountRows.map(r => normName(r.account_name)))
      const notApplied = accountingDef.filter((d,i,arr) => {
        const k=normName(d.account_name)
        return arr.findIndex(x=>normName(x.account_name)===k&&x.dr_cr===d.dr_cr)===i && !jvNameSet.has(k)
      })

      sectionHeader('Accounting Definition - Applied Rules')
      row5([
        { t:'Account',        fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Dr/Cr',          fill:HEAD_BG, color:[255,255,255], size:8, align:'C' },
        { t:'Amount',         fill:HEAD_BG, color:[255,255,255], size:8, align:'R' },
        { t:'Rule / Condition', fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Status',         fill:HEAD_BG, color:[255,255,255], size:8, align:'C' },
      ], 7)

      let totalDr = 0, totalCr = 0
      for (const commodity of sortedKeys) {
        groupBand(commodity ? commodity.toUpperCase() : 'SHARED - all items')
        const gRows = groups.get(commodity)!
        let gDr = 0, gCr = 0
        for (const ar of gRows) {
          const def = defByName.get(normName(ar.account_name)+'|'+(ar.dr_cr||'').toLowerCase())
          const match = !!def && def.dr_cr===ar.dr_cr
          const status = !def?'EXTRA':match?'PASS':'WRONG TYPE'
          const rawCond = def?.condition_text||(def?'Always applies':'-')
          const cond = rawCond.replace(/\s+AND\s+/gi, '\nAND ')
          const ss = STATUS_S[status]!
          const isDr = ar.dr_cr==='Debit'
          const amtCol: [number,number,number] = isDr ? DR_T : CR_T
          if (ar.amount!=null) { isDr?(gDr+=ar.amount):(gCr+=ar.amount) }
          row5([
            { t:safe(ar.account_name), bold:true, color:TXT },
            { t:safe(ar.dr_cr), color:isDr?DR_T:CR_T, size:8, align:'C', bold:true },
            { t:ar.amount!=null?fmt(ar.amount):'-', bold:true, color:ar.amount!=null?amtCol:TXT_DIM, size:8, align:'R' },
            { t:safe(cond), color:TXT, size:7.5 },
            { t:status, align:'C', bold:true, size:8, fill:ss.fill, color:ss.text },
          ])
        }
        totalDr+=gDr; totalCr+=gCr
        if (gRows.length>1 && (gDr>0 || gCr>0)) {
          row5([
            { t:'', fill:null },
            { t:'Subtotal', size:7.5, color:TXT_DIM, span:1 },
            { t:gDr>0?fmt(gDr):gCr>0?fmt(gCr):'-', mono:true, color:gDr>0?DR_T:CR_T, size:7.5, align:'R' },
            { t:'', fill:null },
            { t:'', fill:null },
          ], 5.5)
        }
      }
      const tDr = jvAccountRows.filter(r=>r.dr_cr==='Debit'&&r.amount!=null).reduce((s,r)=>s+r.amount!,0)
      const tCr = jvAccountRows.filter(r=>r.dr_cr==='Credit'&&r.amount!=null).reduce((s,r)=>s+r.amount!,0)
      const balanced = Math.abs(tDr-tCr)<0.01
      need(9)
      need(8)
      doc.setFillColor(...TOT_F); doc.rect(M, y, CW, 8, 'FD')
      doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(...TXT)
      doc.text('TOTALS', M+3, y+5.2)
      doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(...DR_T)
      doc.setFillColor(...DR_F); doc.rect(M+COLS5[0], y, COLS5[1]+COLS5[2], 8, 'FD')
      doc.text(`DR  ${fmt(tDr)}`, M+COLS5[0]+COLS5[1]+COLS5[2]-2, y+5.2, { align:'right' })
      doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(...CR_T)
      doc.setFillColor(...CR_F); doc.rect(M+COLS5[0]+COLS5[1]+COLS5[2], y, COLS5[3], 8, 'FD')
      doc.text(`CR  ${fmt(tCr)}`, M+COLS5[0]+COLS5[1]+COLS5[2]+COLS5[3]-2, y+5.2, { align:'right' })
      const bSt = balanced ? GRN_F : RED_F
      const bTc = balanced ? GRN_T : RED_T
      const bTxt = balanced ? 'DR = CR  OK' : 'DR != CR  !'
      doc.setFillColor(...bSt); doc.rect(M+COLS5[0]+COLS5[1]+COLS5[2]+COLS5[3], y, COLS5[4], 8, 'FD')
      doc.setFont('helvetica','bold'); doc.setFontSize(8); doc.setTextColor(...bTc)
      doc.text(bTxt, M+COLS5[0]+COLS5[1]+COLS5[2]+COLS5[3]+COLS5[4]/2, y+5.2, { align:'center' })
      doc.setDrawColor(...BDR); doc.rect(M, y, CW, 8, 'S')
      y += 8

      if (notApplied.length > 0) {
        y += 3
        groupBand('NOT APPLIED THIS TRANSACTION', true)
        row5([
          { t:'Account',           fill:HEAD_BG, color:[255,255,255], size:7.5 },
          { t:'Dr/Cr',             fill:HEAD_BG, color:[255,255,255], size:7.5, align:'C' },
          { t:'-',                 fill:HEAD_BG, color:[255,255,255], size:7.5, align:'C' },
          { t:'Why not applied',   fill:HEAD_BG, color:[255,255,255], size:7.5 },
          { t:'-',                 fill:HEAD_BG, color:[255,255,255], size:7.5, align:'C' },
        ], 6)
        for (const d of notApplied) {
          const condLabel = d.condition_text || '-'
          row5([
            { t:safe(d.account_name), color:TXT_DIM },
            { t:safe(d.dr_cr), color:TXT_DIM, size:8, align:'C' },
            { t:'-', color:TXT_DIM, size:8, align:'C' },
            { t:safe(condLabel.replace(/\s+AND\s+/gi,'\nAND ')), color:TXT_DIM, size:7.5 },
            { t:'n/a', color:TXT_DIM, size:8, align:'C' },
          ])
        }
      }
    }

    // ── Footer ──
    need(10); y += 5
    doc.setDrawColor(...BDR); doc.line(M, y-1, M+CW, y-1)
    doc.setFont('helvetica','italic'); doc.setFontSize(7.5); doc.setTextColor(...TXT_DIM)
    doc.text(safe(`Generated by RhythmERP Automation - JV Verification  |  ${pbRefNo}`), M, y+2)

    const filename = `${pbRefNo.replace(/[\\/]/g, '-')}_JV_Report.pdf`
    const blob = doc.output('blob')
    const pdfUrl = URL.createObjectURL(blob)
    const dlBtn = `<a href="${pdfUrl}" download="${filename}" style="position:fixed;top:8px;right:12px;z-index:9999;padding:6px 14px;background:#3F51B5;color:#fff;border-radius:6px;font:13px/1 sans-serif;text-decoration:none">⬇ Download</a>`
    const win = window.open('', '_blank')
    if (win) {
      win.document.write(
        `<!doctype html><html><head><title>${filename}</title></head>` +
        `<body style="margin:0;height:100vh">${dlBtn}` +
        `<embed src="${pdfUrl}" type="application/pdf" width="100%" height="100%"/>` +
        `</body></html>`
      )
      win.document.close()
    }
    setTimeout(() => URL.revokeObjectURL(pdfUrl), 120_000)
  }, [selectedPB, jvSteps, jvCompRows, jvAccountRows, accountingDef, pbRefNo])

  // ── Inventory JV tab state ──────────────────────────────
  const [jvTab, setJvTab] = useState<'purchase' | 'inventory' | 'crosscheck'>('purchase')
  const [invVerifying, setInvVerifying] = useState(false)
  const [invSteps, setInvSteps] = useState<JVVerifyStep[]>([])
  const [invCommodityRows, setInvCommodityRows] = useState<InvCommodityRow[]>([])
  const [invJvRows, setInvJvRows] = useState<{ account_name: string; dr_cr: string; commodity: string; amount: number | null }[]>([])
  const [invError, setInvError] = useState('')
  const [invJvMeta, setInvJvMeta] = useState<import('@/lib/api').JVMeta | null>(null)
  const [fullViewOpen, setFullViewOpen] = useState(false)
  // Inventory tab has its own PB selection, independent of purchase tab
  const [invSelectedPB, setInvSelectedPB] = useState<PBListItem | null>(null)
  const [invPbRefNo, setInvPbRefNo] = useState('')


  // ── Cross-Check tab state ───────────────────────────────
  const [ccSelectedPB, setCcSelectedPB] = useState<PBListItem | null>(null)
  const [ccPbRefNo, setCcPbRefNo] = useState('')
  const [ccLoading, setCcLoading] = useState(false)
  const [ccResult, setCcResult] = useState<CrossCheckResponse | null>(null)
  const [ccError, setCcError] = useState('')
  const [ccFullViewOpen, setCcFullViewOpen] = useState(false)
  const ccExportXlsRef = useRef<(() => void) | null>(null)
  const ccExportPdfRef = useRef<(() => void) | null>(null)
  const ccOnFullViewRef = useRef<(() => void) | null>(null)

  const handleCcVerifyFor = useCallback(async (pb: PBListItem) => {
    if (!token || !tenantId) return
    setCcLoading(true)
    setCcError('')
    setCcResult(null)
    try {
      const res = await crossCheckJV(token, tenantId, pb.ref_no, String(pb.id))
      setCcResult(res)
    } catch (err) {
      if (!handleAuthError(err)) setCcError(err instanceof Error ? err.message : String(err))
    } finally {
      setCcLoading(false)
    }
  }, [token, tenantId]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Inventory JV exports ────────────────────────────────

  const exportInvJvReport = useCallback(() => {
    if (!invSelectedPB || invSteps.length === 0) return
    const ok = invSteps.every(s => s.ok)
    const pbRef = invSelectedPB.ref_no

    const escXml = (v: string | number) => String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')
    const cell = (style: string, value: string | number, mergeAcross?: number) => {
      const type = typeof value === 'number' ? 'Number' : 'String'
      return `<Cell${mergeAcross != null ? ` ss:MergeAcross="${mergeAcross}"` : ''}${style ? ` ss:StyleID="${style}"` : ''}><Data ss:Type="${type}">${escXml(value)}</Data></Cell>`
    }
    const emptyCell = (style = 'sVal') => `<Cell ss:StyleID="${style}"><Data ss:Type="String"></Data></Cell>`
    const fmtN = (n: number | null | undefined) => n != null ? n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'

    const rows: string[] = []
    rows.push(`<Row ss:Height="28">${cell('sTitle', 'INV JV VERIFICATION REPORT', 3)}${cell(ok ? 'sPass' : 'sFail', ok ? '✓ PASSED' : '✕ FAILED')}</Row>`)
    rows.push(`<Row ss:Height="16">${cell('sMeta', `Document: ${pbRef}`, 2)}${cell('sMeta', `Generated: ${new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}`, 2)}</Row>`)
    rows.push('<Row ss:Height="8"/>')

    rows.push(`<Row ss:Height="19">${cell('sSection', 'DOCUMENT DETAILS', 4)}</Row>`)
    rows.push(`<Row>${cell('sLabel', 'Supplier')}${cell('sVal', invSelectedPB.supplier ?? '—', 3)}</Row>`)
    rows.push(`<Row>${cell('sLabel', 'Date')}${cell('sVal', invSelectedPB.date ?? '—')}${cell('sLabel', 'PB Ref')}${cell('sVal', pbRef)}${emptyCell()}</Row>`)
    rows.push('<Row ss:Height="8"/>')

    rows.push(`<Row ss:Height="19">${cell('sSection', 'VERIFICATION STEPS', 4)}</Row>`)
    rows.push(`<Row>${cell('sHead', 'Step')}${cell('sHeadC', 'Result')}${cell('sHead', 'Detail', 2)}</Row>`)
    for (const s of invSteps) {
      rows.push(`<Row>${cell(s.ok ? 'sPassText' : 'sFailText', s.label)}${cell(s.ok ? 'sPass' : 'sFail', s.ok ? '✓ PASS' : '✕ FAIL')}${cell('sVal', s.detail ?? '', 2)}</Row>`)
    }
    rows.push('<Row ss:Height="8"/>')

    if (invCommodityRows.length > 0) {
      rows.push(`<Row ss:Height="19">${cell('sSection', 'PER-COMMODITY CROSS-CHECK', 4)}</Row>`)
      rows.push(`<Row>${cell('sHead', 'Commodity')}${cell('sHeadR', 'PURB Purchase Exempt DR')}${cell('sHeadR', 'INV Closing Stock DR')}${cell('sHeadC', 'Match')}${emptyCell('sHead')}</Row>`)
      for (const r of invCommodityRows) {
        rows.push(`<Row>${cell('sVal', r.commodity)}${r.purb_purchase_exempt_dr != null ? cell('sDr', r.purb_purchase_exempt_dr) : emptyCell('sValR')}${r.inv_closing_stock_dr != null ? cell('sDr', r.inv_closing_stock_dr) : emptyCell('sValR')}${cell(r.match ? 'sPass' : 'sFail', r.match ? 'MATCH' : 'MISMATCH')}${emptyCell()}</Row>`)
      }
      const totPurb = invCommodityRows.reduce((s,r) => s + (r.purb_purchase_exempt_dr ?? 0), 0)
      const totInv  = invCommodityRows.reduce((s,r) => s + (r.inv_closing_stock_dr  ?? 0), 0)
      rows.push(`<Row ss:Height="18">${cell('sTotalL', 'TOTAL', 1)}${cell('sTotalDr', totPurb)}${cell('sTotalDr', totInv)}${cell(Math.abs(totPurb-totInv)<0.02?'sPass':'sFail', Math.abs(totPurb-totInv)<0.02?'DR = DR ✓':'DR ≠ DR ✕')}${emptyCell()}</Row>`)
      rows.push('<Row ss:Height="8"/>')
    }

    if (invJvRows.length > 0) {
      rows.push(`<Row ss:Height="19">${cell('sSection', 'INV JV ACCOUNTING ENTRIES', 4)}</Row>`)
      rows.push(`<Row>${cell('sHead', 'Commodity')}${cell('sHead', 'Account')}${cell('sHeadC', 'Dr/Cr')}${cell('sHeadR', 'Amount')}${emptyCell('sHead')}</Row>`)
      const groups = new Map<string, typeof invJvRows>()
      for (const r of invJvRows) { const k = r.commodity||''; if(!groups.has(k)) groups.set(k,[]); groups.get(k)!.push(r) }
      for (const [commodity, gRows] of groups) {
        rows.push(`<Row ss:Height="15">${cell('sGroup', commodity ? commodity.toUpperCase() : 'SHARED', 4)}</Row>`)
        for (const r of gRows) {
          rows.push(`<Row>${emptyCell()}${cell('sVal', r.account_name)}${cell('sDrCrBadge', r.dr_cr)}${r.amount!=null?cell(r.dr_cr==='Debit'?'sDr':'sCr', r.amount):emptyCell('sValR')}${emptyCell()}</Row>`)
        }
      }
      const tDr = invJvRows.filter(r=>r.dr_cr==='Debit'&&r.amount!=null).reduce((s,r)=>s+r.amount!,0)
      const tCr = invJvRows.filter(r=>r.dr_cr==='Credit'&&r.amount!=null).reduce((s,r)=>s+r.amount!,0)
      const bal = Math.abs(tDr-tCr)<0.02
      rows.push(`<Row ss:Height="18">${cell('sTotalL', 'TOTALS', 1)}${emptyCell('sTotalL')}${cell('sTotalDr', tDr)}${cell('sTotalCr', tCr)}${cell(bal?'sPass':'sFail', bal?'DR = CR ✓':'DR ≠ CR ✕')}</Row>`)
    }
    rows.push('<Row ss:Height="12"/>')
    rows.push(`<Row ss:Height="14">${cell('sMeta', 'Generated by Pacs Automation — Inventory JV Verification Report', 4)}</Row>`)

    const XL_BORDER_DARK = '<Borders><Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/><Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/><Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/><Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/></Borders>'
    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
<Styles>
<Style ss:ID="Default" ss:Name="Normal"><Font ss:FontName="Calibri" ss:Size="10" ss:Color="#212121"/><Alignment ss:Vertical="Center"/></Style>
<Style ss:ID="sTitle"><Font ss:Bold="1" ss:Size="15" ss:Color="#FFFFFF"/><Interior ss:Color="#283593" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="2"/></Style>
<Style ss:ID="sMeta"><Font ss:Italic="1" ss:Size="9" ss:Color="#546E7A"/><Alignment ss:Vertical="Center" ss:Indent="1"/></Style>
<Style ss:ID="sSection"><Font ss:Bold="1" ss:Size="10" ss:Color="#1A237E"/><Interior ss:Color="#C5CAE9" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sLabel"><Font ss:Bold="1" ss:Size="10" ss:Color="#37474F"/><Interior ss:Color="#ECEFF1" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sVal"><Font ss:Color="#212121"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sValR"><Font ss:Color="#212121"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDr"><Font ss:Bold="1" ss:Color="#0D47A1"/><NumberFormat ss:Format="&quot;DR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sCr"><Font ss:Bold="1" ss:Color="#4A148C"/><NumberFormat ss:Format="&quot;CR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHead"><Font ss:Bold="1" ss:Size="10" ss:Color="#FFFFFF"/><Interior ss:Color="#3949AB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Left" ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHeadC"><Font ss:Bold="1" ss:Size="10" ss:Color="#FFFFFF"/><Interior ss:Color="#3949AB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHeadR"><Font ss:Bold="1" ss:Size="10" ss:Color="#FFFFFF"/><Interior ss:Color="#3949AB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Right" ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sPass"><Font ss:Bold="1" ss:Size="10" ss:Color="#1B5E20"/><Interior ss:Color="#A5D6A7" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sFail"><Font ss:Bold="1" ss:Size="10" ss:Color="#B71C1C"/><Interior ss:Color="#EF9A9A" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sPassText"><Font ss:Bold="1" ss:Color="#2E7D32"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sFailText"><Font ss:Bold="1" ss:Color="#C62828"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDim"><Font ss:Color="#78909C"/><Interior ss:Color="#F9FAFB" ss:Pattern="Solid"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDimC"><Font ss:Color="#78909C"/><Interior ss:Color="#F9FAFB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sGroup"><Font ss:Bold="1" ss:Italic="1" ss:Size="9" ss:Color="#1A237E"/><Interior ss:Color="#E8EAF6" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDrCrBadge"><Font ss:Bold="1" ss:Size="9" ss:Color="#37474F"/><Interior ss:Color="#ECEFF1" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sTotalL"><Font ss:Bold="1" ss:Size="10" ss:Color="#212121"/><Interior ss:Color="#CFD8DC" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sTotalDr"><Font ss:Bold="1" ss:Color="#0D47A1"/><Interior ss:Color="#BBDEFB" ss:Pattern="Solid"/><NumberFormat ss:Format="&quot;DR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sTotalCr"><Font ss:Bold="1" ss:Color="#4A148C"/><Interior ss:Color="#E1BEE7" ss:Pattern="Solid"/><NumberFormat ss:Format="&quot;CR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
</Styles>
<Worksheet ss:Name="INV JV Report">
<Table ss:DefaultRowHeight="18">
<Column ss:Width="160"/>
<Column ss:Width="120"/>
<Column ss:Width="80"/>
<Column ss:Width="140"/>
<Column ss:Width="80"/>
${rows.join('\n')}
</Table>
</Worksheet>
</Workbook>`

    const blob = new Blob([xml], { type: 'application/vnd.ms-excel;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${pbRef.replace(/[\\/]/g, '-')}_INV_JV_Report.xls`
    document.body.appendChild(a); a.click(); a.remove()
    URL.revokeObjectURL(url)
  }, [invSelectedPB, invSteps, invCommodityRows, invJvRows])

  const exportInvJvPdf = useCallback(async () => {
    if (!invSelectedPB || invSteps.length === 0) return
    const ok = invSteps.every(s => s.ok)
    const pbRef = invSelectedPB.ref_no

    const safe = (v: string | number | null | undefined) =>
      String(v ?? '').replace(/₹/g,'Rs. ').replace(/[—–]/g,'-').replace(/['']/g,"'")
        .replace(/[""]/g,'"').replace(/·/g,'|').replace(/≥/g,'>=').replace(/≤/g,'<=')
        .replace(/×/g,'x').replace(/ /g,' ').replace(/↔/g,'<->').replace(/≠/g,'!=')
        .replace(/✓/g,'OK').replace(/✕/g,'X')
    const fmt = (n: number) => n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    const NAVY: [number,number,number]   = [40, 53, 147]
    const NAVY_D: [number,number,number] = [26, 35, 126]
    const HEAD_BG: [number,number,number]= [57, 73, 171]
    const SEC_BG: [number,number,number] = [197, 202, 233]
    const LBL_BG: [number,number,number] = [236, 239, 241]
    const BDR: [number,number,number]    = [176, 176, 176]
    const TXT: [number,number,number]    = [33, 33, 33]
    const TXT_DIM: [number,number,number]= [84, 100, 114]
    const DR_T: [number,number,number]   = [13, 71, 161]
    const CR_T: [number,number,number]   = [74, 20, 140]
    const GRN_F: [number,number,number]  = [165, 214, 167], GRN_T: [number,number,number] = [27, 94, 32]
    const RED_F: [number,number,number]  = [239, 154, 154], RED_T: [number,number,number] = [183, 28, 28]
    const DR_F: [number,number,number]   = [187, 222, 251]
    const CR_F: [number,number,number]   = [225, 190, 231]
    const TOT_F: [number,number,number]  = [207, 216, 220]

    const { jsPDF } = await import('jspdf')
    const doc = new jsPDF({ unit: 'mm', format: 'a4' })
    const PW = 210, PH = 297, M = 14, CW = PW - M * 2

    let y = M
    const need = (h: number) => { if (y + h > PH - M - 8) { doc.addPage(); y = M } }

    type CS = { t: string; span?: number; align?: 'L'|'C'|'R'; color?: [number,number,number]; fill?: [number,number,number]|null; bold?: boolean; italic?: boolean; size?: number; mono?: boolean; lbl?: boolean }
    const makeRow = (cols: number[]) => (cells: CS[], h = 6.5) => {
      const PAD = 2.5, MAX_LINES = 5
      let colIdx = 0
      const measured = cells.map(c => {
        const span = c.span ?? 1
        const cw = cols.slice(colIdx, colIdx+span).reduce((a,b)=>a+b,0)
        const fs = c.size ?? (c.lbl ? 8 : 9)
        doc.setFont(c.mono?'courier':'helvetica',(c.bold||c.lbl)&&c.italic?'bolditalic':c.bold||c.lbl?'bold':c.italic?'italic':'normal')
        doc.setFontSize(fs)
        let lines: string[] = doc.splitTextToSize(safe(c.t), cw-PAD*2)
        if (lines.length > MAX_LINES) { lines = lines.slice(0,MAX_LINES); lines[MAX_LINES-1]=lines[MAX_LINES-1].replace(/.{3}$/,'')+'...' }
        colIdx += span
        return { c, cw, fs, lines }
      })
      const rh = Math.max(h, ...measured.map(m => m.lines.length * m.fs * 0.353 * 1.25 + 2.4))
      need(rh)
      doc.setDrawColor(...BDR)
      let cx = M
      for (const { c, cw, fs, lines } of measured) {
        if (c.fill !== null) {
          const bg = c.fill ?? (c.lbl ? LBL_BG : null)
          if (bg) { doc.setFillColor(...bg); doc.rect(cx,y,cw,rh,'FD') } else doc.rect(cx,y,cw,rh,'S')
        }
        doc.setFont(c.mono?'courier':'helvetica',(c.bold||c.lbl)&&c.italic?'bolditalic':c.bold||c.lbl?'bold':c.italic?'italic':'normal')
        doc.setFontSize(fs); doc.setTextColor(...(c.color ?? (c.lbl ? TXT : TXT)))
        const tx = c.align==='C'?cx+cw/2:c.align==='R'?cx+cw-PAD:cx+PAD
        const alignOpt = c.align==='C'?'center' as const:c.align==='R'?'right' as const:'left' as const
        const lineStep = fs*0.353*1.25
        let ly = y+(rh-lines.length*lineStep)/2+fs*0.353*0.9
        for (const ln of lines) { doc.text(ln,tx,ly,{align:alignOpt}); ly+=lineStep }
        cx += cw
      }
      y += rh
    }

    const COLS4: number[] = [52, 50, 50, 30]
    const row4 = makeRow(COLS4)
    const COLS3: number[] = [70, 70, 42]
    const row3 = makeRow(COLS3)

    const sectionHeader = (title: string) => {
      need(14); y += 4
      doc.setFillColor(...SEC_BG); doc.rect(M,y,CW,7.5,'F')
      doc.setDrawColor(...BDR); doc.rect(M,y,CW,7.5,'S')
      doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(...NAVY_D)
      doc.text(title.toUpperCase(), M+3, y+5)
      y += 7.5
    }

    const groupBand = (title: string) => {
      need(7)
      doc.setFillColor(...[232,234,246] as [number,number,number]); doc.rect(M,y,CW,6,'F')
      doc.setDrawColor(...BDR); doc.rect(M,y,CW,6,'S')
      doc.setFont('helvetica','bolditalic'); doc.setFontSize(8); doc.setTextColor(...NAVY_D)
      doc.text(safe(title), M+3, y+4)
      y += 6
    }

    // Title
    doc.setFillColor(...NAVY); doc.rect(M,y,CW,16,'F')
    doc.setFont('helvetica','bold'); doc.setFontSize(15); doc.setTextColor(255,255,255)
    doc.text('INV JV VERIFICATION REPORT', M+4, y+10.5)
    const chipText = ok ? 'PASSED' : 'FAILED'
    const chipFill = ok ? GRN_F : RED_F, chipTxt = ok ? GRN_T : RED_T
    doc.setFontSize(10)
    const chipW = doc.getTextWidth(chipText)+7
    doc.setFillColor(...chipFill); doc.roundedRect(PW-M-chipW-2,y+4.5,chipW,7.5,1.5,1.5,'F')
    doc.setTextColor(...chipTxt); doc.text(chipText, PW-M-chipW+1, y+9.5)
    y += 16
    doc.setFont('helvetica','italic'); doc.setFontSize(8); doc.setTextColor(...TXT_DIM)
    y += 5
    doc.text(safe(`Document: ${pbRef}   |   Generated: ${new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}`), M+1, y)
    y += 3

    // Document Details
    sectionHeader('Document Details')
    row4([{ t:'Supplier', lbl:true }, { t:safe(invSelectedPB.supplier??'-'), span:3 }])
    row4([{ t:'Date', lbl:true }, { t:safe(invSelectedPB.date??'-') }, { t:'PB Ref', lbl:true }, { t:safe(pbRef) }])

    // Steps
    sectionHeader('Verification Steps')
    row4([
      { t:'Step', fill:HEAD_BG, color:[255,255,255], size:8 },
      { t:'Result', fill:HEAD_BG, color:[255,255,255], size:8, align:'C' },
      { t:'Detail', fill:HEAD_BG, color:[255,255,255], size:8, span:2 },
    ], 7)
    for (const s of invSteps) {
      row4([
        { t:safe(s.label), bold:true, color:s.ok ? GRN_T : RED_T },
        { t:s.ok ? 'PASS' : 'FAIL', align:'C', bold:true, size:8, fill:s.ok ? GRN_F : RED_F, color:s.ok ? GRN_T : RED_T },
        { t:safe(s.detail ?? ''), color:TXT_DIM, size:7.5, span:2 },
      ])
    }

    // Per-commodity
    if (invCommodityRows.length > 0) {
      sectionHeader('Per-Commodity Cross-Check')
      row3([
        { t:'Commodity', fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'PURB Purchase Exempt DR', fill:HEAD_BG, color:[255,255,255], size:8, align:'R' },
        { t:'INV Closing Stock DR', fill:HEAD_BG, color:[255,255,255], size:8, align:'R' },
      ], 7)
      // Add a 4th match column
      const COLS4c: number[] = [76, 42, 42, 22]
      const row4c = makeRow(COLS4c)
      row4c([
        { t:'Commodity', fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'PURB Exempt DR', fill:HEAD_BG, color:[255,255,255], size:7.5, align:'R' },
        { t:'INV Closing DR', fill:HEAD_BG, color:[255,255,255], size:7.5, align:'R' },
        { t:'Match', fill:HEAD_BG, color:[255,255,255], size:8, align:'C' },
      ], 7)
      for (const r of invCommodityRows) {
        row4c([
          { t:safe(r.commodity), bold:true, color:TXT },
          { t:r.purb_purchase_exempt_dr != null ? fmt(r.purb_purchase_exempt_dr) : '—', mono:true, color:DR_T, size:8, align:'R' },
          { t:r.inv_closing_stock_dr != null ? fmt(r.inv_closing_stock_dr) : '—', mono:true, color:DR_T, size:8, align:'R' },
          { t:r.match?'OK':'FAIL', align:'C', bold:true, size:8, fill:r.match?GRN_F:RED_F, color:r.match?GRN_T:RED_T },
        ])
      }
      const totP = invCommodityRows.reduce((s,r)=>s+(r.purb_purchase_exempt_dr??0),0)
      const totI = invCommodityRows.reduce((s,r)=>s+(r.inv_closing_stock_dr??0),0)
      const tBal = Math.abs(totP-totI) < 0.02
      need(9)
      doc.setFillColor(...TOT_F); doc.rect(M,y,CW,8,'FD')
      doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(...TXT)
      doc.text('TOTAL', M+3, y+5.2)
      doc.setFillColor(...DR_F); doc.rect(M+COLS4c[0],y,COLS4c[1],8,'FD')
      doc.setTextColor(...DR_T); doc.text(fmt(totP), M+COLS4c[0]+COLS4c[1]-2, y+5.2, {align:'right'})
      doc.setFillColor(...DR_F); doc.rect(M+COLS4c[0]+COLS4c[1],y,COLS4c[2],8,'FD')
      doc.setTextColor(...DR_T); doc.text(fmt(totI), M+COLS4c[0]+COLS4c[1]+COLS4c[2]-2, y+5.2, {align:'right'})
      doc.setFillColor(...(tBal?GRN_F:RED_F)); doc.rect(M+COLS4c[0]+COLS4c[1]+COLS4c[2],y,COLS4c[3],8,'FD')
      doc.setFont('helvetica','bold'); doc.setFontSize(8); doc.setTextColor(...(tBal?GRN_T:RED_T))
      doc.text(tBal?'OK':'FAIL', M+COLS4c[0]+COLS4c[1]+COLS4c[2]+COLS4c[3]/2, y+5.2, {align:'center'})
      doc.setDrawColor(...BDR); doc.rect(M,y,CW,8,'S')
      y += 8
    }

    // INV JV accounting entries
    if (invJvRows.length > 0) {
      sectionHeader('INV JV Accounting Entries')
      const COLS3e: number[] = [80, 28, 74]
      const row3e = makeRow(COLS3e)
      row3e([
        { t:'Account', fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Dr/Cr', fill:HEAD_BG, color:[255,255,255], size:8, align:'C' },
        { t:'Amount', fill:HEAD_BG, color:[255,255,255], size:8, align:'R' },
      ], 7)
      const groups = new Map<string, typeof invJvRows>()
      for (const r of invJvRows) { const k=r.commodity||''; if(!groups.has(k)) groups.set(k,[]); groups.get(k)!.push(r) }
      const sortedKeys = [...groups.keys()].sort((a,b)=>a===''?1:b===''?-1:a.localeCompare(b))
      let tDr = 0, tCr = 0
      for (const commodity of sortedKeys) {
        groupBand(commodity ? commodity.toUpperCase() : 'SHARED')
        for (const r of groups.get(commodity)!) {
          const isDr = r.dr_cr === 'Debit'
          if (r.amount != null) { isDr ? (tDr += r.amount) : (tCr += r.amount) }
          row3e([
            { t:safe(r.account_name), bold:true, color:TXT },
            { t:safe(r.dr_cr), color:isDr?DR_T:CR_T, size:8, align:'C', bold:true },
            { t:r.amount!=null?fmt(r.amount):'-', bold:true, color:r.amount!=null?(isDr?DR_T:CR_T):TXT_DIM, size:8, align:'R' },
          ])
        }
      }
      const bal = Math.abs(tDr-tCr)<0.02
      need(9)
      doc.setFillColor(...TOT_F); doc.rect(M,y,CW,8,'FD')
      doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(...TXT)
      doc.text('TOTALS', M+3, y+5.2)
      doc.setFillColor(...DR_F); doc.rect(M+COLS3e[0],y,COLS3e[1],8,'FD')
      doc.setTextColor(...DR_T); doc.text(`DR`, M+COLS3e[0]+COLS3e[1]/2, y+5.2, {align:'center'})
      doc.setFillColor(...CR_F); doc.rect(M+COLS3e[0]+COLS3e[1],y,COLS3e[2]/2,8,'FD')
      doc.setTextColor(...DR_T); doc.text(fmt(tDr), M+COLS3e[0]+COLS3e[1]+COLS3e[2]/2-2, y+5.2, {align:'right'})
      doc.setFillColor(...CR_F); doc.rect(M+COLS3e[0]+COLS3e[1]+COLS3e[2]/2,y,COLS3e[2]/2,8,'FD')
      doc.setTextColor(...CR_T); doc.text(fmt(tCr), M+COLS3e[0]+COLS3e[1]+COLS3e[2]-2, y+5.2, {align:'right'})
      doc.setDrawColor(...BDR); doc.rect(M,y,CW,8,'S')
      y += 8
      need(6); y += 3
      doc.setFont('helvetica','bold'); doc.setFontSize(9)
      doc.setTextColor(...(bal?GRN_T:RED_T))
      doc.text(bal ? 'DR = CR  ✓ Balanced' : 'DR ≠ CR  ✕ Unbalanced', M+3, y)
      y += 5
    }

    // Footer
    need(10); y += 5
    doc.setDrawColor(...BDR); doc.line(M,y-1,M+CW,y-1)
    doc.setFont('helvetica','italic'); doc.setFontSize(7.5); doc.setTextColor(...TXT_DIM)
    doc.text(safe(`Generated by RhythmERP Automation - INV JV Verification  |  ${pbRef}`), M, y+2)

    const filename = `${pbRef.replace(/[\\/]/g,'-')}_INV_JV_Report.pdf`
    const blob = doc.output('blob')
    const pdfUrl = URL.createObjectURL(blob)
    const dlBtn = `<a href="${pdfUrl}" download="${filename}" style="position:fixed;top:8px;right:12px;z-index:9999;padding:6px 14px;background:#3F51B5;color:#fff;border-radius:6px;font:13px/1 sans-serif;text-decoration:none">⬇ Download</a>`
    const win = window.open('', '_blank')
    if (win) {
      win.document.write(`<!doctype html><html><head><title>${filename}</title></head><body style="margin:0;height:100vh">${dlBtn}<embed src="${pdfUrl}" type="application/pdf" width="100%" height="100%"/></body></html>`)
      win.document.close()
    }
    setTimeout(() => URL.revokeObjectURL(pdfUrl), 120_000)
  }, [invSelectedPB, invSteps, invCommodityRows, invJvRows])

  const handleInvVerify = async () => { if (invSelectedPB) handleInvVerifyFor(invSelectedPB) }

  const handleInvVerifyFor = async (pb: PBListItem) => {
    if (!token || !tenantId) return
    const pbDate = pb.date?.slice(0, 10) || ''
    if (!pbDate) { setInvError('PB date not available'); return }
    setInvVerifying(true)
    setInvSteps([])
    setInvCommodityRows([])
    setInvJvRows([])
    setInvJvMeta(null)
    setInvError('')
    try {
      const res = await verifyInvJV(token, tenantId, pb.ref_no, pbDate, pb.id)
      setInvSteps(res.steps)
      setInvCommodityRows(res.commodity_rows || [])
      setInvJvRows(res.jv_rows)
      setInvJvMeta(res.jv_meta || null)
    } catch (err) {
      if (!handleAuthError(err)) setInvError(err instanceof Error ? err.message : String(err))
    } finally {
      setInvVerifying(false)
    }
  }

  const canVerify = !!token && !!tenantId && !!pbRefNo.trim() && !verifying
  return (
    <div className="relative flex flex-col h-full min-h-0 gap-4">
      <div className="bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col min-h-0 flex-1 overflow-hidden">
        {/* Header */}
        <div className="px-4 border-b border-gray-200 dark:border-gray-700 shrink-0 flex items-center gap-0 h-11">
          <Search className="size-4 text-[#3F51B5] dark:text-[#7986CB] mr-2 shrink-0" />
          {(['purchase', 'inventory', 'crosscheck'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setJvTab(tab)}
              className={`h-full px-4 text-[12px] font-medium border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                jvTab === tab
                  ? 'border-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB] dark:border-[#7986CB]'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {tab === 'crosscheck' && <GitCompare className="size-3" />}
              {tab === 'purchase' ? 'Purchase Account JV' : tab === 'inventory' ? 'Inventory Account JV' : 'Cross-Check'}
            </button>
          ))}
        </div>

        {jvTab === 'inventory' && (
          <div className="p-4 overflow-y-auto flex-1 min-h-0 space-y-4">
            {/* No PB selected — show PB list */}
            {!invSelectedPB && !invPbRefNo.trim() && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-[11px] text-gray-700 dark:text-gray-300">Select Purchase Booking</Label>
                  <button onClick={loadPBList} disabled={pbListLoading} className="text-[11px] text-[#3F51B5] dark:text-[#7986CB] flex items-center gap-1 hover:underline cursor-pointer disabled:opacity-50">
                    <RefreshCw className={`size-3 ${pbListLoading ? 'animate-spin' : ''}`} />Refresh
                  </button>
                </div>
                {pbListLoading && pbList.length === 0 && <LoadingCard message="FETCHING" steps={[{ label: 'Fetching purchase bookings', done: false }]} />}
                {pbList.length > 0 && (
                  <>
                    <Input value={pbSearch} onChange={(e) => setPbSearch(e.target.value)} placeholder="Search by ref no or supplier…" className="h-8 text-[12px] mb-2" />
                    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden max-h-64 overflow-y-auto">
                      {pbList.filter(pb => { const q = pbSearch.toLowerCase(); return !q || pb.ref_no.toLowerCase().includes(q) || pb.supplier.toLowerCase().includes(q) }).map((pb, _i) => (
                        <button key={pb.id ?? `${pb.ref_no}-${_i}`} onClick={() => { setInvPbRefNo(pb.ref_no); setInvSelectedPB(pb); handleInvVerifyFor(pb) }}
                          className="w-full text-left px-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 hover:bg-[#3F51B5]/5 dark:hover:bg-[#3F51B5]/10 transition-colors cursor-pointer">
                          <div className="flex items-center justify-between gap-3">
                            <span className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100 shrink-0">{pb.ref_no}</span>
                            {pb.amount && <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0 font-medium">₹{Number(pb.amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>}
                          </div>
                          {pb.supplier && (
                            <div className="mt-0.5 flex items-center justify-between gap-2">
                              <span className="text-[11px] text-gray-600 dark:text-gray-300 truncate font-medium">{pb.supplier}</span>
                              {pb.date && <span className="text-[10px] text-gray-400 dark:text-gray-500 shrink-0">{pb.date}</span>}
                            </div>
                          )}
                          {(pb.division || pb.department || pb.type_of_sale || pb.location) && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {[pb.division, pb.department, pb.type_of_sale, pb.location].filter(Boolean).map((tag) => (
                                <span key={tag} className="px-1.5 py-0.5 rounded text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">{tag}</span>
                              ))}
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Results — same card layout as purchase tab */}
            {(invVerifying || invSteps.length > 0 || invError) && (() => {
              const invPassed = invSteps.length > 0 && invSteps.every(s => s.ok)
              const SECTION_STRIP = 'px-4 py-1.5 bg-gray-100 dark:bg-gray-800/80 border-y border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-widest text-gray-500 dark:text-gray-400'
              const pill = (color: 'green'|'blue'|'purple'|'red'|'gray', label: string) => {
                const cls = {
                  green:  'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-700',
                  blue:   'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border-blue-200 dark:border-blue-700',
                  purple: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 border-purple-200 dark:border-purple-700',
                  red:    'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-700',
                  gray:   'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 border-gray-200 dark:border-gray-600',
                }[color]
                return <span className={`inline-flex items-center px-1.5 py-px rounded text-[10px] font-semibold border ${cls}`}>{label}</span>
              }
              const fmtAmt = (n: number | null | undefined) =>
                n != null ? n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'

              // Group INV JV rows by commodity for the accounting entries table
              const invGroups = new Map<string, typeof invJvRows>()
              for (const row of invJvRows) {
                const key = row.commodity || ''
                if (!invGroups.has(key)) invGroups.set(key, [])
                invGroups.get(key)!.push(row)
              }
              const invSortedKeys = [...invGroups.keys()].sort((a, b) => a===''?1:b===''?-1:a.localeCompare(b))
              const invTotalDr = invJvRows.filter(r => r.dr_cr==='Debit').reduce((s,r)=>s+(r.amount??0),0)
              const invTotalCr = invJvRows.filter(r => r.dr_cr==='Credit').reduce((s,r)=>s+(r.amount??0),0)
              const invBalanced = Math.abs(invTotalDr - invTotalCr) < 0.02
              const invHasAmounts = invJvRows.some(r => r.amount != null)

              // Summary cards: parse step details
              const invStep = invSteps.find(s => s.n === 3)  // Found INV JV step
              const totalStep = invSteps.find(s => s.n === 4) // total match
              const commodityStep = invSteps.find(s => s.n === 6) // per-commodity

              return (
                <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-white dark:bg-gray-900 shadow-sm">

                  {/* Header bar */}
                  <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2 min-w-0">
                      <FileBarChart2 className="size-3.5 shrink-0 text-[#3F51B5] dark:text-[#7986CB]" />
                      <span className="text-[12px] font-mono font-bold text-gray-800 dark:text-gray-100 truncate">{invSelectedPB?.ref_no || invPbRefNo}</span>
                      {!invVerifying && invSteps.length > 0 && (invPassed ? pill('green', '✓ Passed') : pill('red', '✕ Failed'))}
                      {invVerifying && <Loader2 className="size-3.5 animate-spin text-[#3F51B5] shrink-0" />}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {!invVerifying && invSteps.length > 0 && (
                        <>
                          <button
                            onClick={() => setFullViewOpen(true)}
                            className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-[#3F51B5]/40 bg-[#3F51B5]/5 text-[#3F51B5] dark:text-[#7986CB] hover:bg-[#3F51B5]/10 dark:hover:bg-[#3F51B5]/20 transition-colors cursor-pointer">
                            <Maximize2 className="size-3" />Full View
                          </button>
                          <button
                            onClick={exportInvJvPdf}
                            className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:border-red-300 dark:hover:border-red-700 transition-colors cursor-pointer">
                            <FileText className="size-3" />PDF
                          </button>
                          <button
                            onClick={exportInvJvReport}
                            className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:border-emerald-300 dark:hover:border-emerald-700 transition-colors cursor-pointer">
                            <FileSpreadsheet className="size-3" />.xls
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => { setInvSelectedPB(null); setInvPbRefNo(''); setInvSteps([]); setInvCommodityRows([]); setInvJvRows([]); setInvJvMeta(null); setInvError('') }}
                        className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-[#3F51B5] dark:hover:text-[#7986CB] hover:border-[#3F51B5]/50 transition-colors cursor-pointer">
                        <RefreshCw className="size-3" />Change
                      </button>
                    </div>
                  </div>

                  {/* Summary grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-gray-100 dark:divide-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <div className="px-4 py-3">
                      <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Supplier</div>
                      <div className="text-[13px] font-medium text-gray-800 dark:text-gray-100 truncate">{invSelectedPB?.supplier ?? '—'}</div>
                    </div>
                    <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0">
                      <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Date</div>
                      <div className="text-[13px] font-medium text-gray-800 dark:text-gray-100">{invSelectedPB?.date?.slice(0,10) ?? '—'}</div>
                    </div>
                    <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0">
                      <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Inventory JV</div>
                      <div className={`text-[13px] font-medium ${invStep ? (invStep.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400') : 'text-gray-400 dark:text-gray-500'}`}>
                        {invStep ? (invStep.ok ? '✓ Entry found' : '✕ Not found') : invVerifying ? 'Checking…' : '—'}
                      </div>
                    </div>
                    <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0">
                      <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Amount Match</div>
                      <div className={`text-[13px] font-medium ${totalStep ? (totalStep.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400') : 'text-gray-400 dark:text-gray-500'}`}>
                        {totalStep ? (totalStep.ok ? '✓ Matched' : '✕ Mismatch') : invVerifying ? 'Checking…' : '—'}
                      </div>
                    </div>
                  </div>
                  {/* Date / FY / Period cross-check row */}
                  {invJvMeta && (
                    <div className="grid grid-cols-3 divide-x divide-gray-100 dark:divide-gray-800 border-b border-gray-200 dark:border-gray-700 bg-gray-50/60 dark:bg-gray-800/30">
                      {([
                        { label: 'Transaction Date', purb: invJvMeta.purb_txn_date, inv: invJvMeta.inv_txn_date },
                        { label: 'Fiscal Year',      purb: invJvMeta.purb_fiscal_year, inv: invJvMeta.inv_fiscal_year },
                        { label: 'Period',           purb: invJvMeta.purb_period, inv: invJvMeta.inv_period },
                      ] as const).map(({ label, purb, inv }) => {
                        const match = purb && inv && purb === inv
                        return (
                          <div key={label} className="px-4 py-2.5">
                            <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5 flex items-center gap-1">
                              {label}
                              {purb && inv && (match
                                ? <CheckCircle2 className="size-3 text-emerald-500 shrink-0" />
                                : <XCircle className="size-3 text-red-500 shrink-0" />)}
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className="text-[11px] font-mono text-gray-700 dark:text-gray-200">{purb || '—'}</span>
                              {purb && inv && purb !== inv && (
                                <span className="text-[10px] text-red-500 font-mono">≠ {inv}</span>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {/* Loading */}
                  {invVerifying && invSteps.length === 0 && (
                    <LoadingCard message="VERIFYING" steps={[
                      { label: 'Fetching PB detail', done: false },
                      { label: 'Locating PURB & INV journal vouchers', done: false },
                      { label: 'Cross-checking amounts per commodity', done: false },
                    ]} />
                  )}

                  {/* Error */}
                  {invError && !invVerifying && (
                    <div className="mx-4 my-3 px-3 py-2 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-[11px] text-red-600 dark:text-red-400">{invError}</div>
                  )}

                  {/* Steps list */}
                  {invSteps.length > 0 && (
                    <>
                      <div className={SECTION_STRIP}>Verification steps</div>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse text-[12px]">
                          <tbody>
                            {invSteps.map((s, i) => (
                              <tr key={i} className={s.ok ? 'bg-white dark:bg-gray-900 hover:bg-gray-50/50 dark:hover:bg-gray-800/20' : 'bg-red-50 dark:bg-red-900/20'}>
                                <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 w-6 text-center">
                                  {s.ok ? <CheckCircle2 className="size-3.5 text-emerald-500 inline" /> : <XCircle className="size-3.5 text-red-500 inline" />}
                                </td>
                                <td className={`px-3 py-2 border border-gray-200 dark:border-gray-700 font-medium ${s.ok ? 'text-gray-700 dark:text-gray-300' : 'text-red-700 dark:text-red-300'}`}>{s.label}</td>
                                <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-gray-400 dark:text-gray-500 text-[11px]">{s.detail ?? ''}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}

                  {/* Per-commodity cross-check table */}
                  {invCommodityRows.length > 0 && (() => {
                    const purbHasPerCommodity = invCommodityRows.some(r => r.purb_purchase_exempt_dr != null)
                    const col1Label = purbHasPerCommodity ? 'PURB Purchase Exempt DR' : 'INV Purchase Exempt CR'
                    const col1Val = (r: InvCommodityRow) => purbHasPerCommodity ? r.purb_purchase_exempt_dr : r.inv_purchase_exempt_cr
                    const col1Total = invCommodityRows.reduce((s, r) => s + ((purbHasPerCommodity ? r.purb_purchase_exempt_dr : r.inv_purchase_exempt_cr) ?? 0), 0)
                    return (
                    <>
                      <div className={SECTION_STRIP}>Per-commodity cross-check</div>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse text-[12px]">
                          <thead>
                            <tr className="bg-gray-50 dark:bg-gray-800/80">
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left">Commodity</th>
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-right whitespace-nowrap">{col1Label}</th>
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-right whitespace-nowrap">INV Closing Stock DR</th>
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-center w-14">Match</th>
                            </tr>
                          </thead>
                          <tbody>
                            {invCommodityRows.map((r, i) => (
                              <tr key={i} className={r.match ? 'bg-white dark:bg-gray-900 hover:bg-gray-50/50 dark:hover:bg-gray-800/20' : 'bg-red-50 dark:bg-red-900/20'}>
                                <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 font-medium text-gray-700 dark:text-gray-300">{r.commodity}</td>
                                <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-right font-mono text-blue-700 dark:text-blue-300 font-semibold">{fmtAmt(col1Val(r))}</td>
                                <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-right font-mono text-blue-700 dark:text-blue-300 font-semibold">{fmtAmt(r.inv_closing_stock_dr)}</td>
                                <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-center">
                                  {r.match ? <CheckCircle2 className="size-3.5 text-emerald-500 inline" /> : <XCircle className="size-3.5 text-red-500 inline" />}
                                </td>
                              </tr>
                            ))}
                            {invCommodityRows.length > 1 && (
                              <tr className="bg-white dark:bg-gray-900">
                                <td className="px-3 py-2.5 border-t-2 border border-gray-300 dark:border-gray-500 font-bold text-[12px] text-gray-700 dark:text-gray-200">Total</td>
                                <td className="px-3 py-2.5 border-t-2 border border-gray-300 dark:border-gray-500 text-right font-mono font-semibold text-blue-700 dark:text-blue-300">
                                  {fmtAmt(col1Total)}
                                </td>
                                <td className="px-3 py-2.5 border-t-2 border border-gray-300 dark:border-gray-500 text-right font-mono font-semibold text-blue-700 dark:text-blue-300">
                                  {fmtAmt(invCommodityRows.reduce((s, r) => s + (r.inv_closing_stock_dr ?? 0), 0))}
                                </td>
                                <td className="px-3 py-2.5 border-t-2 border border-gray-300 dark:border-gray-500 text-center">
                                  {invCommodityRows.every(r => r.match) ? <CheckCircle2 className="size-3.5 text-emerald-500 inline" /> : <XCircle className="size-3.5 text-red-500 inline" />}
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )})()}

                  {/* INV JV accounting entries — grouped by commodity */}
                  {invJvRows.length > 0 && (
                    <>
                      <div className={SECTION_STRIP}>INV JV accounting entries</div>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse text-[12px]">
                          <thead>
                            <tr className="bg-gray-50 dark:bg-gray-800/80">
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left w-12">DR/CR</th>
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left">Account</th>
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-right w-32">Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {invSortedKeys.map(commodity => {
                              const rows = invGroups.get(commodity)!
                              const gDr = rows.filter(r=>r.dr_cr==='Debit').reduce((s,r)=>s+(r.amount??0),0)
                              const gCr = rows.filter(r=>r.dr_cr==='Credit').reduce((s,r)=>s+(r.amount??0),0)
                              return (
                                <React.Fragment key={commodity||'__shared__'}>
                                  <tr className="bg-indigo-50 dark:bg-indigo-950/40">
                                    <td colSpan={3} className="px-3 py-1.5 border border-indigo-100 dark:border-indigo-900/60">
                                      <div className="flex items-center justify-between">
                                        <span className="text-[11px] font-semibold text-indigo-700 dark:text-indigo-300 uppercase tracking-wide">{commodity || 'Shared'}</span>
                                        <span className="text-[10px] font-mono text-indigo-400 dark:text-indigo-500">{rows.length} {rows.length===1?'entry':'entries'}</span>
                                      </div>
                                    </td>
                                  </tr>
                                  {rows.map((row, ri) => {
                                    const isDebit = row.dr_cr === 'Debit'
                                    return (
                                      <tr key={ri} className="bg-white dark:bg-gray-900 hover:bg-gray-50/50 dark:hover:bg-gray-800/20">
                                        <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-center">
                                          {isDebit ? pill('blue','DR') : pill('purple','CR')}
                                        </td>
                                        <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 font-medium text-gray-800 dark:text-gray-100">{row.account_name}</td>
                                        <td className={`px-3 py-2 border border-gray-200 dark:border-gray-700 text-right font-mono font-semibold ${isDebit?'text-blue-700 dark:text-blue-300':'text-purple-700 dark:text-purple-300'}`}>
                                          {fmtAmt(row.amount)}
                                        </td>
                                      </tr>
                                    )
                                  })}
                                  {rows.length > 1 && (
                                    <tr className="bg-gray-50 dark:bg-gray-800/50">
                                      <td colSpan={2} className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] text-gray-400 dark:text-gray-500 font-medium">Subtotal</td>
                                      <td className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-right font-mono text-[11px]">
                                        {gDr>0 && <span className="text-blue-600 dark:text-blue-400">DR {fmtAmt(gDr)}</span>}
                                        {gDr>0 && gCr>0 && <span className="text-gray-300 dark:text-gray-600 mx-1">·</span>}
                                        {gCr>0 && <span className="text-purple-600 dark:text-purple-400">CR {fmtAmt(gCr)}</span>}
                                      </td>
                                    </tr>
                                  )}
                                </React.Fragment>
                              )
                            })}
                          </tbody>
                          {invHasAmounts && (
                            <tfoot>
                              <tr className="bg-white dark:bg-gray-900">
                                <td colSpan={2} className="px-3 py-2.5 border-t-2 border border-gray-300 dark:border-gray-500 font-bold text-[12px] text-gray-700 dark:text-gray-200">Total</td>
                                <td className="px-3 py-2.5 border-t-2 border border-gray-300 dark:border-gray-500 text-right">
                                  <div className="flex items-center justify-end gap-1.5 font-mono text-[12px] font-semibold">
                                    <span className="text-blue-700 dark:text-blue-300">DR {fmtAmt(invTotalDr)}</span>
                                    <span className={invBalanced?'text-emerald-600 dark:text-emerald-400':'text-red-500 dark:text-red-400'}>{invBalanced?'=':'≠'}</span>
                                    <span className="text-purple-700 dark:text-purple-300">CR {fmtAmt(invTotalCr)}</span>
                                    {invBalanced ? <CheckCircle2 className="size-3 text-emerald-500" /> : <XCircle className="size-3 text-red-500" />}
                                  </div>
                                </td>
                              </tr>
                            </tfoot>
                          )}
                        </table>
                      </div>
                    </>
                  )}

                  {/* ── Full View Portal Modal ── */}
                  {fullViewOpen && (
                    <DialogPrimitive.Root open={fullViewOpen} onOpenChange={setFullViewOpen}>
                      <DialogPrimitive.Portal>
                        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
                        <DialogPrimitive.Content className="fixed inset-4 z-50 flex flex-col bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
                          <DialogPrimitive.Title className="sr-only">JV Check Full View — {invSelectedPB?.ref_no || invPbRefNo}</DialogPrimitive.Title>

                          {/* Modal header */}
                          <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 dark:border-gray-700 shrink-0 bg-gradient-to-r from-[#3F51B5]/[0.06] to-transparent">
                            <div className="flex items-center gap-3">
                              <FileBarChart2 className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
                              <span className="text-[14px] font-bold font-mono text-gray-800 dark:text-gray-100">{invSelectedPB?.ref_no || invPbRefNo}</span>
                              {invPassed ? pill('green', '✓ Passed') : pill('red', '✕ Failed')}
                            </div>
                            <div className="flex items-center gap-2">
                              <button onClick={exportInvJvPdf} className="text-[11px] flex items-center gap-1 h-7 px-2.5 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-red-600 hover:border-red-300 transition-colors cursor-pointer"><FileText className="size-3" />PDF</button>
                              <button onClick={exportInvJvReport} className="text-[11px] flex items-center gap-1 h-7 px-2.5 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-emerald-600 hover:border-emerald-300 transition-colors cursor-pointer"><FileSpreadsheet className="size-3" />.xls</button>
                              <button onClick={() => setFullViewOpen(false)} className="size-7 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors cursor-pointer"><X className="size-4" /></button>
                            </div>
                          </div>

                          {/* Modal body — scrollable */}
                          <div className="flex-1 overflow-y-auto min-h-0">

                            {/* Meta strip */}
                            <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-gray-100 dark:divide-gray-800 border-b border-gray-200 dark:border-gray-700">
                              <div className="px-5 py-3"><div className="text-[10px] text-gray-400 font-medium mb-0.5">Supplier</div><div className="text-[13px] font-medium text-gray-800 dark:text-gray-100">{invSelectedPB?.supplier ?? '—'}</div></div>
                              <div className="px-5 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0"><div className="text-[10px] text-gray-400 font-medium mb-0.5">PB Date</div><div className="text-[13px] font-medium text-gray-800 dark:text-gray-100">{invSelectedPB?.date?.slice(0,10) ?? '—'}</div></div>
                              {invJvMeta && (
                                <>
                                  <div className="px-5 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0"><div className="text-[10px] text-gray-400 font-medium mb-0.5">Fiscal Year</div><div className={`text-[13px] font-medium ${invJvMeta.purb_fiscal_year === invJvMeta.inv_fiscal_year ? 'text-gray-800 dark:text-gray-100' : 'text-red-600 dark:text-red-400'}`}>{invJvMeta.purb_fiscal_year || '—'}</div></div>
                                  <div className="px-5 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0"><div className="text-[10px] text-gray-400 font-medium mb-0.5">Period</div><div className={`text-[13px] font-medium ${invJvMeta.purb_period === invJvMeta.inv_period ? 'text-gray-800 dark:text-gray-100' : 'text-red-600 dark:text-red-400'}`}>{invJvMeta.purb_period || '—'}</div></div>
                                </>
                              )}
                            </div>

                            {/* Two-column layout: steps left, commodity right */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 divide-y lg:divide-y-0 lg:divide-x divide-gray-200 dark:divide-gray-700">

                              {/* Left: Verification steps */}
                              <div className="p-5">
                                <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Verification Steps</h3>
                                <div className="space-y-1.5">
                                  {invSteps.map((s, i) => (
                                    <div key={i} className={`flex items-start gap-2.5 px-3 py-2 rounded-lg text-[12px] ${s.ok ? 'bg-emerald-50 dark:bg-emerald-900/10' : 'bg-red-50 dark:bg-red-900/10'}`}>
                                      {s.ok ? <CheckCircle2 className="size-3.5 text-emerald-500 shrink-0 mt-px" /> : <XCircle className="size-3.5 text-red-500 shrink-0 mt-px" />}
                                      <div className="min-w-0">
                                        <div className={`font-medium leading-tight ${s.ok ? 'text-gray-700 dark:text-gray-200' : 'text-red-700 dark:text-red-300'}`}>{s.label}</div>
                                        {s.detail && <div className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5 font-mono truncate">{s.detail}</div>}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>

                              {/* Right: Per-commodity + accounting entries */}
                              <div className="p-5 space-y-5">
                                {invCommodityRows.length > 0 && (() => {
                                  const purbHasPerCommodity = invCommodityRows.some(r => r.purb_purchase_exempt_dr != null)
                                  const col1Label = purbHasPerCommodity ? 'PURB Purchase Exempt DR' : 'INV Purchase Exempt CR'
                                  const col1Val = (r: InvCommodityRow) => purbHasPerCommodity ? r.purb_purchase_exempt_dr : r.inv_purchase_exempt_cr
                                  return (
                                    <>
                                      <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Per-Commodity Cross-Check</h3>
                                      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                                        <table className="w-full border-collapse text-[12px]">
                                          <thead><tr className="bg-gray-50 dark:bg-gray-800/80">
                                            <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">Commodity</th>
                                            <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 whitespace-nowrap">{col1Label}</th>
                                            <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 whitespace-nowrap">INV Closing Stock DR</th>
                                            <th className="px-3 py-2 text-center text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 w-12">✓</th>
                                          </tr></thead>
                                          <tbody>
                                            {invCommodityRows.map((r, i) => (
                                              <tr key={i} className={r.match ? 'hover:bg-gray-50/50 dark:hover:bg-gray-800/20' : 'bg-red-50 dark:bg-red-900/20'}>
                                                <td className="px-3 py-2 border-b border-gray-100 dark:border-gray-800 text-gray-700 dark:text-gray-300 font-medium text-[11px]">{r.commodity}</td>
                                                <td className="px-3 py-2 border-b border-gray-100 dark:border-gray-800 text-right font-mono text-blue-700 dark:text-blue-300">{fmtAmt(col1Val(r))}</td>
                                                <td className="px-3 py-2 border-b border-gray-100 dark:border-gray-800 text-right font-mono text-blue-700 dark:text-blue-300">{fmtAmt(r.inv_closing_stock_dr)}</td>
                                                <td className="px-3 py-2 border-b border-gray-100 dark:border-gray-800 text-center">{r.match ? <CheckCircle2 className="size-3.5 text-emerald-500 inline" /> : <XCircle className="size-3.5 text-red-500 inline" />}</td>
                                              </tr>
                                            ))}
                                          </tbody>
                                        </table>
                                      </div>
                                    </>
                                  )
                                })()}

                                {invJvRows.length > 0 && (
                                  <>
                                    <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3 mt-5">INV JV Accounting Entries</h3>
                                    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                                      <table className="w-full border-collapse text-[12px]">
                                        <thead><tr className="bg-gray-50 dark:bg-gray-800/80">
                                          <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 w-12">DR/CR</th>
                                          <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">Account</th>
                                          <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">Amount</th>
                                        </tr></thead>
                                        <tbody>
                                          {invSortedKeys.map(key => {
                                            const rows = invGroups.get(key)!
                                            return (
                                              <React.Fragment key={key}>
                                                {key && <tr><td colSpan={3} className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800/60 text-[10px] font-semibold text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-800">{key}</td></tr>}
                                                {rows.map((row, ri) => (
                                                  <tr key={ri} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/20">
                                                    <td className={`px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 font-semibold text-[11px] ${row.dr_cr === 'Debit' ? 'text-blue-700 dark:text-blue-300' : 'text-rose-600 dark:text-rose-400'}`}>{row.dr_cr === 'Debit' ? 'DR' : 'CR'}</td>
                                                    <td className="px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-gray-700 dark:text-gray-300">{row.account_name}</td>
                                                    <td className="px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-right font-mono text-gray-700 dark:text-gray-300">{fmtAmt(row.amount)}</td>
                                                  </tr>
                                                ))}
                                              </React.Fragment>
                                            )
                                          })}
                                        </tbody>
                                        <tfoot><tr className={`${invBalanced ? 'bg-emerald-50 dark:bg-emerald-900/10' : 'bg-red-50 dark:bg-red-900/10'}`}>
                                          <td colSpan={2} className="px-3 py-2 font-bold text-[11px] text-gray-700 dark:text-gray-200">Total</td>
                                          <td className="px-3 py-2 text-right font-mono font-bold text-[11px]">
                                            <span className="text-blue-700 dark:text-blue-300">DR {fmtAmt(invTotalDr)}</span>
                                            <span className="mx-1 text-gray-400">=</span>
                                            <span className="text-rose-600 dark:text-rose-400">CR {fmtAmt(invTotalCr)}</span>
                                          </td>
                                        </tr></tfoot>
                                      </table>
                                    </div>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                        </DialogPrimitive.Content>
                      </DialogPrimitive.Portal>
                    </DialogPrimitive.Root>
                  )}

                </div>
              )
            })()}
          </div>
        )}

        {jvTab === 'purchase' && <div ref={scrollContainerRef} className="p-4 overflow-y-auto flex-1 min-h-0 space-y-4 relative">
          {/* Token panel — same as full purchase flow */}
          {showTokenInput && (
            <div ref={tokenSectionRef} className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
              <Label className="text-[11px] text-orange-600 dark:text-orange-400 mb-1.5 block font-medium">ERP Credentials</Label>
              <div className="flex items-center gap-2 mb-2">
                <Input
                  type="password"
                  value={localToken}
                  onChange={(e) => setLocalToken(e.target.value)}
                  placeholder="Paste your Bearer token here..."
                  className={`h-9 text-[12px] flex-1 ${
                    localToken && (localToken.startsWith('Bearer ') ? localToken.slice(7) : localToken).startsWith('eyJ') && localToken.split('.').length === 3 && localToken.length > 100
                      ? 'border-green-400'
                      : localToken ? 'border-red-400' : ''
                  }`}
                />
              </div>
              {(() => {
                if (!localToken) return null
                const t = localToken.startsWith('Bearer ') ? localToken.slice(7) : localToken
                const isValid = t.startsWith('eyJ') && t.split('.').length === 3 && t.length > 100
                if (isValid) return (
                  <p className="text-[11px] text-green-600 dark:text-green-400 flex items-center gap-1 mb-2">
                    <span className="inline-block size-2 rounded-full bg-green-500" />
                    Token looks valid
                  </p>
                )
                return (
                  <div ref={tokenErrorRef} className="mb-2 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-2.5 space-y-1.5">
                    <div className="flex items-center gap-1.5">
                      <AlertTriangle className="size-3 text-red-500 shrink-0" />
                      <span className="text-[11px] font-semibold text-red-600 dark:text-red-400">
                        {!t.startsWith('eyJ') ? 'Token must start with eyJ…' : 'Token format looks incorrect'}
                      </span>
                    </div>
                    <p className="text-[11px] text-red-500 dark:text-red-400">
                      Copy from DevTools → Network → any request → Authorization header. Remove the "Bearer " prefix.
                    </p>
                  </div>
                )
              })()}
              <div className="flex flex-wrap gap-1.5 mb-2">
                {[
                  { id: '795', name: 'Jalpan Builders' },
                  { id: '666', name: 'Jay Kisan Ltd' },
                  { id: '686', name: 'Agristack Company' },
                  { id: '751', name: 'Tech Neo' },
                ].map(t => (
                  <button
                    key={t.id}
                    onClick={() => setLocalTenantId(t.id)}
                    className={`px-2 py-0.5 rounded-full text-[11px] font-medium border transition-colors cursor-pointer ${
                      localTenantId === t.id
                        ? 'bg-orange-500 text-white border-orange-500'
                        : 'bg-white dark:bg-gray-800 text-orange-600 dark:text-orange-400 border-orange-300 dark:border-orange-700 hover:bg-orange-50 dark:hover:bg-orange-900/30'
                    }`}
                  >
                    {t.id} · {t.name}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <Input
                  type="text"
                  value={localTenantId}
                  onChange={(e) => setLocalTenantId(e.target.value)}
                  placeholder="Tenant ID (e.g. 708, 711)"
                  className="h-9 text-[12px] w-48"
                />
                <Button
                  onClick={() => { setShowTokenInput(false); loadPBList() }}
                  variant="ghost"
                  size="sm"
                  className="h-9 text-[12px] cursor-pointer"
                >
                  Done
                </Button>
              </div>
              <p className="text-[11px] text-orange-500 dark:text-orange-400 mt-1.5">Credentials stay in your browser session. Clear below to reset.</p>
            </div>
          )}

          {/* PB list — only shown when token panel is closed */}
          {!showTokenInput && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="text-[11px] text-gray-700 dark:text-gray-300">Select Purchase Booking</Label>
                <button
                  onClick={loadPBList}
                  disabled={pbListLoading}
                  className="text-[11px] text-[#3F51B5] dark:text-[#7986CB] flex items-center gap-1 hover:underline cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw className={`size-3 ${pbListLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>

              {pbListError && (
                <p className="text-[11px] text-red-500 dark:text-red-400 mb-2">{pbListError}</p>
              )}

              {pbListLoading && pbList.length === 0 && (
                <LoadingCard message="FETCHING" steps={[{ label: 'Fetching purchase bookings', done: false }]} />
              )}

              {!pbListLoading && pbList.length === 0 && !pbListError && (
                <p className="text-[12px] text-gray-400 dark:text-gray-500 py-2">
                  No purchase bookings found. Click Refresh or check your token.
                </p>
              )}

              {pbList.length > 0 && pbListOpen && (
                <>
                  <Input
                    value={pbSearch}
                    onChange={(e) => setPbSearch(e.target.value)}
                    placeholder="Search by ref no or supplier…"
                    className="h-8 text-[12px] mb-2"
                  />
                  <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden max-h-64 overflow-y-auto">
                    {pbList
                      .filter(pb => {
                        const q = pbSearch.toLowerCase()
                        return !q || pb.ref_no.toLowerCase().includes(q) || pb.supplier.toLowerCase().includes(q)
                      })
                      .map((pb, _i) => (
                        <button
                          key={pb.id ?? `${pb.ref_no}-${_i}`}
                          onClick={() => {
                            setPbRefNo(pb.ref_no); setSelectedPB(pb); setPbListOpen(false)
                            if (jvTab === 'purchase') {
                              handleVerify(pb.ref_no)
                              if (pb.id) {
                                setPbItemsLoading(true); setPbItems([]); setPbTaxableAmount(null); setPbDiscountAmount(null)
                                fetchPBItems(localToken || erpToken, localTenantId || erpTenantId, pb.id)
                                  .then((result) => { setPbItems(result.items); setPbTaxableAmount(result.taxable_amount); setPbDiscountAmount(result.discount_amount) })
                                  .catch(() => {})
                                  .finally(() => setPbItemsLoading(false))
                              }
                            }
                          }}
                          disabled={verifying}
                          className="w-full text-left px-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 hover:bg-[#3F51B5]/5 dark:hover:bg-[#3F51B5]/10 transition-colors cursor-pointer disabled:opacity-50"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <span className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100 shrink-0">{pb.ref_no}</span>
                            {pb.amount && (
                              <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0 font-medium">
                                ₹{Number(pb.amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                              </span>
                            )}
                          </div>
                          {pb.supplier && (
                            <div className="mt-0.5 flex items-center justify-between gap-2">
                              <span className="text-[11px] text-gray-600 dark:text-gray-300 truncate font-medium">{pb.supplier}</span>
                              {pb.date && <span className="text-[10px] text-gray-400 dark:text-gray-500 shrink-0">{pb.date}</span>}
                            </div>
                          )}
                          {(pb.division || pb.department || pb.type_of_sale || pb.location) && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {[pb.division, pb.department, pb.type_of_sale, pb.location].filter(Boolean).map((tag) => (
                                <span key={tag} className="px-1.5 py-0.5 rounded text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </button>
                      ))
                    }
                  </div>
                </>
              )}
            </div>
          )}

          {/* Results view — shown after a PB is selected */}
          {pbRefNo && !pbListOpen && (() => {
            const fieldMismatch = (jvCompRows ?? []).some(r =>
              r.pb !== '—' && r.jv !== '—' && r.pb.trim().toLowerCase() !== r.jv.trim().toLowerCase()
            )
            const _defByNameEarly = new Map<string, typeof accountingDef[0]>()
            for (const d of accountingDef) {
              const k = d.account_name.trim().toLowerCase() + '|' + (d.dr_cr || '').toLowerCase()
              if (!_defByNameEarly.has(k)) _defByNameEarly.set(k, d)
            }
            const accountRowFail = jvAccountRows.some(r => !_defByNameEarly.has(r.account_name.trim().toLowerCase()+'|'+(r.dr_cr||'').toLowerCase()))
            const pbAmt = selectedPB?.amount != null ? Number(selectedPB.amount) : null
            const _uiCr = jvAccountRows.filter(r => r.dr_cr === 'Credit')
            const _uiPayRow = _uiCr.find(r => r.account_name.toLowerCase().includes('payable')) ?? _uiCr.reduce<typeof _uiCr[0]|null>((b,r)=>(r.amount??0)>(b?.amount??0)?r:b,null)
            const amountMismatch = pbAmt != null && _uiPayRow?.amount != null && Math.abs(pbAmt - _uiPayRow.amount) > 0.02
            const passed = jvSteps.length > 0 && jvSteps.every(s => s.ok) && !fieldMismatch && !accountRowFail && !amountMismatch
            const failed = jvSteps.length > 0 && !passed
            const foundStep = jvSteps.find(s => s.n === 1)
            const fieldsStep = jvSteps.find(s => s.fields)
            const balanceStep = jvSteps.find(s => s.detail && !s.fields)
            const balM = balanceStep?.detail?.match(/DR\s*=\s*([\d,]+\.?\d*)\s+[|]CR[|]\s*=\s*([\d,]+\.?\d*)/)

            const normName = (s: string) => s.trim().toLowerCase()
            const fmtAmt = (n: number | null | undefined) =>
              n != null ? n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'

            const defByName = new Map<string, typeof accountingDef[0]>()
            for (const d of accountingDef) {
              const k = normName(d.account_name) + '|' + (d.dr_cr || '').toLowerCase()
              if (!defByName.has(k)) defByName.set(k, d)
            }
            const groups = new Map<string, typeof jvAccountRows>()
            for (const row of jvAccountRows) {
              const key = row.commodity || ''
              if (!groups.has(key)) groups.set(key, [])
              groups.get(key)!.push(row)
            }
            const sortedKeys = [...groups.keys()].sort((a, b) => a===''?1:b===''?-1:a.localeCompare(b))
            const jvNameSet = new Set(jvAccountRows.map(r => normName(r.account_name)))
            const notApplied = accountingDef.filter((d, i, arr) => {
              const k = normName(d.account_name)
              return arr.findIndex(x => normName(x.account_name)===k && x.dr_cr===d.dr_cr)===i && !jvNameSet.has(k)
            })
            const totalDr = jvAccountRows.filter(r => r.dr_cr==='Debit').reduce((s,r)=>s+(r.amount??0),0)
            const totalCr = jvAccountRows.filter(r => r.dr_cr==='Credit').reduce((s,r)=>s+(r.amount??0),0)
            const hasAmounts = jvAccountRows.some(r => r.amount!=null)
            const balanced = Math.abs(totalDr-totalCr)<0.02

            const xrows: { label: string; pb: string; jv: string; indent?: boolean }[] = jvCompRows ?? fieldsStep?.fields?.map(f => ({ label: f.field, pb: '—', jv: f.value })) ?? []

            // shared class constants
            const SECTION_STRIP = 'px-4 py-1.5 bg-gray-100 dark:bg-gray-800/80 border-y border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-widest text-gray-500 dark:text-gray-400'
            const pill = (color: 'green'|'blue'|'purple'|'red'|'gray', label: string) => {
              const cls = {
                green:  'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-700',
                blue:   'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border-blue-200 dark:border-blue-700',
                purple: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 border-purple-200 dark:border-purple-700',
                red:    'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-700',
                gray:   'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 border-gray-200 dark:border-gray-600',
              }[color]
              return <span className={`inline-flex items-center px-1.5 py-px rounded text-[10px] font-semibold border ${cls}`}>{label}</span>
            }
            const statusColor = (s: string): 'green'|'red'|'gray' =>
              s==='PASS' ? 'green' : s==='EXTRA' || s==='WRONG TYPE' ? 'red' : 'gray'

            const renderCond = (condText: string) =>
              <span className="text-[12px] font-medium text-gray-800 dark:text-gray-200">{condText || 'Always applies'}</span>

            return (
              <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-white dark:bg-gray-900 shadow-sm">

                {/* 1. Header bar */}
                <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileBarChart2 className="size-3.5 shrink-0 text-[#3F51B5] dark:text-[#7986CB]" />
                    <span className="text-[12px] font-mono font-bold text-gray-800 dark:text-gray-100 truncate">{pbRefNo}</span>
                    {!verifying && jvSteps.length > 0 && (passed ? pill('green', '✓ Passed') : pill('red', '✕ Failed'))}
                    {verifying && <Loader2 className="size-3.5 animate-spin text-[#3F51B5] shrink-0" />}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button onClick={() => setPurbFullViewOpen(true)} disabled={verifying || jvSteps.length === 0}
                      className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-[#3F51B5]/40 bg-[#3F51B5]/5 text-[#3F51B5] dark:text-[#7986CB] hover:bg-[#3F51B5]/10 dark:hover:bg-[#3F51B5]/20 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">
                      <Maximize2 className="size-3" />Full View
                    </button>
                    <button onClick={exportJvPdf} disabled={verifying || jvSteps.length === 0}
                      className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">
                      <FileText className="size-3" />PDF
                    </button>
                    <button onClick={exportJvReport} disabled={verifying || jvSteps.length === 0}
                      className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">
                      <Download className="size-3" />.xls
                    </button>
                    <button
                      onClick={() => { setPbListOpen(true); setJvSteps([]); setJvError(''); setPbRefNo(''); setSelectedPB(null); setPbItems([]); setPbTaxableAmount(null); setPbDiscountAmount(null); setPurbMeta(null) }}
                      className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-[#3F51B5] dark:hover:text-[#7986CB] hover:border-[#3F51B5]/50 dark:hover:border-[#7986CB]/50 transition-colors cursor-pointer">
                      <RefreshCw className="size-3" />Change
                    </button>
                  </div>
                </div>

                {/* 2. Summary grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-gray-100 dark:divide-gray-800 border-b border-gray-200 dark:border-gray-700">
                  <div className="px-4 py-3">
                    <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Supplier</div>
                    <div className="text-[13px] font-medium text-gray-800 dark:text-gray-100 truncate">{selectedPB?.supplier ?? '—'}</div>
                  </div>
                  <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0">
                    <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Amount</div>
                    <div className="text-[13px] font-mono font-medium text-gray-800 dark:text-gray-100 truncate">
                      {selectedPB?.amount
                        ? <>₹{Number(selectedPB.amount).toLocaleString('en-IN',{maximumFractionDigits:0})}{selectedPB.date && <span className="text-gray-400 dark:text-gray-500 font-sans font-normal"> · {selectedPB.date}</span>}</>
                        : <span className="font-sans font-normal">{selectedPB?.date ?? '—'}</span>}
                    </div>
                  </div>
                  <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0">
                    <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Journal Voucher</div>
                    <div className={`text-[13px] font-medium ${foundStep ? (foundStep.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400') : 'text-gray-400 dark:text-gray-500'}`}>
                      {foundStep ? (foundStep.ok ? '✓ Entry found' : '✕ Not found') : verifying ? 'Checking…' : '—'}
                    </div>
                  </div>
                  <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0">
                    <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Balance Check</div>
                    <div className={`text-[13px] font-medium ${balanceStep ? (balanceStep.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400') : 'text-gray-400 dark:text-gray-500'}`}>
                      {balanceStep
                        ? (balanceStep.ok
                          ? <>✓ Matched{balM && <span className="text-[11px] font-mono font-normal ml-1 text-gray-400 dark:text-gray-500">(DR={balM[1]})</span>}</>
                          : '✕ Unbalanced')
                        : verifying ? 'Checking…' : '—'}
                    </div>
                  </div>
                </div>

                {/* Transaction date / FY / period meta row */}
                {purbMeta && (
                  <div className="grid grid-cols-3 divide-x divide-gray-100 dark:divide-gray-800 border-b border-gray-200 dark:border-gray-700 bg-gray-50/60 dark:bg-gray-800/30">
                    {([
                      { label: 'Transaction Date', val: purbMeta.transaction_date },
                      { label: 'Fiscal Year',      val: purbMeta.fiscal_year },
                      { label: 'Period',           val: purbMeta.period },
                    ] as const).map(({ label, val }) => (
                      <div key={label} className="px-4 py-2.5">
                        <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">{label}</div>
                        <span className="text-[11px] font-mono font-medium text-gray-700 dark:text-gray-200">{val || '—'}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* verifying loading state */}
                {verifying && jvSteps.length === 0 && (
                  <LoadingCard message="VERIFYING" steps={[
                    { label: 'Locating journal voucher', done: false },
                    { label: 'Checking account entries', done: false },
                    { label: 'Validating balance', done: false },
                  ]} />
                )}

                {/* errors */}
                {jvError && !verifying && (
                  <div className="mx-4 my-3 px-3 py-2 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-[11px] text-red-600 dark:text-red-400">{jvError}</div>
                )}

                {/* 3. Field cross-check — real table */}
                {xrows.length > 0 && (
                  <>
                    <div className={SECTION_STRIP}>Field cross-check</div>
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse text-[12px]">
                        <thead>
                          <tr className="bg-gray-50 dark:bg-gray-800/80">
                            {(['Field','Purchase Booking','Journal Voucher','Match'] as const).map(h => (
                              <th key={h} className={`px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left${h==='Match'?' w-14 text-center':''}`}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {xrows.map((row, ri) => {
                            const match = row.pb!=='—' && row.jv!=='—' && row.pb.trim().toLowerCase()===row.jv.trim().toLowerCase()
                            const unk = row.pb==='—' || row.jv==='—'
                            const fail = !unk && !match
                            if (row.indent) {
                              return (
                                <tr key={ri} className={fail ? 'bg-red-50 dark:bg-red-900/20' : 'bg-gray-50/60 dark:bg-gray-800/30'}>
                                  <td className={`pl-7 pr-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[11px] ${fail ? 'text-red-600 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>
                                    <span className="mr-1 opacity-50">·</span>{row.label}
                                  </td>
                                  <td className={`px-3 py-1.5 border border-gray-200 dark:border-gray-700 font-mono text-[11px] ${fail ? 'text-red-600 dark:text-red-400 font-semibold' : 'text-gray-500 dark:text-gray-400'}`}>{row.pb}</td>
                                  <td className={`px-3 py-1.5 border border-gray-200 dark:border-gray-700 font-mono text-[11px] ${fail ? 'text-red-600 dark:text-red-400 font-semibold' : 'text-gray-500 dark:text-gray-400'}`}>{row.jv}</td>
                                  <td className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-center">
                                    {unk ? <span className="text-gray-300 dark:text-gray-600">—</span>
                                      : match ? <CheckCircle2 className="size-3 text-emerald-400 inline" />
                                      : <XCircle className="size-3 text-red-500 inline" />}
                                  </td>
                                </tr>
                              )
                            }
                            return (
                              <tr key={ri} className={fail ? 'bg-red-50 dark:bg-red-900/20' : 'bg-white dark:bg-gray-900 hover:bg-gray-50/50 dark:hover:bg-gray-800/30'}>
                                <td className={`px-3 py-2 border border-gray-200 dark:border-gray-700 font-medium ${fail ? 'text-red-700 dark:text-red-300' : 'text-gray-700 dark:text-gray-300'}`}>{row.label||'—'}</td>
                                <td className={`px-3 py-2 border border-gray-200 dark:border-gray-700 font-mono ${fail ? 'text-red-600 dark:text-red-400 font-semibold' : row.pb==='—'?'text-gray-300 dark:text-gray-600':''}`}>{row.pb}</td>
                                <td className={`px-3 py-2 border border-gray-200 dark:border-gray-700 font-mono ${fail ? 'text-red-600 dark:text-red-400 font-semibold' : row.jv==='—'?'text-gray-300 dark:text-gray-600':''}`}>{row.jv}</td>
                                <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-center">
                                  {unk ? <span className="text-gray-300 dark:text-gray-600">—</span>
                                    : match ? <CheckCircle2 className="size-3.5 text-emerald-500 inline" />
                                    : <XCircle className="size-3.5 text-red-500 inline" />}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}

                {/* 4 + 5. Accounting entries — single continuous table */}
                {(jvAccountRows.length > 0 || accountingDefLoading) && (
                  <>
                    <div className={SECTION_STRIP}>Accounting entries</div>
                    {accountingDefLoading ? (
                      <div className="px-4 py-4 text-[11px] text-gray-400 dark:text-gray-500 italic flex items-center gap-2">
                        <Loader2 className="size-3 animate-spin" />Loading accounting definition…
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse text-[12px]">
                          <thead>
                            <tr className="bg-gray-50 dark:bg-gray-800/80">
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left w-12">DR/CR</th>
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left">Account</th>
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left w-20">Status</th>
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left">Condition</th>
                              <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-right w-28">Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {sortedKeys.map(commodity => {
                              const rows = groups.get(commodity)!
                              const gDr = rows.filter(r=>r.dr_cr==='Debit').reduce((s,r)=>s+(r.amount??0),0)
                              const gCr = rows.filter(r=>r.dr_cr==='Credit').reduce((s,r)=>s+(r.amount??0),0)
                              const hasGrpAmt = rows.some(r=>r.amount!=null)
                              return (
                                <React.Fragment key={commodity||'__shared__'}>
                                  <tr className="bg-indigo-50 dark:bg-indigo-950/40">
                                    <td colSpan={5} className="px-3 py-1.5 border border-indigo-100 dark:border-indigo-900/60">
                                      <div className="flex items-center justify-between">
                                        <span className="text-[11px] font-semibold text-indigo-700 dark:text-indigo-300 uppercase tracking-wide">
                                          {commodity || 'Shared — all items'}
                                        </span>
                                        <span className="text-[10px] font-mono text-indigo-400 dark:text-indigo-500">{rows.length} {rows.length===1?'entry':'entries'}</span>
                                      </div>
                                    </td>
                                  </tr>
                                  {rows.map((row, ri) => {
                                    const def = defByName.get(normName(row.account_name)+'|'+(row.dr_cr||'').toLowerCase())
                                    const drCrMatch = !!def && def.dr_cr===row.dr_cr
                                    const status = !def?'EXTRA':drCrMatch?'PASS':'WRONG TYPE'
                                    const condText = def?.condition_text||(def?'Always applies':'')
                                    const isDebit = row.dr_cr==='Debit'
                                    return (
                                      <tr key={ri} className="bg-white dark:bg-gray-900 hover:bg-gray-50/50 dark:hover:bg-gray-800/20">
                                        <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-center">
                                          {isDebit ? pill('blue','DR') : pill('purple','CR')}
                                        </td>
                                        <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 font-medium text-gray-800 dark:text-gray-100">{row.account_name}</td>
                                        <td className="px-3 py-2 border border-gray-200 dark:border-gray-700">{pill(statusColor(status), status)}</td>
                                        <td className="px-3 py-2 border border-gray-200 dark:border-gray-700">
                                          {condText ? renderCond(condText) : <span className="text-gray-300 dark:text-gray-600">—</span>}
                                        </td>
                                        <td className={`px-3 py-2 border border-gray-200 dark:border-gray-700 text-right font-mono font-semibold ${isDebit?'text-blue-700 dark:text-blue-300':'text-purple-700 dark:text-purple-300'}`}>
                                          {fmtAmt(row.amount)}
                                        </td>
                                      </tr>
                                    )
                                  })}
                                  {hasGrpAmt && rows.length > 1 && (
                                    <tr className="bg-gray-50 dark:bg-gray-800/50">
                                      <td colSpan={4} className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] text-gray-400 dark:text-gray-500 font-medium">Subtotal</td>
                                      <td className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-right font-mono text-[11px]">
                                        {gDr>0 && <span className="text-blue-600 dark:text-blue-400">DR {fmtAmt(gDr)}</span>}
                                        {gDr>0 && gCr>0 && <span className="text-gray-300 dark:text-gray-600 mx-1">·</span>}
                                        {gCr>0 && <span className="text-purple-600 dark:text-purple-400">CR {fmtAmt(gCr)}</span>}
                                      </td>
                                    </tr>
                                  )}
                                </React.Fragment>
                              )
                            })}
                          </tbody>
                          {hasAmounts && (
                            <tfoot>
                              <tr className="bg-white dark:bg-gray-900">
                                <td colSpan={4} className="px-3 py-2.5 border-t-2 border border-gray-300 dark:border-gray-500 font-bold text-[12px] text-gray-700 dark:text-gray-200">Total</td>
                                <td className="px-3 py-2.5 border-t-2 border border-gray-300 dark:border-gray-500 text-right">
                                  <div className="flex items-center justify-end gap-1.5 font-mono text-[12px] font-semibold">
                                    <span className="text-blue-700 dark:text-blue-300">DR {fmtAmt(totalDr)}</span>
                                    <span className={balanced?'text-emerald-600 dark:text-emerald-400':'text-red-500 dark:text-red-400'}>{balanced?'=':'≠'}</span>
                                    <span className="text-purple-700 dark:text-purple-300">CR {fmtAmt(totalCr)}</span>
                                    {balanced ? <CheckCircle2 className="size-3 text-emerald-500" /> : <XCircle className="size-3 text-red-500" />}
                                  </div>
                                </td>
                              </tr>
                            </tfoot>
                          )}
                        </table>
                      </div>
                    )}

                    {/* 6. Not-applied rules — collapsible, own bordered table */}
                    {notApplied.length > 0 && (
                      <div className="border-t border-gray-100 dark:border-gray-800">
                        <button
                          onClick={() => setNotAppliedOpen(o => !o)}
                          className="flex items-center gap-1.5 w-full px-4 py-2 text-[11px] text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors cursor-pointer"
                        >
                          <ChevronDown className={`size-3.5 transition-transform duration-150 ${notAppliedOpen?'rotate-180':''}`} />
                          {notApplied.length} rule{notApplied.length!==1?'s':''} not applied this transaction
                        </button>
                        {notAppliedOpen && (
                          <div className="overflow-x-auto border-t border-gray-100 dark:border-gray-800">
                            <table className="w-full border-collapse text-[12px]">
                              <thead>
                                <tr className="bg-gray-50 dark:bg-gray-800/60">
                                  <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left w-12">DR/CR</th>
                                  <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left">Account</th>
                                  <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left">Why not applied</th>
                                </tr>
                              </thead>
                              <tbody>
                                {notApplied.map((def, ri) => (
                                  <tr key={ri} className="bg-gray-50/50 dark:bg-gray-800/20">
                                    <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-center">
                                      {pill('gray', def.dr_cr==='Debit'?'DR':'CR')}
                                    </td>
                                    <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-gray-400 dark:text-gray-500">{def.account_name}</td>
                                    <td className="px-3 py-2 border border-gray-200 dark:border-gray-700">
                                      {def.condition_text
                                        ? renderCond(def.condition_text)
                                        : <span className="text-gray-300 dark:text-gray-600">—</span>}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}

              {/* ── Purchase JV Full View Modal ── */}
              {purbFullViewOpen && (
                <DialogPrimitive.Root open={purbFullViewOpen} onOpenChange={setPurbFullViewOpen}>
                  <DialogPrimitive.Portal>
                    <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
                    <DialogPrimitive.Content className="fixed inset-4 z-50 flex flex-col bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
                      <DialogPrimitive.Title className="sr-only">Purchase JV Full View — {selectedPB?.ref_no || pbRefNo}</DialogPrimitive.Title>

                      {/* Modal header */}
                      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 dark:border-gray-700 shrink-0 bg-gradient-to-r from-[#3F51B5]/[0.06] to-transparent">
                        <div className="flex items-center gap-3">
                          <FileBarChart2 className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
                          <span className="text-[14px] font-bold font-mono text-gray-800 dark:text-gray-100">{selectedPB?.ref_no || pbRefNo}</span>
                          {passed ? pill('green', '✓ Passed') : pill('red', '✕ Failed')}
                        </div>
                        <div className="flex items-center gap-2">
                          <button onClick={exportJvPdf} className="text-[11px] flex items-center gap-1 h-7 px-2.5 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-red-600 hover:border-red-300 transition-colors cursor-pointer"><FileText className="size-3" />PDF</button>
                          <button onClick={exportJvReport} className="text-[11px] flex items-center gap-1 h-7 px-2.5 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-emerald-600 hover:border-emerald-300 transition-colors cursor-pointer"><Download className="size-3" />.xls</button>
                          <button onClick={() => setPurbFullViewOpen(false)} className="size-7 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors cursor-pointer"><X className="size-4" /></button>
                        </div>
                      </div>

                      {/* Modal body */}
                      <div className="flex-1 overflow-y-auto min-h-0">
                        {/* Meta strip */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-gray-100 dark:divide-gray-800 border-b border-gray-200 dark:border-gray-700">
                          <div className="px-5 py-3"><div className="text-[10px] text-gray-400 font-medium mb-0.5">Supplier</div><div className="text-[13px] font-medium text-gray-800 dark:text-gray-100">{selectedPB?.supplier ?? '—'}</div></div>
                          <div className="px-5 py-3"><div className="text-[10px] text-gray-400 font-medium mb-0.5">Amount</div><div className="text-[13px] font-mono font-medium text-gray-800 dark:text-gray-100">{selectedPB?.amount ? `₹${Number(selectedPB.amount).toLocaleString('en-IN',{maximumFractionDigits:0})}` : '—'}</div></div>
                          {purbMeta && (
                            <>
                              <div className="px-5 py-3"><div className="text-[10px] text-gray-400 font-medium mb-0.5">Fiscal Year</div><div className="text-[13px] font-medium text-gray-800 dark:text-gray-100">{purbMeta.fiscal_year || '—'}</div></div>
                              <div className="px-5 py-3"><div className="text-[10px] text-gray-400 font-medium mb-0.5">Period</div><div className="text-[13px] font-medium text-gray-800 dark:text-gray-100">{purbMeta.period || '—'}</div></div>
                            </>
                          )}
                        </div>

                        {/* Two-column: steps left, entries right */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 divide-y lg:divide-y-0 lg:divide-x divide-gray-200 dark:divide-gray-700">
                          {/* Left: steps + field cross-check */}
                          <div className="p-5 space-y-4">
                            <div>
                              <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Verification Steps</h3>
                              <div className="space-y-1.5">
                                {jvSteps.map((s, i) => (
                                  <div key={i} className={`flex items-start gap-2.5 px-3 py-2 rounded-lg text-[12px] ${s.ok ? 'bg-emerald-50 dark:bg-emerald-900/10' : 'bg-red-50 dark:bg-red-900/10'}`}>
                                    {s.ok ? <CheckCircle2 className="size-3.5 text-emerald-500 shrink-0 mt-px" /> : <XCircle className="size-3.5 text-red-500 shrink-0 mt-px" />}
                                    <div className="min-w-0">
                                      <div className={`font-medium leading-tight ${s.ok ? 'text-gray-700 dark:text-gray-200' : 'text-red-700 dark:text-red-300'}`}>{s.label}</div>
                                      {s.detail && <div className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5 font-mono">{s.detail}</div>}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                            {xrows.length > 0 && (
                              <div>
                                <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Field Cross-Check</h3>
                                <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                                  <table className="w-full border-collapse text-[12px]">
                                    <thead><tr className="bg-gray-50 dark:bg-gray-800/80">
                                      {(['Field','PB Value','JV Value','✓'] as const).map(h => (
                                        <th key={h} className="px-3 py-2 text-left text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">{h}</th>
                                      ))}
                                    </tr></thead>
                                    <tbody>
                                      {xrows.map((row, ri) => {
                                        const match = row.pb!=='—' && row.jv!=='—' && row.pb.trim().toLowerCase()===row.jv.trim().toLowerCase()
                                        const unk = row.pb==='—' || row.jv==='—'
                                        const fail = !unk && !match
                                        return (
                                          <tr key={ri} className={fail ? 'bg-red-50 dark:bg-red-900/20' : ''}>
                                            <td className={`px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 font-medium text-[11px] ${fail?'text-red-700 dark:text-red-300':'text-gray-700 dark:text-gray-300'} ${row.indent?'pl-6':''}`}>{row.label||'—'}</td>
                                            <td className={`px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 font-mono text-[11px] ${fail?'text-red-600 font-semibold':row.pb==='—'?'text-gray-300 dark:text-gray-600':''}`}>{row.pb}</td>
                                            <td className={`px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 font-mono text-[11px] ${fail?'text-red-600 font-semibold':row.jv==='—'?'text-gray-300 dark:text-gray-600':''}`}>{row.jv}</td>
                                            <td className="px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-center">{unk ? <span className="text-gray-300">—</span> : match ? <CheckCircle2 className="size-3 text-emerald-500 inline" /> : <XCircle className="size-3 text-red-500 inline" />}</td>
                                          </tr>
                                        )
                                      })}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Right: accounting entries */}
                          {jvAccountRows.length > 0 && (
                            <div className="p-5">
                              <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Accounting Entries</h3>
                              <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                                <table className="w-full border-collapse text-[12px]">
                                  <thead><tr className="bg-gray-50 dark:bg-gray-800/80">
                                    <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 w-12">DR/CR</th>
                                    <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">Account</th>
                                    <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">Amount</th>
                                  </tr></thead>
                                  <tbody>
                                    {sortedKeys.map(key => {
                                      const rows = groups.get(key)!
                                      return (
                                        <React.Fragment key={key}>
                                          {key && <tr><td colSpan={3} className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800/60 text-[10px] font-semibold text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-800">{key}</td></tr>}
                                          {rows.map((row, ri) => (
                                            <tr key={ri} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/20">
                                              <td className={`px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 font-semibold text-[11px] ${row.dr_cr==='Debit'?'text-blue-700 dark:text-blue-300':'text-rose-600 dark:text-rose-400'}`}>{row.dr_cr==='Debit'?'DR':'CR'}</td>
                                              <td className="px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-gray-700 dark:text-gray-300">{row.account_name}</td>
                                              <td className="px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-right font-mono text-gray-700 dark:text-gray-300">{fmtAmt(row.amount)}</td>
                                            </tr>
                                          ))}
                                        </React.Fragment>
                                      )
                                    })}
                                  </tbody>
                                  <tfoot><tr className={balanced ? 'bg-emerald-50 dark:bg-emerald-900/10' : 'bg-red-50 dark:bg-red-900/10'}>
                                    <td colSpan={2} className="px-3 py-2 font-bold text-[11px] text-gray-700 dark:text-gray-200">Total</td>
                                    <td className="px-3 py-2 text-right font-mono font-bold text-[11px]">
                                      <span className="text-blue-700 dark:text-blue-300">DR {fmtAmt(totalDr)}</span>
                                      <span className="mx-1 text-gray-400">=</span>
                                      <span className="text-rose-600 dark:text-rose-400">CR {fmtAmt(totalCr)}</span>
                                    </td>
                                  </tr></tfoot>
                                </table>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </DialogPrimitive.Content>
                  </DialogPrimitive.Portal>
                </DialogPrimitive.Root>
              )}

              </div>
            )
          })()}
        </div>}

        {/* ── Cross-Check tab ─────────────────────────────────────── */}
        {jvTab === 'crosscheck' && (() => {
          const fmtN = (n: number | null | undefined) =>
            n != null ? n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'

          const passIcon = (ok: boolean) => ok
            ? <CheckCircle2 className="size-3.5 text-emerald-500 shrink-0" />
            : <XCircle className="size-3.5 text-red-500 shrink-0" />

          const ccPill = (ok: boolean) => ok
            ? <span className="inline-flex items-center px-1.5 py-px rounded text-[10px] font-semibold border bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-700">✓ Passed</span>
            : <span className="inline-flex items-center px-1.5 py-px rounded text-[10px] font-semibold border bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-700">✕ Failed</span>

          return (
            <div className="p-4 overflow-y-auto flex-1 min-h-0 space-y-4">
              {/* PB selector */}
              {!ccSelectedPB ? (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-[11px] text-gray-700 dark:text-gray-300">Select Purchase Booking</Label>
                    <button onClick={loadPBList} disabled={pbListLoading} className="text-[11px] text-[#3F51B5] dark:text-[#7986CB] flex items-center gap-1 hover:underline cursor-pointer disabled:opacity-50">
                      <RefreshCw className={`size-3 ${pbListLoading ? 'animate-spin' : ''}`} />Refresh
                    </button>
                  </div>
                  {pbListLoading && pbList.length === 0 && <LoadingCard message="FETCHING" steps={[{ label: 'Fetching purchase bookings', done: false }]} />}
                  {!token && <Button onClick={() => setShowTokenInput(true)} variant="outline" size="sm" className="h-8 text-[12px] gap-1.5 cursor-pointer"><Key className="size-3" />Set Token</Button>}
                  {pbList.length > 0 && (
                    <>
                      <Input value={pbSearch} onChange={(e) => setPbSearch(e.target.value)} placeholder="Search by ref no or supplier…" className="h-8 text-[12px] mb-2" />
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden max-h-64 overflow-y-auto">
                        {pbList.filter(pb => { const q = pbSearch.toLowerCase(); return !q || pb.ref_no.toLowerCase().includes(q) || pb.supplier.toLowerCase().includes(q) }).map((pb, _i) => (
                          <button key={pb.id ?? `${pb.ref_no}-${_i}`}
                            onClick={() => { setCcSelectedPB(pb); setCcPbRefNo(pb.ref_no); handleCcVerifyFor(pb) }}
                            className="w-full text-left px-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 hover:bg-[#3F51B5]/5 dark:hover:bg-[#3F51B5]/10 transition-colors cursor-pointer">
                            <div className="flex items-center justify-between gap-3">
                              <span className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100 shrink-0">{pb.ref_no}</span>
                              {pb.amount && <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0 font-medium">₹{Number(pb.amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>}
                            </div>
                            {pb.supplier && (
                              <div className="mt-0.5 flex items-center justify-between gap-2">
                                <span className="text-[11px] text-gray-600 dark:text-gray-300 truncate font-medium">{pb.supplier}</span>
                                {pb.date && <span className="text-[10px] text-gray-400 dark:text-gray-500 shrink-0">{pb.date}</span>}
                              </div>
                            )}
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              ) : (() => {
                const ccPassed = ccResult ? ccResult.checks.every(c => c.ok) : false
                return (
                <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-white dark:bg-gray-900 shadow-sm">
                  {/* Header bar */}
                  <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2 min-w-0">
                      <GitCompare className="size-3.5 shrink-0 text-[#3F51B5] dark:text-[#7986CB]" />
                      <span className="text-[12px] font-mono font-bold text-gray-800 dark:text-gray-100 truncate">{ccSelectedPB.ref_no}</span>
                      {!ccLoading && ccResult && ccPill(ccPassed)}
                      {ccLoading && <Loader2 className="size-3.5 animate-spin text-[#3F51B5] shrink-0" />}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {!ccLoading && ccResult && (
                        <>
                          <button
                            onClick={() => ccOnFullViewRef.current?.()}
                            className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-[#3F51B5]/40 bg-[#3F51B5]/5 text-[#3F51B5] dark:text-[#7986CB] hover:bg-[#3F51B5]/10 dark:hover:bg-[#3F51B5]/20 transition-colors cursor-pointer">
                            <Maximize2 className="size-3" />Full View
                          </button>
                          <button
                            onClick={() => ccExportPdfRef.current?.()}
                            className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:border-red-300 dark:hover:border-red-700 transition-colors cursor-pointer">
                            <FileText className="size-3" />PDF
                          </button>
                          <button
                            onClick={() => ccExportXlsRef.current?.()}
                            className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:border-emerald-300 dark:hover:border-emerald-700 transition-colors cursor-pointer">
                            <FileSpreadsheet className="size-3" />.xls
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => { setCcSelectedPB(null); setCcPbRefNo(''); setCcResult(null); setCcError('') }}
                        className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-[#3F51B5] dark:hover:text-[#7986CB] hover:border-[#3F51B5]/50 transition-colors cursor-pointer">
                        <RefreshCw className="size-3" />Change
                      </button>
                    </div>
                  </div>

                  {/* Loading */}
                  {ccLoading && (
                    <LoadingCard message="VERIFYING" steps={[
                      { label: 'Fetching PB detail', done: false },
                      { label: 'Scanning JV report for PURB + INV entries', done: false },
                      { label: 'Cross-checking amounts, GST, and structure', done: false },
                    ]} />
                  )}

                  {/* Error */}
                  {ccError && !ccLoading && (
                    <div className="flex items-center gap-2 text-red-600 text-[12px] p-3 m-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                      <AlertTriangle className="size-4 shrink-0" />{ccError}
                    </div>
                  )}

                  {ccResult && !ccLoading && (() => {
                    const r = ccResult
                    const overallOk = r.checks.every(c => c.ok)
                    const failedChecks = r.checks.filter(c => !c.ok)

                    // ── Export helpers ────────────────────────────────────
                    const escXml = (v: string | number) => String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')
                    const cell = (style: string, value: string | number, mergeAcross?: number) => {
                      const type = typeof value === 'number' ? 'Number' : 'String'
                      return `<Cell${mergeAcross != null ? ` ss:MergeAcross="${mergeAcross}"` : ''}${style ? ` ss:StyleID="${style}"` : ''}><Data ss:Type="${type}">${escXml(value)}</Data></Cell>`
                    }
                    const emptyCell = () => `<Cell ss:StyleID="sVal"><Data ss:Type="String"></Data></Cell>`

                    const exportCcXls = () => {
                      const rows: string[] = []
                      const statusText = overallOk ? '✓ PASSED' : `✕ FAILED (${failedChecks.length} issue${failedChecks.length>1?'s':''})`
                      rows.push(`<Row ss:Height="28">${cell('sTitle','CROSS-CHECK JV REPORT',4)}${cell(overallOk?'sPass':'sFail',statusText)}</Row>`)
                      rows.push(`<Row ss:Height="16">${cell('sMeta',`PB: ${r.pb_ref_no}`,2)}${cell('sMeta',`INV: ${r.inv_ref_no||'not found'}`,2)}${cell('sMeta',`Generated: ${new Date().toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'})}`,0)}</Row>`)
                      rows.push('<Row ss:Height="8"/>')
                      rows.push(`<Row ss:Height="19">${cell('sSection','AMOUNTS',5)}</Row>`)
                      rows.push(`<Row>${cell('sLabel','')  }${cell('sLabel','Purchase Booking')}${cell('sLabel','PURB JV')}${cell('sLabel','INV JV')}${cell('sLabel','Match')}</Row>`)
                      rows.push(`<Row>${cell('sLabel','Taxable')}${cell('sVal',r.pb_meta.taxable)}${cell('sVal',r.purb_jv.purchase_gst_dr)}${cell('sVal',r.inv_jv.total_dr)}${cell(r.checks.find(c=>c.id==='taxable_vs_purb')?.ok?'sPass':'sFail',r.checks.find(c=>c.id==='taxable_vs_purb')?.ok?'✓':'✕')}</Row>`)
                      if (r.pb_meta.gst_total > 0) rows.push(`<Row>${cell('sLabel','GST')}${cell('sVal',r.pb_meta.gst_total)}${cell('sVal',r.purb_jv.gst_dr)}${emptyCell()}${cell(r.checks.find(c=>c.id==='gst_total_match')?.ok?'sPass':'sFail',r.checks.find(c=>c.id==='gst_total_match')?.ok?'✓':'✕')}</Row>`)
                      rows.push(`<Row>${cell('sLabel','Payable / Total')}${cell('sVal',r.pb_meta.total)}${cell('sVal',r.purb_jv.payable)}${emptyCell()}${cell(r.checks.find(c=>c.id==='payable_vs_pb')?.ok?'sPass':'sFail',r.checks.find(c=>c.id==='payable_vs_pb')?.ok?'✓':'✕')}</Row>`)
                      rows.push('<Row ss:Height="8"/>')
                      rows.push(`<Row ss:Height="19">${cell('sSection','ALL CHECKS',5)}</Row>`)
                      for (const chk of r.checks) {
                        rows.push(`<Row>${cell('sLabel',chk.category.toUpperCase())}${cell(chk.ok?'sPass':'sFail',chk.ok?'✓ '+chk.label:'✕ '+chk.label,2)}${cell('sVal',chk.detail||'',1)}</Row>`)
                      }
                      const styles = `<Styles>
                        <Style ss:ID="sTitle"><Alignment ss:Horizontal="Left"/><Font ss:Bold="1" ss:Size="13"/><Interior ss:Color="#3F51B5" ss:Pattern="Solid"/><Font ss:Color="#FFFFFF" ss:Bold="1" ss:Size="13"/></Style>
                        <Style ss:ID="sPass"><Interior ss:Color="#D1FAE5" ss:Pattern="Solid"/><Font ss:Color="#065F46" ss:Bold="1"/></Style>
                        <Style ss:ID="sFail"><Interior ss:Color="#FEE2E2" ss:Pattern="Solid"/><Font ss:Color="#991B1B" ss:Bold="1"/></Style>
                        <Style ss:ID="sSection"><Font ss:Bold="1"/><Interior ss:Color="#EEF2FF" ss:Pattern="Solid"/><Font ss:Color="#3730A3" ss:Bold="1"/></Style>
                        <Style ss:ID="sLabel"><Font ss:Bold="1" ss:Size="10"/><Interior ss:Color="#F9FAFB" ss:Pattern="Solid"/></Style>
                        <Style ss:ID="sVal"><Alignment ss:Horizontal="Right"/><NumberFormat ss:Format="#,##0.00"/></Style>
                        <Style ss:ID="sMeta"><Font ss:Italic="1" ss:Color="#6B7280"/></Style>
                      </Styles>`
                      const xml = `<?xml version="1.0"?><?mso-application progid="Excel.Sheet"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">${styles}<Worksheet ss:Name="Cross-Check"><Table>${rows.join('')}</Table></Worksheet></Workbook>`
                      const blob = new Blob([xml], { type: 'application/vnd.ms-excel' })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a'); a.href = url; a.download = `cross-check-${r.pb_ref_no.replace(/\//g,'-')}.xls`; a.click()
                      URL.revokeObjectURL(url)
                    }

                    const exportCcPdf = () => {
                      const lines: string[] = []
                      lines.push(`CROSS-CHECK JV REPORT — ${overallOk ? 'PASSED' : 'FAILED'}`)
                      lines.push(`PB: ${r.pb_ref_no}  |  INV: ${r.inv_ref_no||'not found'}  |  FY: ${r.purb_jv.fiscal_year}  Period: ${r.purb_jv.period}`)
                      lines.push(`Supplier: ${ccSelectedPB!.supplier||'—'}  |  Date: ${ccSelectedPB!.date||'—'}`)
                      lines.push('')
                      lines.push('AMOUNTS')
                      lines.push(`  Taxable:   PB ${fmtN(r.pb_meta.taxable)}  |  PURB JV ${fmtN(r.purb_jv.purchase_gst_dr)}  |  INV JV ${fmtN(r.inv_jv.total_dr)}`)
                      if (r.pb_meta.gst_total > 0) lines.push(`  GST:       PB ${fmtN(r.pb_meta.gst_total)}  |  PURB JV ${fmtN(r.purb_jv.gst_dr)}`)
                      lines.push(`  Payable:   PB ${fmtN(r.pb_meta.total)}  |  PURB JV ${fmtN(r.purb_jv.payable)}`)
                      lines.push('')
                      lines.push('CHECKS')
                      for (const chk of r.checks) {
                        lines.push(`  ${chk.ok ? '✓' : '✕'} [${chk.category}] ${chk.label}`)
                        if (!chk.ok && chk.detail) lines.push(`      ${chk.detail}`)
                      }
                      const content = lines.join('\n')
                      const win = window.open('', '_blank')
                      if (win) { win.document.write(`<html><head><title>Cross-Check ${r.pb_ref_no}</title><style>body{font-family:monospace;font-size:12px;padding:24px;white-space:pre}</style></head><body>${content.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</body></html>`); win.document.close(); win.print() }
                    }

                    // ── Full View state (local to this IIFE via ref) ─────
                    // We use a separate state declared at component level
                    const chkIcon = (ok: boolean) => ok
                      ? <CheckCircle2 className="size-3.5 text-emerald-500 shrink-0" />
                      : <XCircle className="size-3.5 text-red-500 shrink-0" />

                    // ── Summary numbers ──────────────────────────────────
                    const taxableChk = r.checks.find(c => c.id === 'taxable_vs_purb')
                    const gstChk     = r.checks.find(c => c.id === 'gst_total_match')
                    const payableChk = r.checks.find(c => c.id === 'payable_vs_pb')
                    const invEqChk   = r.checks.find(c => c.id === 'inv_eq_purb_minus_gst')

                    return (
                      <>
                        {/* ── Compact amount summary grid ─────────────── */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-gray-100 dark:divide-gray-800 border-b border-gray-200 dark:border-gray-700">
                          {[
                            { label: 'Supplier', value: ccSelectedPB!.supplier ?? '—', mono: false },
                            { label: 'Date', value: ccSelectedPB!.date ?? '—', mono: false },
                            { label: 'FY / Period', value: `${r.purb_jv.fiscal_year} · ${r.purb_jv.period}`, mono: false },
                            { label: 'INV JV Ref', value: r.inv_ref_no || 'Not found', mono: true },
                          ].map(({ label, value, mono }) => (
                            <div key={label} className="px-4 py-3">
                              <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">{label}</div>
                              <div className={`text-[13px] font-medium text-gray-800 dark:text-gray-100 truncate ${mono ? 'font-mono text-[11px]' : ''}`}>{value}</div>
                            </div>
                          ))}
                        </div>

                        {/* ── 3-source comparison table ───────────────── */}
                        <div className="border-b border-gray-200 dark:border-gray-700">
                          <div className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800/60 text-[10px] font-semibold uppercase tracking-widest text-gray-500 dark:text-gray-400">
                            Amount Cross-Check — PB vs PURB JV vs INV JV
                          </div>
                          {/* column headers */}
                          <div className="grid grid-cols-[1fr_auto_auto_auto_auto] text-[10px] font-semibold uppercase text-gray-400 bg-gray-50/60 dark:bg-gray-800/30 px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 gap-x-4">
                            <span>Line</span>
                            <span className="text-right w-24">PB</span>
                            <span className="text-right w-24">PURB JV</span>
                            <span className="text-right w-24">INV JV</span>
                            <span className="w-4" />
                          </div>
                          {/* Taxable */}
                          <div className={`grid grid-cols-[1fr_auto_auto_auto_auto] px-3 py-2 gap-x-4 border-b border-gray-100 dark:border-gray-800 ${taxableChk && !taxableChk.ok ? 'bg-red-50/40 dark:bg-red-900/5' : ''}`}>
                            <div>
                              <div className="text-[12px] font-medium text-gray-800 dark:text-gray-200">Taxable Amount</div>
                              <div className="text-[10px] text-gray-400 mt-0.5">Purchase @gst · Closing Stock</div>
                            </div>
                            <span className="text-right w-24 font-mono text-[12px] self-center text-gray-700 dark:text-gray-200">{fmtN(r.pb_meta.taxable)}</span>
                            <span className="text-right w-24 font-mono text-[12px] self-center text-blue-700 dark:text-blue-300">{fmtN(r.purb_jv.purchase_gst_dr)}</span>
                            <span className="text-right w-24 font-mono text-[12px] self-center text-rose-600 dark:text-rose-400">{fmtN(r.inv_jv.total_dr)}</span>
                            <span className="self-center">{taxableChk && chkIcon(taxableChk.ok)}</span>
                          </div>
                          {/* GST */}
                          {r.pb_meta.gst_total > 0 && (
                            <div className={`grid grid-cols-[1fr_auto_auto_auto_auto] px-3 py-2 gap-x-4 border-b border-gray-100 dark:border-gray-800 ${gstChk && !gstChk.ok ? 'bg-red-50/40 dark:bg-red-900/5' : ''}`}>
                              <div>
                                <div className="text-[12px] font-medium text-gray-800 dark:text-gray-200">GST</div>
                                <div className="text-[10px] text-gray-400 mt-0.5">
                                  {r.purb_jv.igst_dr > 0 ? `IGST` : 'CGST + SGST'}
                                  {r.checks.find(c=>c.id.startsWith('gst_rate_')) && (() => { const rc = r.checks.find(c=>c.id.startsWith('gst_rate_')); return rc ? ` · ${rc.label.match(/\d+\.?\d*%/)?.[0]||''}` : '' })()}
                                </div>
                              </div>
                              <span className="text-right w-24 font-mono text-[12px] self-center text-gray-700 dark:text-gray-200">{fmtN(r.pb_meta.gst_total)}</span>
                              <span className="text-right w-24 font-mono text-[12px] self-center text-blue-700 dark:text-blue-300">{fmtN(r.purb_jv.gst_dr)}</span>
                              <span className="text-right w-24 font-mono text-[12px] self-center text-gray-400">—</span>
                              <span className="self-center">{gstChk && chkIcon(gstChk.ok)}</span>
                            </div>
                          )}
                          {/* Payable */}
                          <div className={`grid grid-cols-[1fr_auto_auto_auto_auto] px-3 py-2 gap-x-4 border-b border-gray-100 dark:border-gray-800 ${payableChk && !payableChk.ok ? 'bg-red-50/40 dark:bg-red-900/5' : ''}`}>
                            <div>
                              <div className="text-[12px] font-medium text-gray-800 dark:text-gray-200">Payable (Total)</div>
                              <div className="text-[10px] text-gray-400 mt-0.5">Taxable + GST{r.pb_meta.tds > 0 ? ' − TDS' : ''}</div>
                            </div>
                            <span className="text-right w-24 font-mono text-[12px] self-center font-semibold text-gray-700 dark:text-gray-200">{fmtN(r.pb_meta.total)}</span>
                            <span className="text-right w-24 font-mono text-[12px] self-center font-semibold text-rose-600 dark:text-rose-400">{fmtN(r.purb_jv.payable)}</span>
                            <span className="text-right w-24 font-mono text-[12px] self-center text-gray-400">—</span>
                            <span className="self-center">{payableChk && chkIcon(payableChk.ok)}</span>
                          </div>
                          {/* INV formula */}
                          {invEqChk && (
                            <div className={`grid grid-cols-[1fr_auto_auto_auto_auto] px-3 py-2 gap-x-4 ${!invEqChk.ok ? 'bg-red-50/40 dark:bg-red-900/5' : 'bg-blue-50/30 dark:bg-blue-900/5'}`}>
                              <div>
                                <div className="text-[12px] font-medium text-gray-800 dark:text-gray-200">INV = PURB − GST</div>
                                <div className="text-[10px] text-gray-400 mt-0.5 font-mono">{fmtN(r.purb_jv.total_dr)} − {fmtN(r.purb_jv.gst_dr)} = {fmtN(r.purb_jv.total_dr - r.purb_jv.gst_dr)}</div>
                              </div>
                              <span className="self-center" />
                              <span className="text-right w-24 font-mono text-[12px] self-center text-gray-400">total DR {fmtN(r.purb_jv.total_dr)}</span>
                              <span className="text-right w-24 font-mono text-[12px] self-center text-rose-600 dark:text-rose-400">{fmtN(r.inv_jv.total_dr)}</span>
                              <span className="self-center">{chkIcon(invEqChk.ok)}</span>
                            </div>
                          )}
                        </div>

                        {/* ── Failed checks callout ────────────────────── */}
                        {failedChecks.length > 0 && (
                          <div className="border-b border-gray-200 dark:border-gray-700">
                            <div className="px-3 py-1.5 bg-red-50 dark:bg-red-900/20 text-[10px] font-semibold uppercase tracking-widest text-red-600 dark:text-red-400 border-b border-red-100 dark:border-red-800">
                              Failed Checks
                            </div>
                            <div className="divide-y divide-gray-100 dark:divide-gray-800">
                              {failedChecks.map(chk => (
                                <div key={chk.id} className="px-3 py-2 flex items-start gap-2 bg-red-50/30 dark:bg-red-900/5">
                                  <XCircle className="size-3.5 text-red-500 shrink-0 mt-0.5" />
                                  <div>
                                    <div className="text-[12px] text-gray-800 dark:text-gray-200">{chk.label}</div>
                                    {chk.detail && <div className="text-[11px] text-gray-400 font-mono mt-0.5">{chk.detail}</div>}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* ── All checks compact list ──────────────────── */}
                        {failedChecks.length === 0 && (
                          <div className="border-b border-gray-200 dark:border-gray-700">
                            <div className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800/60 text-[10px] font-semibold uppercase tracking-widest text-gray-500 dark:text-gray-400">
                              All Checks Passed
                            </div>
                            <div className="divide-y divide-gray-100 dark:divide-gray-800">
                              {r.checks.map(chk => (
                                <div key={chk.id} className="px-3 py-1.5 flex items-center gap-2">
                                  <CheckCircle2 className="size-3 text-emerald-500 shrink-0" />
                                  <span className="text-[11px] text-gray-600 dark:text-gray-400">{chk.label}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* ── Per-commodity ────────────────────────────── */}
                        {r.commodity_rows.length > 0 && (
                          <div className="border-b border-gray-200 dark:border-gray-700">
                            <div className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800/60 text-[10px] font-semibold uppercase tracking-widest text-gray-500 dark:text-gray-400">
                              Per-Commodity — PURB Purchase@GST = INV Closing Stock
                            </div>
                            <div className="overflow-x-auto">
                              <table className="w-full text-[11px]">
                                <thead>
                                  <tr className="text-gray-400 border-b border-gray-100 dark:border-gray-800">
                                    <th className="px-3 py-1.5 text-left">Commodity</th>
                                    <th className="px-3 py-1.5 text-right">PURB Purchase@GST</th>
                                    <th className="px-3 py-1.5 text-right">PURB GST (I/C/S)</th>
                                    <th className="px-3 py-1.5 text-right">INV Closing DR</th>
                                    <th className="px-3 py-1.5 text-center w-8" />
                                  </tr>
                                </thead>
                                <tbody>
                                  {r.commodity_rows.map((row, i) => {
                                    const gstParts = [
                                      row.purb_igst ? `I ${fmtN(row.purb_igst)}` : null,
                                      row.purb_cgst ? `C ${fmtN(row.purb_cgst)}` : null,
                                      row.purb_sgst ? `S ${fmtN(row.purb_sgst)}` : null,
                                    ].filter(Boolean).join(' / ')
                                    return (
                                      <tr key={i} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50/50 dark:hover:bg-gray-800/20">
                                        <td className="px-3 py-1.5 font-medium text-gray-700 dark:text-gray-300">{row.commodity}</td>
                                        <td className="px-3 py-1.5 text-right font-mono text-blue-700 dark:text-blue-300">{fmtN(row.purb_purchase_gst)}</td>
                                        <td className="px-3 py-1.5 text-right font-mono text-gray-400 text-[10px]">{gstParts || '—'}</td>
                                        <td className="px-3 py-1.5 text-right font-mono text-rose-600 dark:text-rose-400">{fmtN(row.inv_closing_dr)}</td>
                                        <td className="px-3 py-1.5 text-center">{chkIcon(row.taxable_match && row.inv_balanced)}</td>
                                      </tr>
                                    )
                                  })}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* ── PURB JV Accounting Entries (grouped by commodity) ── */}
                        {r.purb_jv.rows.length > 0 && (() => {
                          // group by commodity
                          const grpMap = new Map<string, typeof r.purb_jv.rows>()
                          for (const row of r.purb_jv.rows) {
                            const key = row.commodity || ''
                            if (!grpMap.has(key)) grpMap.set(key, [])
                            grpMap.get(key)!.push(row)
                          }
                          // put empty-commodity (Payable) last
                          const keys = [...grpMap.keys()].sort((a, b) => a === '' ? 1 : b === '' ? -1 : a.localeCompare(b))

                          return (
                            <div className="border-b border-gray-200 dark:border-gray-700">
                              <div className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800/60 text-[10px] font-semibold uppercase tracking-widest text-gray-500 dark:text-gray-400">
                                PURB JV Accounting Entries · {r.pb_ref_no}
                              </div>
                              <table className="w-full text-[11px]">
                                <thead>
                                  <tr className="bg-gray-50/60 dark:bg-gray-800/30 text-gray-400 border-b border-gray-200 dark:border-gray-700">
                                    <th className="px-3 py-1.5 text-left w-10">DR/CR</th>
                                    <th className="px-3 py-1.5 text-left">Account</th>
                                    <th className="px-3 py-1.5 text-right">Amount</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {keys.map(key => {
                                    const rows = grpMap.get(key)!
                                    const subDr = rows.filter(r => r.dr_cr === 'Debit').reduce((s, r) => s + r.amount, 0)
                                    const subCr = rows.filter(r => r.dr_cr === 'Credit').reduce((s, r) => s + r.amount, 0)
                                    return (
                                      <React.Fragment key={key || '__payable__'}>
                                        {key && (
                                          <tr className="bg-gray-50 dark:bg-gray-800/50">
                                            <td colSpan={2} className="px-3 py-1 text-[10px] font-semibold text-gray-600 dark:text-gray-400 border-b border-gray-100 dark:border-gray-800">
                                              {key} <span className="font-normal text-gray-400">· {rows.length} {rows.length === 1 ? 'entry' : 'entries'}</span>
                                            </td>
                                            <td className="px-3 py-1 text-[10px] text-right text-gray-400 border-b border-gray-100 dark:border-gray-800 font-mono">
                                              {subDr > 0 && <span className="text-blue-600 dark:text-blue-400">DR {fmtN(subDr)}</span>}
                                              {subDr > 0 && subCr > 0 && <span className="mx-1">·</span>}
                                              {subCr > 0 && <span className="text-rose-500">CR {fmtN(subCr)}</span>}
                                            </td>
                                          </tr>
                                        )}
                                        {rows.map((row, ri) => (
                                          <tr key={ri} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50/50 dark:hover:bg-gray-800/20">
                                            <td className={`px-3 py-1.5 font-semibold ${row.dr_cr === 'Debit' ? 'text-blue-700 dark:text-blue-300' : 'text-rose-600 dark:text-rose-400'}`}>
                                              {row.dr_cr === 'Debit' ? 'DR' : 'CR'}
                                            </td>
                                            <td className="px-3 py-1.5 text-gray-700 dark:text-gray-300">{row.account_name}</td>
                                            <td className="px-3 py-1.5 text-right font-mono text-gray-700 dark:text-gray-300">{fmtN(row.amount)}</td>
                                          </tr>
                                        ))}
                                      </React.Fragment>
                                    )
                                  })}
                                </tbody>
                                <tfoot>
                                  <tr className={`${r.checks.find(c => c.id === 'purb_balanced')?.ok ? 'bg-emerald-50 dark:bg-emerald-900/10' : 'bg-red-50 dark:bg-red-900/10'}`}>
                                    <td colSpan={2} className="px-3 py-2 font-bold text-[11px] text-gray-700 dark:text-gray-200">Total</td>
                                    <td className="px-3 py-2 text-right font-mono font-bold text-[11px]">
                                      <span className="text-blue-700 dark:text-blue-300">DR {fmtN(r.purb_jv.total_dr)}</span>
                                      <span className="mx-1 text-gray-400">=</span>
                                      <span className="text-rose-600 dark:text-rose-400">CR {fmtN(r.purb_jv.payable)}</span>
                                    </td>
                                  </tr>
                                </tfoot>
                              </table>
                            </div>
                          )
                        })()}

                        {/* ── INV JV Accounting Entries (grouped by commodity) ── */}
                        {r.inv_jv.rows.length > 0 && (() => {
                          const grpMap = new Map<string, typeof r.inv_jv.rows>()
                          for (const row of r.inv_jv.rows) {
                            const key = row.commodity || ''
                            if (!grpMap.has(key)) grpMap.set(key, [])
                            grpMap.get(key)!.push(row)
                          }
                          const keys = [...grpMap.keys()].sort((a, b) => a === '' ? 1 : b === '' ? -1 : a.localeCompare(b))

                          return (
                            <div className="border-b border-gray-200 dark:border-gray-700">
                              <div className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800/60 text-[10px] font-semibold uppercase tracking-widest text-gray-500 dark:text-gray-400">
                                INV JV Accounting Entries · {r.inv_ref_no || '—'}
                              </div>
                              <table className="w-full text-[11px]">
                                <thead>
                                  <tr className="bg-gray-50/60 dark:bg-gray-800/30 text-gray-400 border-b border-gray-200 dark:border-gray-700">
                                    <th className="px-3 py-1.5 text-left w-10">DR/CR</th>
                                    <th className="px-3 py-1.5 text-left">Account</th>
                                    <th className="px-3 py-1.5 text-right">Amount</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {keys.map(key => {
                                    const rows = grpMap.get(key)!
                                    const subDr = rows.filter(r => r.dr_cr === 'Debit').reduce((s, r) => s + r.amount, 0)
                                    const subCr = rows.filter(r => r.dr_cr === 'Credit').reduce((s, r) => s + r.amount, 0)
                                    return (
                                      <React.Fragment key={key || '__inv_other__'}>
                                        {key && (
                                          <tr className="bg-gray-50 dark:bg-gray-800/50">
                                            <td colSpan={2} className="px-3 py-1 text-[10px] font-semibold text-gray-600 dark:text-gray-400 border-b border-gray-100 dark:border-gray-800">
                                              {key} <span className="font-normal text-gray-400">· {rows.length} {rows.length === 1 ? 'entry' : 'entries'}</span>
                                            </td>
                                            <td className="px-3 py-1 text-[10px] text-right text-gray-400 border-b border-gray-100 dark:border-gray-800 font-mono">
                                              {subDr > 0 && <span className="text-blue-600 dark:text-blue-400">DR {fmtN(subDr)}</span>}
                                              {subDr > 0 && subCr > 0 && <span className="mx-1">·</span>}
                                              {subCr > 0 && <span className="text-rose-500">CR {fmtN(subCr)}</span>}
                                            </td>
                                          </tr>
                                        )}
                                        {rows.map((row, ri) => (
                                          <tr key={ri} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50/50 dark:hover:bg-gray-800/20">
                                            <td className={`px-3 py-1.5 font-semibold ${row.dr_cr === 'Debit' ? 'text-blue-700 dark:text-blue-300' : 'text-rose-600 dark:text-rose-400'}`}>
                                              {row.dr_cr === 'Debit' ? 'DR' : 'CR'}
                                            </td>
                                            <td className="px-3 py-1.5 text-gray-700 dark:text-gray-300">{row.account_name}</td>
                                            <td className="px-3 py-1.5 text-right font-mono text-gray-700 dark:text-gray-300">{fmtN(row.amount)}</td>
                                          </tr>
                                        ))}
                                      </React.Fragment>
                                    )
                                  })}
                                </tbody>
                                <tfoot>
                                  <tr className={`${r.checks.find(c => c.id === 'inv_balanced')?.ok ? 'bg-emerald-50 dark:bg-emerald-900/10' : 'bg-red-50 dark:bg-red-900/10'}`}>
                                    <td colSpan={2} className="px-3 py-2 font-bold text-[11px] text-gray-700 dark:text-gray-200">Total</td>
                                    <td className="px-3 py-2 text-right font-mono font-bold text-[11px]">
                                      <span className="text-blue-700 dark:text-blue-300">DR {fmtN(r.inv_jv.closing_dr)}</span>
                                      <span className="mx-1 text-gray-400">=</span>
                                      <span className="text-rose-600 dark:text-rose-400">CR {fmtN(r.inv_jv.exempt_cr)}</span>
                                    </td>
                                  </tr>
                                </tfoot>
                              </table>
                            </div>
                          )
                        })()}

                        {/* ── Full View modal (same shell as Purchase + INV tabs) ── */}
                        {ccFullViewOpen && (
                          <DialogPrimitive.Root open={ccFullViewOpen} onOpenChange={setCcFullViewOpen}>
                            <DialogPrimitive.Portal>
                              <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
                              <DialogPrimitive.Content className="fixed inset-4 z-50 flex flex-col bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
                                <DialogPrimitive.Title className="sr-only">Cross-Check Full View — {r.pb_ref_no}</DialogPrimitive.Title>

                                {/* Modal header */}
                                <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 dark:border-gray-700 shrink-0 bg-gradient-to-r from-[#3F51B5]/[0.06] to-transparent">
                                  <div className="flex items-center gap-3">
                                    <GitCompare className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
                                    <span className="text-[14px] font-bold font-mono text-gray-800 dark:text-gray-100">{r.pb_ref_no}</span>
                                    {overallOk ? ccPill(true) : ccPill(false)}
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <button onClick={exportCcPdf} className="text-[11px] flex items-center gap-1 h-7 px-2.5 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-red-600 hover:border-red-300 transition-colors cursor-pointer"><FileText className="size-3" />PDF</button>
                                    <button onClick={exportCcXls} className="text-[11px] flex items-center gap-1 h-7 px-2.5 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-emerald-600 hover:border-emerald-300 transition-colors cursor-pointer"><FileSpreadsheet className="size-3" />.xls</button>
                                    <button onClick={() => setCcFullViewOpen(false)} className="size-7 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors cursor-pointer"><X className="size-4" /></button>
                                  </div>
                                </div>

                                {/* Modal body */}
                                <div className="flex-1 overflow-y-auto min-h-0">
                                  {/* Meta strip */}
                                  <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-gray-100 dark:divide-gray-800 border-b border-gray-200 dark:border-gray-700">
                                    <div className="px-5 py-3"><div className="text-[10px] text-gray-400 font-medium mb-0.5">Supplier</div><div className="text-[13px] font-medium text-gray-800 dark:text-gray-100">{ccSelectedPB!.supplier ?? '—'}</div></div>
                                    <div className="px-5 py-3"><div className="text-[10px] text-gray-400 font-medium mb-0.5">PB Date</div><div className="text-[13px] font-medium text-gray-800 dark:text-gray-100">{ccSelectedPB!.date?.slice(0,10) ?? '—'}</div></div>
                                    <div className="px-5 py-3"><div className="text-[10px] text-gray-400 font-medium mb-0.5">Fiscal Year</div><div className="text-[13px] font-medium text-gray-800 dark:text-gray-100">{r.purb_jv.fiscal_year || '—'}</div></div>
                                    <div className="px-5 py-3"><div className="text-[10px] text-gray-400 font-medium mb-0.5">Period</div><div className="text-[13px] font-medium text-gray-800 dark:text-gray-100">{r.purb_jv.period || '—'}</div></div>
                                  </div>

                                  {/* Two-column: checks left, JV entries right */}
                                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 divide-y lg:divide-y-0 lg:divide-x divide-gray-200 dark:divide-gray-700">

                                    {/* Left: all checks */}
                                    <div className="p-5 space-y-4">
                                      <div>
                                        <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Verification Checks</h3>
                                        <div className="space-y-1.5">
                                          {r.checks.map((chk, i) => (
                                            <div key={i} className={`flex items-start gap-2.5 px-3 py-2 rounded-lg text-[12px] ${chk.ok ? 'bg-emerald-50 dark:bg-emerald-900/10' : 'bg-red-50 dark:bg-red-900/10'}`}>
                                              {chk.ok ? <CheckCircle2 className="size-3.5 text-emerald-500 shrink-0 mt-px" /> : <XCircle className="size-3.5 text-red-500 shrink-0 mt-px" />}
                                              <div className="min-w-0">
                                                <div className={`font-medium leading-tight ${chk.ok ? 'text-gray-700 dark:text-gray-200' : 'text-red-700 dark:text-red-300'}`}>{chk.label}</div>
                                                {chk.detail && <div className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5 font-mono">{chk.detail}</div>}
                                              </div>
                                            </div>
                                          ))}
                                        </div>
                                      </div>

                                      {/* Amount chain */}
                                      {r.amount_chain.length > 0 && (
                                        <div>
                                          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Amount Chain</h3>
                                          <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                                            <table className="w-full border-collapse text-[12px]">
                                              <thead><tr className="bg-gray-50 dark:bg-gray-800/80">
                                                <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">Line</th>
                                                <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">PB</th>
                                                <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">PURB JV</th>
                                                <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">INV JV</th>
                                                <th className="px-3 py-2 text-center text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 w-8">✓</th>
                                              </tr></thead>
                                              <tbody>
                                                {r.amount_chain.map((row, i) => {
                                                  const isEq = row.sign === 'eq'
                                                  return (
                                                    <tr key={i} className={isEq ? 'bg-blue-50/40 dark:bg-blue-900/5' : 'hover:bg-gray-50/50 dark:hover:bg-gray-800/20'}>
                                                      <td className={`px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 ${isEq ? 'font-semibold text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-400'}`}>
                                                        <span className="font-mono text-gray-400 mr-1">{row.sign === 'minus' ? '−' : row.sign === 'plus' ? '+' : row.sign === 'eq' ? '=' : ' '}</span>
                                                        {row.label}
                                                        {row.note && <span className="ml-1 text-[10px] text-gray-400 bg-gray-100 dark:bg-gray-800 px-1 rounded">{row.note}</span>}
                                                      </td>
                                                      <td className={`px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-right font-mono ${isEq ? 'font-semibold text-blue-700 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}`}>{fmtN(Math.abs(row.amount))}</td>
                                                      <td className="px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-right font-mono text-gray-400">{row.cross?.purb != null ? fmtN(row.cross.purb) : '—'}</td>
                                                      <td className="px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-right font-mono text-gray-400">{row.cross?.inv != null ? fmtN(row.cross.inv) : '—'}</td>
                                                      <td className="px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-center">{row.ok != null ? (row.ok ? <CheckCircle2 className="size-3.5 text-emerald-500 inline" /> : <XCircle className="size-3.5 text-red-500 inline" />) : null}</td>
                                                    </tr>
                                                  )
                                                })}
                                              </tbody>
                                            </table>
                                          </div>
                                        </div>
                                      )}
                                    </div>

                                    {/* Right: PURB entries + INV entries + per-commodity */}
                                    <div className="p-5 space-y-5">
                                      {[
                                        { title: `PURB JV Accounting Entries · ${r.pb_ref_no}`, rows: r.purb_jv.rows, totalDr: r.purb_jv.total_dr, balanced: r.checks.find(c=>c.id==='purb_balanced')?.ok ?? true },
                                        { title: `INV JV Accounting Entries · ${r.inv_ref_no||'—'}`, rows: r.inv_jv.rows, totalDr: r.inv_jv.total_dr, balanced: r.checks.find(c=>c.id==='inv_balanced')?.ok ?? true },
                                      ].map(({ title, rows, totalDr, balanced }) => {
                                        if (rows.length === 0) return null
                                        const grp = new Map<string, typeof rows>()
                                        for (const row of rows) {
                                          const k = row.commodity || ''
                                          if (!grp.has(k)) grp.set(k, [])
                                          grp.get(k)!.push(row)
                                        }
                                        const sortedK = [...grp.keys()].sort((a,b)=>a===''?1:b===''?-1:a.localeCompare(b))
                                        const totDr = rows.filter(r=>r.dr_cr==='Debit').reduce((s,r)=>s+r.amount,0)
                                        const totCr = rows.filter(r=>r.dr_cr==='Credit').reduce((s,r)=>s+r.amount,0)
                                        return (
                                          <div key={title}>
                                            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">{title}</h3>
                                            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                                              <table className="w-full border-collapse text-[12px]">
                                                <thead><tr className="bg-gray-50 dark:bg-gray-800/80">
                                                  <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 w-12">DR/CR</th>
                                                  <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">Account</th>
                                                  <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">Amount</th>
                                                </tr></thead>
                                                <tbody>
                                                  {sortedK.map(key => {
                                                    const krows = grp.get(key)!
                                                    return (
                                                      <React.Fragment key={key}>
                                                        {key && <tr><td colSpan={3} className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800/60 text-[10px] font-semibold text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-800">{key}</td></tr>}
                                                        {krows.map((row, ri) => (
                                                          <tr key={ri} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/20">
                                                            <td className={`px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 font-semibold text-[11px] ${row.dr_cr==='Debit'?'text-blue-700 dark:text-blue-300':'text-rose-600 dark:text-rose-400'}`}>{row.dr_cr==='Debit'?'DR':'CR'}</td>
                                                            <td className="px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-gray-700 dark:text-gray-300">{row.account_name}</td>
                                                            <td className="px-3 py-1.5 border-b border-gray-100 dark:border-gray-800 text-right font-mono text-gray-700 dark:text-gray-300">{fmtN(row.amount)}</td>
                                                          </tr>
                                                        ))}
                                                      </React.Fragment>
                                                    )
                                                  })}
                                                </tbody>
                                                <tfoot><tr className={balanced ? 'bg-emerald-50 dark:bg-emerald-900/10' : 'bg-red-50 dark:bg-red-900/10'}>
                                                  <td colSpan={2} className="px-3 py-2 font-bold text-[11px] text-gray-700 dark:text-gray-200">Total</td>
                                                  <td className="px-3 py-2 text-right font-mono font-bold text-[11px]">
                                                    <span className="text-blue-700 dark:text-blue-300">DR {fmtN(totDr)}</span>
                                                    <span className="mx-1 text-gray-400">=</span>
                                                    <span className="text-rose-600 dark:text-rose-400">CR {fmtN(totCr)}</span>
                                                  </td>
                                                </tr></tfoot>
                                              </table>
                                            </div>
                                          </div>
                                        )
                                      })}

                                      {/* Per-commodity */}
                                      {r.commodity_rows.length > 0 && (
                                        <div>
                                          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">Per-Commodity Cross-Check</h3>
                                          <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                                            <table className="w-full border-collapse text-[12px]">
                                              <thead><tr className="bg-gray-50 dark:bg-gray-800/80">
                                                <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700">Commodity</th>
                                                <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 whitespace-nowrap">PURB Purchase@GST</th>
                                                <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 whitespace-nowrap">PURB GST</th>
                                                <th className="px-3 py-2 text-right text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 whitespace-nowrap">INV Closing DR</th>
                                                <th className="px-3 py-2 text-center text-[10px] font-semibold uppercase text-gray-400 border-b border-gray-200 dark:border-gray-700 w-12">✓</th>
                                              </tr></thead>
                                              <tbody>
                                                {r.commodity_rows.map((row, i) => {
                                                  const gstTotal = (row.purb_igst ?? 0) + (row.purb_cgst ?? 0) + (row.purb_sgst ?? 0)
                                                  return (
                                                    <tr key={i} className={(row.taxable_match && row.inv_balanced) ? 'hover:bg-gray-50/50 dark:hover:bg-gray-800/20' : 'bg-red-50 dark:bg-red-900/20'}>
                                                      <td className="px-3 py-2 border-b border-gray-100 dark:border-gray-800 text-gray-700 dark:text-gray-300 font-medium text-[11px]">{row.commodity}</td>
                                                      <td className="px-3 py-2 border-b border-gray-100 dark:border-gray-800 text-right font-mono text-blue-700 dark:text-blue-300">{fmtN(row.purb_purchase_gst)}</td>
                                                      <td className="px-3 py-2 border-b border-gray-100 dark:border-gray-800 text-right font-mono text-gray-500">{gstTotal > 0 ? fmtN(gstTotal) : '—'}</td>
                                                      <td className="px-3 py-2 border-b border-gray-100 dark:border-gray-800 text-right font-mono text-blue-700 dark:text-blue-300">{fmtN(row.inv_closing_dr)}</td>
                                                      <td className="px-3 py-2 border-b border-gray-100 dark:border-gray-800 text-center">{(row.taxable_match && row.inv_balanced) ? <CheckCircle2 className="size-3.5 text-emerald-500 inline" /> : <XCircle className="size-3.5 text-red-500 inline" />}</td>
                                                    </tr>
                                                  )
                                                })}
                                              </tbody>
                                            </table>
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </DialogPrimitive.Content>
                            </DialogPrimitive.Portal>
                          </DialogPrimitive.Root>
                        )}

                        {(ccExportXlsRef.current = exportCcXls, ccExportPdfRef.current = exportCcPdf, ccOnFullViewRef.current = () => setCcFullViewOpen(true), null)}
                      </>
                    )
                  })()}
                </div>
              )
              })()}
            </div>
          )
        })()}

        {/* Bottom bar */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 shrink-0 flex items-center gap-2">
          {!token ? (
            <Button
              onClick={() => setShowTokenInput(true)}
              variant="outline"
              size="sm"
              className="h-8 text-[12px] gap-1.5 cursor-pointer"
            >
              <Key className="size-3" />
              Set Token
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={loadPBList}
                disabled={pbListLoading}
                className="text-[11px] text-[#3F51B5] dark:text-[#7986CB] flex items-center gap-1 hover:underline cursor-pointer disabled:opacity-50"
                title="Re-fetch purchase bookings"
              >
                <RefreshCw className={`size-3 ${pbListLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <button
                onClick={() => setShowTokenInput(true)}
                className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 hover:text-red-500 dark:hover:text-red-400 transition-colors cursor-pointer"
                title="Click to change or clear token"
              >
                <CheckCircle2 className="size-3" />
                Token set · Change
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}