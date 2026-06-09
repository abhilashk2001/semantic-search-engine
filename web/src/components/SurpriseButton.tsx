import { useState } from "react";
import { api } from "../api";

interface Props {
  onPick: (query: string) => void;
}

export function SurpriseButton({ onPick }: Props) {
  const [loading, setLoading] = useState(false);

  async function surprise() {
    setLoading(true);
    try {
      const paragraph = await api.sample();
      onPick(paragraph.text);
    } catch {
      /* leave the query unchanged on failure */
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={surprise}
      disabled={loading}
      title="Pick a random Wikipedia paragraph and find its nearest neighbors"
      className="shrink-0 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-300 transition hover:bg-white/10 disabled:opacity-50"
    >
      {loading ? "picking…" : "✨ Surprise me"}
    </button>
  );
}
