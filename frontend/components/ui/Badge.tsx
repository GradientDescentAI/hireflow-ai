import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "success" | "warning" | "danger" | "ai" | "outline";
}

const variants = {
  default: "bg-primary/10 text-primary",
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  danger: "bg-danger/10 text-danger",
  ai: "bg-accent-ai/10 text-accent-ai",
  outline: "border border-outline-variant text-on-surface-variant bg-transparent",
};

export function Badge({ children, className, variant = "default" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-label-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export function AiBadge({ label = "AI" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-accent-ai/10 px-2 py-0.5 text-label-xs font-medium text-accent-ai">
      <span className="material-symbols-outlined text-[12px]">auto_awesome</span>
      {label}
    </span>
  );
}
