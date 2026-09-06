import {
  BadgeCheck,
  Film,
  ListChecks,
  Mail,
  MailWarning,
  Users,
} from "lucide-react";
import { useAuth } from "../../context/useAuth";
import useAdminAnime from "../../hooks/useAdminAnime";
import useAdminUsers from "../../hooks/useAdminUsers";
import useAdminSystemStatus from "../../hooks/useAdminSystemStatus";

function StatCard({ icon: Icon, value, label }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--sky)]/25">
        <Icon className="h-5 w-5 text-[var(--primary)]" />
      </div>
      <div>
        <p className="text-lg font-bold text-[var(--primary)]">{value}</p>
        <p className="text-xs text-[var(--text-muted)]">{label}</p>
      </div>
    </div>
  );
}

function AdminOverviewPage() {
  const { token } = useAuth();
  const {
    animeList,
    isLoading: isAnimeLoading,
    error: animeError,
  } = useAdminAnime(token);
  const {
    users,
    isLoading: isUsersLoading,
    error: usersError,
  } = useAdminUsers(token);
  const { status: systemStatus, isLoading: isStatusLoading } =
    useAdminSystemStatus(token);

  const hasError = animeError || usersError;
  const totalUsers = users.length;
  const verifiedUsers = users.filter((rowUser) => rowUser.is_verified).length;
  const totalTrackedSeries = users.reduce(
    (sum, rowUser) => sum + rowUser.tracked_series_count,
    0,
  );

  return (
    <main className="mx-auto max-w-4xl px-4 py-6 sm:px-6">
      <h1 className="mb-6 text-xl font-bold text-[var(--primary)]">Overview</h1>

      {hasError && (
        <p className="rounded-lg border border-[var(--pink)] bg-[var(--pink-light)] p-4 text-sm text-[var(--primary)]">
          Could not load admin data. Is the AniFerret backend running?
        </p>
      )}

      {!hasError && (
        <div className="grid grid-cols-1 gap-4 sm:max-w-3xl sm:grid-cols-2 lg:grid-cols-3">
          <StatCard
            icon={Film}
            value={isAnimeLoading ? "…" : animeList.length}
            label="Total Anime"
          />
          <StatCard
            icon={Users}
            value={isUsersLoading ? "…" : totalUsers}
            label="Total Users"
          />
          <StatCard
            icon={BadgeCheck}
            value={isUsersLoading ? "…" : `${verifiedUsers} / ${totalUsers}`}
            label="Verified Users"
          />
          <StatCard
            icon={ListChecks}
            value={isUsersLoading ? "…" : totalTrackedSeries}
            label="Series Tracked (All Users)"
          />

          <div className="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
                systemStatus?.smtp_configured
                  ? "bg-[var(--sky)]/25"
                  : "bg-[var(--pink-light)]"
              }`}
            >
              {systemStatus?.smtp_configured ? (
                <Mail className="h-5 w-5 text-[var(--primary)]" />
              ) : (
                <MailWarning className="h-5 w-5 text-[var(--pink)]" />
              )}
            </div>
            <div>
              <p className="text-sm font-bold text-[var(--primary)]">
                {isStatusLoading
                  ? "…"
                  : systemStatus?.smtp_configured
                    ? "Configured"
                    : "Not Configured"}
              </p>
              <p className="text-xs text-[var(--text-muted)]">
                Email Delivery (SMTP)
              </p>
            </div>
          </div>
        </div>
      )}

      {!isStatusLoading && systemStatus && !systemStatus.smtp_configured && (
        <p className="mt-4 max-w-2xl rounded-lg border border-[var(--pink)] bg-[var(--pink-light)] p-4 text-xs text-[var(--primary)]">
          SMTP isn&apos;t configured, so verification and password-reset emails
          are silently skipped (logged, never sent). Use the Users page&apos;s
          &quot;Mark Verified&quot; action to unblock an account manually.
        </p>
      )}
    </main>
  );
}

export default AdminOverviewPage;
