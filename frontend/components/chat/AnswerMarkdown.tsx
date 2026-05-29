"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import { normalizeCurrencyDisplay } from "@/lib/formatters";

export function AnswerMarkdown({ content }: { content: string }) {
  if (!content?.trim()) return null;
  const display = normalizeCurrencyDisplay(content);

  return (
    <div className="answer-prose text-sm leading-relaxed">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
        {display}
      </ReactMarkdown>
    </div>
  );
}
