/**
 * Axios API client for StockTracker backend.
 *
 * All HTTP communication with the FastAPI backend is centralized here.
 * The Vite dev server proxies `/api` requests to `localhost:8000`,
 * so we use a relative base URL that works in both dev and production.
 */

import axios from "axios";
import type {
  ConfigUpdateRequest,
  MarketType,
  MessageResponse,
  SchedulerStatus,
  Stock,
  StockListResponse,
} from "../types/stock";

// ── Axios Instance ───────────────────────────────────────────────────

const api = axios.create({
  baseURL: "/api",
  timeout: 15_000,
  headers: { "Content-Type": "application/json" },
});

// ── Stock Endpoints ──────────────────────────────────────────────────

/** Fetch all tracked stocks with their latest data. */
export async function fetchStocks(): Promise<StockListResponse> {
  const { data } = await api.get<StockListResponse>("/stocks");
  return data;
}

/** Add a new stock ticker and return its initial data. */
export async function addStock(
  symbol: string,
  market: MarketType = "CN",
): Promise<Stock> {
  const { data } = await api.post<Stock>("/stocks", { symbol, market });
  return data;
}

/** Remove a stock from the tracking list. */
export async function removeStock(symbol: string): Promise<MessageResponse> {
  const { data } = await api.delete<MessageResponse>(`/stocks/${symbol}`);
  return data;
}

/** Get a single stock's data by symbol. */
export async function getStock(symbol: string): Promise<Stock> {
  const { data } = await api.get<Stock>(`/stocks/${symbol}`);
  return data;
}

// ── Scheduler & Config Endpoints ─────────────────────────────────────

/** Get the current scheduler status. */
export async function fetchSchedulerStatus(): Promise<SchedulerStatus> {
  const { data } = await api.get<SchedulerStatus>("/scheduler/status");
  return data;
}

/** Update scheduler / app configuration at runtime. */
export async function updateConfig(
  config: ConfigUpdateRequest,
): Promise<MessageResponse> {
  const { data } = await api.patch<MessageResponse>("/config", config);
  return data;
}

/** Trigger an immediate stock data refresh. */
export async function triggerRefresh(): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>("/scheduler/refresh");
  return data;
}

// ── Health Check ─────────────────────────────────────────────────────

/** Ping the backend to check connectivity. */
export async function healthCheck(): Promise<{ status: string }> {
  const { data } = await api.get<{ status: string }>("/health");
  return data;
}

export default api;
