interface Props {
  k: number;
  efSearch: number;
  onK: (value: number) => void;
  onEf: (value: number) => void;
}

function Slider({
  label,
  hint,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  hint: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block">
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-sm font-medium text-gray-200">
          {label} <span className="text-indigo-300">{value}</span>
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
        value={efSearch}
        min={10}
        max={200}
        onChange={onEf}
      />
      <Slider
        label="k results"
        hint="how many"
        value={k}
        min={1}
        max={20}
        onChange={onK}
      />
    </div>
  );
}
