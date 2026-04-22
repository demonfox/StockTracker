/**
 * Root application component for StockTracker.
 *
 * Composes the full dashboard layout:
 * - Header with branding, status indicators, and controls
 * - Market summary strip with stat cards
 * - StockTable with sortable columns and color-coded data
 * - AddStockModal for adding new tickers
 * - Footer with attribution
 */

import { useState } from "react";
import { useStocks } from "./hooks/useStocks";
import Header from "./components/Header";
import MarketSummary from "./components/MarketSummary";
import StockTable from "./components/StockTable";
import AddStockModal from "./components/AddStockModal";

function App() {
  const {
    stocks,
    loading,
    refreshing,
    error,
    lastRefresh,
    schedulerStatus,
    pollInterval,
    addStock,
    removeStock,
    triggerBackendRefresh,
    updateConfig,
    setPollInterval,
  } = useStocks();

  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-surface-background font-sans">
      {/* ── Header ── */}
      <Header
        schedulerStatus={schedulerStatus}
        lastRefresh={lastRefresh}
        refreshing={refreshing}
        stockCount={stocks.length}
        pollInterval={pollInterval}
        onRefresh={triggerBackendRefresh}
        onAddStock={() => setModalOpen(true)}
        onPollIntervalChange={setPollInterval}
        onUpdateConfig={updateConfig}
      />

      {/* ── Main Content ── */}
      <main className="max-w-[1440px] mx-auto px-4 sm:px-6 py-5 pt-5 space-y-5">
        {/* Error banner */}
        {error && (
          <div
            className="flex items-center gap-2 p-3.5 rounded-xl bg-red-50 border border-red-100
                        text-red-700 text-sm animate-in fade-in slide-in-from-top-2 duration-300"
          >
            <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Market Summary Strip */}
        <MarketSummary
          stockCount={stocks.length}
          schedulerStatus={schedulerStatus}
          lastRefresh={lastRefresh}
          refreshing={refreshing}
          pollInterval={pollInterval}
          onRefresh={triggerBackendRefresh}
        />

        {/* Stock Data Table */}
        <StockTable
          stocks={stocks}
          loading={loading}
          onRemoveStock={removeStock}
          onAddStock={() => setModalOpen(true)}
        />
      </main>

      {/* ── Footer ── */}
      <footer className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 flex items-center justify-between">
        <p className="text-[11px] text-content-muted">
          数据来源:{" "}
          <a
            href="https://github.com/akfamily/akshare"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary/70 hover:text-primary transition-colors"
          >
            AkShare
          </a>
          {" · 仅供参考，不构成投资建议"}
        </p>
        <a
          href="/api/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="text-[11px] text-content-muted hover:text-primary transition-colors"
        >
          API 文档 ↗
        </a>
      </footer>

      {/* ── Add Stock Modal ── */}
      <AddStockModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onAdd={addStock}
      />
    </div>
  );
}

export default App;
