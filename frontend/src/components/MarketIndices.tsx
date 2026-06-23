/**
 * Market Indices panel with tab-based market switching.
 *
 * Displays 3 major indices for the selected market (CN / HK / US).
 * For CN and HK markets, each index card includes an intraday line chart
 * showing minute-by-minute price movement with a prev-close reference line.
 */

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type {
  IndexQuote,
  IndexMinuteData,
  IndicesMinuteResponse,
  IndicesResponse,
  MarketStatusInfo,
  MarketType,
} from "../types/stock";

// ── Tab Definitions ──────────────────────────────────────────────────

interface MarketTab {
  key: MarketType;
  label: string;
  flag: string;
}

const MARKET_TABS: MarketTab[] = [
  { key: "CN", label: "沪深A股", flag: "🇨🇳" },
  { key: "HK", label: "港股", flag: "🇭🇰" },
  { key: "US", label: "美股", flag: "🇺🇸" },
];

// ── Props ────────────────────────────────────────────────────────────

interface MarketIndicesProps {
  indices: IndicesResponse | null;
  minuteData: IndicesMinuteResponse | null;
  loading: boolean;
  marketStatus?: MarketStatusInfo;
}

// ── Helpers ──────────────────────────────────────────────────────────

/**
 * Get the color class for price change display.
 * CN market: red = up, green = down (Chinese convention)
 * HK/US markets: green = up, red = down (Western convention)
 */
function getChangeColor(changePercent: number | null, market: MarketType): string {
  if (changePercent === null || changePercent === 0) return "text-content-secondary";
  if (market === "CN") {
    return changePercent > 0 ? "text-red-600" : "text-emerald-600";
  }
  return changePercent > 0 ? "text-emerald-600" : "text-red-600";
}

function getChangeBgColor(changePercent: number | null, market: MarketType): string {
  if (changePercent === null || changePercent === 0) return "bg-gray-50";
  if (market === "CN") {
    return changePercent > 0 ? "bg-red-50/60" : "bg-emerald-50/60";
  }
  return changePercent > 0 ? "bg-emerald-50/60" : "bg-red-50/60";
}

/**
 * Get the line color for the chart.
 * CN: red for up, green for down
 * HK/US: green for up, red for down
 */
function getLineColor(changePercent: number | null, market: MarketType): string {
  if (changePercent === null || changePercent === 0) return "#6b7280";
  if (market === "CN") {
    return changePercent > 0 ? "#dc2626" : "#059669";
  }
  return changePercent > 0 ? "#059669" : "#dc2626";
}

function formatPrice(price: number | null): string {
  if (price === null) return "—";
  return price.toFixed(2);
}

function formatPercent(percent: number | null): string {
  if (percent === null) return "—";
  const sign = percent > 0 ? "+" : "";
  return `${sign}${percent.toFixed(2)}%`;
}

function formatChange(change: number | null): string {
  if (change === null) return "—";
  const sign = change > 0 ? "+" : "";
  return `${sign}${change.toFixed(2)}`;
}

/**
 * Format time string from "HHMM" to "HH:MM".
 */
function formatTime(time: string): string {
  if (time.length === 4) {
    return `${time.slice(0, 2)}:${time.slice(2)}`;
  }
  return time;
}

// ── Component ────────────────────────────────────────────────────────

