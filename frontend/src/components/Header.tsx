/**
 * Application header with branding, market status, controls, and settings.
 *
 * Features:
 * - Logo and app title
 * - Real-time scheduler status indicator with pulse animation
 * - "Add Stock" primary CTA button
 * - Last refresh timestamp with countdown
 * - Refresh button with loading spinner
 * - Settings dropdown for poll interval configuration
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  RefreshCw,
  Plus,
  Settings,
  Activity,
  Clock,
  ChevronDown,
} from "lucide-react";
import type { ConfigUpdateRequest, SchedulerStatus } from "../types/stock";

// ── Props ────────────────────────────────────────────────────────────

interface HeaderProps {
  schedulerStatus: SchedulerStatus | null;
  lastRefresh: Date | null;
  refreshing: boolean;
  stockCount: number;
  pollInterval: number;
  onRefresh: () => void;
  onAddStock: () => void;
  onPollIntervalChange: (ms: number) => void;
  onUpdateConfig: (config: ConfigUpdateRequest) => Promise<boolean>;
}

// ── Poll interval presets ────────────────────────────────────────────

const INTERVAL_OPTIONS = [
  { label: "10秒", value: 10_000 },
  { label: "30秒", value: 30_000 },
  { label: "1分钟", value: 60_000 },
  { label: "5分钟", value: 300_000 },
  { label: "关闭自动刷新", value: 0 },
];

// ── Component ────────────────────────────────────────────────────────

export default function Header({
  schedulerStatus,
  lastRefresh,
  refreshing,
  stockCount,
  pollInterval,
  onRefresh,
  onAddStock,
  onPollIntervalChange,
  onUpdateConfig,
}: HeaderProps) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const settingsRef = useRef<HTMLDivElement>(null);

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Close settings dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (settingsRef.current && !settingsRef.current.contains(e.target as Node)) {
        setSettingsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isMarketHours = useCallback(() => {
    const h = currentTime.getHours();
    const m = currentTime.getMinutes();
    const mins = h * 60 + m;
    const day = currentTime.getDay();
    if (day === 0 || day === 6) return false;
    return (mins >= 570 && mins <= 690) || (mins >= 780 && mins <= 900);
  }, [currentTime]);

  const marketOpen = isMarketHours();

  const formatRefreshTime = () => {
    if (!lastRefresh) return "暂无数据";
    const diff = Math.floor((currentTime.getTime() - lastRefresh.getTime()) / 1000);
    if (diff < 5) return "刚刚更新";
    if (diff < 60) return `${diff}秒前`;
    if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
    return lastRefresh.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const currentIntervalLabel =
    INTERVAL_OPTIONS.find((o) => o.value === pollInterval)?.label ?? "自定义";

  return (
    <header className="header-glass sticky top-0 z-50 border-b border-white/10">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* ── Left: Logo + Market Status ── */}
        <div className="flex items-center gap-4">
          {/* Logo */}
          <div className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-primary-dark
                            flex items-center justify-center shadow-lg shadow-primary/20
                            group-hover:shadow-primary/40 transition-shadow duration-300">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-content-primary tracking-tight leading-tight">
                StockTracker
              </h1>
              <p className="text-[10px] text-content-muted leading-none tracking-wider uppercase">
                A股实时追踪
              </p>
            </div>
          </div>

          {/* Divider */}
          <div className="hidden sm:block w-px h-8 bg-gray-200" />

          {/* Market Status */}
          <div className="hidden sm:flex items-center gap-3">
            <div
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
                ${marketOpen
                  ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
                  : "bg-gray-100 text-gray-500 ring-1 ring-gray-200"
                }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  marketOpen ? "bg-emerald-500 animate-pulse" : "bg-gray-400"
                }`}
              />
              {marketOpen ? "交易中" : "已休市"}
            </div>

            {schedulerStatus && (
              <div
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
                  ${schedulerStatus.running
                    ? "bg-blue-50 text-blue-700 ring-1 ring-blue-200"
                    : "bg-amber-50 text-amber-700 ring-1 ring-amber-200"
                  }`}
              >
                <Activity className="w-3 h-3" />
                {schedulerStatus.running ? "调度运行中" : "调度已暂停"}
              </div>
            )}
          </div>
        </div>

        {/* ── Right: Actions ── */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Refresh time badge */}
          <div className="hidden md:flex items-center gap-1.5 text-xs text-content-muted">
            <Clock className="w-3.5 h-3.5" />
            <span>{formatRefreshTime()}</span>
          </div>

          {/* Refresh button */}
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                       text-content-secondary bg-white ring-1 ring-gray-200
                       hover:bg-gray-50 hover:ring-gray-300
                       active:bg-gray-100
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all duration-200 cursor-pointer"
            title="从AkShare拉取最新数据"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`}
            />
            <span className="hidden sm:inline">
              {refreshing ? "刷新中" : "刷新"}
            </span>
          </button>

          {/* Add Stock button */}
          <button
            onClick={onAddStock}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold
                       text-white bg-gradient-to-r from-primary to-primary-dark
                       hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-[1px]
                       active:translate-y-0 active:shadow-md
                       transition-all duration-200 cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" strokeWidth={2.5} />
            <span>添加股票</span>
          </button>

          {/* Settings dropdown */}
          <div className="relative" ref={settingsRef}>
            <button
              onClick={() => setSettingsOpen(!settingsOpen)}
              className={`inline-flex items-center gap-1 p-2 rounded-lg text-content-muted
                         hover:bg-gray-100 hover:text-content-secondary
                         transition-all duration-200 cursor-pointer
                         ${settingsOpen ? "bg-gray-100 text-content-secondary" : ""}`}
              title="设置"
            >
              <Settings className="w-4 h-4" />
              <ChevronDown
                className={`w-3 h-3 transition-transform duration-200 ${
                  settingsOpen ? "rotate-180" : ""
                }`}
              />
            </button>

            {settingsOpen && (
              <div
                className="absolute right-0 top-full mt-2 w-56 bg-white rounded-xl
                            shadow-xl shadow-black/8 ring-1 ring-black/5
                            animate-in fade-in slide-in-from-top-2 duration-200 z-50"
              >
                <div className="px-3 py-2 border-b border-gray-100">
                  <p className="text-xs font-semibold text-content-primary">
                    自动刷新间隔
                  </p>
                  <p className="text-[10px] text-content-muted mt-0.5">
                    当前: {currentIntervalLabel}
                  </p>
                </div>
                <div className="p-1.5">
                  {INTERVAL_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => {
                        onPollIntervalChange(opt.value);
                        setSettingsOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg text-xs cursor-pointer
                                  transition-colors duration-150
                                  ${pollInterval === opt.value
                                    ? "bg-primary/8 text-primary font-medium"
                                    : "text-content-secondary hover:bg-gray-50"
                                  }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                {/* Market hours only toggle */}
                <div className="px-3 py-2.5 border-t border-gray-100">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold text-content-primary">
                        仅交易时段刷新
                      </p>
                      <p className="text-[10px] text-content-muted mt-0.5">
                        休市时跳过数据拉取
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        const newValue = !(schedulerStatus?.market_hours_only ?? false);
                        onUpdateConfig({ market_hours_only: newValue });
                      }}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full
                                  transition-colors duration-200 focus:outline-none cursor-pointer
                                  ${schedulerStatus?.market_hours_only
                                    ? "bg-primary"
                                    : "bg-gray-300"
                                  }`}
                      role="switch"
                      aria-checked={schedulerStatus?.market_hours_only ?? false}
                      aria-label="仅交易时段刷新"
                    >
                      <span
                        className={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow-sm
                                    transform transition-transform duration-200
                                    ${schedulerStatus?.market_hours_only
                                      ? "translate-x-[18px]"
                                      : "translate-x-[3px]"
                                    }`}
                      />
                    </button>
                  </div>
                </div>
                <div className="px-3 py-2 border-t border-gray-100">
                  <div className="flex items-center justify-between text-[10px] text-content-muted">
                    <span>追踪 {stockCount} 只股票</span>
                    <span>
                      {currentTime.toLocaleTimeString("zh-CN", {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
