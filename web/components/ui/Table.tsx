"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ChevronUp } from "lucide-react";
import { staggerContainer, fadeUp } from "@/lib/motion";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  align?: "left" | "right" | "center";
  sortable?: boolean;
  /** Value used for sorting (defaults to the rendered cell if omitted). */
  sortValue?: (row: T) => string | number;
  render: (row: T) => React.ReactNode;
}

/** Animated, sortable data table with staggered row entrance + empty state. */
export function Table<T>({
  columns,
  rows,
  keyOf,
  empty,
  className,
}: {
  columns: Column<T>[];
  rows: T[];
  keyOf: (row: T) => string | number;
  empty?: React.ReactNode;
  className?: string;
}) {
  const [sort, setSort] = useState<{ key: string; dir: 1 | -1 } | null>(null);

  const sorted = useMemo(() => {
    if (!sort) return rows;
    const col = columns.find((c) => c.key === sort.key);
    if (!col?.sortValue) return rows;
    return [...rows].sort((a, b) => {
      const av = col.sortValue!(a);
      const bv = col.sortValue!(b);
      if (av < bv) return -1 * sort.dir;
      if (av > bv) return 1 * sort.dir;
      return 0;
    });
  }, [rows, sort, columns]);

  const toggleSort = (key: string) =>
    setSort((s) => (s?.key === key ? { key, dir: s.dir === 1 ? -1 : 1 } : { key, dir: 1 }));

  if (rows.length === 0 && empty) {
    return <div className="rounded-lg border border-subtle/12 bg-surface p-9 text-center">{empty}</div>;
  }

  return (
    <div className={cn("overflow-x-auto rounded-lg border border-subtle/12 bg-surface shadow-e1", className)}>
      <table className="w-full min-w-[640px] border-collapse text-body">
        <thead>
          <tr className="border-b border-subtle/12">
            {columns.map((c) => (
              <th
                key={c.key}
                className={cn(
                  "px-4 py-3 text-caption font-semibold uppercase tracking-wide text-ink-muted",
                  c.align === "right" && "text-right",
                  c.align === "center" && "text-center",
                  !c.align && "text-left",
                )}
              >
                {c.sortable ? (
                  <button
                    onClick={() => toggleSort(c.key)}
                    className="inline-flex items-center gap-1 hover:text-ink"
                  >
                    {c.header}
                    <motion.span
                      animate={{
                        rotate: sort?.key === c.key && sort.dir === -1 ? 180 : 0,
                        opacity: sort?.key === c.key ? 1 : 0.35,
                      }}
                      transition={{ type: "spring", stiffness: 400, damping: 26 }}
                    >
                      <ChevronUp className="h-3.5 w-3.5" />
                    </motion.span>
                  </button>
                ) : (
                  c.header
                )}
              </th>
            ))}
          </tr>
        </thead>
        <motion.tbody variants={staggerContainer(0.03)} initial="hidden" animate="show">
          {sorted.map((row) => (
            <motion.tr
              key={keyOf(row)}
              variants={fadeUp}
              className="group border-b border-subtle/8 transition-colors last:border-0 hover:bg-surface-raised/60"
            >
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={cn(
                    "px-4 py-3 align-middle",
                    c.align === "right" && "text-right",
                    c.align === "center" && "text-center",
                  )}
                >
                  {c.render(row)}
                </td>
              ))}
            </motion.tr>
          ))}
        </motion.tbody>
      </table>
    </div>
  );
}
