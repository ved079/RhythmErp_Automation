const PREF_KEY = 'browser-notify-enabled'

export function isBrowserNotifySupported(): boolean {
  return typeof window !== 'undefined' && 'Notification' in window
}

export function getBrowserNotifyPreference(): boolean {
  if (typeof window === 'undefined') return false
  try {
    return localStorage.getItem(PREF_KEY) === '1'
  } catch {
    return false
  }
}

export function setBrowserNotifyPreference(enabled: boolean): void {
  try {
    if (enabled) localStorage.setItem(PREF_KEY, '1')
    else localStorage.removeItem(PREF_KEY)
  } catch {
    // silent fail
  }
}

export function getBrowserNotifyPermission(): NotificationPermission {
  if (!isBrowserNotifySupported()) return 'denied'
  return Notification.permission
}

export async function requestBrowserNotifyPermission(): Promise<NotificationPermission> {
  if (!isBrowserNotifySupported()) return 'denied'
  try {
    return await Notification.requestPermission()
  } catch {
    return Notification.permission
  }
}

export function browserNotify(title: string, message: string): boolean {
  if (!isBrowserNotifySupported()) return false
  if (!getBrowserNotifyPreference()) return false
  if (Notification.permission !== 'granted') return false
  try {
    const notif = new Notification(title, {
      body: message,
      tag: `pacs-${Date.now()}`,
      icon: '/favicon.ico',
      silent: false,
    })
    notif.onclick = () => {
      window.focus()
      notif.close()
    }
    return true
  } catch {
    return false
  }
}
