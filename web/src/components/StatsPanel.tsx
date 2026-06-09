import type { StatsResponse } from "../types";

interface Props {
  stats: StatsResponse | null;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-1 text-sm">
      <span className="text-gray-400">{label}</span>
      <span className="font-mono text-gray-200">{value}</span>
    </div>
  );
}

export function StatsPanel({ stats }: Props) {
  if (!stats) {
    return (
      <div className="rounded-xl border border-white/5 bg-white/[0.03] p-5">
        <h2 className="mb-3 text-sm font-semibold tracking-wide text-gray-300">
          INDEX STATS
        </h2>
        <p className="text-sm text-gray-500">Loading…</p>
      </div>
    );
  }

  const layers = Object.entries(stats.layer_distribution).sort(
    (a, b) => Number(a[0]) - Number(b[0]),
  );

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.03] p-5">
      <h2 className="mb-3 text-sm font-semibold tracking-wide text-gray-300">
        INDEX STATS
      </h2>
      <Row label="vectors" value={stats.node_count.toLocaleString()} />
      <Row label="dimensions" value={String(stats.config.dim)} />
      <Row label="metric" value={stats.config.metric} />
      <Row label="M" value={String(stats.config.M)} />
      <Row label="ef_construction" value={String(stats.config.ef_construction)} />
      {stats.build_time_ms != null && (
        <Row label="build time" value={`${(stats.build_time_ms / 1000).toFixed(1)}s`} />
      )}
      <div className="mt-3 border-t border-white/5 pt-3">
        <span className="text-xs text-gray-500">layer distribution</span>
        <div className="mt-2 space-y-1">
          {layers.map(([layer, count]) => {
            const total = stats.node_count || 1;
            const pct = (count / total) * 100;
            return (
              <div key={layer} className="flex items-center gap-2 text-xs">
                <span className="w-6 text-gray-500">L{layer}</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/10">
                  <div
                    className="h-full bg-indigo-400/70"
                    style={{ width: `${Math.max(pct, 1)}%` }}
                  />
                </div>
                <span className="w-14 text-right font-mono text-gray-400">
                  {count.toLocaleString()}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
