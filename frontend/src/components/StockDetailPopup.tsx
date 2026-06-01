/**
 * Stock detail popup panel.
 *
 * Displays key financial metrics for a stock when the user clicks a row
 * in the StockTable. Currently supports CN (A-share) stocks with:
 * - 52-week price trend chart (weekly close prices)
 * - Valuation metrics (P/E, P/B)
 * - Market data (cap, volume, turnover)
 *
 * Uses a modal overlay with smooth animations.
 */

import { useEffect, useState } from "react";
import { X, TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from "recharts";
import type { Stock } from "../types/stock";
import { fetchStockKline, type KlinePoint } from "../services/api";

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

// ── Component ────────────────────────────────────────────────────────

export default function StockDetailPopup({ stock, open, onClose }: StockDetailPopupProps) {
  const [klineData, setKlineData] = useState<KlinePoint[]>([]);
  const [klineLoading, setKlineLoading] = useState(false);

  // Keyboard: Escape to close
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && open) onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  // Fetch K-line data when popup opens
  useEffect(() => {
    if (!open || !stock) {
      setKlineData([]);
      return;
    }
    let cancelled = false;
    setKlineLoading(true);
    fetchStockKline(stock.symbol)
      .then((res) => {
        if (!cancelled) setKlineData(res.points);
      })
      .catch(() => {
        if (!cancelled) setKlineData([]);
      })
      .finally(() => {
        if (!cancelled) setKlineLoading(false);
      });
    return () => { cancelled = true; };
  }, [open, stock]);

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

          {/* ── 52-Week Price Trend Chart ── */}
          <section>
            <h3 className="text-[11px] font-semibold text-content-muted uppercase tracking-wider mb-3">
              52 周价格走势
            </h3>
            {klineLoading ? (
              <div className="h-[160px] flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
              </div>
            ) : klineData.length > 0 ? (
              <div className="h-[160px] -mx-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={klineData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="klineGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#1677FF" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#1677FF" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 9, fill: "#8C8C8C" }}
                      tickFormatter={(v: string) => v.slice(5, 7) + "月"}
                      interval="preserveStartEnd"
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      domain={["dataMin", "dataMax"]}
                      tick={{ fontSize: 9, fill: "#8C8C8C" }}
                      tickFormatter={(v: number) => v.toFixed(0)}
                      axisLine={false}
                      tickLine={false}
                      width={45}
                    />
                    <Tooltip
                      contentStyle={{
                        fontSize: 11,
                        borderRadius: 8,
                        border: "1px solid #f0f0f0",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                      }}
                      labelFormatter={(label) => `周: ${label}`}
                      formatter={(value) => [`¥${Number(value).toFixed(2)}`, "收盘价"]}
                    />
                    {stock.current_price !== null && (
                      <ReferenceLine
                        y={stock.current_price}
                        stroke="#1677FF"
                        strokeDasharray="3 3"
                        strokeOpacity={0.6}
                      />
                    )}
                    <Area
                      type="monotone"
                      dataKey="close"
                      stroke="#1677FF"
                      strokeWidth={1.5}
                      fill="url(#klineGradient)"
                      dot={false}
                      activeDot={{ r: 3, fill: "#1677FF", stroke: "#fff", strokeWidth: 2 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
                {/* Legend: 52w high/low + current */}
                <div className="flex items-center justify-between text-[10px] mt-1 px-2">
                  <span className="text-stock-down font-mono">
                    52周低: {fmtPrice(stock.low_52w)}
                  </span>
                  <span className="text-primary font-mono font-semibold">
                    现价: {fmtPrice(stock.current_price)}
                  </span>
                  <span className="text-stock-up font-mono">
                    52周高: {fmtPrice(stock.high_52w)}
                  </span>
                </div>
              </div>
            ) : (
              <div className="h-[160px] flex items-center justify-center text-xs text-content-muted">
                暂无 K 线数据
              </div>
            )}
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
