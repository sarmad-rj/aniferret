import { Eye, PlayCircle } from "lucide-react";

function RewatchModeToggle({ isRewatchMode, onToggle }) {
  return (
    <div className="inline-flex items-center rounded-full border border-[var(--border)] bg-[var(--surface)] p-1 text-xs font-medium">
      <button
        type="button"
        onClick={() => onToggle(false)}
        className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 transition-colors ${
          isRewatchMode
            ? "text-[var(--text-muted)]"
            : "bg-[var(--primary)] text-[var(--surface)]"
        }`}
      >
        <PlayCircle className="h-3.5 w-3.5" />
        Normal Watch
      </button>
      <button
        type="button"
        onClick={() => onToggle(true)}
        className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 transition-colors ${
          isRewatchMode
            ? "bg-[var(--primary)] text-[var(--surface)]"
            : "text-[var(--text-muted)]"
        }`}
      >
        <Eye className="h-3.5 w-3.5" />
        Foreshadowing Index
      </button>
    </div>
  );
}

export default RewatchModeToggle;
