const EXAMPLES = [
  "how do volcanoes erupt",
  "effects of climate change on the planet",
  "famous classical music composers",
  "how does the human heart work",
  "the history of ancient Rome",
  "what causes the northern lights",
  "how do airplanes stay in the air",
  "the life cycle of a star",
  "why is the ocean salty",
  "how vaccines protect against disease",
  "the rules of the game of chess",
  "how photosynthesis works in plants",
];

interface Props {
  onPick: (query: string) => void;
}

export function SurpriseButton({ onPick }: Props) {
  function surprise() {
    const choice = EXAMPLES[Math.floor(Math.random() * EXAMPLES.length)];
    onPick(choice);
  }
  return (
    <button
      onClick={surprise}
      className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-300 transition hover:bg-white/10"
    >
      ✨ Surprise me
    </button>
  );
}
