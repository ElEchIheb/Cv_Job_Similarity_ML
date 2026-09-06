"use client";

import { forwardRef } from "react";
import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

interface CardProps extends Omit<HTMLMotionProps<"div">, "ref"> {
  /** Adds a hover lift (translateY + shadow growth). */
  interactive?: boolean;
  /** Elevation level 1–4. */
  elevation?: 1 | 2 | 3 | 4;
  /** Frosted-glass surface. */
  glass?: boolean;
}

const shadows = { 1: "shadow-e1", 2: "shadow-e2", 3: "shadow-e3", 4: "shadow-e4" } as const;

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { interactive, elevation = 2, glass, className, children, ...props },
  ref,
) {
  return (
    <motion.div
      ref={ref}
      whileHover={interactive ? { y: -4 } : undefined}
      transition={{ type: "spring", stiffness: 300, damping: 24 }}
      className={cn(
        "relative rounded-lg border border-subtle/12",
        glass ? "glass" : "bg-surface",
        shadows[elevation],
        interactive && "cursor-pointer transition-shadow hover:shadow-e4 hover:border-accent/30",
        className,
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
});

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex items-start justify-between gap-4 p-5 pb-3", className)} {...props} />;
}
export function CardBody({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-5 pt-2", className)} {...props} />;
}
export function CardFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex items-center gap-3 p-5 pt-3 border-t border-subtle/10", className)} {...props} />;
}
export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("font-display text-h4 font-semibold text-ink", className)} {...props} />;
}
