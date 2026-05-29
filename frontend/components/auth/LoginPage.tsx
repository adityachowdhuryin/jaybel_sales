"use client";

import { useAuth } from "@/hooks/useAuth";

export function LoginPage() {
  const { signIn } = useAuth();

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-[var(--bg)] px-4 overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(14,165,233,0.14),transparent_35%),radial-gradient(circle_at_85%_15%,rgba(109,40,217,0.14),transparent_35%),radial-gradient(circle_at_50%_100%,rgba(16,185,129,0.10),transparent_30%)]" />
      <div className="relative w-full max-w-md rounded-xl border border-[var(--border)] bg-[var(--panel)] p-8 shadow-panel">
        <h1 className="text-2xl font-semibold text-[var(--text)]">
          Jaybel Sales Analytics
        </h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Sign in with your Google account to access sales analytics powered by
          Vertex AI Agent Engine.
        </p>
        <button type="button" onClick={() => signIn()} className="mt-6 flex w-full ui-btn-primary py-3">
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
