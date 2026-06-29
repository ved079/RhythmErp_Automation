'use client'

import React, { type Dispatch, type SetStateAction, useState } from 'react'
import { KeyRound, Star, Trash2, Plus, X, ShieldCheck, Pencil, Eye, EyeOff, Check } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import type { ErpCred } from '@/lib/types'

const EMPTY_FORM = { name: '', email: '', password: '', tenantUrl: 'https://rhythmerp.algorhythms.in', isDefault: false }

interface Props {
  erpCredentials: ErpCred[]
  activeCredId: string | null
  setActiveCredId: (id: string | null) => void
  credLoading: boolean
  credFormOpen: boolean
  setCredFormOpen: (open: boolean) => void
  credForm: typeof EMPTY_FORM
  setCredForm: Dispatch<SetStateAction<typeof EMPTY_FORM>>
  credSaving: boolean
  saveCredential: () => void
  setDefaultCred: (id: string) => Promise<void>
  deleteCred: (id: string) => Promise<void>
  updateCredential: (id: string, data: Partial<typeof EMPTY_FORM>) => Promise<void>
  getPassword: (id: string) => string
  erpToken: string
  setErpToken: (token: string) => void
  erpTenantId: string
  setErpTenantId: (id: string) => void
}

function PasswordInput({ value, onChange, placeholder, className }: { value: string; onChange: (v: string) => void; placeholder?: string; className?: string }) {
  const [show, setShow] = useState(false)
  return (
    <div className="relative">
      <input
        type={show ? 'text' : 'password'}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className={`pr-8 ${className}`}
      />
      <button
        type="button"
        onClick={() => setShow(s => !s)}
        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer"
        tabIndex={-1}
      >
        {show ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
      </button>
    </div>
  )
}

const INPUT = 'w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-[12px] bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-[#3F51B5]/50'

export function CredentialsScreen({
  erpCredentials,
  activeCredId,
  setActiveCredId,
  credLoading,
  credFormOpen,
  setCredFormOpen,
  credForm,
  setCredForm,
  credSaving,
  saveCredential,
  setDefaultCred,
  deleteCred,
  updateCredential,
  getPassword,
  erpToken,
  setErpToken,
  erpTenantId,
  setErpTenantId,
}: Props) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState(EMPTY_FORM)
  const [editSaving, setEditSaving] = useState(false)

  const activeCred = erpCredentials.find(c => c.id === activeCredId) ?? erpCredentials.find(c => c.isDefault) ?? null

  const openAdd = () => {
    setEditingId(null)
    setCredForm(EMPTY_FORM)
    setCredFormOpen(true)
  }

  const closeAdd = () => {
    setCredForm(EMPTY_FORM)
    setCredFormOpen(false)
  }

  const openEdit = (cred: ErpCred) => {
    setCredFormOpen(false)
    setEditingId(cred.id)
    setEditForm({ name: cred.name, email: cred.email, password: getPassword(cred.id), tenantUrl: cred.tenantUrl, isDefault: cred.isDefault })
  }

  const closeEdit = () => {
    setEditingId(null)
    setEditForm(EMPTY_FORM)
  }

  const saveEdit = async () => {
    if (!editingId) return
    setEditSaving(true)
    await updateCredential(editingId, editForm)
    setEditSaving(false)
    closeEdit()
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden bg-[#F1F2F7] dark:bg-gray-900">
      {/* Tab bar */}
      <div className="border-b border-gray-300 dark:border-gray-500/70 bg-gray-50/50 dark:bg-gray-800/30 shrink-0">
        <div className="flex items-center h-10 px-4">
          <div className="flex items-center gap-1.5 px-4 h-full text-[12px] font-medium border-b-2 border-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB] bg-white dark:bg-gray-900">
            <KeyRound className="size-3.5" />
            <span>ERP Credentials</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-xl mx-auto space-y-5">

          <div>
            <h2 className="text-[15px] font-semibold text-gray-800 dark:text-gray-100">Saved Credentials</h2>
            <p className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5">
              Login accounts used for UI Selenium test runs. The starred credential is the default.
            </p>
          </div>

          {activeCred && (
            <div className="flex items-center gap-2.5 px-4 py-2.5 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700/40 rounded-lg">
              <ShieldCheck className="size-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <div className="text-[12px]">
                <span className="font-medium text-emerald-700 dark:text-emerald-400">Active: </span>
                <span className="text-gray-700 dark:text-gray-300">{activeCred.name}</span>
                <span className="text-gray-400 dark:text-gray-500 ml-1">· {activeCred.email}</span>
              </div>
            </div>
          )}

          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
            {credLoading ? (
              <div className="flex items-center justify-center gap-2 py-10 text-[12px] text-gray-400">
                <Loader2 className="size-4 animate-spin" /> Loading...
              </div>
            ) : erpCredentials.length === 0 && !credFormOpen ? (
              <div className="flex flex-col items-center justify-center py-10 gap-3">
                <KeyRound className="size-8 text-gray-300 dark:text-gray-600" />
                <p className="text-[12px] text-gray-400 dark:text-gray-500">No saved credentials yet.</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700/60">
                {erpCredentials.map(cred => {
                  const isActive = activeCred?.id === cred.id
                  const isEditing = editingId === cred.id

                  if (isEditing) {
                    return (
                      <div key={cred.id} className="bg-gray-50/60 dark:bg-gray-800/60 p-4 space-y-3 border-l-2 border-[#3F51B5]">
                        <div className="flex items-center justify-between">
                          <p className="text-[11px] font-semibold text-[#3F51B5] dark:text-[#7986CB] uppercase tracking-wider">Edit Credential</p>
                          <button onClick={closeEdit} className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 cursor-pointer">
                            <X className="size-3.5" />
                          </button>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <input
                            placeholder="Label"
                            value={editForm.name}
                            onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))}
                            className={`col-span-2 ${INPUT}`}
                          />
                          <input
                            placeholder="ERP Email"
                            value={editForm.email}
                            onChange={e => setEditForm(f => ({ ...f, email: e.target.value }))}
                            className={INPUT}
                          />
                          <PasswordInput
                            value={editForm.password}
                            onChange={v => setEditForm(f => ({ ...f, password: v }))}
                            placeholder="ERP Password"
                            className={INPUT}
                          />
                          <input
                            placeholder="Tenant URL"
                            value={editForm.tenantUrl}
                            onChange={e => setEditForm(f => ({ ...f, tenantUrl: e.target.value }))}
                            className={`col-span-2 ${INPUT}`}
                          />
                        </div>
                        <label className="flex items-center gap-2 text-[12px] text-gray-600 dark:text-gray-300 cursor-pointer select-none">
                          <input type="checkbox" checked={editForm.isDefault} onChange={e => setEditForm(f => ({ ...f, isDefault: e.target.checked }))} className="rounded" />
                          Set as default
                        </label>
                        <div className="flex gap-2 pt-1">
                          <button
                            onClick={saveEdit}
                            disabled={editSaving || !editForm.name || !editForm.email}
                            className="flex items-center gap-1.5 px-4 py-2 bg-[#3F51B5] hover:bg-[#3949AB] disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg text-[12px] font-medium transition-colors cursor-pointer"
                          >
                            {editSaving ? <Loader2 className="size-3.5 animate-spin" /> : <Check className="size-3.5" />}
                            {editSaving ? 'Saving...' : 'Save Changes'}
                          </button>
                          <button onClick={closeEdit} className="px-4 py-2 border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 rounded-lg text-[12px] font-medium hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer">
                            Cancel
                          </button>
                        </div>
                      </div>
                    )
                  }

                  return (
                    <div
                      key={cred.id}
                      onClick={() => setActiveCredId(cred.id)}
                      className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${
                        isActive ? 'bg-[#3F51B5]/5 dark:bg-[#3F51B5]/10' : 'hover:bg-gray-50 dark:hover:bg-gray-700/40'
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className={`text-[13px] font-medium truncate ${isActive ? 'text-[#3F51B5] dark:text-[#7986CB]' : 'text-gray-800 dark:text-gray-200'}`}>
                            {cred.name}
                          </span>
                          {isActive && <span className="text-[10px] bg-[#3F51B5] text-white px-1.5 py-0.5 rounded-full shrink-0">Active</span>}
                          {cred.isDefault && <span className="text-[10px] bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 px-1.5 py-0.5 rounded-full shrink-0">Default</span>}
                        </div>
                        <div className="text-[11px] text-gray-400 dark:text-gray-500 truncate mt-0.5">{cred.email}</div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          title="Edit credential"
                          onClick={e => { e.stopPropagation(); openEdit(cred) }}
                          className="p-1.5 rounded-md text-gray-300 dark:text-gray-600 hover:text-[#3F51B5] hover:bg-[#3F51B5]/10 transition-colors cursor-pointer"
                        >
                          <Pencil className="size-3.5" />
                        </button>
                        <button
                          title={cred.isDefault ? 'Default credential' : 'Set as default'}
                          onClick={e => { e.stopPropagation(); setDefaultCred(cred.id) }}
                          className={`p-1.5 rounded-md transition-colors cursor-pointer ${
                            cred.isDefault
                              ? 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                              : 'text-gray-300 dark:text-gray-600 hover:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20'
                          }`}
                        >
                          <Star className="size-3.5" fill={cred.isDefault ? 'currentColor' : 'none'} />
                        </button>
                        <button
                          title="Delete credential"
                          onClick={e => { e.stopPropagation(); deleteCred(cred.id) }}
                          className="p-1.5 rounded-md text-gray-300 dark:text-gray-600 hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors cursor-pointer"
                        >
                          <Trash2 className="size-3.5" />
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Add form */}
            {credFormOpen && (
              <div className="border-t border-gray-100 dark:border-gray-700/60 bg-gray-50/50 dark:bg-gray-800/50 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">New Credential</p>
                  <button onClick={closeAdd} className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors cursor-pointer">
                    <X className="size-3.5" />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    placeholder="Label (e.g. Vedant Prod)"
                    value={credForm.name}
                    onChange={e => setCredForm(f => ({ ...f, name: e.target.value }))}
                    className={`col-span-2 ${INPUT}`}
                  />
                  <input
                    placeholder="ERP Email"
                    value={credForm.email}
                    onChange={e => setCredForm(f => ({ ...f, email: e.target.value }))}
                    className={INPUT}
                  />
                  <PasswordInput
                    value={credForm.password}
                    onChange={v => setCredForm(f => ({ ...f, password: v }))}
                    placeholder="ERP Password"
                    className={INPUT}
                  />
                  <input
                    placeholder="Tenant URL"
                    value={credForm.tenantUrl}
                    onChange={e => setCredForm(f => ({ ...f, tenantUrl: e.target.value }))}
                    className={`col-span-2 ${INPUT}`}
                  />
                </div>
                <label className="flex items-center gap-2 text-[12px] text-gray-600 dark:text-gray-300 cursor-pointer select-none">
                  <input type="checkbox" checked={credForm.isDefault} onChange={e => setCredForm(f => ({ ...f, isDefault: e.target.checked }))} className="rounded" />
                  Set as default
                </label>
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={saveCredential}
                    disabled={credSaving || !credForm.name || !credForm.email || !credForm.password}
                    className="flex items-center gap-1.5 px-4 py-2 bg-[#3F51B5] hover:bg-[#3949AB] disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg text-[12px] font-medium transition-colors cursor-pointer"
                  >
                    {credSaving ? <Loader2 className="size-3.5 animate-spin" /> : <Plus className="size-3.5" />}
                    {credSaving ? 'Saving...' : 'Save'}
                  </button>
                  <button onClick={closeAdd} className="px-4 py-2 border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 rounded-lg text-[12px] font-medium hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer">
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Add button */}
            {!credFormOpen && !editingId && (
              <div className={`px-4 py-3 ${erpCredentials.length > 0 ? 'border-t border-gray-100 dark:border-gray-700/60' : ''}`}>
                <button
                  onClick={openAdd}
                  className="flex items-center gap-1.5 text-[12px] text-[#3F51B5] dark:text-[#7986CB] hover:text-[#3949AB] font-medium transition-colors cursor-pointer"
                >
                  <Plus className="size-3.5" />
                  Add Credential
                </button>
              </div>
            )}
          </div>

          {/* API Token section */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
            <details>
              <summary className="flex items-center gap-2 px-4 py-3 text-[12px] font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200 select-none list-none">
                <span className="flex-1">API Token <span className="font-normal text-gray-400">(for API tests only)</span></span>
                <span className="text-[11px] text-gray-300 dark:text-gray-600">▾</span>
              </summary>
              <div className="px-4 pb-4 space-y-2 border-t border-gray-100 dark:border-gray-700/60 pt-3">
                <div>
                  <label className="text-[11px] text-gray-400 dark:text-gray-500 mb-1 block">Bearer Token</label>
                  <PasswordInput value={erpToken} onChange={setErpToken} placeholder="Bearer eyJ..." className={INPUT} />
                </div>
                <div>
                  <label className="text-[11px] text-gray-400 dark:text-gray-500 mb-1 block">Tenant ID</label>
                  <input type="text" value={erpTenantId} onChange={e => setErpTenantId(e.target.value)} placeholder="e.g. 681" className={INPUT} />
                </div>
              </div>
            </details>
          </div>

        </div>
      </div>
    </div>
  )
}
