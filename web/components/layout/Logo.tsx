import { cn } from "@/lib/utils";

/** NeuralHire logo lockup — a neural node glyph + wordmark. */
export function Logo({ compact = false, className }: { compact?: boolean; className?: string }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <span className="relative grid h-9 w-9 place-items-center">
        <svg viewBox="0 0 40 40" className="h-9 w-9" aria-hidden>
          <defs>
            <linearGradient id="logo-grad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7c5cff" />
              <stop offset="100%" stopColor="#22cfee" />
            </linearGradient>
          </defs>
          <rect x="2" y="2" width="36" height="36" rx="11" fill="url(#logo-grad)" opacity="0.14" />
          <rect x="2" y="2" width="36" height="36" rx="11" fill="none" stroke="url(#logo-grad)" strokeWidth="1.5" />
          <g stroke="url(#logo-grad)" strokeWidth="1.6" fill="url(#logo-grad)">
            <circle cx="13" cy="14" r="2.4" />
            <circle cx="27" cy="11" r="2.4" />
            <circle cx="20" cy="22" r="2.6" />
            <circle cx="13" cy="29" r="2.4" />
            <circle cx="28" cy="28" r="2.4" />
            <line x1="13" y1="14" x2="20" y2="22" opacity="0.6" />
            <line x1="27" y1="11" x2="20" y2="22" opacity="0.6" />
            <line x1="20" y1="22" x2="13" y2="29" opacity="0.6" />
            <line x1="20" y1="22" x2="28" y2="28" opacity="0.6" />
          </g>
        </svg>
      </span>
      {!compact && (
        <span className="font-display text-h4 font-semibold tracking-tight text-ink">
          Neural<span className="text-gradient">Hire</span>
        </span>
      )}
    </div>
  );
}
