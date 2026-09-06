import type { Transition, Variants } from "framer-motion";

/**
 * Shared motion language. Spring physics over linear easing; durations kept in
 * the 150–400ms band for micro-interactions, ~1.2s reserved for the score reveal.
 */

export const spring: Transition = { type: "spring", stiffness: 260, damping: 26, mass: 0.9 };
export const springSoft: Transition = { type: "spring", stiffness: 180, damping: 24 };
export const springSnappy: Transition = { type: "spring", stiffness: 420, damping: 30 };
export const easeOutExpo: Transition = { duration: 0.4, ease: [0.16, 1, 0.3, 1] };

/** Fade + slide-up used for hero, stat cards, table rows. */
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: spring },
};

/** Container that staggers its children ~40ms apart. */
export const staggerContainer = (stagger = 0.04, delay = 0): Variants => ({
  hidden: {},
  show: {
    transition: { staggerChildren: stagger, delayChildren: delay },
  },
});

/** Route transition: cross-fade + slight slide. */
export const pageTransition: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.18, ease: "easeIn" } },
};

/** Modal / overlay spring entrance. */
export const overlayScale: Variants = {
  hidden: { opacity: 0, scale: 0.96, y: 8 },
  show: { opacity: 1, scale: 1, y: 0, transition: springSnappy },
  exit: { opacity: 0, scale: 0.98, y: 4, transition: { duration: 0.14 } },
};

/** Verdict badge "the verdict is in" beat — scale-in with a glow pulse. */
export const verdictReveal: Variants = {
  hidden: { opacity: 0, scale: 0.6 },
  show: {
    opacity: 1,
    scale: 1,
    transition: { type: "spring", stiffness: 340, damping: 18, delay: 0.05 },
  },
};
