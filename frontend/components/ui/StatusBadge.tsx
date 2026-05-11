import { cn, STATUS_COLORS, STATUS_LABELS } from "@/lib/utils";

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-label-xs font-medium",
        STATUS_COLORS[status] ?? "bg-neutral-200 text-neutral-700"
      )}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}
