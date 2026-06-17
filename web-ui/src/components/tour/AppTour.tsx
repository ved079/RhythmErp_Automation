'use client'

import { useEffect, useRef, useCallback } from 'react'
import { driver, type DriveStep } from 'driver.js'
import 'driver.js/dist/driver.css'

// ─── Full Tour Steps (Dashboard — first-time walkthrough) ────
const FULL_TOUR_STEPS: DriveStep[] = [
  {
    element: '[data-tour="sidebar-toggle"]',
    popover: {
      title: 'Toggle Sidebar',
      description:
        'Click this button (or press Ctrl+B) to expand or collapse the Module Navigator sidebar. The sidebar is your main way to navigate between test modules.',
      side: 'bottom' as const,
      align: 'start' as const,
    },
  },
  {
    element: '[data-tour="sidebar-modules"]',
    popover: {
      title: 'Module Navigator',
      description:
        'Browse all RhythmERP test modules here. Modules with tests show a green badge count. Expand groups like "Common Settings" or "Commodity Settings" to find sub-modules.',
      side: 'right' as const,
      align: 'start' as const,
    },
  },
  {
    element: '[data-tour="tab-bar"]',
    popover: {
      title: 'Tab Navigation',
      description:
         'Once you select a module, use these tabs to switch between Test Runner, Live Execution, Results, and Schedule views.',
      side: 'bottom' as const,
      align: 'center' as const,
    },
  },
  {
    element: '[data-tour="dashboard"]',
    popover: {
      title: 'Dashboard Overview',
      description:
        'The Dashboard shows a health overview of all automation modules — total modules, pass rates, and quick navigation to any module.',
      side: 'bottom' as const,
      align: 'center' as const,
    },
  },
  {
    element: '[data-tour="test-runner"]',
    popover: {
      title: 'Test Runner',
      description:
        'Select and execute tests from here. You can run all tests, selected tests, or filter by priority (Smoke, Regression).',
      side: 'bottom' as const,
      align: 'center' as const,
    },
  },
  {
    element: '[data-tour="run-buttons"]',
    popover: {
      title: 'Run Controls',
      description:
        'Start test execution with these buttons. "Run All" executes every pending test. "Run Selected" runs only checked tests. Use priority buttons for quick smoke/regression runs.',
      side: 'bottom' as const,
      align: 'start' as const,
    },
  },
  {
    element: '[data-tour="live-execution"]',
    popover: {
      title: 'Live Execution',
      description:
        'Watch your tests run in real-time here. You\'ll see a terminal console with live output, test progress, and the ability to stop a running test.',
      side: 'bottom' as const,
      align: 'center' as const,
    },
  },
  {
    element: '[data-tour="results"]',
    popover: {
      title: 'Results & History',
      description:
        'After tests complete, view detailed results here — pass/fail breakdowns, test history over time, and the ability to report bugs for failed tests.',
      side: 'bottom' as const,
      align: 'center' as const,
    },
  },
  {
    element: '[data-tour="schedule-runs"]',
    popover: {
      title: 'Schedule Runs',
      description:
        'Set up scheduled test runs with cron expressions. Automate your QA pipeline by scheduling smoke tests daily or regression tests weekly.',
      side: 'bottom' as const,
      align: 'center' as const,
    },
  },
  {
    element: '[data-tour="universal-search"]',
    popover: {
      title: 'Universal Search',
      description:
        'Quickly search for modules, test cases, or results across the entire application. Click this icon to open the search panel.',
      side: 'bottom' as const,
      align: 'center' as const,
    },
  },
  {
    element: '[data-tour="dark-mode"]',
    popover: {
      title: 'Dark Mode Toggle',
      description:
        'Switch between light and dark themes. Your preference is saved automatically for your next visit.',
      side: 'bottom' as const,
      align: 'center' as const,
    },
  },
  {
    element: '[data-tour="keyboard-shortcuts"]',
    popover: {
      title: 'Keyboard Shortcuts',
      description:
        'Access keyboard shortcuts for faster navigation — press Ctrl+/ anytime to see all shortcuts, or click this button. Shortcuts include Ctrl+R to run tests, Ctrl+D for dark mode, and Ctrl+1-5 to switch tabs.',
      side: 'bottom' as const,
      align: 'center' as const,
    },
  },
  {
    element: '[data-tour="notifications"]',
    popover: {
      title: 'Notifications',
      description:
        'Get notified about test completions, scheduled run results, and bug report updates. The orange badge shows unread notifications.',
      side: 'bottom' as const,
      align: 'center' as const,
    },
  },
  {
    element: '[data-tour="user-menu"]',
    popover: {
      title: 'Your Account',
      description:
        'This shows your name and avatar. Admin and QA Lead users will also see an Admin Panel link nearby.',
      side: 'bottom' as const,
      align: 'end' as const,
    },
  },
  {
    element: '[data-tour="logout-btn"]',
    popover: {
      title: 'Sign Out',
      description:
        'Click here to securely sign out of your session. Always log out when you\'re done, especially on shared machines.',
      side: 'bottom' as const,
      align: 'end' as const,
    },
  },
]

