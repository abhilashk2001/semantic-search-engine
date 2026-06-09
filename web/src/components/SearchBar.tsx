interface Props {
  value: string;
  onChange: (value: string) => void;
}

export function SearchBar({ value, onChange }: Props) {
  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search 10,000 Wikipedia paragraphs — try “how do volcanoes erupt”"
        aria-label="Search query"
        autoFocus
        className="w-full rounded-xl border border-white/10 bg-white/5 px-5 py-4 text-lg text-gray-100 placeholder-gray-500 outline-none transition focus:border-indigo-400/60 focus:bg-white/10"
      />
    </div>
  );
}
