/**
 * Custom React hook for stock data management.
 *
 * Provides:
 * - Auto-polling with configurable interval
 * - CRUD operations (add / remove stocks)
 * - Manual refresh trigger
 * - Loading, error, and last-refresh states
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  addStock as apiAddStock,
  fetchSchedulerStatus,
  fetchStocks,
  removeStock as apiRemoveStock,
  triggerRefresh as apiTriggerRefresh,
  updateConfig as apiUpdateConfig,
} from "../services/api";
import type {
  ConfigUpdateRequest,
  MarketType,
  SchedulerStatus,
  Stock,
} from "../types/stock";

// ── Default polling interval (ms) ────────────────────────────────────
const DEFAULT_POLL_INTERVAL = 30_000;

// ── Hook Return Type ─────────────────────────────────────────────────

export interface UseStocksReturn {
  /** All tracked stocks */
  stocks: Stock[];
  /** True while initial fetch is in progress */
  loading: boolean;
  /** True while any background refresh is running */
  refreshing: boolean;
  /** Latest error message, or null */
  error: string | null;
  /** Timestamp of the last successful data fetch */
  lastRefresh: Date | null;
  /** Scheduler status from backend */
  schedulerStatus: SchedulerStatus | null;
  /** Polling interval in milliseconds */
  pollInterval: number;

  // Actions
  addStock: (symbol: string, market?: MarketType) => Promise<Stock | null>;
  removeStock: (symbol: string) => Promise<boolean>;
  refresh: () => Promise<void>;
  triggerBackendRefresh: () => Promise<boolean>;
  updateConfig: (config: ConfigUpdateRequest) => Promise<boolean>;
  setPollInterval: (ms: number) => void;
}

// ── Hook Implementation ──────────────────────────────────────────────

export function useStocks(
  initialPollInterval: number = DEFAULT_POLL_INTERVAL,
): UseStocksReturn {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [schedulerStatus, setSchedulerStatus] =
    useState<SchedulerStatus | null>(null);
  const [pollInterval, setPollInterval] = useState(initialPollInterval);

  // Ref to track if the component is mounted
  const mountedRef = useRef(true);
  // Ref to prevent concurrent fetches
  const fetchingRef = useRef(false);

  // ── Core data fetch ──────────────────────────────────────────────

  const loadStocks = useCallback(async (isInitial = false) => {
    if (fetchingRef.current) return;
    fetchingRef.current = true;

    if (isInitial) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }

    const response = await fetchStocks();
    if (!mountedRef.current) {
      fetchingRef.current = false;
      return;
    }

    setStocks(response.stocks);
    setError(null);
    setLastRefresh(new Date());

    if (isInitial) {
      setLoading(false);
    } else {
      setRefreshing(false);
    }

    fetchingRef.current = false;
  }, []);

  // ── Load scheduler status ────────────────────────────────────────

  const loadSchedulerStatus = useCallback(async () => {
    const status = await fetchSchedulerStatus();
    if (mountedRef.current) {
      setSchedulerStatus(status);
    }
  }, []);

  // ── Add a stock ──────────────────────────────────────────────────

  const addStock = useCallback(
    async (symbol: string, market: MarketType = "CN"): Promise<Stock | null> => {
      setError(null);

      const newStock = await apiAddStock(symbol, market);
      if (!mountedRef.current) return null;

      // Refresh the full list to get accurate sort order and count
      await loadStocks();
      return newStock;
    },
    [loadStocks],
  );

  // ── Remove a stock ───────────────────────────────────────────────

  const removeStock = useCallback(
    async (symbol: string): Promise<boolean> => {
      setError(null);

      await apiRemoveStock(symbol);
      if (!mountedRef.current) return false;

      // Optimistic UI: remove from local state immediately
      setStocks((prev) => prev.filter((s) => s.symbol !== symbol));
      return true;
    },
    [],
  );

  // ── Manual refresh (re-fetch from local DB) ──────────────────────

  const refresh = useCallback(async () => {
    await loadStocks();
  }, [loadStocks]);

  // ── Trigger backend refresh (re-fetch from AkShare) ──────────────

  const triggerBackendRefresh = useCallback(async (): Promise<boolean> => {
    setError(null);

    await apiTriggerRefresh();
    if (!mountedRef.current) return false;

    // After backend refresh, reload local data
    await loadStocks();
    return true;
  }, [loadStocks]);

  // ── Update config ────────────────────────────────────────────────

  const updateConfigAction = useCallback(
    async (config: ConfigUpdateRequest): Promise<boolean> => {
      setError(null);

      await apiUpdateConfig(config);
      if (!mountedRef.current) return false;

      // Reload scheduler status after config change
      await loadSchedulerStatus();
      return true;
    },
    [loadSchedulerStatus],
  );

  // ── Initial load ─────────────────────────────────────────────────

  useEffect(() => {
    mountedRef.current = true;
    loadStocks(true);
    loadSchedulerStatus();

    return () => {
      mountedRef.current = false;
    };
  }, [loadStocks, loadSchedulerStatus]);

  // ── Polling ──────────────────────────────────────────────────────

  useEffect(() => {
    if (pollInterval <= 0) return;

    const timer = setInterval(() => {
      loadStocks();
      loadSchedulerStatus();
    }, pollInterval);

    return () => clearInterval(timer);
  }, [pollInterval, loadStocks, loadSchedulerStatus]);

  // ── Return ───────────────────────────────────────────────────────

  return {
    stocks,
    loading,
    refreshing,
    error,
    lastRefresh,
    schedulerStatus,
    pollInterval,
    addStock,
    removeStock,
    refresh,
    triggerBackendRefresh,
    updateConfig: updateConfigAction,
    setPollInterval,
  };
}

export default useStocks;
