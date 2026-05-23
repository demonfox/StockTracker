/**
 * TypeScript type definitions for StockTracker.
 *
 * These types mirror the backend Pydantic schemas
 * and provide type safety across the frontend codebase.
 */

// ── Stock Data Types ─────────────────────────────────────────────────

/** Full stock record as returned by `GET /api/stocks` */
export interface Stock {
  id: number;
  symbol: string;
  name: string | null;
  market: "CN" | "US" | "HK";

  // Price
  current_price: number | null;
  open_price: number | null;
  high_price: number | null;
  low_price: number | null;
  close_price: number | null;

  // Volume
  volume: number | null;
  turnover: number | null;
  turnover_rate: number | null;

  // Change
  change_amount: number | null;
  change_percent: number | null;
  amplitude: number | null;

  // Fundamentals
  market_cap: number | null;
  circulating_market_cap: number | null;
  pe_ratio: number | null;
  pb_ratio: number | null;

  // 52-week range
  high_52w: number | null;
  low_52w: number | null;

  // Timestamps (ISO strings from backend)
  last_trade_time: string | null;
  updated_at: string | null;
  created_at: string | null;
}

/** Response wrapper for GET /api/stocks */
export interface StockListResponse {
  count: number;
  stocks: Stock[];
}

/** Request body for POST /api/stocks */
export interface StockCreateRequest {
  symbol: string;
  market: "CN" | "US" | "HK";
}

/** Supported market type */
export type MarketType = "CN" | "US" | "HK";

// ── Scheduler & Config Types ─────────────────────────────────────────

/** Real-time open/closed status for each market */
export interface MarketStatusInfo {
  cn_open: boolean;
  us_open: boolean;
  hk_open: boolean;
}

/** Response from GET /api/scheduler/status */
export interface SchedulerStatus {
  running: boolean;
  refresh_interval_seconds: number;
  market_hours_only: boolean;
  next_run: string | null;
  market_status: MarketStatusInfo;
}

/** Request body for PATCH /api/config */
export interface ConfigUpdateRequest {
  refresh_interval_seconds?: number;
  market_hours_only?: boolean;
}

/** Generic message response from the API */
export interface MessageResponse {
  message: string;
  success: boolean;
}

// ── UI State Types ───────────────────────────────────────────────────

/** Current loading / error state for the stocks hook */
export interface StocksState {
  stocks: Stock[];
  loading: boolean;
  error: string | null;
  lastRefresh: Date | null;
}

/** Sort direction for table columns */
export type SortDirection = "ascend" | "descend" | null;

/** Sort configuration */
export interface SortConfig {
  field: keyof Stock;
  direction: SortDirection;
}

// ── Market Index Types ───────────────────────────────────────────────

/** Real-time quote for a single market index */
export interface IndexQuote {
  symbol: string;
  name: string;
  market: "CN" | "US" | "HK";
  current_price: number | null;
  change_amount: number | null;
  change_percent: number | null;
}

/** Response from GET /api/indices */
export interface IndicesResponse {
  cn: IndexQuote[];
  hk: IndexQuote[];
  us: IndexQuote[];
}

// ── Index Minute Data Types ─────────────────────────────────────────

/** A single minute-level price point */
export interface IndexMinutePoint {
  time: string;
  price: number;
}

/** Intraday minute data for a single market index */
export interface IndexMinuteData {
  symbol: string;
  name: string;
  market: "CN" | "HK" | "US";
  date: string | null;
  prev_close: number | null;
  points: IndexMinutePoint[];
}

/** Response from GET /api/indices/minute */
export interface IndicesMinuteResponse {
  cn: IndexMinuteData[];
  hk: IndexMinuteData[];
  us: IndexMinuteData[];
}
