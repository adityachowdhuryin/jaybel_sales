"use client";

import type { HTMLAttributes, ReactNode } from "react";

type Tone = "default" | "muted";

const TONE_CLASS: Record<Tone, string> = {
  default: "ui-card",
  muted: "ui-card-muted",
};

export function Card({
  children,
  tone = "default",
  className = "",
  ...props
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode; tone?: Tone }) {
  return (
    <div {...props} className={`${TONE_CLASS[tone]} ${className}`.trim()}>
      {children}
    </div>
  );
}

