/**
 * Main stock data table — the core content area of the dashboard.
 *
 * Features:
 * - Sortable columns with visual indicators
 * - Red (up) / Green (down) color coding following China market convention
 * - Responsive horizontal scroll on small screens
 * - Row hover animations and staggered entry
 * - Delete action per row
 * - Empty state with call-to-action
 */

import { useCallback, useMemo, useState } from "react";
import { ArrowUpDown, ArrowUp, ArrowDown, Trash2, Plus } from "lucide-react";
import type { Stock, SortConfig, SortDirection } from "../types/stock";

// ── Props ────────────────────────────────────────────────────────────

interface StockTableProps {
  stocks: Stock[];
  loading: boolean;
  onRemoveStock: (symbol: string) => void;
  onAddStock: () => void;
}

// ── Column definition ────────────────────────────────────────────────

interface Column {
  key: keyof Stock;
  label: string;
  align: "left" | "right" | "center";
  sortable: boolean;
  width?: string;
  render: (stock: Stock) => React.ReactNode;
}

// ── Formatters ───────────────────────────────────────────────────────

function formatPrice(n: number | null, market?: string): string {
  if (n === null || n === undefined) return "—";
  if (market === "US") return `$${n.toFixed(2)}`;
  return n.toFixed(2);
}

function formatPercent(n: number | null): string {
  if (n === null || n === undefined) return "—";
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(2)}%`;
}

function formatChange(n: number | null, market?: string): string {
  if (n === null || n === undefined) return "—";
  const sign = n > 0 ? "+" : "";
  const prefix = market === "US" ? "$" : "";
  return `${sign}${prefix}${n.toFixed(2)}`;
}

function formatVolume(n: number | null): string {
  if (n === null || n === undefined) return "—";
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿`;
  if (n >= 1e4) return `${(n / 1e4).toFixed(0)}万`;
  return n.toLocaleString("zh-CN");
}

