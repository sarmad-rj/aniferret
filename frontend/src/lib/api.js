const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      body?.detail?.message ?? `Request failed with status ${response.status}`,
    );
  }

  return response.json();
}

export function fetchAnimeList() {
  return request("/anime");
}

export function fetchDossier(animeSlug, checkpoint) {
  const params = new URLSearchParams({ checkpoint });
  return request(`/dossier/${animeSlug}?${params.toString()}`);
}

export function postQuery({ animeSlug, checkpoint, question }) {
  return request("/query", {
    method: "POST",
    body: JSON.stringify({ anime_slug: animeSlug, checkpoint, question }),
  });
}

export function postGroupSessionEvaluate(checkpoints) {
  return request("/group-session/evaluate", {
    method: "POST",
    body: JSON.stringify({ checkpoints }),
  });
}

export function fetchAnimeSources(animeSlug) {
  return request(`/anime/${animeSlug}/sources`);
}

export function postImportAnime(query) {
  return request("/anime/import", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}

export function fetchWatchOrder(franchiseSlug) {
  return request(`/franchises/${franchiseSlug}/watch-order`);
}