// ─── Quick Tour Step Templates (per tab) ─────────────────────
// Only what's on screen right now — no sidebar, no dark mode, no notifications.
const QUICK_TOUR_STEPS: Record<string, DriveStep[]> = {
  'test-runner': [
    {
      element: '[data-tour="tab-bar"]',
      popover: {
        title: 'Tab Navigation',
        description:
          'You\'re on Test Runner. Use these tabs to switch to other views like Live Execution or Results.',
        side: 'bottom' as const,
        align: 'center' as const,
      },
    },
    {
      element: '[data-tour="test-runner"]',
      popover: {
        title: 'Test Runner',
        description:
          'Select and execute tests from here. Check the tests you want to run, or use the priority filter buttons.',
        side: 'bottom' as const,
        align: 'center' as const,
      },
    },
    {
      element: '[data-tour="run-buttons"]',
      popover: {
        title: 'Run Controls',
        description:
          'Start test execution here. "Run All" runs every pending test, "Run Selected" runs only checked tests. Use Smoke/Regression buttons for quick priority runs.',
        side: 'bottom' as const,
        align: 'start' as const,
      },
    },
  ],
  'live-execution': [
    {
      element: '[data-tour="tab-bar"]',
      popover: {
        title: 'Tab Navigation',
        description:
          'You\'re on Live Execution. Use these tabs to switch to other views like Test Runner or Results.',
        side: 'bottom' as const,
        align: 'center' as const,
      },
    },
    {
      element: '[data-tour="live-execution"]',
      popover: {
        title: 'Live Execution',
        description:
          'Watch your tests run in real-time here — live terminal output, test progress, and the ability to stop a running test.',
        side: 'bottom' as const,
        align: 'center' as const,
      },
    },
  ],
  results: [
    {
      element: '[data-tour="tab-bar"]',
      popover: {
        title: 'Tab Navigation',
        description:
          'You\'re on Results. Use these tabs to switch to other views like Test Runner or Live Execution.',
        side: 'bottom' as const,
        align: 'center' as const,
      },
    },
    {
      element: '[data-tour="results"]',
      popover: {
        title: 'Results & History',
        description:
          'View pass/fail breakdowns, test history over time, and report bugs for failed tests from here.',
        side: 'bottom' as const,
        align: 'center' as const,
      },
    },
  ],
  schedule: [
    {
      element: '[data-tour="tab-bar"]',
      popover: {
        title: 'Tab Navigation',
        description:
          'You\'re on Schedule. Use these tabs to switch to other views like Test Runner or Results.',
        side: 'bottom' as const,
        align: 'center' as const,
      },
    },
    {
      element: '[data-tour="schedule-runs"]',
      popover: {
        title: 'Schedule Runs',
        description:
          'Set up scheduled test runs with cron expressions. Automate your QA pipeline — schedule smoke tests daily or regression tests weekly.',
        side: 'bottom' as const,
        align: 'center' as const,
      },
    },
  ],
}

