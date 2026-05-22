/**
 * Market Indices panel with tab-based market switching.
 *
 * Displays 3 major indices for the selected market (CN / HK / US).
 * Click a market tab to switch the view.
 */

import { useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { IndexQuote, IndicesResponse, MarketType } from "../types/stock";

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
  loading: boolean;
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

function formatPrice(price: number | null): string {
  if (price === null) return "—";
  if (price >= 10000) return price.toFixed(2);
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

// ── Component ────────────────────────────────────────────────────────

export default function MarketIndices({ indices, loading }: MarketIndicesProps) {
  const [activeMarket, setActiveMarket] = useState<MarketType>("CN");

  const currentIndices: IndexQuote[] = indices
    ? indices[activeMarket.toLowerCase() as "cn" | "hk" | "us"]
    : [];

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
            {currentIndices.map((index) => (
              <IndexCard key={index.symbol} index={index} market={activeMarket} />
            ))}
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
}

function IndexCard({ index, market }: IndexCardProps) {
  const changeColor = getChangeColor(index.change_percent, market);
  const bgColor = getChangeBgColor(index.change_percent, market);

  const TrendIcon = index.change_percent === null || index.change_percent === 0
    ? Minus
    : index.change_percent > 0
      ? TrendingUp
      : TrendingDown;

  return (
    <div
      className={`relative rounded-xl p-4 ${bgColor} border border-border-subtle/50
                  transition-all duration-200 hover:shadow-md hover:scale-[1.01]`}
    >
      {/* Index name */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-content-secondary">
          {index.name}
        </span>
        <TrendIcon className={`w-4 h-4 ${changeColor}`} />
      </div>

      {/* Current price */}
      <p className={`text-2xl font-bold tabular-nums ${changeColor}`}>
        {formatPrice(index.current_price)}
      </p>

      {/* Change row */}
      <div className="flex items-center gap-3 mt-2">
        <span className={`text-sm font-mono font-semibold ${changeColor}`}>
          {formatPercent(index.change_percent)}
        </span>
        <span className={`text-xs font-mono ${changeColor}`}>
          {formatChange(index.change_amount)}
        </span>
      </div>
    </div>
  );
}
