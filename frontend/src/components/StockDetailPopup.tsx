/**
 * Stock detail popup panel.
 *
 * Displays key financial metrics for a stock when the user clicks a row
 * in the StockTable. Currently supports CN (A-share) stocks with:
 * - Price range (today + 52-week)
 * - Valuation metrics (P/E, P/B)
 * - Market data (cap, volume, turnover)
 *
 * Uses a modal overlay with smooth animations.
 */

import { useEffect } from "react";
import { X, TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { Stock } from "../types/stock";

// ── Props ────────────────────────────────────────────────────────────

interface StockDetailPopupProps {
  stock: Stock | null;
  open: boolean;
  onClose: () => void;
}

// ── Formatters ───────────────────────────────────────────────────────

function fmtPrice(n: number | null): string {
  if (n === null || n === undefined) return "—";
  return n.toFixed(2);
}

function fmtPercent(n: number | null): string {
  if (n === null || n === undefined) return "—";
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(2)}%`;
}

function fmtLargeNumber(n: number | null): string {
  if (n === null || n === undefined) return "—";
  if (n >= 1e12) return `${(n / 1e12).toFixed(2)}万亿`;
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿`;
  if (n >= 1e4) return `${(n / 1e4).toFixed(0)}万`;
  return n.toLocaleString("zh-CN");
}