function formatCurrency(n: number | null, market?: string): string {
  if (n === null || n === undefined) return "—";
  if (market === "US") {
    if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
    if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
    if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
    return `$${n.toLocaleString("en-US")}`;
  }
  if (n >= 1e12) return `${(n / 1e12).toFixed(2)}万亿`;
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿`;
  if (n >= 1e4) return `${(n / 1e4).toFixed(0)}万`;
  return n.toLocaleString("zh-CN");
}

function getChangeColor(change: number | null, market?: string): string {
  if (change === null || change === undefined || change === 0) {
    return "text-content-secondary";
  }
  // US: green up, red down; CN: red up, green down
  if (market === "US") {
    return change > 0 ? "text-emerald-600" : "text-red-600";
  }
  return change > 0 ? "text-stock-up" : "text-stock-down";
}

function getChangeBg(change: number | null, market?: string): string {
  if (change === null || change === undefined || change === 0) return "";
  if (market === "US") {
    return change > 0 ? "bg-emerald-50/50" : "bg-red-50/50";
  }
  return change > 0 ? "bg-red-50/50" : "bg-emerald-50/50";
}

function MarketBadge({ market }: { market: string }) {
  if (market === "US") {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold
                        bg-blue-50 text-blue-600 ring-1 ring-blue-200/60">
        US
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold
                      bg-red-50 text-red-600 ring-1 ring-red-200/60">
      CN
    </span>
  );
}

// ── Component ────────────────────────────────────────────────────────

export default function StockTable({
  stocks,
  loading,
  onRemoveStock,
  onAddStock,
}: StockTableProps) {
  const [sort, setSort] = useState<SortConfig>({
    field: "change_percent",
    direction: "descend",
  });
  const [deletingSymbol, setDeletingSymbol] = useState<string | null>(null);

  // ── Column definitions ───────────────────────────────────────────

  const columns: Column[] = useMemo(
    () => [
      {
        key: "market",
        label: "市场",
        align: "center",
        sortable: true,
        width: "w-16",
        render: (s) => <MarketBadge market={s.market} />,
      },
      {
        key: "symbol",
        label: "代码",
        align: "left",
        sortable: true,
        width: "w-24",
        render: (s) => (
          <span className="font-mono font-semibold text-content-primary text-[13px]">
            {s.symbol}
          </span>
        ),
      },
      {
        key: "name",
        label: "名称",
        align: "left",
        sortable: true,
        width: "w-28",
        render: (s) => (
          <span className="font-medium text-content-primary truncate block max-w-[120px]">
            {s.name ?? "—"}
          </span>
        ),
      },
      {
        key: "current_price",
        label: "现价",
        align: "right",
        sortable: true,
        render: (s) => (
          <span
            className={`font-mono font-semibold text-[13px] ${getChangeColor(s.change_percent, s.market)}`}
          >
            {formatPrice(s.current_price, s.market)}
          </span>
        ),
      },
      {
        key: "change_percent",
        label: "涨跌幅",
        align: "right",
        sortable: true,
        render: (s) => {
          const color = getChangeColor(s.change_percent, s.market);
          return (
            <span
              className={`inline-flex items-center justify-end font-mono font-semibold text-[13px]
                          px-2 py-0.5 rounded ${color} ${getChangeBg(s.change_percent, s.market)}`}
            >
              {formatPercent(s.change_percent)}
            </span>
          );
        },
      },
      {
        key: "change_amount",
        label: "涨跌额",
        align: "right",
        sortable: true,
        render: (s) => (
          <span className={`font-mono text-xs ${getChangeColor(s.change_percent, s.market)}`}>
            {formatChange(s.change_amount, s.market)}
          </span>
        ),
      },
      {
        key: "open_price",
        label: "开盘",
        align: "right",
        sortable: true,
        render: (s) => (
          <span className="font-mono text-xs text-content-secondary">
            {formatPrice(s.open_price, s.market)}
          </span>
        ),
      },
      {
        key: "high_price",
        label: "最高",
        align: "right",
        sortable: true,
        render: (s) => (
          <span className="font-mono text-xs text-stock-up/70">
            {formatPrice(s.high_price, s.market)}
          </span>
        ),
      },
      {
        key: "low_price",
        label: "最低",
        align: "right",
        sortable: true,
        render: (s) => (
          <span className="font-mono text-xs text-stock-down/70">
            {formatPrice(s.low_price, s.market)}
          </span>
        ),
      },
      {
        key: "volume",
        label: "成交量",
        align: "right",
        sortable: true,
        render: (s) => (
          <span className="font-mono text-xs text-content-secondary">
            {formatVolume(s.volume)}
          </span>
        ),
      },
      {
        key: "turnover",
        label: "成交额",
        align: "right",
        sortable: true,
        render: (s) => (
          <span className="font-mono text-xs text-content-secondary">
            {formatCurrency(s.turnover, s.market)}
          </span>
        ),
      },
      {
        key: "market_cap",
        label: "总市值",
        align: "right",
        sortable: true,
        render: (s) => (
          <span className="font-mono text-xs text-content-secondary">
            {formatCurrency(s.market_cap, s.market)}
          </span>
        ),
      },
      {
        key: "pe_ratio",
        label: "市盈率",
        align: "right",
        sortable: true,
        render: (s) => (
          <span className="font-mono text-xs text-content-secondary">
            {s.pe_ratio !== null ? s.pe_ratio.toFixed(2) : "—"}
          </span>
        ),
      },
      {
        key: "turnover_rate",
        label: "换手率",
        align: "right",
        sortable: true,
        render: (s) => (
          <span className="font-mono text-xs text-content-secondary">
            {s.turnover_rate !== null ? `${s.turnover_rate.toFixed(2)}%` : "—"}
          </span>
        ),
      },
    ],
    [],
  );

  // ── Sorting logic ────────────────────────────────────────────────

  const handleSort = useCallback((field: keyof Stock) => {
    setSort((prev) => {
      if (prev.field !== field) return { field, direction: "descend" };
      const cycle: SortDirection[] = ["descend", "ascend", null];
      const idx = cycle.indexOf(prev.direction);
      return { field, direction: cycle[(idx + 1) % cycle.length] };
    });
  }, []);

  const sortedStocks = useMemo(() => {
    if (!sort.direction) return stocks;
    const arr = [...stocks];
    const dir = sort.direction === "ascend" ? 1 : -1;
    arr.sort((a, b) => {
      const va = a[sort.field];
      const vb = b[sort.field];
      if (va === null || va === undefined) return 1;
      if (vb === null || vb === undefined) return -1;
      if (typeof va === "string" && typeof vb === "string") {
        return dir * va.localeCompare(vb, "zh-CN");
      }
      return dir * ((va as number) - (vb as number));
    });
    return arr;
  }, [stocks, sort]);

  // ── Delete handler ───────────────────────────────────────────────

  const handleDelete = useCallback(
    async (symbol: string) => {
      setDeletingSymbol(symbol);
      onRemoveStock(symbol);
      // Small delay for animation
      setTimeout(() => setDeletingSymbol(null), 300);
    },
    [onRemoveStock],
  );

  // ── Sort icon ────────────────────────────────────────────────────

  const SortIcon = ({ field }: { field: keyof Stock }) => {
    if (sort.field !== field || !sort.direction) {
      return <ArrowUpDown className="w-3 h-3 text-content-muted/50" />;
    }
    return sort.direction === "ascend" ? (
      <ArrowUp className="w-3 h-3 text-primary" />
    ) : (
      <ArrowDown className="w-3 h-3 text-primary" />
    );
  };

  // ── Loading state ────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex items-center justify-center py-24">
          <div className="flex flex-col items-center gap-3">
            <div className="relative w-12 h-12">
              <div className="absolute inset-0 rounded-full border-[3px] border-gray-100" />
              <div className="absolute inset-0 rounded-full border-[3px] border-primary border-t-transparent animate-spin" />
            </div>
            <span className="text-sm text-content-muted">加载行情数据...</span>
          </div>
        </div>
      </div>
    );
  }

  // ── Empty state ──────────────────────────────────────────────────

  if (stocks.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex flex-col items-center justify-center py-24 px-6">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5
                          flex items-center justify-center mb-6">
            <svg
              className="w-10 h-10 text-primary/60"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-content-primary mb-2">
            还没有追踪任何股票
          </h3>
          <p className="text-sm text-content-muted mb-6 text-center max-w-sm">
            添加你的第一只股票（A股/美股），实时追踪价格、涨跌幅、成交量等关键指标
          </p>
          <button
            onClick={onAddStock}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold
                       text-white bg-gradient-to-r from-primary to-primary-dark
                       hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-[1px]
                       active:translate-y-0
                       transition-all duration-200 cursor-pointer"
          >
            <Plus className="w-4 h-4" strokeWidth={2.5} />
            添加股票
          </button>
        </div>
      </div>
    );
  }

  // ── Table ────────────────────────────────────────────────────────

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      {/* Table header bar */}
      <div className="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-content-primary">
            实时行情
          </h2>
          <span className="text-xs text-content-muted bg-gray-100 px-2 py-0.5 rounded-full tabular-nums">
            {stocks.length} 只
          </span>
        </div>
        <p className="text-[10px] text-content-muted">
          点击表头排序 · A股红涨绿跌 · 美股绿涨红跌
        </p>
      </div>

      {/* Scrollable table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-secondary/70">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-3 py-2.5 text-[11px] font-semibold text-content-muted uppercase tracking-wider
                              whitespace-nowrap select-none
                              ${col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left"}
                              ${col.sortable ? "cursor-pointer hover:bg-gray-100/80 transition-colors" : ""}
                              ${col.width ?? ""}`}
                  onClick={col.sortable ? () => handleSort(col.key) : undefined}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {col.sortable && <SortIcon field={col.key} />}
                  </span>
                </th>
              ))}
              <th className="px-3 py-2.5 text-[11px] font-semibold text-content-muted text-center w-14">
                操作
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedStocks.map((stock, idx) => (
              <tr
                key={stock.id}
                className={`stock-row border-t border-gray-50 transition-all duration-200
                            hover:bg-surface-secondary/60
                            ${deletingSymbol === stock.symbol ? "opacity-0 scale-y-0 h-0" : ""}
                            `}
                style={{
                  animationDelay: `${idx * 30}ms`,
                }}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`px-3 py-2.5 whitespace-nowrap
                                ${col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left"}`}
                  >
                    {col.render(stock)}
                  </td>
                ))}
                <td className="px-3 py-2.5 text-center">
                  <button
                    onClick={() => handleDelete(stock.symbol)}
                    className="p-1.5 rounded-lg text-content-muted/50 hover:text-stock-up
                               hover:bg-red-50 transition-all duration-200 cursor-pointer
                               opacity-0 group-hover:opacity-100"
                    title={`删除 ${stock.name ?? stock.symbol}`}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-5 py-2.5 border-t border-gray-100 flex items-center justify-between">
        <p className="text-[10px] text-content-muted">
          数据来源: AkShare · 仅供参考，不构成投资建议
        </p>
        <p className="text-[10px] text-content-muted tabular-nums">
          v1.0.0
        </p>
      </div>
    </div>
  );
}
