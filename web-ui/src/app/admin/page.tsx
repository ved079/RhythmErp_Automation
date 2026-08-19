'use client'

import React from 'react'
import Image from 'next/image'
import { useRouter, useSearchParams } from 'next/navigation'
import { useTheme } from 'next-themes'
import { useAdminState } from '@/hooks/admin/useAdminState'
import { SystemHealthSection } from '@/components/admin/sections/SystemHealthSection'
import { OverviewSection } from '@/components/admin/sections/OverviewSection'
import { AuditLogSection } from '@/components/admin/sections/AuditLogSection'
import { TestsSection } from '@/components/admin/sections/TestsSection'
import { SettingsSection } from '@/components/admin/sections/SettingsSection'
import { EnvironmentsSection } from '@/components/admin/sections/EnvironmentsSection'
import { EnvDialog } from '@/components/admin/EnvDialog'
import { ModulesSection } from '@/components/admin/sections/ModulesSection'
import { ModuleDialog } from '@/components/admin/ModuleDialog'
import { UsersSection } from '@/components/admin/sections/UsersSection'
import { UserDialog } from '@/components/admin/UserDialog'
import { ResetPasswordDialog } from '@/components/admin/ResetPasswordDialog'
import { TestVisibilitySection } from '@/components/admin/sections/TestVisibilitySection'
import { BugReportsSection } from '@/components/admin/sections/BugReportsSection'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from '@/components/ui/dialog'
import {
  LayoutDashboard, ClipboardList, FolderTree, EyeOff, Inbox,
  Globe, Settings, Users as UsersIcon, Activity, FileText,
  ChevronLeft, LogOut, Menu, Sun, Moon, Home, Shield, ChevronRight,
} from 'lucide-react'
import LoadingCard from '@/components/ui/LoadingCard'

