const CHECKPOINT_RE = /^S(\d+)E(\d+)$/i;

export function buildCheckpointSequence(seasonEpisodeCounts) {
  const sequence = [];
  (seasonEpisodeCounts ?? []).forEach((episodeCount, seasonIndex) => {
    const season = seasonIndex + 1;
    for (let episode = 1; episode <= episodeCount; episode += 1) {
      sequence.push(`S${season}E${episode}`);
    }
  });
  return sequence;
}

export function formatCheckpointLabel(checkpoint) {
  const match = CHECKPOINT_RE.exec(checkpoint ?? "");
  if (!match) {
    return checkpoint ?? "";
  }
  const [, season, episode] = match;
  return `Season ${season}, Episode ${episode}`;
}

export function parseCheckpointEpisode(checkpoint) {
  const match = CHECKPOINT_RE.exec(checkpoint ?? "");
  return match ? Number(match[2]) : null;
}

export function isValidCheckpointFormat(checkpoint) {
  return CHECKPOINT_RE.test(checkpoint ?? "");
}

export function checkpointFromCumulativeEpisodes(
  seasonEpisodeCounts,
  watchedEpisodes,
) {
  const counts = seasonEpisodeCounts ?? [];
  if (counts.length === 0) {
    return null;
  }

  // Treats watchedEpisodes as a running count across seasons back-to-back. This
  // is exact when the count actually came from the franchise's season-1 MAL
  // entry (the common case for a multi-season match, since AniFerret's stored
  // mal_id is conventionally season 1's) -- watchedEpisodes never exceeds season
  // 1's own length in that case, so it always resolves within season 1
  // correctly. For any other case it's a best-effort starting point, not a
  // guarantee -- the caller must still treat this as an editable default, never
  // submit it without the user seeing and confirming it (see MalSkippedEntry's
  // docstring on the backend for why).
  let remaining = Math.max(watchedEpisodes, 1);
  for (let seasonIndex = 0; seasonIndex < counts.length; seasonIndex += 1) {
    const seasonLength = counts[seasonIndex];
    if (remaining <= seasonLength) {
      return `S${seasonIndex + 1}E${remaining}`;
    }
    remaining -= seasonLength;
  }

  const lastSeason = counts.length;
  return `S${lastSeason}E${counts[lastSeason - 1]}`;
}
