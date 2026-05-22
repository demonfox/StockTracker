/**
 * Custom React hook for market index data.
 *
 * Fetches real-time quotes for major indices across CN, HK, and US
 * markets with configurable polling interval.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchIndices } from "../services/api";
import type { IndicesResponse } from "../types/stock";

// ── Default polling interval (ms) — less frequent than stock data ────
const DEFAULT_INDICES_POLL_INTERVAL = 60_000;

export interface UseIndicesReturn {
  /** Grouped index data by market */
  indices: IndicesResponse | null;
  /** True while the initial fetch is in progress */
  loading: boolean;
  /** Latest error message, or null */
  error: string | null;
}

export function useIndices(
  pollInterval: number = DEFAULT_INDICES_POLL_INTERVAL,
): UseIndicesReturn {
  const [indices, setIndices] = useState<IndicesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const mountedRef = useRef(true);
  const fetchingRef = useRef(false);

  const loadIndices = useCallback(async (isInitial = false) => {
    if (fetchingRef.current) return;
    fetchingRef.current = true;

    if (isInitial) {
      setLoading(true);
    }

    try {
      const data = await fetchIndices();
      if (mountedRef.current) {
        setIndices(data);
        setError(null);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : "Failed to fetch indices");
      }
    } finally {
      if (mountedRef.current && isInitial) {
        setLoading(false);
      }
      fetchingRef.current = false;
    }
  }, []);

  // Initial load
  useEffect(() => {
    mountedRef.current = true;
    loadIndices(true);

    return () => {
      mountedRef.current = false;
    };
  }, [loadIndices]);

  // Polling
  useEffect(() => {
    if (pollInterval <= 0) return;

    const timer = setInterval(() => {
      loadIndices();
    }, pollInterval);

    return () => clearInterval(timer);
  }, [pollInterval, loadIndices]);

  return { indices, loading, error };
}

export default useIndices;