export default function AdminPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { theme, setTheme } = useTheme()
  const isDark = theme === 'dark'

  const s = useAdminState()

  // Sync section from URL on mount — must be before early returns
  React.useEffect(() => {
    const section = searchParams.get('section')
    if (section) s.setActiveSection(section)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Update URL when section changes — must be before early returns
  const handleSectionChange = React.useCallback((id: string) => {
    s.setActiveSection(id)
    router.replace(`/admin?section=${id}`, { scroll: false })
  }, [s, router])

  if (s.authLoading) {
    return <LoadingCard />
  }
  if (!s.user) return null

  const userInitials = s.user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

  const sidebarItems = [
    { id: 'overview', icon: LayoutDashboard, label: 'Overview' },
    { id: 'tests', icon: ClipboardList, label: 'Test Management' },
    { id: 'modules', icon: FolderTree, label: 'Modules' },
    { id: 'test-visibility', icon: EyeOff, label: 'Test Visibility' },
    { id: 'bug-reports', icon: Inbox, label: 'Bug Reports' },
    { id: 'environments', icon: Globe, label: 'Environments' },
    { id: 'users', icon: UsersIcon, label: 'Users' },
    { id: 'settings', icon: Settings, label: 'Settings' },
    { id: 'system-health', icon: Activity, label: 'System Health' },
    { id: 'audit-log', icon: FileText, label: 'Audit Log' },
  ]

  return (
    <div className="h-screen flex flex-col bg-[#F1F2F7] dark:bg-gray-900 overflow-hidden">
      {/* ─── HEADER ─────────────────────────────────── */}
      <header className="h-[52px] bg-white dark:bg-gray-900 shrink-0 z-10 flex items-center px-3 border-b border-gray-100 dark:border-gray-800">
        {/* Left */}
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Button variant="ghost" size="icon" onClick={() => s.setSidebarOpen(!s.sidebarOpen)}
            className="size-7 cursor-pointer shrink-0 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded">
            <Menu className="size-4" />
          </Button>
          <Image src="/agdi-logo-new.webp" width={60} height={24} className="object-contain shrink-0" alt="agDi Logo" />
          <div className="hidden md:flex items-center gap-1.5 min-w-0">
            <ChevronRight className="size-3.5 text-gray-300 dark:text-gray-600 shrink-0" />
            <span className="text-[12px] text-gray-400 dark:text-gray-500">Admin</span>
            <ChevronRight className="size-3 text-gray-300 dark:text-gray-600 shrink-0" />
            <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200 truncate">
              {sidebarItems.find(i => i.id === s.activeSection)?.label ?? 'Overview'}
            </span>
          </div>
        </div>
        {/* Right */}
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={() => setTheme(isDark ? 'light' : 'dark')}
            className="size-7 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer rounded">
            {isDark ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}
          </Button>
          <Button variant="ghost" size="icon" onClick={() => router.push('/')}
            className="size-7 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer rounded"
            title="Back to User Panel">
            <Home className="size-3.5" />
          </Button>
          <Separator orientation="vertical" className="h-4 mx-1" />
          <div className="flex items-center gap-1.5">
            <Avatar className="size-6">
              <AvatarFallback className="bg-[#6777EF] text-white text-[10px] font-bold">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <div className="hidden sm:flex flex-col leading-none">
              <span className="text-[12px] text-gray-700 dark:text-gray-200 font-medium max-w-[100px] truncate">{s.user.name}</span>
              <span className="text-[10px] text-gray-400 dark:text-gray-500">Admin</span>
            </div>
            <Button variant="ghost" size="icon" onClick={s.handleLogout} className="size-7 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer rounded">
              <LogOut className="size-3.5" />
            </Button>
          </div>
        </div>
      </header>

      {/* ─── BODY ──────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ─── SIDEBAR ────────────────────────────── */}
        <div className={`shrink-0 transition-all duration-200 ease-in-out overflow-hidden ${s.sidebarOpen ? 'w-60' : 'w-0'}`}>
          <aside className="w-60 bg-gradient-to-b from-[#F7FBF8] via-[#EAF5EC] to-[#D6EDDC] dark:from-[#1e293b] dark:via-[#1e293b] dark:to-[#1e293b] h-full flex flex-col font-['Poppins'] shadow-[-1px_0px_0px_#D4E3D9] dark:shadow-[-1px_0px_0px_#334155]">
            <div className="px-3 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="size-3.5 text-[#1B4332] dark:text-green-300" />
                <span className="text-[13px] font-medium text-[#1B4332] dark:text-green-300 font-['Poppins']">Admin Controls</span>
              </div>
              <button onClick={() => s.setSidebarOpen(false)} className="text-[#495584] dark:text-gray-400 hover:text-[#1B4332] dark:hover:text-green-300 transition-colors cursor-pointer p-0.5 rounded hover:bg-[rgba(82,183,136,0.08)]">
                <ChevronLeft className="size-4" />
              </button>
            </div>
            <ScrollArea className="flex-1">
              <div className="py-2 px-2">
                {sidebarItems.map(item => {
                  const Icon = item.icon
                  const isActive = s.activeSection === item.id
                  const badgeCount = item.id === 'bug-reports' ? s.adminUnreadChats : 0
                  return (
                    <button key={item.id} onClick={() => handleSectionChange(item.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-['Poppins'] transition-all duration-150 cursor-pointer mb-0.5 ${
                        isActive
                          ? 'bg-gradient-to-r from-[#DFF3E3] via-[#C8E6C9] to-[#B7E4C7] dark:bg-[#1B4332]/25 text-[#1B4332] dark:text-green-300 font-semibold shadow-[rgba(34,197,94,0.25)_2px_0px_4px_inset,rgba(34,197,94,0.15)_0px_2px_6px] rounded-[5px]'
                          : 'text-[#545454] dark:text-gray-300 font-medium hover:text-[#6777EF] dark:hover:text-indigo-400 hover:bg-[rgba(82,183,136,0.08)] hover:shadow-[rgba(82,183,136,0.5)_2px_0px_inset] hover:rounded-[5px]'
                      }`}>
                      <Icon className="size-4 shrink-0" />
                      <span className="flex-1 text-left">{item.label}</span>
                      {badgeCount > 0 && (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-[#3F51B5] text-white leading-none">{badgeCount}</span>
                      )}
                    </button>
                  )
                })}
              </div>
            </ScrollArea>
            <div className="relative shrink-0 overflow-hidden" style={{ height: 99 }}>
              <Image src="/agri2.png" alt="" fill className="object-cover" sizes="280px" style={{ objectPosition: 'center 25%' }} />
            </div>
          </aside>
        </div>

        {/* ─── MAIN CONTENT ────────────────────────── */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <ErrorBoundary>
            {s.activeSection === 'bug-reports' ? (
            <BugReportsSection
              bugReports={s.bugReports}
              bugsLoaded={s.bugsLoaded}
              onBugReportsChange={s.setBugReports}
              adminUnreadChats={s.adminUnreadChats}
              userName={s.user?.name || 'Admin'}
              bugSubTab={s.bugSubTab}
              setBugSubTab={s.setBugSubTab}
              bugStatusFilter={s.bugStatusFilter}
              setBugStatusFilter={s.setBugStatusFilter}
              bugSearch={s.bugSearch}
              setBugSearch={s.setBugSearch}
              bugModuleFilter={s.bugModuleFilter}
              setBugModuleFilter={s.setBugModuleFilter}
              bugPriorityFilter={s.bugPriorityFilter}
              setBugPriorityFilter={s.setBugPriorityFilter}
              expandedBug={s.expandedBug}
              setExpandedBug={s.setExpandedBug}
              bugReplyText={s.bugReplyText}
              setBugReplyText={s.setBugReplyText}
              pendingBugStatus={s.pendingBugStatus}
              setPendingBugStatus={s.setPendingBugStatus}
              handleBugStatusChange={s.handleBugStatusChange}
              handleBugReply={s.handleBugReply}
              handleMarkBugRead={s.handleMarkBugRead}
            />
          ) : (
            <div className="flex-1 overflow-y-auto min-h-0 p-6">
              {s.activeSection === 'overview' ? (
                <OverviewSection
                  stats={s.stats}
                  tests={s.tests}
                  testsLoaded={s.testsLoaded}
                  environments={s.environments}
                  envLoaded={s.envLoaded}
                  auditLog={s.auditLog}
                  hiddenWidgets={s.hiddenWidgets}
                  widgetDialogOpen={s.widgetDialogOpen}
                  setWidgetDialogOpen={s.setWidgetDialogOpen}
                  toggleWidgetVisibility={s.toggleWidgetVisibility}
                />
              ) : s.activeSection === 'tests' ? (
                <TestsSection tests={s.tests} testsLoaded={s.testsLoaded} />
              ) : s.activeSection === 'test-visibility' ? (
                <TestVisibilitySection />
              ) : s.activeSection === 'modules' ? (
                <ModulesSection
                  modules={s.modules}
                  modulesLoaded={s.modulesLoaded}
                  onAdd={() => { s.setEditingModule(null); s.setModuleDialogOpen(true) }}
                  onEdit={(mod) => { s.setEditingModule(mod); s.setModuleDialogOpen(true) }}
                  onToggleStatus={s.handleToggleModuleStatus}
                  onDelete={(target) => { s.setDeleteTarget(target); s.setDeleteDialogOpen(true) }}
                  onSeed={s.handleSeedModules}
                />
              ) : s.activeSection === 'environments' ? (
                <EnvironmentsSection
                  environments={s.environments}
                  envLoaded={s.envLoaded}
                  onAdd={() => { s.setEditingEnv(null); s.setEnvDialogOpen(true) }}
                  onEdit={(env) => { s.setEditingEnv(env); s.setEnvDialogOpen(true) }}
                  onToggle={s.handleToggleEnv}
                  onDelete={(target) => { s.setDeleteTarget(target); s.setDeleteDialogOpen(true) }}
                />
              ) : s.activeSection === 'users' ? (
                <UsersSection
                  users={s.users}
                  usersLoaded={s.usersLoaded}
                  selectedUserIds={s.selectedUserIds}
                  bulkActionConfirmOpen={s.bulkActionConfirmOpen}
                  setBulkActionConfirmOpen={s.setBulkActionConfirmOpen}
                  bulkActionType={s.bulkActionType}
                  setBulkActionType={s.setBulkActionType}
                  onAdd={() => { s.setEditingUser(null); s.setUserDialogOpen(true) }}
                  onEdit={(u) => { s.setEditingUser(u); s.setUserDialogOpen(true) }}
                  onResetPassword={(u) => { s.setResetPasswordUser(u); s.setResetPasswordDialogOpen(true) }}
                  onDelete={(target) => { s.setDeleteTarget(target); s.setDeleteDialogOpen(true) }}
                  onBulkAction={s.handleBulkAction}
                  onToggleSelection={s.toggleUserSelection}
                  onToggleAll={s.toggleAllUsers}
                  onClearSelection={() => s.setSelectedUserIds(new Set())}
                />
              ) : s.activeSection === 'settings' ? (
                <SettingsSection />
              ) : s.activeSection === 'system-health' ? (
                <SystemHealthSection modulesLoaded={s.modulesLoaded} />
              ) : s.activeSection === 'audit-log' ? (
                <AuditLogSection auditLog={s.auditLog} auditLoaded={s.auditLoaded} />
              ) : null}
            </div>
          )}
          </ErrorBoundary>
        </main>
      </div>

      {/* ─── DIALOGS ───────────────────────────────── */}
      <EnvDialog key={s.editingEnv?.id || 'new'} open={s.envDialogOpen} onOpenChange={s.setEnvDialogOpen} editingEnv={s.editingEnv} onSave={s.handleSaveEnv} />
      <UserDialog key={s.editingUser?.id || 'user-new'} open={s.userDialogOpen} onOpenChange={s.setUserDialogOpen} editingUser={s.editingUser} onSave={s.handleSaveUser} allModules={s.modules} />
      <ResetPasswordDialog open={s.resetPasswordDialogOpen} onOpenChange={s.setResetPasswordDialogOpen} user={s.resetPasswordUser} onReset={s.handleResetPassword} />
      <ModuleDialog key={s.editingModule?.id || 'module-new'} open={s.moduleDialogOpen} onOpenChange={s.setModuleDialogOpen} editingModule={s.editingModule} onSave={s.handleSaveModule} allModules={s.modules} />
      <Dialog open={s.deleteDialogOpen} onOpenChange={s.setDeleteDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">Confirm Delete</DialogTitle>
            <DialogDescription className="font-['Poppins'] text-[#888]">
              Are you sure you want to delete <strong>{s.deleteTarget?.label}</strong>? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => s.setDeleteDialogOpen(false)} className="font-['Poppins']">Cancel</Button>
            <Button onClick={s.handleDelete} className="bg-[#F44336] hover:bg-[#D32F2F] text-white font-['Poppins']">Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
