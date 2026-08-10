'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'

interface Environment {
  id: string; name: string; baseUrl: string; browser: string
  status: 'active' | 'inactive'; lastUsed?: string; color: string
}

export function EnvDialog({ open, onOpenChange, editingEnv, onSave }: {
  open: boolean; onOpenChange: (v: boolean) => void
  editingEnv: Environment | null; onSave: (data: Partial<Environment>) => void
}) {
  const [name, setName] = useState(editingEnv?.name || '')
  const [baseUrl, setBaseUrl] = useState(editingEnv?.baseUrl || '')
  const [browser, setBrowser] = useState(editingEnv?.browser || 'Chrome')
  const [color, setColor] = useState(editingEnv?.color || 'bg-green-500')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">{editingEnv ? 'Edit Environment' : 'Add Environment'}</DialogTitle>
          <DialogDescription className="font-['Poppins'] text-[#888]">
            {editingEnv ? 'Update environment configuration.' : 'Configure a new test environment.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label className="text-xs font-['Poppins']">Name</Label>
            <Input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Staging" className="h-9 text-sm font-['Poppins']" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-['Poppins']">Base URL</Label>
            <Input value={baseUrl} onChange={e => setBaseUrl(e.target.value)} placeholder="https://staging.rhythmerp.com" className="h-9 text-sm font-['Poppins']" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-['Poppins']">Browser</Label>
            <Select value={browser} onValueChange={setBrowser}>
              <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="Chrome">Chrome</SelectItem>
                <SelectItem value="Firefox">Firefox</SelectItem>
                <SelectItem value="Edge">Edge</SelectItem>
                <SelectItem value="Safari">Safari</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-['Poppins']">Color</Label>
            <div className="flex gap-2">
              {['bg-green-500', 'bg-blue-500', 'bg-orange-500', 'bg-red-500', 'bg-purple-500', 'bg-teal-500'].map(c => (
                <button key={c} onClick={() => setColor(c)}
                  className={`w-7 h-7 rounded-full ${c} cursor-pointer transition-transform ${color === c ? 'ring-2 ring-[#3F51B5] ring-offset-2 scale-110' : 'hover:scale-110'}`} />
              ))}
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="font-['Poppins']">Cancel</Button>
          <Button onClick={() => onSave({ name, baseUrl, browser, color })} disabled={!name || !baseUrl}
            className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Poppins']">
            {editingEnv ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
