const SELECTED_ANIME_STORAGE_KEY = "aniferret_selected_anime";

export function getStoredSelectedSlug() {
  try {
    return localStorage.getItem(SELECTED_ANIME_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredSelectedSlug(slug) {
  try {
    if (slug) {
      localStorage.setItem(SELECTED_ANIME_STORAGE_KEY, slug);
    } else {
      localStorage.removeItem(SELECTED_ANIME_STORAGE_KEY);
    }
  } catch {
    // Storage unavailable — selection just won't survive a refresh.
  }
}
