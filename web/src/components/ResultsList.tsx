import type { SearchResponse } from "../types";

interface Props {
  data: SearchResponse | null;
  status: "idle" | "loading" | "waking" | "error";
  error: string | null;
}

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(1, score)) * 100;
  return (
    <div className="flex shrink-0 flex-col items-end">
      <span className="font-mono text-sm text-indigo-300">{score.toFixed(3)}</span>
      <div className="mt-1 h-1.5 w-16 overflow-hidden rounded-full bg-white/10">
        <div className="h-full bg-indigo-400" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function ResultsList({ data, status, error }: Props) {
  if (status === "error") {
    return (
      <p className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-300">
        {error ?? "Something went wrong."}
      </p>
    );
  }

  if (status === "waking") {
    return (
      <p className="animate-pulse p-4 text-gray-400">
        Waking the server… the free-tier backend spins down when idle. This takes
        a few seconds on the first request.
      </p>
    );
  }

  if (!data) {
    return (
      <p className="p-4 text-gray-500">
        Type a phrase above to search by meaning, not keywords.
      </p>
    );
  }

  if (data.results.length === 0) {
    return <p className="p-4 text-gray-500">No results.</p>;
  }

  return (
    <div>
      <div className="mb-3 flex items-center gap-2 text-sm text-gray-400">
        <span className="rounded-full bg-emerald-500/15 px-2.5 py-0.5 font-mono text-emerald-300">
          found in {data.latency_ms.toFixed(2)} ms
        </span>
        <span>
          top {data.results.length} · ef_search {data.ef_search}
        </span>
      </div>
      <ul className="space-y-2">
        {data.results.map((r) => (
          <li
            key={r.id}
            className="flex items-start gap-4 rounded-lg border border-white/5 bg-white/[0.03] p-4 transition hover:bg-white/[0.06]"
          >
            <p className="flex-1 leading-relaxed text-gray-200">{r.text}</p>
            <ScoreBadge score={r.score} />
          </li>
        ))}
      </ul>
    </div>
  );
}
