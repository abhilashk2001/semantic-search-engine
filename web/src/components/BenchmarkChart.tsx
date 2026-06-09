import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import type { BenchmarkResults } from "../types";
import resultsData from "../data/results.json";

const results = resultsData as BenchmarkResults;

export function BenchmarkChart() {
  const [liveRecall, setLiveRecall] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runLiveCheck() {
    setRunning(true);
    setError(null);
    try {
      const res = await api.benchmark(20);
      setLiveRecall(res.recall_at_k);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRunning(false);
    }
  }

  const data = results.sweep.map((p) => ({
    ef: p.ef_search,
    recall: p.recall_at_10,
    latency: p.p50_latency_ms,
  }));

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.03] p-5">
      <h2 className="mb-1 text-sm font-semibold tracking-wide text-gray-300">
        RECALL vs LATENCY
      </h2>
      <p className="mb-3 text-xs text-gray-500">
        {results.n.toLocaleString()} vectors · recall@{results.k} and p50 latency
        as ef_search varies
      </p>
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 8, bottom: 5, left: -8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff12" />
            <XAxis
              dataKey="latency"
              type="number"
              domain={["dataMin", "dataMax"]}
              tickFormatter={(v) => `${v.toFixed(1)}ms`}
              stroke="#9ca3af"
              fontSize={11}
            />
            <YAxis
              dataKey="recall"
              domain={[0.9, 1]}
              tickFormatter={(v) => v.toFixed(2)}
              stroke="#9ca3af"
              fontSize={11}
            />
            <Tooltip
              contentStyle={{
                background: "#11111a",
                border: "1px solid #ffffff20",
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(value: number, name) =>
                name === "recall"
                  ? [value.toFixed(3), "recall@10"]
                  : [`${value}ms`, "p50 latency"]
              }
              labelFormatter={(_, payload) =>
                payload && payload[0]
                  ? `ef_search = ${payload[0].payload.ef}`
                  : ""
              }
            />
            <Line
              type="monotone"
              dataKey="recall"
              stroke="#818cf8"
              strokeWidth={2}
              dot={{ r: 3, fill: "#818cf8" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 flex items-center gap-3">
        <button
          onClick={runLiveCheck}
          disabled={running}
          className="rounded-lg border border-indigo-400/40 bg-indigo-500/10 px-3 py-1.5 text-sm text-indigo-200 transition hover:bg-indigo-500/20 disabled:opacity-50"
        >
          {running ? "checking…" : "run live recall check"}
        </button>
        {liveRecall != null && (
          <span className="font-mono text-sm text-emerald-300">
            live recall@10 = {liveRecall.toFixed(3)}
          </span>
        )}
        {error && <span className="text-sm text-red-300">{error}</span>}
      </div>
    </div>
  );
}