function fmtVolume(n: number | null): string {
  if (n === null || n === undefined) return "—";
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿`;
  if (n >= 1e4) return `${(n / 1e4).toFixed(0)}万`;
  return n.toLocaleString("zh-CN");
}

function fmtRatio(n: number | null): string {
  if (n === null || n === undefined) return "—";
  return n.toFixed(2);
}

// ── Helper: 52-week position percentage ──────────────────────────────

function get52wPosition(current: number | null, low: number | null, high: number | null): number | null {
  if (current === null || low === null || high === null) return null;
  if (high === low) return 50;
  return ((current - low) / (high - low)) * 100;
}

// ── Component ────────────────────────────────────────────────────────

export default function StockDetailPopup({ stock, open, onClose }: StockDetailPopupProps) {
  // Keyboard: Escape to close
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && open) onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open || !stock) return null;

  const changeColor =
    stock.change_percent === null || stock.change_percent === 0
      ? "text-content-secondary"
      : stock.change_percent > 0
        ? "text-stock-up"
        : "text-stock-down";

  const TrendIcon =
    stock.change_percent === null || stock.change_percent === 0
      ? Minus
      : stock.change_percent > 0
        ? TrendingUp
        : TrendingDown;

  const position52w = get52wPosition(stock.current_price, stock.low_52w, stock.high_52w);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm
                    animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl shadow-black/10
                    animate-in fade-in zoom-in-95 slide-in-from-bottom-4 duration-300
                    max-h-[90vh] overflow-y-auto"
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 p-1.5 rounded-lg text-content-muted
                     hover:bg-gray-100 hover:text-content-secondary
                     transition-colors cursor-pointer z-10"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header: Stock identity + price */}
        <div className="px-6 pt-6 pb-4 border-b border-gray-100">
          <div className="flex items-start gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-red-50 to-red-100
                            flex items-center justify-center flex-shrink-0">
              <TrendIcon className={`w-5 h-5 ${changeColor}`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-content-primary truncate">
                  {stock.name ?? stock.symbol}
                </h2>
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold
                                  bg-red-50 text-red-600 ring-1 ring-red-200/60">
                  CN
                </span>
              </div>
              <p className="text-xs text-content-muted font-mono mt-0.5">
                {stock.symbol}
              </p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className={`text-2xl font-bold tabular-nums ${changeColor}`}>
                {fmtPrice(stock.current_price)}
              </p>
              <div className="flex items-center justify-end gap-2 mt-0.5">
                <span className={`text-sm font-mono font-semibold ${changeColor}`}>
                  {fmtPercent(stock.change_percent)}
                </span>
                <span className={`text-xs font-mono ${changeColor}`}>
                  {stock.change_amount !== null
                    ? `${stock.change_amount > 0 ? "+" : ""}${stock.change_amount.toFixed(2)}`
                    : "—"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Body: Metric sections */}
        <div className="px-6 py-5 space-y-5">

          {/* ── 52-Week Range ── */}
          <section>
            <h3 className="text-[11px] font-semibold text-content-muted uppercase tracking-wider mb-3">
              52 周价格区间
            </h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono text-stock-down">{fmtPrice(stock.low_52w)}</span>
                <span className="text-content-muted">当前位置</span>
                <span className="font-mono text-stock-up">{fmtPrice(stock.high_52w)}</span>
              </div>
              {/* Visual bar */}
              <div className="relative h-2 rounded-full bg-gray-100 overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-stock-down/30 via-yellow-200/50 to-stock-up/30"
                  style={{ width: "100%" }}
                />
                {position52w !== null && (
                  <div
                    className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full
                               bg-white border-2 border-primary shadow-sm"
                    style={{ left: `calc(${Math.min(Math.max(position52w, 2), 98)}% - 6px)` }}
                  />
                )}
              </div>
              {position52w !== null && (
                <p className="text-[10px] text-content-muted text-center">
                  当前价格位于 52 周区间的 {position52w.toFixed(0)}% 位置
                </p>
              )}
            </div>
          </section>

          {/* ── Today's Range ── */}
          <section>
            <h3 className="text-[11px] font-semibold text-content-muted uppercase tracking-wider mb-3">
              今日行情
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <MetricItem label="开盘价" value={fmtPrice(stock.open_price)} />
              <MetricItem label="昨收价" value={fmtPrice(stock.close_price)} />
              <MetricItem label="最高价" value={fmtPrice(stock.high_price)} color="text-stock-up" />
              <MetricItem label="最低价" value={fmtPrice(stock.low_price)} color="text-stock-down" />
              <MetricItem label="振幅" value={stock.amplitude !== null ? `${stock.amplitude.toFixed(2)}%` : "—"} />
              <MetricItem label="换手率" value={stock.turnover_rate !== null ? `${stock.turnover_rate.toFixed(2)}%` : "—"} />
            </div>
          </section>

          {/* ── Valuation ── */}
          <section>
            <h3 className="text-[11px] font-semibold text-content-muted uppercase tracking-wider mb-3">
              估值指标
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <MetricItem label="市盈率 (P/E)" value={fmtRatio(stock.pe_ratio)} />
              <MetricItem label="市净率 (P/B)" value={fmtRatio(stock.pb_ratio)} />
            </div>
          </section>

          {/* ── Market Data ── */}
          <section>
            <h3 className="text-[11px] font-semibold text-content-muted uppercase tracking-wider mb-3">
              市场数据
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <MetricItem label="总市值" value={fmtLargeNumber(stock.market_cap)} />
              <MetricItem label="流通市值" value={fmtLargeNumber(stock.circulating_market_cap)} />
              <MetricItem label="成交量" value={fmtVolume(stock.volume)} />
              <MetricItem label="成交额" value={fmtLargeNumber(stock.turnover)} />
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
          <p className="text-[10px] text-content-muted">
            数据来源: Tencent Finance · 仅供参考
          </p>
          {stock.last_trade_time && (
            <p className="text-[10px] text-content-muted font-mono tabular-nums">
              更新: {formatTime(stock.last_trade_time)}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────────

interface MetricItemProps {
  label: string;
  value: string;
  color?: string;
}

function MetricItem({ label, value, color }: MetricItemProps) {
  return (
    <div className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-surface-secondary/60">
      <span className="text-xs text-content-muted">{label}</span>
      <span className={`text-sm font-mono font-semibold ${color ?? "text-content-primary"}`}>
        {value}
      </span>
    </div>
  );
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "—";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
