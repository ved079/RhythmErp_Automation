'use client'

interface Step {
  label: string
  done: boolean
}

interface Props {
  message?: string
  steps?: Step[]
}

export default function LoadingCard({ message = 'LOADING', steps }: Props) {
  return (
    <div className="lc-root">
      {/* Backdrop blur */}
      <div className="lc-backdrop" />

      <div className="lc-card">
        {/* Heartbeat rings behind the spinner */}
        <div className="lc-pulse-wrap">
          <span className="lc-pulse lc-pulse-1" />
          <span className="lc-pulse lc-pulse-2" />
          <span className="lc-pulse lc-pulse-3" />

          {/* Spinner ring */}
          <div className="lc-ring-wrap">
            <svg className="lc-ring-svg" viewBox="0 0 64 64" fill="none" aria-hidden="true">
              <circle cx="32" cy="32" r="26" className="lc-track" strokeWidth="2.5" />
              <circle cx="32" cy="32" r="26" className="lc-arc" strokeWidth="2.5" strokeLinecap="round"
                strokeDasharray="163.36" strokeDashoffset="122.52" />
            </svg>
            {/* Inner spinning arc */}
            <svg className="lc-ring-inner" viewBox="0 0 40 40" fill="none" aria-hidden="true">
              <circle cx="20" cy="20" r="14" className="lc-arc-inner" strokeWidth="2" strokeLinecap="round"
                strokeDasharray="87.96" strokeDashoffset="70" />
            </svg>
            {/* Logo inside ring */}
            <div className="lc-ring-logo">
              <img src="/agdi-logo-new.png" alt="" className="lc-logo-inner" />
            </div>
          </div>
        </div>

        {/* Label */}
        <p className="lc-label">{message}</p>

        {/* Steps or dots */}
        {steps && steps.length > 0 ? (
          <div className="lc-steps">
            {steps.map((step, i) => (
              <div
                key={i}
                className={`lc-step ${step.done ? 'lc-step-done' : 'lc-step-active'}`}
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <span className="lc-step-icon-wrap">
                  {step.done ? (
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" className="lc-check-icon" aria-hidden="true">
                      <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : (
                    <span className="lc-dot-spin" />
                  )}
                </span>
                <span className="lc-step-text">{step.label}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="lc-dots" aria-hidden="true">
            <span className="lc-dot lc-dot-1" />
            <span className="lc-dot lc-dot-2" />
            <span className="lc-dot lc-dot-3" />
          </div>
        )}
      </div>

      <style>{`
        /* ── Root ── */
        .lc-root {
          position: fixed;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 50;
          pointer-events: none;
        }

        /* ── Backdrop ── */
        .lc-backdrop {
          position: absolute;
          inset: 0;
          background: rgba(0,0,0,0.06);
          backdrop-filter: blur(1px);
          -webkit-backdrop-filter: blur(1px);
        }

        /* ── Card ── */
        .lc-card {
          position: relative;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 18px;
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 20px;
          padding: 32px 48px 28px;
          box-shadow:
            0 0 0 1px color-mix(in srgb, var(--primary) 8%, transparent),
            0 8px 32px rgba(0,0,0,0.12),
            0 2px 8px rgba(0,0,0,0.06);
          min-width: 210px;
          animation: lc-card-breathe 3s ease-in-out infinite;
        }

        /* ── Pulse rings (heartbeat) ── */
        .lc-pulse-wrap {
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 80px;
          height: 80px;
        }
        .lc-pulse {
          position: absolute;
          inset: 0;
          border-radius: 50%;
          border: 2px solid var(--primary);
          opacity: 0;
          animation: lc-heartbeat 2.4s ease-out infinite;
        }
        .lc-pulse-1 { animation-delay: 0s; }
        .lc-pulse-2 { animation-delay: 0.6s; }
        .lc-pulse-3 { animation-delay: 1.2s; }

        /* ── Spinner ring ── */
        .lc-ring-wrap {
          position: absolute;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .lc-ring-svg {
          position: absolute;
          width: 80px;
          height: 80px;
          animation: lc-spin-cw 2s linear infinite;
        }
        .lc-ring-inner {
          position: absolute;
          width: 48px;
          height: 48px;
          animation: lc-spin-ccw 1.4s linear infinite;
        }
        .lc-track { stroke: var(--border); fill: none; }
        .lc-arc   { stroke: var(--primary); fill: none; }
        .lc-arc-inner {
          stroke: color-mix(in srgb, var(--primary) 55%, transparent);
          fill: none;
        }

        /* Logo inside */
        .lc-ring-logo {
          position: relative;
          z-index: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 30px;
          height: 30px;
          animation: lc-logo-pulse 2.4s ease-in-out infinite;
        }
        .lc-logo-inner {
          width: 26px;
          height: auto;
          object-fit: contain;
        }

        /* ── Label ── */
        .lc-label {
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.22em;
          color: var(--primary);
          margin: 0;
          font-family: var(--font-sans, system-ui, sans-serif);
          animation: lc-label-pulse 2.4s ease-in-out infinite;
        }

        /* ── Steps ── */
        .lc-steps {
          display: flex;
          flex-direction: column;
          gap: 8px;
          width: 100%;
        }
        .lc-step {
          display: flex;
          align-items: center;
          gap: 9px;
          font-size: 12px;
          font-family: var(--font-sans, system-ui, sans-serif);
          animation: lc-step-in 0.25s ease both;
        }
        .lc-step-done {
          color: var(--muted-foreground);
        }
        .lc-step-active {
          color: var(--card-foreground);
          font-weight: 500;
        }
        .lc-step-icon-wrap {
          flex-shrink: 0;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .lc-check-icon {
          color: #10b981;
          animation: lc-check-pop 0.3s cubic-bezier(0.34,1.56,0.64,1) both;
        }
        .lc-dot-spin {
          display: block;
          width: 10px;
          height: 10px;
          border-radius: 50%;
          border: 2px solid color-mix(in srgb, var(--primary) 25%, transparent);
          border-top-color: var(--primary);
          animation: lc-spin-cw 0.75s linear infinite;
        }
        .lc-step-text {
          transition: opacity 0.3s, text-decoration 0.3s;
        }
        .lc-step-done .lc-step-text {
          text-decoration: line-through;
          text-decoration-color: color-mix(in srgb, var(--muted-foreground) 50%, transparent);
          opacity: 0.5;
        }

        /* ── Dots (no-steps mode) ── */
        .lc-dots {
          display: flex;
          gap: 6px;
          align-items: center;
        }
        .lc-dot {
          display: inline-block;
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: var(--border);
          animation: lc-dot-bounce 1.2s ease-in-out infinite;
        }
        .lc-dot-1 { animation-delay: 0s; }
        .lc-dot-2 { animation-delay: 0.15s; }
        .lc-dot-3 { animation-delay: 0.3s; }

        /* ── Keyframes ── */
        @keyframes lc-heartbeat {
          0%   { transform: scale(0.85); opacity: 0.5; }
          30%  { opacity: 0.25; }
          100% { transform: scale(1.55); opacity: 0; }
        }
        @keyframes lc-spin-cw  { to { transform: rotate(360deg); } }
        @keyframes lc-spin-ccw { to { transform: rotate(-360deg); } }
        @keyframes lc-card-breathe {
          0%, 100% { transform: scale(1); }
          50%      { transform: scale(1.008); }
        }
        @keyframes lc-logo-pulse {
          0%, 100% { transform: scale(1); opacity: 0.9; }
          50%      { transform: scale(1.12); opacity: 1; }
        }
        @keyframes lc-label-pulse {
          0%, 100% { opacity: 0.7; }
          50%      { opacity: 1; }
        }
        @keyframes lc-step-in {
          from { opacity: 0; transform: translateX(-6px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes lc-check-pop {
          from { transform: scale(0) rotate(-15deg); opacity: 0; }
          to   { transform: scale(1) rotate(0deg);  opacity: 1; }
        }
        @keyframes lc-dot-bounce {
          0%, 80%, 100% { transform: scale(0.75); background: var(--border); }
          40%           { transform: scale(1.3);  background: var(--primary); }
        }

        @media (prefers-reduced-motion: reduce) {
          .lc-ring-svg, .lc-ring-inner, .lc-dot, .lc-dot-spin,
          .lc-pulse, .lc-card, .lc-ring-logo, .lc-label { animation: none; }
        }
      `}</style>
    </div>
  )
}
