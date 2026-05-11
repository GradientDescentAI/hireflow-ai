"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { authApi } from "@/lib/api";
import { saveSession } from "@/lib/auth";
import { Button } from "@/components/ui/Button";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});
type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormValues) => {
    setError("");
    try {
      const res = await authApi.login(data.email, data.password);
      saveSession({
        recruiter_id: res.data.recruiter_id,
        tenant_id: res.data.tenant_id,
        role: res.data.role,
        name: res.data.name,
        email: data.email,
        access_token: res.data.access_token,
      });
      // Set a cookie so the SSR middleware can detect authentication
      document.cookie = "hf_session_exists=1; path=/; max-age=86400; SameSite=Lax";
      router.push("/");
    } catch {
      setError("Invalid email or password. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-surface-container-low to-primary/5 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/10 mb-4">
            <span className="material-symbols-outlined text-primary text-3xl">psychology</span>
          </div>
          <h1 className="text-headline-lg text-on-surface">HireFlow AI</h1>
          <p className="text-body-sm text-on-surface-variant mt-1">
            AI-powered hiring for Indian SMBs
          </p>
          <div className="inline-flex items-center gap-1 mt-2 rounded-full bg-accent-ai/10 px-3 py-1 text-label-xs text-accent-ai">
            <span className="material-symbols-outlined text-[12px]">auto_awesome</span>
            Powered by Riya
          </div>
        </div>

        {/* Card */}
        <div className="bg-surface-container-lowest rounded-xl border border-outline-variant p-6 shadow-sm">
          <h2 className="text-headline-sm text-on-surface mb-6">Sign in to your account</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="label">Email address</label>
              <input
                type="email"
                autoComplete="email"
                className="input"
                placeholder="you@company.com"
                {...register("email")}
              />
              {errors.email && (
                <p className="mt-1 text-label-xs text-danger">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label className="label">Password</label>
              <input
                type="password"
                autoComplete="current-password"
                className="input"
                placeholder="••••••••"
                {...register("password")}
              />
              {errors.password && (
                <p className="mt-1 text-label-xs text-danger">{errors.password.message}</p>
              )}
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-danger/10 border border-danger/20 px-3 py-2.5 text-body-sm text-danger">
                <span className="material-symbols-outlined text-[16px]">error</span>
                {error}
              </div>
            )}

            <Button type="submit" className="w-full justify-center" loading={isSubmitting}>
              Sign in
            </Button>
          </form>
        </div>

        <p className="mt-4 text-center text-label-xs text-on-surface-variant">
          Access is by invite only.{" "}
          <a href="mailto:support@hireflow.in" className="text-primary hover:underline">
            Contact support
          </a>
        </p>
      </div>
    </div>
  );
}
