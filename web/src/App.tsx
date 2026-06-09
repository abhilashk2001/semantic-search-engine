import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { SearchResponse, StatsResponse } from "./types";
import { SearchBar } from "./components/SearchBar";
import { Controls } from "./components/Controls";
import { ResultsList } from "./components/ResultsList";
import { StatsPanel } from "./components/StatsPanel";
import { BenchmarkChart } from "./components/BenchmarkChart";
import { SurpriseButton } from "./components/SurpriseButton";

type Status = "idle" | "loading" | "waking" | "error";

export default function App() {
  const [query, setQuery] = useState("");
  const [k, setK] = useState(10);
  const [efSearch, setEfSearch] = useState(50);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);

  useEffect(() => {
    api.stats().then(setStats).catch(() => undefined);
  }, []);

  const runSearch = useCallback(async (q: string, kk: number, ef: number) => {
    setStatus("loading");
    setError(null);
    const wakeTimer = setTimeout(
      () => setStatus((s) => (s === "loading" ? "waking" : s)),
      3500,
    );
    try {
      const resp = await api.search({ query: q, k: kk, ef_search: ef });
      setData(resp);
      setStatus("idle");
    } catch (e) {
      setError((e as Error).message);
      setStatus("error");
    } finally {
      clearTimeout(wakeTimer);
    }
  }, []);

  // Debounced live search whenever the query or either slider changes.
  useEffect(() => {
    if (!query.trim()) {
      setData(null);
      setStatus("idle");
      return;
    }
    const handle = setTimeout(() => runSearch(query, k, efSearch), 300);
    return () => clearTimeout(handle);
  }, [query, k, efSearch, runSearch]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Semantic Search Engine{" "}
          <span className="text-indigo-400">from Scratch</span>
        </h1>
        <p className="mt-2 max-w-2xl text-gray-400">
          Live semantic search over 10,000 Wikipedia paragraphs. It runs on an{" "}
          <span className="text-gray-200">HNSW vector index I wrote myself</span>,
          with no vector-search libraries doing the work. Type a phrase and it
          finds results by meaning instead of matching keywords.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
        <main className="space-y-5">
          <SearchBar value={query} onChange={setQuery} />
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1">
              <Controls
                k={k}
                efSearch={efSearch}
                onK={setK}
                onEf={setEfSearch}
              />
            </div>
            <SurpriseButton onPick={setQuery} />
          </div>
          <ResultsList data={data} status={status} error={error} />
        </main>

        <aside className="space-y-6">
          <StatsPanel stats={stats} />
          <BenchmarkChart />
        </aside>
      </div>

      <footer className="mt-12 border-t border-white/5 pt-6 text-sm text-gray-600">
        Backend: <span className="font-mono">{api.baseUrl}</span>
      </footer>
    </div>
  );
}
