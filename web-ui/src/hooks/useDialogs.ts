'use client'

import { useState } from 'react'
import type { RunSnapshot } from '@/lib/types'
import type { ScreenshotEntry } from '@/components/screenshot/ScreenshotGallery'

export function useDialogs() {
  const [reportDialogOpen, setReportDialogOpen] = useState(false)
  const [reportingTest, setReportingTest] = useState<{ id: string; name: string; error?: string } | null>(null)
  const [profileDialogOpen, setProfileDialogOpen] = useState(false)
  const [runDetailDialogOpen, setRunDetailDialogOpen] = useState(false)
  const [selectedRunForDetail, setSelectedRunForDetail] = useState<RunSnapshot | null>(null)
  const [runComparisonOpen, setRunComparisonOpen] = useState(false)
  const [runHistoryOpen, setRunHistoryOpen] = useState(false)
  const [credentialsOpen, setCredentialsOpen] = useState(false)
  const [showTokenHelp, setShowTokenHelp] = useState(false)
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [lightboxIndex, setLightboxIndex] = useState(0)
  const [screenshotCompareOpen, setScreenshotCompareOpen] = useState(false)
  const [compareScreenshots, setCompareScreenshots] = useState<[ScreenshotEntry | null, ScreenshotEntry | null]>([null, null])
  const [quickSwitcherOpen, setQuickSwitcherOpen] = useState(false)
  const [quickSearch, setQuickSearch] = useState('')
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [notifDropdownOpen, setNotifDropdownOpen] = useState(false)

  return {
    reportDialogOpen, setReportDialogOpen,
    reportingTest, setReportingTest,
    profileDialogOpen, setProfileDialogOpen,
    runDetailDialogOpen, setRunDetailDialogOpen,
    selectedRunForDetail, setSelectedRunForDetail,
    runComparisonOpen, setRunComparisonOpen,
    runHistoryOpen, setRunHistoryOpen,
    credentialsOpen, setCredentialsOpen,
    showTokenHelp, setShowTokenHelp,
    lightboxOpen, setLightboxOpen,
    lightboxIndex, setLightboxIndex,
    screenshotCompareOpen, setScreenshotCompareOpen,
    compareScreenshots, setCompareScreenshots,
    quickSwitcherOpen, setQuickSwitcherOpen,
    quickSearch, setQuickSearch,
    showShortcuts, setShowShortcuts,
    notifDropdownOpen, setNotifDropdownOpen,
  }
}
