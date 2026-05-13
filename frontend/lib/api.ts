import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// Attach Bearer token on every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = sessionStorage.getItem("hf_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Redirect to /login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      sessionStorage.removeItem("hf_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ───────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; recruiter_id: string; tenant_id: string; role: string; name: string }>(
      "/auth/login",
      { email, password }
    ),
};

// ── Jobs ───────────────────────────────────────────────────────────────────────
export const jobsApi = {
  list: () => api.get("/jobs"),
  get: (id: string) => api.get(`/jobs/${id}`),
  create: (body: { raw_jd_text?: string; raw_jd_url?: string }) => api.post("/jobs", body),
  update: (id: string, body: Partial<unknown>) => api.patch(`/jobs/${id}`, body),
  confirm: (id: string) => api.post(`/jobs/${id}/confirm`),
  distribute: (id: string, body: { channels: string[]; channel_config: Record<string, unknown> }) =>
    api.post(`/jobs/${id}/distribute`, body),
  score: (id: string) => api.post(`/jobs/${id}/score`),
  uploadCV: (id: string, formData: FormData) =>
    api.post(`/jobs/${id}/upload-cv`, formData, {
      // Let axios set the correct Content-Type boundary for multipart
      headers: { "Content-Type": undefined },
    }),
  applications: (id: string, params?: { channel?: string; status?: string }) =>
    api.get(`/jobs/${id}/applications`, { params }),
  shortlist: (id: string) => api.get(`/jobs/${id}/shortlist`),
  linkedinDraft: (id: string) => api.get<{ post_body: string; character_count: number }>(`/jobs/${id}/linkedin-draft`),
  audit: (id: string) => api.get(`/jobs/${id}/audit`),
  posts: (id: string) => api.get(`/jobs/${id}/posts`),
};

// ── Shortlist ──────────────────────────────────────────────────────────────────
export const shortlistApi = {
  update: (
    scoreId: string,
    body: {
      recruiter_status?: "approved" | "rejected" | "hold";
      nps_thumb?: boolean;
      override_score?: number;
      override_reason?: string;
    }
  ) => api.patch(`/shortlist/${scoreId}`, body),
};

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsApi = {
  dashboard: () => api.get("/analytics/dashboard"),
};

// ── Personas ──────────────────────────────────────────────────────────────────
export const personasApi = {
  health: () => api.get("/personas/health"),
};

// ── Share ─────────────────────────────────────────────────────────────────────
export const shareApi = {
  get: (token: string) => api.get(`/share/${token}`),
};
