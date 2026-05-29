"use client";

import type { RefObject } from "react";
import { downloadChartPng, downloadCsv, printReportWindow } from "@/lib/export";
import type { ChatMessage } from "@/types";

export function DownloadBar({
  message,
  chartRef,
}: {
  message: ChatMessage;
  chartRef?: RefObject<HTMLDivElement>;
}) {
  const cols =
    message.columns?.length
      ? message.columns
      : message.rows?.[0]
        ? Object.keys(message.rows[0])
        : [];

  if (message.streaming) return null;

  const canCsv = (message.rows?.length ?? 0) > 0 && cols.length > 0;
  const canChart = Boolean(message.chartSpec && message.rows?.length);
  const canReport = Boolean(message.content || message.question);

  if (!canCsv && !canChart && !canReport) return null;

  return (
    <div className="mt-3 pt-3 border-t border-[var(--border)]">
      <div className="flex flex-wrap gap-2 mb-2">
        {canCsv && (
          <button
            type="button"
            className="ui-btn-secondary text-xs px-3 py-1.5"
            onClick={() =>
              downloadCsv(
                message.rows!,
                cols,
                `results-${message.queryId || Date.now()}.csv`
              )
            }
          >
            Download CSV
          </button>
        )}
        {canReport && (
          <>
            <button
              type="button"
              className="ui-btn-secondary text-xs px-3 py-1.5"
              onClick={() =>
                printReportWindow({
                  question: message.question || "",
                  answer: message.content,
                  sql: message.sql,
                  rows: message.rows,
                  columns: cols,
                })
              }
            >
              Print / Save PDF
            </button>
          </>
        )}
        {canChart && (
          <button
            type="button"
            className="ui-btn-secondary text-xs px-3 py-1.5"
            onClick={() => {
              const el = chartRef?.current;
              if (el) downloadChartPng(el, `chart-${message.queryId || Date.now()}.png`);
            }}
          >
            Download chart PNG
          </button>
        )}
      </div>
    </div>
  );
}