export default function MarketIndices({ indices, minuteData, loading, marketStatus }: MarketIndicesProps) {
  const [activeMarket, setActiveMarket] = useState<MarketType>("CN");

  // Auto-focus on the first active market (priority: CN → HK → US)
  useEffect(() => {
    if (!marketStatus) return;
    if (marketStatus.cn_open) {
      setActiveMarket("CN");
    } else if (marketStatus.hk_open) {
      setActiveMarket("HK");
    } else if (marketStatus.us_open) {
      setActiveMarket("US");
    }
  }, [marketStatus]);

  const currentIndices: IndexQuote[] = indices
    ? indices[activeMarket.toLowerCase() as "cn" | "hk" | "us"]
    : [];

  // Get minute data for the active market
  const currentMinuteData: IndexMinuteData[] | null =
    minuteData
      ? minuteData[activeMarket.toLowerCase() as "cn" | "hk" | "us"]
      : null;

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-border-subtle shadow-sm overflow-hidden">
      {/* Tab bar */}
      <div className="flex items-center border-b border-border-subtle">
        {MARKET_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveMarket(tab.key)}
            className={`
              flex items-center gap-1.5 px-5 py-3 text-sm font-medium transition-all duration-200
              border-b-2 -mb-[1px]
              ${activeMarket === tab.key
                ? "border-primary text-primary bg-primary/5"
                : "border-transparent text-content-secondary hover:text-content-primary hover:bg-gray-50"
              }
            `}
          >
            <span className="text-base">{tab.flag}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Index cards */}
      <div className="p-5">
        {loading && !indices ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="ml-2 text-sm text-content-muted">加载指数数据...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {currentIndices.map((index) => {
              // Find matching minute data for this index
              const minute = currentMinuteData?.find(
                (m) => m.symbol === index.symbol,
              ) ?? null;

              return (
                <IndexCard
                  key={index.symbol}
                  index={index}
                  market={activeMarket}
                  minuteData={minute}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Index Card Sub-component ─────────────────────────────────────────

interface IndexCardProps {
  index: IndexQuote;
  market: MarketType;
  minuteData: IndexMinuteData | null;
}

function IndexCard({ index, market, minuteData }: IndexCardProps) {
  const changeColor = getChangeColor(index.change_percent, market);
  const bgColor = getChangeBgColor(index.change_percent, market);
  const lineColor = getLineColor(index.change_percent, market);

  const TrendIcon = index.change_percent === null || index.change_percent === 0
    ? Minus
    : index.change_percent > 0
      ? TrendingUp
      : TrendingDown;

  const hasChartData = minuteData && minuteData.points.length > 1;

  return (
    <div
      className={`relative rounded-xl p-4 ${bgColor} border border-border-subtle/50
                  transition-all duration-200 hover:shadow-md hover:scale-[1.01]`}
    >
      <div className="flex items-center gap-3">
        {/* Left: text info */}
        <div className={hasChartData ? "flex-shrink-0 min-w-0" : "flex-1"}>
          {/* Index name */}
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-sm font-medium text-content-secondary truncate">
              {index.name}
            </span>
            <TrendIcon className={`w-3.5 h-3.5 flex-shrink-0 ${changeColor}`} />
          </div>

          {/* Current price */}
          <p className={`text-xl font-bold tabular-nums ${changeColor}`}>
            {formatPrice(index.current_price)}
          </p>

          {/* Change info */}
          <div className="mt-1 space-y-0.5">
            <p className={`text-xs font-mono font-semibold ${changeColor}`}>
              {formatPercent(index.change_percent)}
            </p>
            <p className={`text-[11px] font-mono ${changeColor}`}>
              {formatChange(index.change_amount)}
            </p>
          </div>
        </div>

        {/* Right: Intraday Line Chart */}
        {hasChartData && (
          <div className="flex-1 min-w-0">
            <IntradayChart
              minuteData={minuteData}
              lineColor={lineColor}
              market={market}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ── Intraday Chart Sub-component ─────────────────────────────────────

interface IntradayChartProps {
  minuteData: IndexMinuteData;
  lineColor: string;
  market: MarketType;
}

function IntradayChart({ minuteData, lineColor, market }: IntradayChartProps) {
  const { points, prev_close } = minuteData;

  // Prepare chart data — sample points if too many for smooth rendering
  const chartData = points.map((p) => ({
    time: p.time,
    price: p.price,
  }));

  // Calculate Y domain with some padding
  const prices = points.map((p) => p.price);
  const allValues = prev_close ? [...prices, prev_close] : prices;
  const minPrice = Math.min(...allValues);
  const maxPrice = Math.max(...allValues);
  const padding = (maxPrice - minPrice) * 0.1 || maxPrice * 0.001;
  const yMin = minPrice - padding;
  const yMax = maxPrice + padding;

  // Show ~5 time labels evenly spaced
  const tickInterval = Math.floor(chartData.length / 5);

  return (
    <div className="-mx-1">
      <ResponsiveContainer width="100%" height={128}>
        <LineChart
          data={chartData}
          margin={{ top: 4, right: 4, bottom: 0, left: 4 }}
        >
          <XAxis
            dataKey="time"
            tick={{ fontSize: 9, fill: "#9ca3af" }}
            tickFormatter={formatTime}
            interval={tickInterval}
            axisLine={false}
            tickLine={false}
          />
          <YAxis domain={[yMin, yMax]} hide />
          {prev_close && (
            <ReferenceLine
              y={prev_close}
              stroke="#9ca3af"
              strokeDasharray="3 3"
              strokeWidth={1}
            />
          )}
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null;
              const point = payload[0];
              const price = point.value as number;
              const time = point.payload.time as string;
              const diff = prev_close ? price - prev_close : null;
              const diffPct = prev_close && prev_close !== 0
                ? ((price - prev_close) / prev_close) * 100
                : null;

              // Color logic matching market convention
              let tooltipColor = "#6b7280";
              if (diff !== null && diff !== 0) {
                if (market === "CN") {
                  tooltipColor = diff > 0 ? "#dc2626" : "#059669";
                } else {
                  tooltipColor = diff > 0 ? "#059669" : "#dc2626";
                }
              }

              return (
                <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-lg px-2.5 py-1.5 shadow-lg text-xs">
                  <p className="text-content-muted">{formatTime(time)}</p>
                  <p className="font-semibold tabular-nums" style={{ color: tooltipColor }}>
                    {price.toFixed(2)}
                    {diffPct !== null && (
                      <span className="ml-1.5 text-[10px]">
                        {diffPct > 0 ? "+" : ""}{diffPct.toFixed(2)}%
                      </span>
                    )}
                  </p>
                </div>
              );
            }}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke={lineColor}
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 3, strokeWidth: 0, fill: lineColor }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
