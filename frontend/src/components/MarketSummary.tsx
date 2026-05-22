/**
 * Compact market summary bar — single horizontal strip.
 *
 * Shows in a condensed row:
 * - Total tracked stocks count
 * - Market status indicators (CN + HK + US)
 * - Last refresh timestamp with countdown
 * - Data source + refresh button
 */

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import type { SchedulerStatus } from "../types/stock";

// ── Props ────────────────────────────────────────────────────────────

interface MarketSummaryProps {
  stockCount: number;
  schedulerStatus: SchedulerStatus | null;
  lastRefresh: Date | null;
  refreshing: boolean;
  pollInterval: number;
  onRefresh: () => void;
}

// ── Component ────────────────────────────────────────────────────────

export default function MarketSummary({
  stockCount,
  schedulerStatus,
  lastRefresh,
  refreshing,
  pollInterval,
  onRefresh,
}: MarketSummaryProps) {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const cnOpen = schedulerStatus?.market_status?.cn_open ?? false;
  const usOpen = schedulerStatus?.market_status?.us_open ?? false;
  const hkOpen = schedulerStatus?.market_status?.hk_open ?? false;

  const nextRefreshIn = () => {
    if (!lastRefresh || pollInterval <= 0) return "—";
    const elapsed = Math.floor((now.getTime() - lastRefresh.getTime()) / 1000);
    const remaining = Math.max(0, Math.floor(pollInterval / 1000) - elapsed);
    if (remaining <= 0) return "即将刷新";
    if (remaining < 60) return `${remaining}s`;
    return `${Math.floor(remaining / 60)}m${remaining % 60}s`;
  };

  const refreshTimeStr = lastRefresh
    ? lastRefresh.toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "—";

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2.5 rounded-xl
                    bg-white/60 backdrop-blur-sm border border-border-subtle text-xs">
      {/* Tracked count */}
      <div className="flex items-center gap-1.5">
        <span className="text-content-muted">追踪</span>
        <span className="font-semibold text-content-primary tabular-nums">{stockCount}</span>
        <span className="text-content-muted">只</span>
      </div>

      <span className="text-border-subtle">|</span>

      {/* Market status dots */}
      <div className="flex items-center gap-3">
        <MarketDot label="A股" open={cnOpen} color="emerald" />
        <MarketDot label="港股" open={hkOpen} color="orange" />
        <MarketDot label="美股" open={usOpen} color="blue" />
      </div>

      <span className="text-border-subtle">|</span>

      {/* Last refresh + countdown */}
      <div className="flex items-center gap-1.5">
        <span className="text-content-muted">刷新</span>
        <span className="font-mono font-medium text-content-primary tabular-nums">
          {refreshTimeStr}
        </span>
        {pollInterval > 0 && (
          <span className="text-content-muted">
            ({nextRefreshIn()})
          </span>
        )}
      </div>

      <span className="text-border-subtle">|</span>

      {/* Data source + refresh action */}
      <div className="flex items-center gap-1.5">
        <span className="text-content-muted">数据源:</span>
        <span className="font-medium text-primary/80">Tencent</span>
        <button
          onClick={onRefresh}
          disabled={refreshing}
          className="ml-1 p-1 rounded-md hover:bg-primary/10 transition-colors duration-200
                     disabled:opacity-50 disabled:cursor-not-allowed"
          title="立即刷新"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-primary ${refreshing ? "animate-spin" : ""}`} />
        </button>
      </div>
    </div>
  );
}

// ── Market Status Dot ────────────────────────────────────────────────

interface MarketDotProps {
  label: string;
  open: boolean;
  color: "emerald" | "orange" | "blue";
}

const DOT_COLORS = {
  emerald: { on: "bg-emerald-500", off: "bg-gray-400" },
  orange: { on: "bg-orange-500", off: "bg-gray-400" },
  blue: { on: "bg-blue-500", off: "bg-gray-400" },
};

const LABEL_COLORS = {
  emerald: { on: "text-emerald-700", off: "text-content-muted" },
  orange: { on: "text-orange-700", off: "text-content-muted" },
  blue: { on: "text-blue-700", off: "text-content-muted" },
};

function MarketDot({ label, open, color }: MarketDotProps) {
  return (
    <div className="flex items-center gap-1">
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          open ? `${DOT_COLORS[color].on} animate-pulse` : DOT_COLORS[color].off
        }`}
      />
      <span className={`text-[11px] font-medium ${
        open ? LABEL_COLORS[color].on : LABEL_COLORS[color].off
      }`}>
        {label}
      </span>
    </div>
  );
}
