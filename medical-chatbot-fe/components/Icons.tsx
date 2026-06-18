/**
 * Custom inline SVG icons (no external/Lottie deps — work offline for the demo).
 * - HealthIcon  : vitals monitor + heartbeat (the "health-monitoring" logo).
 * - RobotFace   : compact monochrome robot face for chat avatars.
 * - RobotMascot : larger colorful waving robot for the empty state.
 *
 * Animations reference the @keyframes defined in app/globals.css. SVG
 * transform-origin uses `transformBox: "view-box"` so origins are in viewBox
 * coordinates. All animations are auto-disabled via prefers-reduced-motion.
 */

interface IconProps {
  className?: string;
}

/** Vitals monitor showing a heartbeat line — the app logo. Uses currentColor. */
export function HealthIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {/* monitor screen */}
      <rect x="2.5" y="3.5" width="19" height="13" rx="2.5" />
      {/* heartbeat trace inside the screen */}
      <path d="M5 11 h2.5 l1.3 -3.2 1.9 6 1.5 -7 1.3 4.4 1.1 -2.4 H19" />
      {/* stand + base */}
      <path d="M12 16.5 v3.8" />
      <path d="M9 20.5 h6" />
    </svg>
  );
}

/** Compact robot face (blink + antenna pulse). Monochrome via currentColor. */
export function RobotFace({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      {/* antenna */}
      <line
        x1="20"
        y1="9"
        x2="20"
        y2="5.5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle
        cx="20"
        cy="4"
        r="2"
        fill="currentColor"
        style={{
          transformBox: "view-box",
          transformOrigin: "20px 4px",
          animation: "robot-antenna 1.6s ease-in-out infinite",
        }}
      />
      {/* head */}
      <rect
        x="8"
        y="9"
        width="24"
        height="22"
        rx="7"
        stroke="currentColor"
        strokeWidth="2.2"
      />
      {/* eyes (blink) */}
      <g
        style={{
          transformBox: "view-box",
          transformOrigin: "20px 19px",
          animation: "robot-blink 4.5s infinite",
        }}
      >
        <circle cx="15" cy="19" r="2.3" fill="currentColor" />
        <circle cx="25" cy="19" r="2.3" fill="currentColor" />
      </g>
      {/* smile */}
      <path
        d="M15.5 24 Q20 27.5 24.5 24"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

/** Larger colorful robot that floats, blinks, and waves. */
export function RobotMascot({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 120 132"
      fill="none"
      className={className}
      role="img"
      aria-label="Robot asisten kesehatan melambai"
    >
      <defs>
        <linearGradient id="robotBodyGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#14b8a6" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
      </defs>

      <g style={{ animation: "robot-float 3.2s ease-in-out infinite" }}>
        {/* antenna */}
        <line x1="60" y1="26" x2="60" y2="14" stroke="#0d9488" strokeWidth="3" strokeLinecap="round" />
        <circle
          cx="60"
          cy="10"
          r="5"
          fill="#5eead4"
          style={{
            transformBox: "view-box",
            transformOrigin: "60px 10px",
            animation: "robot-antenna 1.6s ease-in-out infinite",
          }}
        />

        {/* resting right arm */}
        <path d="M80 80 L92 96" stroke="url(#robotBodyGrad)" strokeWidth="9" strokeLinecap="round" />
        <circle cx="93" cy="98" r="6" fill="#06b6d4" />

        {/* body */}
        <rect x="40" y="72" width="40" height="34" rx="13" fill="url(#robotBodyGrad)" />
        <circle cx="60" cy="88" r="4.5" fill="#bbf7e6" />
        {/* feet */}
        <rect x="46" y="103" width="12" height="8" rx="3" fill="#0d9488" />
        <rect x="62" y="103" width="12" height="8" rx="3" fill="#0d9488" />

        {/* head */}
        <rect x="25" y="40" width="6" height="13" rx="3" fill="#0d9488" />
        <rect x="89" y="40" width="6" height="13" rx="3" fill="#0d9488" />
        <rect x="30" y="24" width="60" height="46" rx="16" fill="url(#robotBodyGrad)" />
        {/* face screen */}
        <rect x="37" y="31" width="46" height="32" rx="11" fill="#0b3b39" />
        {/* eyes (blink) */}
        <g
          style={{
            transformBox: "view-box",
            transformOrigin: "60px 45px",
            animation: "robot-blink 4.5s infinite",
          }}
        >
          <circle cx="51" cy="45" r="4.5" fill="#7ef0d6" />
          <circle cx="69" cy="45" r="4.5" fill="#7ef0d6" />
        </g>
        {/* smile */}
        <path d="M52 53 Q60 59 68 53" stroke="#7ef0d6" strokeWidth="2.5" strokeLinecap="round" fill="none" />

        {/* waving left arm */}
        <g
          style={{
            transformBox: "view-box",
            transformOrigin: "40px 80px",
            animation: "robot-wave 1.9s ease-in-out infinite",
          }}
        >
          <path d="M40 80 L24 60" stroke="url(#robotBodyGrad)" strokeWidth="9" strokeLinecap="round" />
          <circle cx="22" cy="57" r="7" fill="#06b6d4" />
        </g>
      </g>
    </svg>
  );
}
