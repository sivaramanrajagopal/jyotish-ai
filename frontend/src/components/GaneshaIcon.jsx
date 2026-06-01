/**
 * GaneshaIcon.jsx
 * Cute, vibrant Ganesha — saffron + orange palette, works on dark header.
 */

export default function GaneshaIcon({ size = 56, glow = false }) {
  const saffron = '#FF9900'
  const deepOrange = '#E47911'
  const skin    = '#FFB347'
  const skinLt  = '#FFD280'
  const red     = '#D13212'
  const cream   = '#FFF8DC'
  const brown   = '#5C2A00'
  const white   = '#FFFFFF'

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 80 80"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={glow ? { filter: `drop-shadow(0 0 8px ${saffron})` } : undefined}
      aria-label="Ganesha"
    >
      {/* ── Halo / aura ── */}
      <circle cx="40" cy="36" r="34" fill={saffron} opacity="0.12" />
      <circle cx="40" cy="36" r="30" fill={saffron} opacity="0.07" />

      {/* ── Left ear ── */}
      <ellipse cx="12" cy="40" rx="11" ry="13" fill={skin} />
      <ellipse cx="12" cy="40" rx="7"  ry="9"  fill={skinLt} opacity="0.6" />
      <ellipse cx="12" cy="40" rx="4"  ry="6"  fill={brown}  opacity="0.25" />

      {/* ── Right ear ── */}
      <ellipse cx="68" cy="40" rx="11" ry="13" fill={skin} />
      <ellipse cx="68" cy="40" rx="7"  ry="9"  fill={skinLt} opacity="0.6" />
      <ellipse cx="68" cy="40" rx="4"  ry="6"  fill={brown}  opacity="0.25" />

      {/* ── Head ── */}
      <ellipse cx="40" cy="42" rx="25" ry="27" fill={skin} />
      <ellipse cx="40" cy="42" rx="22" ry="24" fill={skinLt} />

      {/* ── Crown base ── */}
      <rect x="18" y="18" width="44" height="7" rx="3.5" fill={deepOrange} />
      {/* Crown peaks */}
      <polygon points="40,4 34,18 46,18"  fill={saffron} />
      <polygon points="28,9 22,18 34,18"  fill={deepOrange} />
      <polygon points="52,9 46,18 58,18"  fill={deepOrange} />
      {/* Crown gems */}
      <circle cx="40" cy="9"  r="3" fill={red}   />
      <circle cx="28" cy="13" r="2" fill={cream} opacity="0.9" />
      <circle cx="52" cy="13" r="2" fill={cream} opacity="0.9" />
      {/* Gold crown dots */}
      <circle cx="33" cy="21" r="1.2" fill={saffron} />
      <circle cx="40" cy="21" r="1.2" fill={saffron} />
      <circle cx="47" cy="21" r="1.2" fill={saffron} />

      {/* ── Forehead tilak / third eye ── */}
      <ellipse cx="40" cy="31" rx="3" ry="3.5" fill={red} />
      <ellipse cx="40" cy="31" rx="1.5" ry="2" fill={cream} />

      {/* ── OM symbol on forehead ── */}
      <text x="40" y="27" textAnchor="middle" fontSize="7"
        fill={deepOrange} fontFamily="serif" fontWeight="bold" opacity="0.9">ॐ</text>

      {/* ── Eyes ── */}
      <ellipse cx="32" cy="40" rx="5" ry="4.5" fill={white} />
      <ellipse cx="48" cy="40" rx="5" ry="4.5" fill={white} />
      <circle  cx="32" cy="40.5" r="3"   fill={brown} />
      <circle  cx="48" cy="40.5" r="3"   fill={brown} />
      <circle  cx="32" cy="40.5" r="1.4" fill={white} />
      <circle  cx="48" cy="40.5" r="1.4" fill={white} />
      <circle  cx="32.6" cy="40.2" r="0.7" fill={brown} />
      <circle  cx="48.6" cy="40.2" r="0.7" fill={brown} />
      {/* Eyelashes */}
      <path d="M28 37.5 Q30 35 32 37" stroke={brown} strokeWidth="0.8" fill="none" />
      <path d="M44 37.5 Q46 35 48 37" stroke={brown} strokeWidth="0.8" fill="none" />

      {/* ── Eyebrows ── */}
      <path d="M27 36 Q32 33 37 35.5" stroke={brown} strokeWidth="1.5" strokeLinecap="round" fill="none" />
      <path d="M43 35.5 Q48 33 53 36" stroke={brown} strokeWidth="1.5" strokeLinecap="round" fill="none" />

      {/* ── Cheek blush ── */}
      <ellipse cx="27" cy="47" rx="5" ry="3" fill={red} opacity="0.18" />
      <ellipse cx="53" cy="47" rx="5" ry="3" fill={red} opacity="0.18" />

      {/* ── Trunk (curling left — auspicious) ── */}
      <path d="M 37 52 Q 30 60 26 63 Q 22 66 22 70 Q 22 73 26 72"
        stroke={deepOrange} strokeWidth="5.5" strokeLinecap="round" fill="none" />
      <path d="M 37 52 Q 30 60 26 63 Q 22 66 22 70 Q 22 73 26 72"
        stroke={skin}      strokeWidth="3.5" strokeLinecap="round" fill="none" />
      <path d="M 37 52 Q 30 60 26 63 Q 22 66 22 70 Q 22 73 26 72"
        stroke={skinLt}    strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.6" />

      {/* ── Right tusk (intact) ── */}
      <path d="M 51 53 Q 60 58 63 67"
        stroke={cream} strokeWidth="3" strokeLinecap="round" fill="none" />
      <path d="M 51 53 Q 60 58 63 67"
        stroke={saffron} strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.4" />

      {/* ── Left tusk (broken — stub) ── */}
      <path d="M 29 53 Q 22 56 19 62"
        stroke={cream} strokeWidth="2" strokeLinecap="round" fill="none" opacity="0.6" />

      {/* ── Necklace ── */}
      <path d="M 20 53 Q 40 58 60 53"
        stroke={saffron} strokeWidth="1.5" strokeDasharray="2 2" fill="none" opacity="0.7" />
    </svg>
  )
}
