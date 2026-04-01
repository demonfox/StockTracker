/**
 * Compact stock card for mobile / grid view.
 *
 * Shows symbol, name, price, change% with color coding,
 * and a delete action button. Used as an alternative to
 * the table on small screens.
 */

import { Trash2, TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { Stock } from "../types/stock";

// ── Props ────────────────────────────────────────────────────────────

interface StockCardProps {
  stock: Stock;
  onRemove: (symbol: string) => void;
}

// ── Component ────────────────────────────────────────────────────────

export default function StockCard({ stock, onRemove }: StockCardProps) {
  const change = stock.change_percent;
  const isUp = change !== null && change > 0;
  const isDown = change !== null && change < 0;

  const colorClass = isUp
    ? "text-stock-up"
    : isDown
      ? "text-stock-down"
      : "text-content-secondary";

  const bgClass = isUp
    ? "bg-red-50/60 ring-red-100"
    : isDown
      ? "bg-emerald-50/60 ring-emerald-100"
      : "bg-gray-50 ring-gray-100";

  const TrendIcon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;

  function formatCurrency(n: number | null): string {
    if (n === null || n === undefined) return "—";
    if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿`;
    if (n >= 1e4) return `${(n / 1e4).toFixed(0)}万`;
    return n.toLocaleString("zh-CN");
  }

  return (
    <div
      className={`relative group p-4 rounded-xl ring-1 ${bgClass}
                  hover:shadow-md hover:-translate-y-0.5
                  transition-all duration-200`}
    >
      {/* Delete button */}
      <button
        onClick={() => onRemove(stock.symbol)}
        className="absolute top-2.5 right-2.5 p-1.5 rounded-lg
                   text-content-muted/0 group-hover:text-content-muted
                   hover:!text-stock-up hover:bg-red-50
                   transition-all duration-200 cursor-pointer"
        title={`删除 ${stock.symbol}`}
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>

      {/* Symbol + Name */}
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
          isUp ? "bg-red-100" : isDown ? "bg-emerald-100" : "bg-gray-200"
        }`}>
          <TrendIcon className={`w-4 h-4 ${colorClass}`} />
        </div>
        <div>
          <p className="text-xs font-mono font-semibold text-content-primary leading-none">
            {stock.symbol}
          </p>
          <p className="text-[11px] text-content-muted mt-0.5 truncate max-w-[100px]">
            {stock.name ?? "—"}
          </p>
        </div>
      </div>

      {/* Price */}
      <p className={`text-xl font-bold font-mono tabular-nums ${colorClass}`}>
        {stock.current_price?.toFixed(2) ?? "—"}
      </p>

      {/* Change */}
      <div className="flex items-center gap-2 mt-1">
        <span className={`text-xs font-mono font-medium ${colorClass}`}>
          {change !== null
            ? `${change > 0 ? "+" : ""}${change.toFixed(2)}%`
            : "—"}
        </span>
        <span className={`text-xs font-mono ${colorClass}`}>
          {stock.change_amount !== null
            ? `${stock.change_amount > 0 ? "+" : ""}${stock.change_amount.toFixed(2)}`
            : ""}
        </span>
      </div>

      {/* Mini stats */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-3 pt-3 border-t border-black/5">
        <div className="flex justify-between text-[10px]">
          <span className="text-content-muted">成交量</span>
          <span className="font-mono text-content-secondary">
            {formatCurrency(stock.volume)}
          </span>
        </div>
        <div className="flex justify-between text-[10px]">
          <span className="text-content-muted">市值</span>
          <span className="font-mono text-content-secondary">
            {formatCurrency(stock.market_cap)}
          </span>
        </div>
        <div className="flex justify-between text-[10px]">
          <span className="text-content-muted">市盈率</span>
          <span className="font-mono text-content-secondary">
            {stock.pe_ratio?.toFixed(1) ?? "—"}
          </span>
        </div>
        <div className="flex justify-between text-[10px]">
          <span className="text-content-muted">换手率</span>
          <span className="font-mono text-content-secondary">
            {stock.turnover_rate ? `${stock.turnover_rate.toFixed(2)}%` : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}
