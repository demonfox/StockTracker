/**
 * Modal dialog for adding a new stock ticker.
 *
 * Features:
 * - Market tab switch (A-share / HK / US)
 * - Symbol input with per-market validation
 * - Common stock quick-select chips per market
 * - Loading spinner during API call
 * - Success / error feedback with auto-close on success
 * - Keyboard support (Enter to submit, Escape to close)
 * - Backdrop click to close
 * - Smooth open/close animation
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { X, Search, TrendingUp, AlertCircle, Check } from "lucide-react";
import type { Stock, MarketType } from "../types/stock";

// ── Props ────────────────────────────────────────────────────────────

interface AddStockModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (symbol: string, market?: MarketType) => Promise<Stock | null>;
}

// ── Quick-pick stocks per market ─────────────────────────────────────

const CN_QUICK_PICKS = [
  { symbol: "600519", name: "贵州茅台" },
  { symbol: "000858", name: "五粮液" },
  { symbol: "601318", name: "中国平安" },
  { symbol: "000001", name: "平安银行" },
  { symbol: "600036", name: "招商银行" },
  { symbol: "300750", name: "宁德时代" },
  { symbol: "601012", name: "隆基绿能" },
  { symbol: "000333", name: "美的集团" },
];

const US_QUICK_PICKS = [
  { symbol: "AAPL", name: "Apple" },
  { symbol: "MSFT", name: "Microsoft" },
  { symbol: "NVDA", name: "NVIDIA" },
  { symbol: "GOOGL", name: "Alphabet" },
  { symbol: "AMZN", name: "Amazon" },
  { symbol: "TSLA", name: "Tesla" },
  { symbol: "META", name: "Meta" },
  { symbol: "NFLX", name: "Netflix" },
];

const HK_QUICK_PICKS = [
  { symbol: "00700", name: "腾讯控股" },
  { symbol: "09988", name: "阿里巴巴" },
  { symbol: "03690", name: "美团" },
  { symbol: "01810", name: "小米集团" },
  { symbol: "09618", name: "京东集团" },
  { symbol: "00941", name: "中国移动" },
  { symbol: "02318", name: "中国平安" },
  { symbol: "01024", name: "快手" },
];

// ── Component ────────────────────────────────────────────────────────

export default function AddStockModal({
  open,
  onClose,
  onAdd,
}: AddStockModalProps) {
  const [market, setMarket] = useState<MarketType>("CN");
  const [symbol, setSymbol] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isCN = market === "CN";
  const isHK = market === "HK";
  const isUS = market === "US";
  const quickPicks = isCN ? CN_QUICK_PICKS : isHK ? HK_QUICK_PICKS : US_QUICK_PICKS;

  // Auto-focus input on open
  useEffect(() => {
    if (open) {
      setSymbol("");
      setError(null);
      setSuccess(null);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  // Reset symbol when switching market
  useEffect(() => {
    setSymbol("");
    setError(null);
    setSuccess(null);
  }, [market]);

  // Keyboard shortcut: Escape to close
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && open) onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  // ── Validation ───────────────────────────────────────────────────

  const validateSymbol = (s: string): string | null => {
    const trimmed = s.trim();
    if (!trimmed) return "请输入股票代码";
    if (isCN) {
      if (!/^\d{6}$/.test(trimmed)) return "A股代码应为6位数字（如 600519）";
    } else if (isHK) {
      if (!/^\d{5}$/.test(trimmed)) return "港股代码应为5位数字（如 00700）";
    } else {
      if (!/^[A-Za-z]{1,5}$/.test(trimmed)) return "美股代码应为1-5位字母（如 AAPL）";
    }
    return null;
  };

  const isSubmitDisabled = isCN
    ? symbol.length !== 6
    : isHK
      ? symbol.length !== 5
      : symbol.length < 1;

  // ── Submit ───────────────────────────────────────────────────────

  const handleSubmit = useCallback(async () => {
    const trimmed = isUS ? symbol.trim().toUpperCase() : symbol.trim();
    const err = validateSymbol(trimmed);
    if (err) {
      setError(err);
      return;
    }

    setSubmitting(true);
    setError(null);

    const result = await onAdd(trimmed, market);

    if (result) {
      setSuccess(`已添加 ${result.name ?? trimmed}`);
      setSymbol("");
      // Auto-close after short delay
      setTimeout(() => {
        onClose();
        setSuccess(null);
      }, 1200);
    } else {
      setError("添加失败，请检查股票代码是否正确");
    }

    setSubmitting(false);
  }, [symbol, market, isUS, onAdd, onClose]);

  const handleQuickPick = useCallback(
    (sym: string) => {
      setSymbol(sym);
      setError(null);
    },
    [],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      let v = e.target.value;
      if (isCN) {
        v = v.replace(/\D/g, "").slice(0, 6);
      } else if (isHK) {
        v = v.replace(/\D/g, "").slice(0, 5);
      } else {
        v = v.replace(/[^A-Za-z]/g, "").slice(0, 5).toUpperCase();
      }
      setSymbol(v);
      setError(null);
      setSuccess(null);
    },
    [isCN, isHK],
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm
                    animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl shadow-black/10
                    animate-in fade-in zoom-in-95 slide-in-from-bottom-4 duration-300"
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

        {/* Header */}
        <div className="px-6 pt-6 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/10 to-primary/5
                            flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-content-primary">
                添加股票
              </h2>
              <p className="text-xs text-content-muted">
                选择市场并输入股票代码开始追踪
              </p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 pb-2">
          {/* Market tabs */}
          <div className="flex rounded-xl bg-surface-secondary p-1 mb-4">
            <button
              onClick={() => setMarket("CN")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium
                          transition-all duration-200 cursor-pointer
                          ${isCN
                            ? "bg-white text-primary shadow-sm"
                            : "text-content-muted hover:text-content-secondary"
                          }`}
            >
              <span>🇨🇳</span>
              <span>A股</span>
            </button>
            <button
              onClick={() => setMarket("HK")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium
                          transition-all duration-200 cursor-pointer
                          ${isHK
                            ? "bg-white text-primary shadow-sm"
                            : "text-content-muted hover:text-content-secondary"
                          }`}
            >
              <span>🇭🇰</span>
              <span>港股</span>
            </button>
            <button
              onClick={() => setMarket("US")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium
                          transition-all duration-200 cursor-pointer
                          ${isUS
                            ? "bg-white text-primary shadow-sm"
                            : "text-content-muted hover:text-content-secondary"
                          }`}
            >
              <span>🇺🇸</span>
              <span>美股</span>
            </button>
          </div>

          {/* Input field */}
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-content-muted" />
            <input
              ref={inputRef}
              type="text"
              value={symbol}
              onChange={handleInputChange}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !submitting) handleSubmit();
              }}
              placeholder={isCN ? "输入股票代码，如 600519" : isHK ? "输入股票代码，如 00700" : "输入股票代码，如 AAPL"}
              className="w-full h-12 pl-10 pr-4 rounded-xl text-sm font-mono
                         bg-surface-secondary border-0 ring-1 ring-gray-200
                         placeholder:text-content-muted/60
                         focus:outline-none focus:ring-2 focus:ring-primary/40
                         transition-all duration-200"
              disabled={submitting}
              maxLength={isCN ? 6 : 5}
              inputMode={(isCN || isHK) ? "numeric" : "text"}
              autoComplete="off"
            />
            {symbol.length > 0 && (
              <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[10px] text-content-muted tabular-nums">
                {symbol.length}/{isCN ? 6 : 5}
              </span>
            )}
          </div>

          {/* Feedback messages */}
          {error && (
            <div className="mt-2.5 flex items-center gap-1.5 text-xs text-red-600
                            animate-in fade-in slide-in-from-top-1 duration-200">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="mt-2.5 flex items-center gap-1.5 text-xs text-emerald-600
                            animate-in fade-in slide-in-from-top-1 duration-200">
              <Check className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{success}</span>
            </div>
          )}

          {/* Quick picks */}
          <div className="mt-4">
            <p className="text-[10px] font-semibold text-content-muted uppercase tracking-wider mb-2">
              {isCN ? "热门A股" : isHK ? "热门港股" : "热门美股"}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {quickPicks.map((pick) => (
                <button
                  key={pick.symbol}
                  onClick={() => handleQuickPick(pick.symbol)}
                  disabled={submitting}
                  className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs
                              ring-1 transition-all duration-200 cursor-pointer
                              ${symbol === pick.symbol
                                ? "bg-primary/8 text-primary ring-primary/30 font-medium"
                                : "bg-white text-content-secondary ring-gray-200 hover:ring-gray-300 hover:bg-gray-50"
                              }`}
                >
                  <span className="font-mono text-[10px] text-content-muted">
                    {pick.symbol}
                  </span>
                  <span>{pick.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 flex items-center justify-end gap-2.5">
          <button
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 rounded-xl text-sm font-medium text-content-secondary
                       hover:bg-gray-100 transition-colors cursor-pointer
                       disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || isSubmitDisabled}
            className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl text-sm font-semibold
                       text-white bg-gradient-to-r from-primary to-primary-dark
                       hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-[0.5px]
                       active:translate-y-0
                       disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none
                       disabled:hover:translate-y-0
                       transition-all duration-200 cursor-pointer"
          >
            {submitting ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                添加中...
              </>
            ) : (
              <>
                <TrendingUp className="w-3.5 h-3.5" />
                添加并追踪
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
