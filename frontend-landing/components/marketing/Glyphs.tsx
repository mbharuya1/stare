// Inline SVG glyphs used throughout the landing. Single-color, currentColor.

interface GlyphProps {
  className?: string;
  size?: number;
}

/** Slim Ionic column. Used in the hero (smaller, simpler). */
export function ColumnGlyph({ className, size = 32 }: GlyphProps) {
  return (
    <svg
      viewBox="0 0 32 64"
      width={size}
      height={size * 2}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {/* base */}
      <rect x="3" y="58" width="26" height="4" rx="0.5" />
      <rect x="6" y="54" width="20" height="4" rx="0.5" />
      {/* shaft fluting */}
      <line x1="9"  y1="14" x2="9"  y2="54" />
      <line x1="13" y1="14" x2="13" y2="54" />
      <line x1="16" y1="14" x2="16" y2="54" />
      <line x1="19" y1="14" x2="19" y2="54" />
      <line x1="23" y1="14" x2="23" y2="54" />
      {/* capital */}
      <rect x="3" y="10" width="26" height="4" rx="0.5" />
      <rect x="6" y="6"  width="20" height="4" rx="0.5" />
      <path d="M3 6 Q16 0, 29 6" />
    </svg>
  );
}

/** Doric column with capital detail. Used on the Lawyer mode card. */
export function DoricColumnGlyph({ className, size = 48 }: GlyphProps) {
  return (
    <svg
      viewBox="0 0 48 64"
      width={size}
      height={(size * 64) / 48}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {/* stepped base */}
      <rect x="2"  y="58" width="44" height="4" />
      <rect x="6"  y="54" width="36" height="4" />
      <rect x="10" y="50" width="28" height="4" />
      {/* shaft with vertical fluting */}
      <line x1="14" y1="14" x2="14" y2="50" />
      <line x1="18" y1="14" x2="18" y2="50" />
      <line x1="22" y1="14" x2="22" y2="50" />
      <line x1="26" y1="14" x2="26" y2="50" />
      <line x1="30" y1="14" x2="30" y2="50" />
      <line x1="34" y1="14" x2="34" y2="50" />
      {/* echinus (cushion under capital) */}
      <path d="M10 14 Q24 8, 38 14" />
      {/* abacus (square cap) */}
      <rect x="6" y="6"  width="36" height="4" />
      <rect x="2" y="2"  width="44" height="4" />
    </svg>
  );
}

/** Open book with quill. Law Student mode glyph. */
export function BookQuillGlyph({ className, size = 48 }: GlyphProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {/* book pages */}
      <path d="M6 12 L22 14 V42 L6 40 Z" />
      <path d="M42 12 L26 14 V42 L42 40 Z" />
      {/* spine fold */}
      <path d="M22 14 Q24 16, 26 14 V42 Q24 44, 22 42 Z" />
      {/* page text lines */}
      <line x1="9"  y1="20" x2="19" y2="21" />
      <line x1="9"  y1="24" x2="19" y2="25" />
      <line x1="9"  y1="28" x2="19" y2="29" />
      <line x1="29" y1="21" x2="39" y2="20" />
      <line x1="29" y1="25" x2="39" y2="24" />
      <line x1="29" y1="29" x2="39" y2="28" />
      {/* quill */}
      <path d="M36 4 L18 22 L16 30 L24 28 L42 10 Z" />
      <line x1="20" y1="26" x2="38" y2="8" />
    </svg>
  );
}

/** Person silhouette with question mark. General User mode glyph. */
export function PersonQuestionGlyph({ className, size = 48 }: GlyphProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {/* head */}
      <circle cx="18" cy="14" r="6" />
      {/* shoulders */}
      <path d="M6 42 Q6 26, 18 26 Q30 26, 30 42" />
      {/* question mark, top-right */}
      <path d="M34 14 Q34 8, 40 8 Q46 8, 44 14 Q42 18, 40 18 V22" />
      <circle cx="40" cy="26" r="0.8" fill="currentColor" />
    </svg>
  );
}
