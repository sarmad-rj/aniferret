import { useState } from "react";
import { Wrench } from "lucide-react";
import { useAuth } from "../../context/useAuth";
import useAdminDataIntegrity from "../../hooks/useAdminDataIntegrity";
import FixEpisodeCountModal from "./FixEpisodeCountModal";
import FixCheckpointModal from "./FixCheckpointModal";
import AssignFactionModal from "./AssignFactionModal";

function StatusBadge({ count }) {
  return (
    <span
      className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${
        count === 0
          ? "bg-[var(--sky)]/25 text-[var(--primary)]"
          : "bg-[var(--pink-light)] text-[var(--primary)]"
      }`}
    >
      {count === 0 ? "All clear" : `${count} flagged`}
    </span>
  );
}

function IntegritySection({ title, description, count, children }) {
  return (
    <section className="mb-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-[var(--primary)]">
            {title}
          </h2>
          <p className="text-xs text-[var(--text-muted)]">{description}</p>
        </div>
        <StatusBadge count={count} />
      </div>
      {count > 0 && children}
    </section>
  );
}

function FixButton({ onClick, label }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1 rounded-md border border-[var(--primary)] px-2 py-1 text-xs font-medium text-[var(--primary)]"
    >
      <Wrench className="h-3 w-3" />
      {label}
    </button>
  );
}

function AdminDataIntegrityPage() {
  const [activeFix, setActiveFix] = useState(null);

  const { token } = useAuth();
  const { report, isLoading, error, refetch } = useAdminDataIntegrity(token);

  const handleFixed = () => {
    setActiveFix(null);
    refetch();
  };

  return (
    <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <h1 className="mb-6 text-xl font-bold text-[var(--primary)]">
        Data Integrity
      </h1>

      {error && (
        <p className="rounded-lg border border-[var(--pink)] bg-[var(--pink-light)] p-4 text-sm text-[var(--primary)]">
          Could not load the data-integrity report.
        </p>
      )}

      {isLoading && !report && (
        <div className="h-40 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface-warm)]" />
      )}

      {report && (
        <>
          <IntegritySection
            title="Episode Count Mismatches"
            description="Anime whose season_episode_counts don't sum to the declared total_episodes."
            count={report.episode_count_mismatches.length}
          >
            <div className="overflow-x-auto rounded-md border border-[var(--border)]">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] text-xs uppercase tracking-wide text-[var(--text-muted)]">
                    <th className="px-3 py-2">Anime</th>
                    <th className="px-3 py-2">Declared Total</th>
                    <th className="px-3 py-2">Season Counts Sum</th>
                    <th className="px-3 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {report.episode_count_mismatches.map((row) => (
                    <tr
                      key={row.anime_slug}
                      className="border-b border-[var(--border)] last:border-0"
                    >
                      <td className="px-3 py-2 font-medium text-[var(--text)]">
                        {row.anime_title}
                      </td>
                      <td className="px-3 py-2 text-[var(--text-muted)]">
                        {row.declared_total_episodes}
                      </td>
                      <td className="px-3 py-2 text-[var(--text-muted)]">
                        {row.season_counts_sum}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <FixButton
                          label="Fix"
                          onClick={() =>
                            setActiveFix({ type: "episode-count", data: row })
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </IntegritySection>

          <IntegritySection
            title="Out-of-Range Checkpoints"
            description="Characters or facts citing a season/episode beyond the anime's declared seasons — the exact bug class that let a later checkpoint wrongly satisfy an earlier one."
            count={report.out_of_range_checkpoints.length}
          >
            <div className="overflow-x-auto rounded-md border border-[var(--border)]">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] text-xs uppercase tracking-wide text-[var(--text-muted)]">
                    <th className="px-3 py-2">Anime</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Entity</th>
                    <th className="px-3 py-2">Field</th>
                    <th className="px-3 py-2">Checkpoint</th>
                    <th className="px-3 py-2">Reason</th>
                    <th className="px-3 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {report.out_of_range_checkpoints.map((row, index) => (
                    <tr
                      // eslint-disable-next-line react/no-array-index-key -- rows have no stable id of their own (a computed report, not a DB entity)
                      key={`${row.entity_type}-${row.entity_id}-${row.field}-${index}`}
                      className="border-b border-[var(--border)] last:border-0"
                    >
                      <td className="px-3 py-2 font-medium text-[var(--text)]">
                        {row.anime_title}
                      </td>
                      <td className="px-3 py-2 text-[var(--text-muted)]">
                        {row.entity_type === "character" ? "Character" : "Fact"}
                      </td>
                      <td className="px-3 py-2 text-[var(--text-muted)]">
                        {row.entity_label}
                      </td>
                      <td className="px-3 py-2 text-[var(--text-muted)]">
                        {row.field}
                      </td>
                      <td className="px-3 py-2 text-[var(--text-muted)]">
                        {row.checkpoint}
                      </td>
                      <td className="px-3 py-2 text-[var(--pink)]">
                        {row.reason}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <FixButton
                          label="Fix"
                          onClick={() =>
                            setActiveFix({ type: "checkpoint", data: row })
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </IntegritySection>

          <IntegritySection
            title="Characters Without a Faction"
            description="Characters with no faction assigned — usually an incomplete import."
            count={report.characters_without_faction.length}
          >
            <div className="overflow-x-auto rounded-md border border-[var(--border)]">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] text-xs uppercase tracking-wide text-[var(--text-muted)]">
                    <th className="px-3 py-2">Anime</th>
                    <th className="px-3 py-2">Character</th>
                    <th className="px-3 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {report.characters_without_faction.map((row) => (
                    <tr
                      key={row.character_id}
                      className="border-b border-[var(--border)] last:border-0"
                    >
                      <td className="px-3 py-2 font-medium text-[var(--text)]">
                        {row.anime_title}
                      </td>
                      <td className="px-3 py-2 text-[var(--text-muted)]">
                        {row.character_name}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <FixButton
                          label="Assign"
                          onClick={() =>
                            setActiveFix({ type: "faction", data: row })
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </IntegritySection>
        </>
      )}

      {activeFix?.type === "episode-count" && (
        <FixEpisodeCountModal
          mismatch={activeFix.data}
          token={token}
          onFixed={handleFixed}
          onClose={() => setActiveFix(null)}
        />
      )}
      {activeFix?.type === "checkpoint" && (
        <FixCheckpointModal
          issue={activeFix.data}
          token={token}
          onFixed={handleFixed}
          onClose={() => setActiveFix(null)}
        />
      )}
      {activeFix?.type === "faction" && (
        <AssignFactionModal
          entry={activeFix.data}
          token={token}
          onFixed={handleFixed}
          onClose={() => setActiveFix(null)}
        />
      )}
    </main>
  );
}

export default AdminDataIntegrityPage;
