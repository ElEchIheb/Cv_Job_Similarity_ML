import { cn } from "@/lib/utils";

const base =
  "w-full rounded-lg border border-subtle/15 bg-surface-raised px-3 text-body text-ink outline-none transition-colors focus:border-accent/50 focus:ring-2 focus:ring-accent/20 placeholder:text-ink-muted disabled:opacity-60";

export function Label({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn("mb-1.5 block text-caption font-medium text-ink-secondary", className)}>{children}</span>;
}

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(base, "h-11", className)} {...props} />;
}

export function Textarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(base, "py-3 leading-relaxed resize-y", className)} {...props} />;
}

export function Select({ className, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={cn(base, "h-11 cursor-pointer", className)} {...props}>
      {children}
    </select>
  );
}

export function FieldGroup({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <label className={cn("block", className)}>
      <Label>{label}</Label>
      {children}
    </label>
  );
}
