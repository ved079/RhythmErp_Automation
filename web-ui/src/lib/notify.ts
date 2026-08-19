/**
 * notify.ts — Desktop notification utility (Notification API)
 * Requests permission on first call, then fires a desktop notification.
 */

export type NotifyOptions = {
  title: string
  body?: string
  icon?: string
}

export function notify({ title, body, icon = '/favicon.ico' }: NotifyOptions) {
  if (!('Notification' in window)) return

  const fire = () =>
    new Notification(title, { body, icon })

  if (Notification.permission === 'granted') {
    fire()
  } else if (Notification.permission !== 'denied') {
    Notification.requestPermission().then((p) => {
      if (p === 'granted') fire()
    })
  }
}

export function notifySuccess(title: string, body?: string) {
  notify({ title: `✅ ${title}`, body })
}

export function notifyError(title: string, body?: string) {
  notify({ title: `❌ ${title}`, body })
}

export function notifyInfo(title: string, body?: string) {
  notify({ title: `ℹ️ ${title}`, body })
}
