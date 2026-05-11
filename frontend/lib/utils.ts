import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatDistanceToNow, parseISO } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function relativeTime(isoString: string): string {
  try {
    return formatDistanceToNow(parseISO(isoString), { addSuffix: true });
  } catch {
    return isoString;
  }
}

export function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function scoreColor(score: number): string {
  if (score >= 80) return "text-success";
  if (score >= 60) return "text-warning";
  return "text-danger";
}

export function scoreBg(score: number): string {
  if (score >= 80) return "bg-success/10 text-success";
  if (score >= 60) return "bg-warning/10 text-warning";
  return "bg-danger/10 text-danger";
}

export const STATUS_LABELS: Record<string, string> = {
  draft: "Draft",
  extraction_complete: "Ready to Review",
  approved: "Approved",
  posted: "Posted",
  collecting: "Collecting",
  scoring: "Scoring",
  shortlisted: "Shortlisted",
  closed: "Closed",
};

export const STATUS_COLORS: Record<string, string> = {
  draft: "bg-neutral-200 text-neutral-700",
  extraction_complete: "bg-primary/10 text-primary",
  approved: "bg-primary/20 text-primary",
  posted: "bg-indigo-100 text-indigo-700",
  collecting: "bg-cyan-100 text-cyan-700",
  scoring: "bg-warning/10 text-warning",
  shortlisted: "bg-success/10 text-success",
  closed: "bg-neutral-200 text-neutral-700",
};

export const CHANNEL_ICONS: Record<string, string> = {
  linkedin: "work",
  email: "email",
  whatsapp: "chat",
  naukri: "business_center",
  indeed: "search",
  telegram: "send",
};
