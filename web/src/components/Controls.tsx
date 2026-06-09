interface Props {
  k: number;
  efSearch: number;
  onK: (value: number) => void;
  onEf: (value: number) => void;
}

function Slider({
  label,
  hint,
  tooltip,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  hint: string;
  tooltip: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block">
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-sm font-medium text-gray-200">
          <span className="group relative cursor-help border-b border-dotted border-gray-500">
            {label}
            <span className="pointer-events-none absolute bottom-full left-0 z-10 mb-2 hidden w-60 rounded-lg border border-white/10 bg-[#11111a] p-2.5 text-xs font-normal leading-snug text-gray-300 shadow-xl group-hover:block">
              {tooltip}
            </span>
          </span>{" "}
          <span className="text-indigo-300">{value}</span>
        </span>
        <span className="text-xs text-gray-500">{hint}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        aria-label={label}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-indigo-400"
      />
    </label>
  );
}

export function Controls({ k, efSearch, onK, onEf }: Props) {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
      <Slider
        label="ef_search"
        hint="recall ↔ latency"
        tooltip="How many nearby paragraphs the search looks at before it answers. Turn it up for better matches, down for faster replies."
        value={efSearch}
        min={10}
        max={200}
        onChange={onEf}
      />
      <Slider
        label="k results"
        hint="how many"
        tooltip="How many results you get back. Set it to 5 and you'll see the 5 closest paragraphs to what you typed."
        value={k}
        min={1}
        max={20}
        onChange={onK}
      />
    </div>
  );
}
