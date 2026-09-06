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
