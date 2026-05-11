import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "outline";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

const variants = {
  primary: "bg-primary text-on-primary hover:bg-primary-container disabled:opacity-50",
  secondary: "bg-surface-container text-on-surface hover:bg-surface-container-high",
  ghost: "text-on-surface hover:bg-surface-container",
  danger: "bg-danger text-white hover:bg-red-700",
  outline: "border border-outline-variant text-on-surface hover:bg-surface-container",
};

const sizes = {
  sm: "px-3 py-1.5 text-label-xs",
  md: "px-4 py-2 text-body-sm",
  lg: "px-6 py-2.5 text-body-md",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", loading, children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center gap-2 rounded font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {loading && (
        <span className="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
      )}
      {children}
    </button>
  )
);
Button.displayName = "Button";
