/**
 * GaneshaIcon.jsx
 * A clean SVG Ganesha face icon — golden cosmic style.
 * Depicts: elephant head, large ears, crown (kireetam), curved trunk,
 * single intact tusk, third eye, and Om symbol on forehead.
 */

export default function GaneshaIcon({ size = 40, glow = false }) {
  const gold   = '#fbbf24'
  const dark   = '#1a0e00'
  const mid    = '#d97706'
  const light  = '#fef3c7'
  const dim    = 'rgba(251,191,36,0.5)'

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={glow ? { filter: `drop-shadow(0 0 6px ${gold})` } : undefined}
      aria-label="Ganesha"
    >
      {/* ── Left ear (large, round) ── */}
      <ellipse cx="11" cy="36" rx="9" ry="11" fill={mid} opacity="0.8" />
      <ellipse cx="11" cy="36" rx="6" ry="7.5" fill={dark} opacity="0.6" />

      {/* ── Right ear ── */}
      <ellipse cx="53" cy="36" rx="9" ry="11" fill={mid} opacity="0.8" />
      <ellipse cx="53" cy="36" rx="6" ry="7.5" fill={dark} opacity="0.6" />

      {/* ── Head / face (oval) ── */}
      <ellipse cx="32" cy="36" rx="20" ry="22" fill={gold} />
      <ellipse cx="32" cy="36" rx="18" ry="20" fill="#fcd34d" />

      {/* ── Crown / kireetam ── */}
      {/* Base band */}
      <rect x="14" y="14" width="36" height="5" rx="2.5" fill={mid} />
      {/* Centre peak */}
      <polygon points="32,4 27,14 37,14" fill={gold} />
      {/* Left peak */}
      <polygon points="22,7 18,14 26,14" fill={mid} />
      {/* Right peak */}
      <polygon points="42,7 38,14 46,14" fill={mid} />
      {/* Crown gem */}
      <circle cx="32" cy="10" r="2.5" fill={light} />

      {/* ── Eyes ── */}
      <ellipse cx="25" cy="33" rx="3.5" ry="3" fill={dark} />
      <ellipse cx="39" cy="33" rx="3.5" ry="3" fill={dark} />
      <circle cx="25" cy="33" r="1.5" fill={light} />
      <circle cx="39" cy="33" r="1.5" fill={light} />
      {/* Pupils */}
      <circle cx="25.5" cy="33" r="0.8" fill={dark} />
      <circle cx="39.5" cy="33" r="0.8" fill={dark} />

      {/* ── Third eye / tilak ── */}
      <ellipse cx="32" cy="26" rx="2" ry="2.5" fill={mid} />
      <ellipse cx="32" cy="26" rx="1" ry="1.5" fill={light} />

      {/* ── Trunk (curling left — auspicious) ── */}
      <path
        d="M 29 43 Q 24 50 20 52 Q 16 54 17 58 Q 18 60 21 59"
        stroke={mid}
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M 29 43 Q 24 50 20 52 Q 16 54 17 58 Q 18 60 21 59"
        stroke={gold}
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />

      {/* ── Right tusk (intact) ── */}
      <path
        d="M 42 44 Q 50 48 52 55"
        stroke={light}
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
        opacity="0.9"
      />
      {/* Left tusk (broken — just a stub) */}
      <path
        d="M 22 44 Q 17 46 15 50"
        stroke={light}
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
        opacity="0.5"
      />

      {/* ── Subtle OM on forehead ── */}
      <text
        x="32"
        y="20"
        textAnchor="middle"
        fontSize="5"
        fill={mid}
        fontFamily="serif"
        opacity="0.7"
      >
        ॐ
      </text>

      {/* ── Brow / forehead markings ── */}
      <line x1="20" y1="28" x2="29" y2="27" stroke={mid} strokeWidth="1.2" strokeLinecap="round" opacity="0.6" />
      <line x1="44" y1="28" x2="35" y2="27" stroke={mid} strokeWidth="1.2" strokeLinecap="round" opacity="0.6" />
    </svg>
  )
}
