import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Pencil, Plus, Trash2 } from "lucide-react";
import { useAuth } from "../../context/useAuth";
import useAdminAnimeDetail from "../../hooks/useAdminAnimeDetail";
import useAdminFactions from "../../hooks/useAdminFactions";
import useAdminCharacters from "../../hooks/useAdminCharacters";
import { deleteAdminCharacter, deleteAdminFaction } from "../../lib/api";
import EditAnimeModal from "./EditAnimeModal";
import FactionFormModal from "./FactionFormModal";
import CharacterFormModal from "./CharacterFormModal";
import ConfirmDeleteModal from "./ConfirmDeleteModal";

function AdminAnimeDetailPage() {
  const [isEditAnimeModalOpen, setIsEditAnimeModalOpen] = useState(false);
  const [factionModalState, setFactionModalState] = useState(null);
  const [characterModalState, setCharacterModalState] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [actionError, setActionError] = useState(null);

  const { animeId } = useParams();
  const { token } = useAuth();
  const {
    anime,
    isLoading: isAnimeLoading,
    error: animeError,
    refetch: refetchAnime,
  } = useAdminAnimeDetail(token, animeId);
  const {
    factions,
    isLoading: isFactionsLoading,
    error: factionsError,
    refetch: refetchFactions,
  } = useAdminFactions(token, animeId);
  const {
    characters,
    isLoading: isCharactersLoading,
    error: charactersError,
    refetch: refetchCharacters,
  } = useAdminCharacters(token, animeId);

  const factionNameById = new Map(
    factions.map((faction) => [faction.id, faction.name]),
  );

  const handleConfirmDelete = async () => {
    if (pendingDelete.type === "faction") {
      await deleteAdminFaction(token, pendingDelete.item.id);
      await Promise.all([refetchFactions(), refetchCharacters()]);
    } else {
      await deleteAdminCharacter(token, pendingDelete.item.id);
      await refetchCharacters();
    }
    setPendingDelete(null);
    setActionError(null);
  };

  const hasError = animeError || factionsError || charactersError;

  return (
    <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <Link
        to="/admin/anime"
        className="mb-4 inline-flex items-center gap-1.5 text-xs font-medium text-[var(--text-muted)]"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Anime Management
      </Link>

      {hasError && (
        <p className="mb-4 rounded-lg border border-[var(--pink)] bg-[var(--pink-light)] p-4 text-sm text-[var(--primary)]">
          {actionError ?? "Could not load this anime's data."}
        </p>
      )}

      {isAnimeLoading && !anime && (
        <div className="h-24 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface-warm)]" />
      )}

      {anime && (
        <div className="mb-6 flex flex-wrap items-start justify-between gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5">
          <div>
            <h1 className="text-xl font-bold text-[var(--primary)]">
              {anime.title}
            </h1>
            <p className="text-xs text-[var(--text-muted)]">
              {anime.slug} &middot; {anime.total_episodes} episodes
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsEditAnimeModalOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-md border border-[var(--primary)] px-3 py-1.5 text-xs font-medium text-[var(--primary)]"
          >
            <Pencil className="h-3.5 w-3.5" />
            Edit Anime
          </button>
        </div>
      )}

      <section className="mb-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-[var(--primary)]">
            Factions
          </h2>
          <button
            type="button"
            onClick={() => setFactionModalState({ mode: "create" })}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--primary)] px-3 py-1.5 text-xs font-medium text-[var(--surface)]"
          >
            <Plus className="h-3.5 w-3.5" />
            Add Faction
          </button>
        </div>

        {isFactionsLoading ? (
          <div className="h-24 animate-pulse rounded-md bg-[var(--surface-warm)]" />
        ) : factions.length === 0 ? (
          <p className="text-xs text-[var(--text-muted)]">No factions yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-md border border-[var(--border)]">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-xs uppercase tracking-wide text-[var(--text-muted)]">
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Parent</th>
                  <th className="px-3 py-2">First Revealed</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {factions.map((faction) => (
                  <tr
                    key={faction.id}
                    className="border-b border-[var(--border)] last:border-0"
                  >
                    <td className="px-3 py-2 font-medium text-[var(--text)]">
                      {faction.name}
                    </td>
                    <td className="px-3 py-2 text-[var(--text-muted)]">
                      {faction.parent_id != null
                        ? (factionNameById.get(faction.parent_id) ?? "—")
                        : "—"}
                    </td>
                    <td className="px-3 py-2 text-[var(--text-muted)]">
                      {faction.first_revealed_at ?? "—"}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center justify-end gap-3">
                        <button
                          type="button"
                          onClick={() =>
                            setFactionModalState({ mode: "edit", faction })
                          }
                          aria-label={`Edit ${faction.name}`}
                          className="text-[var(--primary)]"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            setPendingDelete({ type: "faction", item: faction })
                          }
                          aria-label={`Delete ${faction.name}`}
                          className="text-[var(--pink)]"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-[var(--primary)]">
            Characters
          </h2>
          <button
            type="button"
            onClick={() => setCharacterModalState({ mode: "create" })}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--primary)] px-3 py-1.5 text-xs font-medium text-[var(--surface)]"
          >
            <Plus className="h-3.5 w-3.5" />
            Add Character
          </button>
        </div>

        {isCharactersLoading ? (
          <div className="h-24 animate-pulse rounded-md bg-[var(--surface-warm)]" />
        ) : characters.length === 0 ? (
          <p className="text-xs text-[var(--text-muted)]">No characters yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-md border border-[var(--border)]">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-xs uppercase tracking-wide text-[var(--text-muted)]">
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Role</th>
                  <th className="px-3 py-2">Faction</th>
                  <th className="px-3 py-2">First Revealed</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {characters.map((character) => (
                  <tr
                    key={character.id}
                    className="border-b border-[var(--border)] last:border-0"
                  >
                    <td className="px-3 py-2 font-medium text-[var(--text)]">
                      {character.name}
                    </td>
                    <td className="px-3 py-2 text-[var(--text-muted)]">
                      {character.role ?? "—"}
                    </td>
                    <td className="px-3 py-2 text-[var(--text-muted)]">
                      {character.faction_id != null
                        ? (factionNameById.get(character.faction_id) ?? "—")
                        : "—"}
                    </td>
                    <td className="px-3 py-2 text-[var(--text-muted)]">
                      {character.first_revealed_at}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center justify-end gap-3">
                        <button
                          type="button"
                          onClick={() =>
                            setCharacterModalState({ mode: "edit", character })
                          }
                          aria-label={`Edit ${character.name}`}
                          className="text-[var(--primary)]"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            setPendingDelete({
                              type: "character",
                              item: character,
                            })
                          }
                          aria-label={`Delete ${character.name}`}
                          className="text-[var(--pink)]"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {isEditAnimeModalOpen && anime && (
        <EditAnimeModal
          anime={anime}
          token={token}
          onSaved={() => {
            setIsEditAnimeModalOpen(false);
            refetchAnime();
          }}
          onClose={() => setIsEditAnimeModalOpen(false)}
        />
      )}

      {factionModalState && (
        <FactionFormModal
          animeId={animeId}
          factions={factions}
          existingFaction={factionModalState.faction ?? null}
          token={token}
          onSaved={() => {
            setFactionModalState(null);
            refetchFactions();
          }}
          onClose={() => setFactionModalState(null)}
        />
      )}

      {characterModalState && (
        <CharacterFormModal
          animeId={animeId}
          factions={factions}
          existingCharacter={characterModalState.character ?? null}
          token={token}
          onSaved={() => {
            setCharacterModalState(null);
            refetchCharacters();
          }}
          onClose={() => setCharacterModalState(null)}
        />
      )}

      {pendingDelete && (
        <ConfirmDeleteModal
          title={
            pendingDelete.type === "faction"
              ? "Delete Faction"
              : "Delete Character"
          }
          description={
            pendingDelete.type === "faction"
              ? `Delete "${pendingDelete.item.name}"? Any characters assigned to it (and any child factions) will be unassigned or removed too.`
              : `Delete "${pendingDelete.item.name}"?`
          }
          onConfirm={handleConfirmDelete}
          onClose={() => setPendingDelete(null)}
        />
      )}
    </main>
  );
}

export default AdminAnimeDetailPage;
