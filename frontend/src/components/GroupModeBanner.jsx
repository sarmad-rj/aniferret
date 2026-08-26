import { Users, X } from "lucide-react";
import { formatCheckpointLabel } from "../lib/checkpoint";

function GroupModeBanner({ checkpoint, onExit }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-[var(--ferret)] bg-[var(--surface-warm)] px-4 py-2.5 text-sm">
      <span className="flex items-center gap-2 text-[var(--primary)]">
        <Users className="h-4 w-4 text-[var(--ferret)]" />
        Group Mode active — locked to {formatCheckpointLabel(checkpoint)}
      </span>
      <button
        type="button"
        onClick={onExit}
        className="inline-flex items-center gap-1 text-xs font-medium text-[var(--text-muted)]"
      >
        <X className="h-3.5 w-3.5" />
        Exit
      </button>
    </div>
  );
}

export default GroupModeBanner;
