/**
 * GaneshaIllustration — stylised South-Indian temple-line art.
 * Theme-aware via CSS variables; scales cleanly for hero & compact banner.
 */

export default function GaneshaIllustration({ size = 112, className = '', compact = false }) {
  const h = Math.round(size * (compact ? 1 : 1.15))
  const id = compact ? 'gn-compact' : 'gn-hero'

  return (
    <div
      className={`ganesha-art ${className}`}
      style={{ width: size, height: h, flexShrink: 0 }}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 200 230"
        width={size}
        height={h}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label="Ganesha"
      >
        <defs>
          <linearGradient id={`${id}-gold`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--orange)" />
            <stop offset="55%" stopColor="var(--orange-dark)" />
            <stop offset="100%" stopColor="var(--orange)" />
          </linearGradient>
          <radialGradient id={`${id}-halo`} cx="50%" cy="42%" r="50%">
            <stop offset="0%" stopColor="var(--orange)" stopOpacity="0.22" />
            <stop offset="100%" stopColor="var(--orange)" stopOpacity="0" />
          </radialGradient>
          <filter id={`${id}-glow`} x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Halo & mandala ring */}
        <circle cx="100" cy="108" r="88" fill={`url(#${id}-halo)`} className="ganesha-halo" />
        <circle
          cx="100" cy="108" r="92"
          stroke={`url(#${id}-gold)`}
          strokeWidth="1.2"
          strokeDasharray="4 6"
          opacity="0.45"
          className="ganesha-ring"
        />
        {!compact && (
          <>
            {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => (
              <line
                key={deg}
                x1="100" y1="108"
                x2={100 + 78 * Math.cos((deg * Math.PI) / 180)}
                y2={108 + 78 * Math.sin((deg * Math.PI) / 180)}
                stroke="var(--orange)"
                strokeWidth="0.6"
                opacity="0.18"
              />
            ))}
          </>
        )}

        {/* Crown (mukuta) */}
        <path
          d="M72 78 Q100 48 128 78 L124 88 Q100 68 76 88 Z"
          fill={`url(#${id}-gold)`}
          opacity="0.9"
        />
        <path
          d="M88 52 L100 38 L112 52 L108 62 L92 62 Z"
          fill="var(--orange-dark)"
          opacity="0.85"
        />

        {/* Head */}
        <ellipse cx="100" cy="102" rx="46" ry="40" fill="var(--card-bg)" stroke={`url(#${id}-gold)`} strokeWidth="2.2" />

        {/* Ears */}
        <path
          d="M58 98 Q42 88 48 72 Q58 78 62 92 Z"
          fill="var(--highlight-bg)"
          stroke={`url(#${id}-gold)`}
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <path
          d="M142 98 Q158 88 152 72 Q142 78 138 92 Z"
          fill="var(--highlight-bg)"
          stroke={`url(#${id}-gold)`}
          strokeWidth="1.5"
          strokeLinejoin="round"
        />

        {/* Eyes */}
        <ellipse cx="84" cy="98" rx="5" ry="6" fill="var(--accent-dark)" opacity="0.85" />
        <ellipse cx="116" cy="98" rx="5" ry="6" fill="var(--accent-dark)" opacity="0.85" />
        <circle cx="85" cy="97" r="1.2" fill="var(--orange)" opacity="0.6" />
        <circle cx="117" cy="97" r="1.2" fill="var(--orange)" opacity="0.6" />

        {/* Trunk */}
        <path
          d="M100 108 Q108 118 106 132 Q102 148 88 158 Q82 162 78 156 Q88 150 94 136 Q98 124 96 112 Z"
          fill="var(--highlight-bg)"
          stroke={`url(#${id}-gold)`}
          strokeWidth="2"
          strokeLinejoin="round"
          filter={compact ? undefined : `url(#${id}-glow)`}
        />

        {/* Tusk hint */}
        <path d="M92 114 L88 124" stroke="var(--orange-dark)" strokeWidth="1.5" strokeLinecap="round" opacity="0.7" />

        {/* Modak (sweet) */}
        <circle cx="128" cy="148" r="9" fill={`url(#${id}-gold)`} opacity="0.95" />
        <path d="M128 139 Q132 144 128 149 Q124 144 128 139" fill="var(--card-bg)" opacity="0.35" />

        {/* Body / dhoti suggestion */}
        <path
          d="M68 142 Q100 158 132 142 L128 178 Q100 196 72 178 Z"
          fill="var(--highlight-bg)"
          stroke={`url(#${id}-gold)`}
          strokeWidth="1.8"
          strokeLinejoin="round"
          opacity="0.95"
        />

        {/* Raised hand (blessing) */}
        <path
          d="M58 130 Q48 118 52 108 Q58 112 62 122 Q64 128 58 130"
          fill="var(--highlight-bg)"
          stroke={`url(#${id}-gold)`}
          strokeWidth="1.5"
        />

        {/* Om at base */}
        {!compact && (
          <text
            x="100" y="218"
            textAnchor="middle"
            fontSize="22"
            fontFamily="serif"
            fill="var(--orange)"
            opacity="0.75"
            className="ganesha-om"
          >
            ॐ
          </text>
        )}

        {/* Decorative lotus base */}
        <ellipse cx="100" cy="200" rx="28" ry="6" fill="var(--orange)" opacity="0.12" />
        {[0, 60, 120, 180, 240, 300].map((deg) => (
          <ellipse
            key={deg}
            cx={100 + 18 * Math.cos((deg * Math.PI) / 180)}
            cy={200 + 5 * Math.sin((deg * Math.PI) / 180)}
            rx="8" ry="4"
            fill="var(--orange)"
            opacity="0.1"
            transform={`rotate(${deg} ${100 + 18 * Math.cos((deg * Math.PI) / 180)} ${200 + 5 * Math.sin((deg * Math.PI) / 180)})`}
          />
        ))}
      </svg>
    </div>
  )
}
