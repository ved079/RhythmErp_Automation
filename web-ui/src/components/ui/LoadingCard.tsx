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
      <div className="lc-backdrop" />

      <div className="lc-card">
        {/* Logo with orbital ring */}
        <div className="lc-orbit-wrap">
          <div className="lc-orbit-ring" />
          <span className="lc-sonar lc-sonar-1" />
          <span className="lc-sonar lc-sonar-2" />
          <div className="lc-logo-center">
            <img src="/agdi-logo-new.png" alt="" className="lc-logo" />
          </div>
        </div>

        {/* Label */}
        <p className="lc-label">{message}</p>

        {/* Steps or bounce dots */}
        {steps && steps.length > 0 ? (
          <div className="lc-steps">
            {steps.map((step, i) => (
              <div
                key={i}
                className={`lc-step ${step.done ? 'lc-step-done' : 'lc-step-active'}`}
                style={{ animationDelay: `${i * 70}ms` }}
              >
                <span className="lc-step-icon">
                  {step.done ? (
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" className="lc-check" aria-hidden="true">
                      <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : (
                    <span className="lc-spinner" />
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
        .lc-root {
          position: fixed;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 50;
          pointer-events: none;
        }
        .lc-backdrop {
          position: absolute;
          inset: 0;
          background: rgba(0,0,0,0.05);
          backdrop-filter: blur(1.5px);
          -webkit-backdrop-filter: blur(1.5px);
        }
        .lc-card {
          position: relative;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 22px;
          padding: 32px 48px 28px;
          box-shadow:
            0 0 0 1px color-mix(in srgb, var(--primary) 6%, transparent),
            0 12px 40px rgba(0,0,0,0.13),
            0 2px 8px rgba(0,0,0,0.06);
          min-width: 210px;
          animation: lc-breathe 3.5s ease-in-out infinite;
        }

        /* ── Orbital logo ── */
        .lc-orbit-wrap {
          position: relative;
          width: 96px;
          height: 96px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        /* Conic-gradient ring that spins */
        .lc-orbit-ring {
          position: absolute;
          inset: 0;
          border-radius: 50%;
          background: conic-gradient(
            from 0deg,
            var(--primary) 0deg,
            color-mix(in srgb, var(--primary) 60%, transparent) 80deg,
            transparent 140deg,
            transparent 360deg
          );
          -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #fff calc(100% - 3px));
          mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #fff calc(100% - 3px));
          animation: lc-orbit-spin 1.6s linear infinite;
        }

        /* Sonar pulse rings */
        .lc-sonar {
          position: absolute;
          inset: 4px;
          border-radius: 50%;
          border: 1.5px solid var(--primary);
          opacity: 0;
          animation: lc-sonar 2.8s ease-out infinite;
        }
        .lc-sonar-1 { animation-delay: 0s; }
        .lc-sonar-2 { animation-delay: 1.4s; }

        /* Logo */
        .lc-logo-center {
          position: relative;
          z-index: 1;
          width: 56px;
          height: 56px;
          border-radius: 14px;
          background: var(--card);
          display: flex;
          align-items: center;
          justify-content: center;
          animation: lc-logo-breathe 3.5s ease-in-out infinite;
        }
        .lc-logo {
          width: 46px;
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
          animation: lc-fade-pulse 3.5s ease-in-out infinite;
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
          animation: lc-step-in 0.22s ease both;
        }
        .lc-step-done  { color: var(--muted-foreground); }
        .lc-step-active { color: var(--card-foreground); font-weight: 500; }
        .lc-step-icon {
          flex-shrink: 0;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .lc-check {
          color: #10b981;
          animation: lc-check-pop 0.28s cubic-bezier(0.34,1.56,0.64,1) both;
        }
        .lc-spinner {
          display: block;
          width: 11px;
          height: 11px;
          border-radius: 50%;
          border: 2px solid color-mix(in srgb, var(--primary) 22%, transparent);
          border-top-color: var(--primary);
          animation: lc-orbit-spin 0.7s linear infinite;
        }
        .lc-step-text { transition: opacity 0.25s; }
        .lc-step-done .lc-step-text {
          text-decoration: line-through;
          text-decoration-color: color-mix(in srgb, var(--muted-foreground) 40%, transparent);
          opacity: 0.45;
        }

        /* ── Bounce dots ── */
        .lc-dots { display: flex; gap: 6px; align-items: center; }
        .lc-dot {
          display: inline-block;
          width: 5px; height: 5px;
          border-radius: 50%;
          background: var(--border);
          animation: lc-dot-bounce 1.2s ease-in-out infinite;
        }
        .lc-dot-1 { animation-delay: 0s; }
        .lc-dot-2 { animation-delay: 0.15s; }
        .lc-dot-3 { animation-delay: 0.3s; }

        /* ── Keyframes ── */
        @keyframes lc-orbit-spin  { to { transform: rotate(360deg); } }
        @keyframes lc-sonar {
          0%   { transform: scale(0.88); opacity: 0.6; }
          100% { transform: scale(1.5);  opacity: 0; }
        }
        @keyframes lc-breathe {
          0%, 100% { transform: scale(1); }
          50%      { transform: scale(1.007); }
        }
        @keyframes lc-logo-breathe {
          0%, 100% { transform: scale(1); }
          50%      { transform: scale(1.06); }
        }
        @keyframes lc-fade-pulse {
          0%, 100% { opacity: 0.65; }
          50%      { opacity: 1; }
        }
        @keyframes lc-step-in {
          from { opacity: 0; transform: translateX(-5px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes lc-check-pop {
          from { transform: scale(0) rotate(-20deg); opacity: 0; }
          to   { transform: scale(1) rotate(0deg);   opacity: 1; }
        }
        @keyframes lc-dot-bounce {
          0%, 80%, 100% { transform: scale(0.75); background: var(--border); }
          40%           { transform: scale(1.3);  background: var(--primary); }
        }

        @media (prefers-reduced-motion: reduce) {
          .lc-orbit-ring, .lc-sonar, .lc-dot, .lc-spinner,
          .lc-card, .lc-logo-center, .lc-label { animation: none; }
        }
      `}</style>
    </div>
  )
}
