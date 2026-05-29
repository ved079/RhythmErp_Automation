'use client'

import { useEffect, useRef, useCallback, useState } from 'react'
import { io, Socket } from 'socket.io-client'

export interface WsNotification {
  type: string
  title: string
  message: string
  userId?: string
  data?: Record<string, unknown>
}

export interface WsRunComplete {
  runId: string
  moduleName: string
  passed: number
  failed: number
  total: number
  duration: string
  rate: number
}

export interface WsBugReply {
  bugReportId: string
  replyAuthor: string
  message: string
}

export interface WsBugStatusChange {
  bugReportId: string
  newStatus: string
  changedBy: string
}

export interface WsScheduleTrigger {
  scheduleId: string
  moduleName: string
  runId: string
}

type WsEventMap = {
  run_complete: WsRunComplete
  bug_reply: WsBugReply
  bug_status_change: WsBugStatusChange
  schedule_trigger: WsScheduleTrigger
  notification: WsNotification
}

type WsEventHandler<K extends keyof WsEventMap> = (data: WsEventMap[K]) => void

export function useNotificationsSocket(userId?: string) {
  const socketRef = useRef<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
  const handlersRef = useRef<Map<string, Set<Function>>>(new Map())

  useEffect(() => {
    // Don't connect if no user is logged in
    if (!userId) {
      socketRef.current = null
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setConnected(false)
      return
    }

    const socket = io('/?XTransformPort=3003', {
      transports: ['websocket', 'polling'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
    })

    socket.on('connect', () => {
      setConnected(true)
      // Join user-specific room for targeted notifications
      if (userId) {
        socket.emit('join', `user:${userId}`)
      }
    })

    socket.on('disconnect', () => {
      setConnected(false)
    })

    socket.on('connect_error', () => {
      setConnected(false)
    })

    // Register all stored handlers
    for (const [event, handlers] of handlersRef.current) {
      for (const handler of handlers) {
        socket.on(event, handler as any)
      }
    }

    socketRef.current = socket

    return () => {
      socket.disconnect()
      socketRef.current = null
      setConnected(false)
    }
  }, [userId])

  const on = useCallback(<K extends keyof WsEventMap>(event: K, handler: WsEventHandler<K>) => {
    if (!handlersRef.current.has(event)) {
      handlersRef.current.set(event, new Set())
    }
    handlersRef.current.get(event)!.add(handler)

    if (socketRef.current) {
      socketRef.current.on(event, handler as any)
    }

    return () => {
      handlersRef.current.get(event)?.delete(handler)
      socketRef.current?.off(event, handler as any)
    }
  }, [])

  const off = useCallback(<K extends keyof WsEventMap>(event: K, handler: WsEventHandler<K>) => {
    handlersRef.current.get(event)?.delete(handler)
    socketRef.current?.off(event, handler as any)
  }, [])

  const emit = useCallback(<K extends keyof WsEventMap>(event: K, data: WsEventMap[K]) => {
    if (socketRef.current) {
      socketRef.current.emit(event, data)
    }
  }, [])

  return { connected, on, off, emit }
}

/**
 * Helper to emit events from the backend (API routes) via the notification service REST endpoint.
 * Uses the gateway pattern with XTransformPort.
 */
export async function emitNotification<K extends keyof WsEventMap>(event: K, data: WsEventMap[K]) {
  try {
    await fetch('/api/emit?XTransformPort=3003', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event, data }),
    })
  } catch (err) {
    console.error('Failed to emit notification:', err)
  }
}
