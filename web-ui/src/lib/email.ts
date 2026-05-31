// ─── Email Utility ────────────────────────────────────────
// Sends emails via SMTP (Gmail / any provider).
// Uses nodemailer under the hood.

import nodemailer from 'nodemailer'

// Lazy-initialize transporter so we don't crash on startup if env vars are missing
let _transporter: nodemailer.Transporter | null = null

function getTransporter(): nodemailer.Transporter {
  if (_transporter) return _transporter

  const host = process.env.SMTP_HOST
  const port = Number(process.env.SMTP_PORT) || 587
  const user = process.env.SMTP_USER
  const pass = process.env.SMTP_PASS

  if (!host || !user || !pass) {
    throw new Error('SMTP credentials not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASS in .env')
  }

  _transporter = nodemailer.createTransport({
    host,
    port,
    secure: port === 465, // true for 465, false for other ports
    auth: {
      user,
      pass,
    },
  })

  return _transporter
}

export interface SendEmailOptions {
  to: string
  subject: string
  html: string
  text?: string
}

/**
 * Send an email using the configured SMTP transporter.
 * Returns true on success, false on failure.
 */
export async function sendEmail({ to, subject, html, text }: SendEmailOptions): Promise<boolean> {
  try {
    const transporter = getTransporter()
    const from = process.env.SMTP_FROM || process.env.SMTP_USER || 'noreply@example.com'

    const info = await transporter.sendMail({
      from,
      to,
      subject,
      html,
      text: text || html.replace(/<[^>]*>/g, ''), // strip HTML for plain text fallback
    })

    console.log(`[Email] Sent to ${to}: ${info.messageId}`)
    return true
  } catch (error) {
    console.error('[Email] Failed to send:', error)
    return false
  }
}

/**
 * Send a password reset OTP email.
 */
export async function sendOtpEmail(to: string, otp: string, userName?: string): Promise<boolean> {
  const greeting = userName ? `Hi ${userName},` : 'Hello,'

  const html = `
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 480px; margin: 0 auto; background: #f9fafb; border-radius: 12px; overflow: hidden;">
      <div style="background: linear-gradient(135deg, #3F51B5, #2E7D32); padding: 24px 32px;">
        <h1 style="color: white; margin: 0; font-size: 20px; font-weight: 600;">RhythmERP Automation</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 4px 0 0; font-size: 13px;">Password Reset Request</p>
      </div>
      <div style="padding: 32px;">
        <p style="color: #333; font-size: 14px; margin: 0 0 16px;">${greeting}</p>
        <p style="color: #555; font-size: 13px; margin: 0 0 24px;">
          We received a request to reset your password. Use the OTP below to proceed:
        </p>
        <div style="background: #E8EAF6; border: 2px dashed #3F51B5; border-radius: 8px; padding: 16px; text-align: center; margin: 0 0 24px;">
          <span style="font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #3F51B5; font-family: 'Courier New', monospace;">${otp}</span>
        </div>
        <p style="color: #777; font-size: 12px; margin: 0 0 8px;">
          ⏱ This OTP expires in <strong>15 minutes</strong>.
        </p>
        <p style="color: #999; font-size: 11px; margin: 0;">
          If you didn't request this, you can safely ignore this email. Your password will remain unchanged.
        </p>
      </div>
      <div style="background: #f1f2f7; padding: 16px 32px; text-align: center;">
        <p style="color: #999; font-size: 10px; margin: 0;">
          © ${new Date().getFullYear()} RhythmERP Automation by AlgoRhythms · This is an automated message
        </p>
      </div>
    </div>
  `

  return sendEmail({
    to,
    subject: 'RhythmERP — Your Password Reset OTP',
    html,
    text: `${greeting}\n\nYour password reset OTP is: ${otp}\n\nThis OTP expires in 15 minutes.\n\nIf you didn't request this, ignore this email.`,
  })
}
