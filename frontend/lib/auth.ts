"use client";

// Lightweight client-side auth — stores JWT in sessionStorage.
// Replace with next-auth in a future pass for SSR-safe session handling.

export interface Session {
  recruiter_id: string;
  tenant_id: string;
  role: string;
  name: string;
  email: string;
  access_token: string;
}

const KEY = "hf_session";

export function saveSession(session: Session): void {
  sessionStorage.setItem(KEY, JSON.stringify(session));
  sessionStorage.setItem("hf_token", session.access_token);
}

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  sessionStorage.removeItem(KEY);
  sessionStorage.removeItem("hf_token");
  // Clear the SSR-readable auth cookie
  if (typeof document !== "undefined") {
    document.cookie = "hf_session_exists=; path=/; max-age=0";
  }
}

export function isAdmin(session: Session | null): boolean {
  return session?.role === "admin" || session?.role === "super_admin";
}
