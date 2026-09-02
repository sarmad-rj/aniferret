const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

async function request(path, options = {}) {
  const { headers: extraHeaders, ...restOptions } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...extraHeaders },
    ...restOptions,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      body?.detail?.message ?? `Request failed with status ${response.status}`,
    );
  }

  return response.json();
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
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

export function postGroupSessionEvaluate(checkpoints, token) {
  return request("/group-session/evaluate", {
    method: "POST",
    body: JSON.stringify({ checkpoints }),
    headers: authHeaders(token),
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

export function registerUser({ email, password, displayName }) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
}

export function loginUser({ email, password }) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function fetchCurrentUser(token) {
  return request("/auth/me", { headers: authHeaders(token) });
}

export function fetchWatchProgress(token) {
  return request("/me/watch-progress", { headers: authHeaders(token) });
}

export function saveWatchProgress(token, entries) {
  return request("/me/watch-progress", {
    method: "PUT",
    body: JSON.stringify({ entries }),
    headers: authHeaders(token),
  });
}
