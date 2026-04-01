/**
 * Market summary strip — horizontal row of compact stat cards.
 *
 * Shows:
 * - Total tracked stocks count
 * - Market status (trading / closed)
 * - Last refresh timestamp with countdown to next
 * - Quick "Refresh Now" action
 */

import { useEffect, useState } from "react";
import {
  BarChart3,
  TrendingUp,
  Clock,
  Zap,
} from "lucide-react";
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

  const isMarketOpen = () => {
    const h = now.getHours();
    const m = now.getMinutes();
    const mins = h * 60 + m;
    const day = now.getDay();
    if (day === 0 || day === 6) return false;
    return (mins >= 570 && mins <= 690) || (mins >= 780 && mins <= 900);
  };

  const marketOpen = isMarketOpen();

  const nextRefreshIn = () => {
    if (!lastRefresh || pollInterval <= 0) return "—";
    const elapsed = Math.floor((now.getTime() - lastRefresh.getTime()) / 1000);
    const remaining = Math.max(0, Math.floor(pollInterval / 1000) - elapsed);
    if (remaining <= 0) return "即将刷新";
    if (remaining < 60) return `${remaining}秒`;
    return `${Math.floor(remaining / 60)}分${remaining % 60}秒`;
  };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {/* Tracked stocks */}
      <div className="stat-card group">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-medium text-content-muted uppercase tracking-wider">
              追踪股票
            </p>
            <p className="text-2xl font-bold text-content-primary mt-1 tabular-nums">
              {stockCount}
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-primary/8 flex items-center justify-center
                          group-hover:bg-primary/12 transition-colors duration-300">
            <BarChart3 className="w-5 h-5 text-primary" />
          </div>
        </div>
        <p className="text-[10px] text-content-muted mt-2">
          {stockCount > 0 ? "实时数据追踪中" : "点击右上角添加股票"}
        </p>
      </div>

      {/* Market status */}
      <div className="stat-card group">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-medium text-content-muted uppercase tracking-wider">
              市场状态
            </p>
            <p className={`text-2xl font-bold mt-1 ${
              marketOpen ? "text-emerald-600" : "text-content-secondary"
            }`}>
              {marketOpen ? "交易中" : "已休市"}
            </p>
          </div>
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center
                           transition-colors duration-300
                           ${marketOpen
                             ? "bg-emerald-50 group-hover:bg-emerald-100"
                             : "bg-gray-100 group-hover:bg-gray-150"
                           }`}>
            <TrendingUp className={`w-5 h-5 ${
              marketOpen ? "text-emerald-600" : "text-gray-400"
            }`} />
          </div>
        </div>
        <p className="text-[10px] text-content-muted mt-2">
          沪深A股 · {now.toLocaleDateString("zh-CN", {
            weekday: "short",
            month: "numeric",
            day: "numeric",
          })}
        </p>
      </div>

      {/* Last refresh */}
      <div className="stat-card group">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-medium text-content-muted uppercase tracking-wider">
              上次刷新
            </p>
            <p className="text-2xl font-bold text-content-primary mt-1 tabular-nums">
              {lastRefresh
                ? lastRefresh.toLocaleTimeString("zh-CN", {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })
                : "—"}
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center
                          group-hover:bg-amber-100 transition-colors duration-300">
            <Clock className="w-5 h-5 text-amber-600" />
          </div>
        </div>
        <p className="text-[10px] text-content-muted mt-2">
          {pollInterval > 0
            ? `下次刷新: ${nextRefreshIn()}`
            : "自动刷新已关闭"}
        </p>
      </div>

      {/* Quick refresh */}
      <div
        className="stat-card group cursor-pointer hover:ring-primary/30 active:scale-[0.98] transition-all duration-200"
        onClick={onRefresh}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") onRefresh();
        }}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-medium text-content-muted uppercase tracking-wider">
              数据源
            </p>
            <p className="text-2xl font-bold text-primary mt-1">
              {refreshing ? "刷新中" : "AkShare"}
            </p>
          </div>
          <div className={`w-10 h-10 rounded-xl bg-primary/8 flex items-center justify-center
                           group-hover:bg-primary/15 transition-colors duration-300
                           ${refreshing ? "animate-pulse" : ""}`}>
            <Zap className={`w-5 h-5 text-primary ${
              refreshing ? "animate-spin" : ""
            }`} />
          </div>
        </div>
        <p className="text-[10px] text-content-muted mt-2">
          {schedulerStatus?.running
            ? `每 ${schedulerStatus.refresh_interval_seconds}s 自动刷新`
            : "点击手动拉取最新行情"}
        </p>
      </div>
    </div>
  );
}
