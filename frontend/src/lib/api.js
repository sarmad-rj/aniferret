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
    const error = new Error(
      body?.detail?.message ?? `Request failed with status ${response.status}`,
    );
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) {
    return null;
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

export function postImportAnime(query, token) {
  return request("/anime/import", {
    method: "POST",
    body: JSON.stringify({ query }),
    headers: authHeaders(token),
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

export function verifyEmail(token) {
  return request("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export function resendVerificationEmail(email) {
  return request("/auth/resend-verification", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function forgotPassword(email) {
  return request("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(token, newPassword) {
  return request("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
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

export function fetchProfile(token) {
  return request("/me/profile", { headers: authHeaders(token) });
}

export function updatePassword(token, currentPassword, newPassword) {
  return request("/me/password", {
    method: "PUT",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
    headers: authHeaders(token),
  });
}

export function deleteAccount(token, password) {
  return request("/me/account", {
    method: "DELETE",
    body: JSON.stringify({ password }),
    headers: authHeaders(token),
  });
}

export function fetchAdminAnimeList(token) {
  return request("/admin/anime", { headers: authHeaders(token) });
}

export function deleteAdminAnime(token, animeId) {
  return request(`/admin/anime/${animeId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function bulkDeleteAdminAnime(token, animeIds) {
  return request("/admin/anime/bulk-delete", {
    method: "POST",
    body: JSON.stringify({ ids: animeIds }),
    headers: authHeaders(token),
  });
}

export function fetchAdminUsers(token) {
  return request("/admin/users", { headers: authHeaders(token) });
}

export function verifyAdminUser(token, userId) {
  return request(`/admin/users/${userId}/verify`, {
    method: "PUT",
    headers: authHeaders(token),
  });
}

export function deleteAdminUser(token, userId) {
  return request(`/admin/users/${userId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function bulkDeleteAdminUsers(token, userIds) {
  return request("/admin/users/bulk-delete", {
    method: "POST",
    body: JSON.stringify({ ids: userIds }),
    headers: authHeaders(token),
  });
}

export function fetchAdminSystemStatus(token) {
  return request("/admin/system-status", { headers: authHeaders(token) });
}

export function fetchAdminDataIntegrityReport(token) {
  return request("/admin/data-integrity", { headers: authHeaders(token) });
}

export function fixAdminAnimeEpisodeCounts(
  token,
  animeId,
  totalEpisodes,
  seasonEpisodeCounts,
) {
  return request(`/admin/anime/${animeId}/episode-counts`, {
    method: "PATCH",
    body: JSON.stringify({
      total_episodes: totalEpisodes,
      season_episode_counts: seasonEpisodeCounts,
    }),
    headers: authHeaders(token),
  });
}

export function fixAdminCharacterCheckpoint(
  token,
  characterId,
  firstRevealedAt,
) {
  return request(`/admin/characters/${characterId}/checkpoint`, {
    method: "PATCH",
    body: JSON.stringify({ first_revealed_at: firstRevealedAt }),
    headers: authHeaders(token),
  });
}

export function fixAdminFactCheckpoint(token, factId, field, checkpoint) {
  return request(`/admin/facts/${factId}/checkpoint`, {
    method: "PATCH",
    body: JSON.stringify({ field, checkpoint }),
    headers: authHeaders(token),
  });
}

export function fetchAdminAnimeFactions(token, animeId) {
  return request(`/admin/anime/${animeId}/factions`, {
    headers: authHeaders(token),
  });
}

export function fixAdminCharacterFaction(token, characterId, factionId) {
  return request(`/admin/characters/${characterId}/faction`, {
    method: "PATCH",
    body: JSON.stringify({ faction_id: factionId }),
    headers: authHeaders(token),
  });
}

export function fetchAdminAnimeDetail(token, animeId) {
  return request(`/admin/anime/${animeId}/detail`, {
    headers: authHeaders(token),
  });
}

export function updateAdminAnimeMetadata(token, animeId, metadata) {
  return request(`/admin/anime/${animeId}/metadata`, {
    method: "PATCH",
    body: JSON.stringify(metadata),
    headers: authHeaders(token),
  });
}

export function createAdminFaction(token, animeId, faction) {
  return request(`/admin/anime/${animeId}/factions`, {
    method: "POST",
    body: JSON.stringify(faction),
    headers: authHeaders(token),
  });
}

export function updateAdminFaction(token, factionId, faction) {
  return request(`/admin/factions/${factionId}`, {
    method: "PATCH",
    body: JSON.stringify(faction),
    headers: authHeaders(token),
  });
}

export function deleteAdminFaction(token, factionId) {
  return request(`/admin/factions/${factionId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function fetchAdminAnimeCharacters(token, animeId) {
  return request(`/admin/anime/${animeId}/characters`, {
    headers: authHeaders(token),
  });
}

export function createAdminCharacter(token, animeId, character) {
  return request(`/admin/anime/${animeId}/characters`, {
    method: "POST",
    body: JSON.stringify(character),
    headers: authHeaders(token),
  });
}

export function updateAdminCharacter(token, characterId, character) {
  return request(`/admin/characters/${characterId}`, {
    method: "PATCH",
    body: JSON.stringify(character),
    headers: authHeaders(token),
  });
}

export function deleteAdminCharacter(token, characterId) {
  return request(`/admin/characters/${characterId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}
