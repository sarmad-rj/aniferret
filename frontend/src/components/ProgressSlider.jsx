import { useMemo, useState } from "react";
import { Lock, MapPin } from "lucide-react";
import {
  buildCheckpointSequence,
  formatCheckpointLabel,
  parseCheckpointEpisode,
} from "../lib/checkpoint";

function ProgressSlider({
  anime,
  checkpoint,
  onCheckpointChange,
  disabled = false,
}) {
  const [isScrubbing, setIsScrubbing] = useState(false);

  const sequence = useMemo(
    () => buildCheckpointSequence(anime?.season_episode_counts),
    [anime],
  );

  if (sequence.length === 0) {
    return null;
  }

  const currentIndex = Math.max(sequence.indexOf(checkpoint), 0);
  const percentComplete =
    sequence.length > 1 ? (currentIndex / (sequence.length - 1)) * 100 : 0;
  const currentEpisode = parseCheckpointEpisode(checkpoint);

  const handleSliderChange = (event) => {
    const nextIndex = Number(event.target.value);
    onCheckpointChange(sequence[nextIndex]);
  };

  const showTooltip = isScrubbing && !disabled;

  return (
    <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 sm:p-6">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-[var(--primary)]">
          Watch Progress
          {disabled && (
            <span className="ml-2 text-xs font-normal text-[var(--text-muted)]">
              (locked by Group Mode)
            </span>
          )}
        </h2>
        <span className="inline-flex items-center gap-1 rounded-full bg-[var(--pink-light)] px-3 py-1 text-xs font-medium text-[var(--primary)]">
          <Lock className="h-3.5 w-3.5 text-[var(--pink)]" />
          Information available up to {formatCheckpointLabel(checkpoint)}
        </span>
      </div>

      <div className="relative pt-9">
        {showTooltip && currentEpisode !== null && (
          <div
            className="pointer-events-none absolute top-0 flex -translate-x-1/2 flex-col items-center"
            style={{ left: `${percentComplete}%` }}
          >
            <span className="inline-flex items-center gap-1 whitespace-nowrap rounded-full bg-[var(--primary)] px-2.5 py-1 text-xs font-semibold text-[var(--surface)] shadow-sm">
              <MapPin className="h-3 w-3 text-[var(--sky)]" />
              Ep. {currentEpisode}
            </span>
            <span className="-mt-px h-2 w-2 rotate-45 bg-[var(--primary)]" />
          </div>
        )}

        <input
          type="range"
          min="0"
          max={sequence.length - 1}
          value={currentIndex}
          onChange={handleSliderChange}
          onMouseEnter={() => setIsScrubbing(true)}
          onMouseLeave={() => setIsScrubbing(false)}
          onFocus={() => setIsScrubbing(true)}
          onBlur={() => setIsScrubbing(false)}
          onTouchStart={() => setIsScrubbing(true)}
          onTouchEnd={() => setIsScrubbing(false)}
          disabled={disabled}
          className="progress-range disabled:opacity-50"
          style={{
            background: `linear-gradient(to right, var(--sky) ${percentComplete}%, var(--border) ${percentComplete}%)`,
          }}
          aria-label="Watch progress checkpoint"
        />
      </div>

      <div className="mt-2 flex justify-between text-xs text-[var(--text-muted)]">
        <span>{sequence[0]}</span>
        <span>{sequence[sequence.length - 1]}</span>
      </div>
    </section>
  );
}

export default ProgressSlider;
