'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'

interface AdminModule {
  id: string; name: string; label: string; parentId?: string; parentLabel?: string
  badge?: string; testCount: number; sortOrder: number; status: 'active' | 'draft' | 'disabled'
  description?: string
}

export function ModuleDialog({ open, onOpenChange, editingModule, onSave, allModules }: {
  open: boolean; onOpenChange: (v: boolean) => void
  editingModule: AdminModule | null; onSave: (data: Partial<AdminModule> & { name: string; label: string }) => void
  allModules: AdminModule[]
}) {
  const [name, setName] = useState(editingModule?.name || '')
  const [label, setLabel] = useState(editingModule?.label || '')
  const [parentId, setParentId] = useState<string>(editingModule?.parentId || 'none')
  const [description, setDescription] = useState(editingModule?.description || '')
  const [status, setStatus] = useState<string>(editingModule?.status || 'active')
  const [sortOrder, setSortOrder] = useState(String(editingModule?.sortOrder ?? 0))

  const parentModules = allModules.filter(m => !m.parentId)

  const availableParents = editingModule
    ? parentModules.filter(p => p.id !== editingModule.id)
    : parentModules

  const handleSave = () => {
    if (!name.trim() || !label.trim()) return
    const selectedParent = parentId !== 'none' ? parentId : undefined
    const parentMod = selectedParent ? allModules.find(m => m.id === selectedParent) : undefined
    onSave({
      name: name.trim(),
      label: label.trim(),
      parentId: selectedParent,
      parentLabel: parentMod?.label,
      description: description.trim(),
      sortOrder: Number(sortOrder) || 0,
      status: status as AdminModule['status'],
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">{editingModule ? 'Edit Module' : 'Add Module'}</DialogTitle>
          <DialogDescription className="font-['Manrope'] text-[#888]">
            {editingModule ? 'Update module configuration.' : 'Create a new test module.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2 max-h-[60vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Name (slug) <span className="text-red-500">*</span></Label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. registration-farmer" className="h-9 text-sm font-['Manrope']" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Label (display) <span className="text-red-500">*</span></Label>
              <Input value={label} onChange={e => setLabel(e.target.value)} placeholder="e.g. Farmer" className="h-9 text-sm font-['Manrope']" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-['Manrope']">Parent Module</Label>
            <Select value={parentId} onValueChange={setParentId}>
              <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="None (Top-level)" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None (Top-level)</SelectItem>
                {availableParents.map(p => (
                  <SelectItem key={p.id} value={p.id}>{p.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-['Manrope']">Description</Label>
            <Textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Brief description of this module..." className="min-h-[60px] text-sm font-['Manrope']" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Status</Label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="disabled">Disabled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Sort Order</Label>
              <Input type="number" value={sortOrder} onChange={e => setSortOrder(e.target.value)} className="h-9 text-sm font-['Manrope']" />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="font-['Roboto']">Cancel</Button>
          <Button onClick={handleSave} disabled={!name.trim() || !label.trim()}
            className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto']">
            {editingModule ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