// ─── Smart Step Filter ─────────────────────────────────────
// Only include steps whose target elements are currently visible in the DOM
function filterVisibleSteps(steps: DriveStep[]): DriveStep[] {
  return steps.filter((step) => {
    if (!step.element) return false
    const selector =
      typeof step.element === 'string' ? step.element : ''
    if (!selector) return false
    const el = document.querySelector(selector)
    if (!el) return false
    // Check if element is visible (not display:none, not visibility:hidden)
    const style = window.getComputedStyle(el)
    return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0'
  })
}

// ─── Build Steps Based on Context ───────────────────────────
function buildTourSteps(selectedModule: string, activeTab: string): DriveStep[] {
  // Dashboard → full tour
  if (selectedModule === 'dashboard') {
    return filterVisibleSteps(FULL_TOUR_STEPS)
  }

  // Module page → quick tour for the current tab
  const quickSteps = QUICK_TOUR_STEPS[activeTab]
  if (quickSteps) {
    const visible = filterVisibleSteps(quickSteps)
    if (visible.length > 0) {
      // Add a "Take Full Tour" hint on the first step's description
      const first = { ...visible[0] }
      first.popover = {
        ...first.popover,
        description:
          first.popover.description +
          '\n\n💡 Want the full tour? Close this and click ? from the Dashboard.',
      }
      return [first, ...visible.slice(1)]
    }
  }

  // Fallback: try full tour with visible steps
  return filterVisibleSteps(FULL_TOUR_STEPS)
}

// ─── localStorage Key ──────────────────────────────────────
const TOUR_COMPLETED_KEY = 'rhythmerp-tour-completed'

// ─── Component ─────────────────────────────────────────────
interface AppTourProps {
  selectedModule: string
  activeTab: string
  onTourStart?: () => void
}

export function AppTour({ selectedModule, activeTab, onTourStart }: AppTourProps) {
  const driverRef = useRef<ReturnType<typeof driver> | null>(null)
  const contextRef = useRef({ selectedModule, activeTab })

  // Keep context ref in sync so the callback always reads fresh values
  useEffect(() => {
    contextRef.current = { selectedModule, activeTab }
  }, [selectedModule, activeTab])

  useEffect(() => {
    const driverInstance = driver({
      showProgress: true,
      showButtons: ['next', 'previous', 'close'],
      nextBtnText: 'Next →',
      prevBtnText: '← Back',
      doneBtnText: '✓ Got it!',
      closeBtnText: 'Skip Tour',
      progressText: '{{current}} of {{total}}',
      animate: true,
      allowClose: true,
      overlayColor: 'rgba(0, 0, 0, 0.55)',
      stagePadding: 6,
      stageRadius: 8,
      popoverClass: 'rhythmerp-tour-popover',
      onHighlightStarted: () => {
        onTourStart?.()
      },
      onDestroyed: () => {
        localStorage.setItem(TOUR_COMPLETED_KEY, 'true')
      },
    })

    driverRef.current = driverInstance

    return () => {
      driverRef.current?.destroy()
    }
  }, [onTourStart])

  const startTour = useCallback(() => {
    if (!driverRef.current) return

    const { selectedModule: mod, activeTab: tab } = contextRef.current
    const steps = buildTourSteps(mod, tab)

    if (steps.length === 0) {
      return
    }

    driverRef.current.setSteps(steps)
    driverRef.current.drive()
  }, [])

  // Expose startTour via a global so the Help button can trigger it
  useEffect(() => {
    ;(window as unknown as Record<string, unknown>).__startTour = startTour
    return () => {
      delete (window as unknown as Record<string, unknown>).__startTour
    }
  }, [startTour])

  return null // This component is invisible — it only manages the driver.js instance
}

// ─── Helper: Trigger Tour from Anywhere ────────────────────
export function startAppTour() {
  const fn = (window as unknown as Record<string, () => void>).__startTour
  if (fn) fn()
}

// ─── Helper: Check if tour was completed ───────────────────
export function isTourCompleted(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem(TOUR_COMPLETED_KEY) === 'true'
}

// ─── Helper: Reset tour status ─────────────────────────────
export function resetTourStatus() {
  if (typeof window === 'undefined') return
  localStorage.removeItem(TOUR_COMPLETED_KEY)
}
