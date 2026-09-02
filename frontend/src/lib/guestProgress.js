const STORAGE_KEY = "aniferret_guest_progress";

function readAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function writeAll(progress) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch {
    // Storage unavailable (private browsing, quota, etc.) — guest progress just
    // won't persist across a refresh; nothing else depends on this succeeding.
  }
}

export function getGuestCheckpoint(animeSlug) {
  return readAll()[animeSlug] ?? null;
}

export function setGuestCheckpoint(animeSlug, checkpoint) {
  const progress = readAll();
  progress[animeSlug] = checkpoint;
  writeAll(progress);
}

export function getAllGuestProgress() {
  return Object.entries(readAll()).map(([animeSlug, checkpoint]) => ({
    anime_slug: animeSlug,
    checkpoint,
  }));
}

export function clearGuestProgress() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to do if storage is unavailable.
  }
}
