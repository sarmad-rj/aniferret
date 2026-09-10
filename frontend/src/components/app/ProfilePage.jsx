import { useEffect, useRef, useState } from "react";
import {
  Link,
  Navigate,
  useNavigate,
  useOutletContext,
} from "react-router-dom";
import {
  ArrowLeft,
  BadgeCheck,
  CalendarDays,
  Film,
  Loader2,
  Lock,
  Mail,
  MapPin,
  Tv,
  UserCircle2,
} from "lucide-react";
import { useAuth } from "../../context/useAuth";
import useProfile from "../../hooks/useProfile";
import { deleteAccount, updatePassword } from "../../lib/api";
import { formatCheckpointLabel } from "../../lib/checkpoint";
import DeleteAccountModal from "../DeleteAccountModal";

function StatCard({ icon: Icon, label, value }) {
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

function CheckpointCard({ card }) {
  const percentComplete =
    card.total_episodes > 0
      ? Math.min(100, (card.current_episode / card.total_episodes) * 100)
      : 0;

  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface)]">
      {card.cover_image_url ? (
        <img
          src={card.cover_image_url}
          alt={card.anime_title}
          className="h-40 w-full object-cover object-top"
        />
      ) : (
        <div className="flex h-40 w-full items-center justify-center bg-[var(--surface-warm)]">
          <Film className="h-8 w-8 text-[var(--ferret)]" />
        </div>
      )}

      <div className="flex flex-1 flex-col gap-2 p-4">
        <h3 className="text-sm font-semibold text-[var(--text)]">
          {card.anime_title}
        </h3>
        <p className="text-xs text-[var(--text-muted)]">
          {formatCheckpointLabel(card.checkpoint)}
        </p>

        <div className="mt-1">
          <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--border)]">
            <div
              className="h-full rounded-full bg-[var(--sky)]"
              style={{ width: `${percentComplete}%` }}
            />
          </div>
          <p className="mt-1 text-xs font-medium text-[var(--text-muted)]">
            Episode {card.current_episode} / {card.total_episodes}
          </p>
        </div>

        <Link
          to={`/app/dossiers?anime=${card.anime_slug}&checkpoint=${encodeURIComponent(card.checkpoint)}`}
          className="mt-auto inline-flex items-center justify-center gap-1.5 rounded-md bg-[var(--primary)] px-3 py-2 text-xs font-medium text-[var(--surface)]"
        >
          <MapPin className="h-3.5 w-3.5" />
          Resume Timeline
        </Link>
      </div>
    </div>
  );
}

function ProfilePage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isSavingPassword, setIsSavingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState(null);
  const [passwordSuccess, setPasswordSuccess] = useState(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  const isFirstImportVersionRef = useRef(true);

  const navigate = useNavigate();
  const { watchProgressImportVersion } = useOutletContext();
  const {
    token,
    isAuthenticated,
    isLoading: isAuthLoading,
    logout,
  } = useAuth();
  const {
    profile,
    isLoading: isProfileLoading,
    error: profileError,
    refetch: refetchProfile,
  } = useProfile(token);

  useEffect(() => {
    // Skip the initial mount -- useProfile's own mount effect already fetches
    // once; this only needs to re-fetch on later bumps (an import completed
    // while already on this page, where Header/ProfilePage are persistent
    // siblings under AppLayout, not remounted by the import itself).
    if (isFirstImportVersionRef.current) {
      isFirstImportVersionRef.current = false;
      return;
    }
    refetchProfile();
  }, [watchProgressImportVersion, refetchProfile]);

  const handlePasswordSubmit = async (event) => {
    event.preventDefault();
    if (isSavingPassword) {
      return;
    }

    setPasswordError(null);
    setPasswordSuccess(null);
    setIsSavingPassword(true);
    try {
      await updatePassword(token, currentPassword, newPassword);
      setPasswordSuccess("Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (submitError) {
      if (submitError.status === 401) {
        setPasswordError("Current password is incorrect.");
      } else if (submitError.status === 422) {
        setPasswordError("New password must be at least 8 characters.");
      } else {
        setPasswordError("Could not update your password. Please try again.");
      }
    } finally {
      setIsSavingPassword(false);
    }
  };

  const handleConfirmDelete = async (password) => {
    setDeleteError(null);
    try {
      await deleteAccount(token, password);
    } catch (deleteAccountError) {
      setDeleteError(
        deleteAccountError.status === 401
          ? "That password is incorrect."
          : "Could not delete your account. Please try again.",
      );
      throw deleteAccountError;
    }
    logout();
    window.location.assign("/");
  };

  if (isAuthLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--primary)]" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <button
        type="button"
        onClick={() => navigate("/app/dossiers")}
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-[var(--text-muted)] hover:text-[var(--primary)]"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>

      <h1 className="mb-6 text-xl font-bold text-[var(--primary)]">
        My Profile
      </h1>

      {profileError && (
        <p className="mb-6 rounded-lg border border-[var(--pink)] bg-[var(--pink-light)] p-4 text-sm text-[var(--primary)]">
          Could not load your profile. Is the AniFerret backend running?
        </p>
      )}

      {isProfileLoading && !profile && (
        <div className="h-40 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface-warm)]" />
      )}

      {profile && (
        <>
          <section className="mb-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-[var(--surface-warm)]">
                <UserCircle2 className="h-10 w-10 text-[var(--ferret)]" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-base font-semibold text-[var(--primary)]">
                    {profile.display_name ?? profile.email}
                  </h2>
                  {profile.is_verified && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-[var(--pink-light)] px-2.5 py-1 text-xs font-medium text-[var(--primary)]">
                      <BadgeCheck className="h-3.5 w-3.5 text-[var(--pink)]" />
                      Verified
                    </span>
                  )}
                </div>
                <p className="mt-1 flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
                  <Mail className="h-3.5 w-3.5 shrink-0" />
                  {profile.email}
                </p>
                <p className="mt-1 flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
                  <CalendarDays className="h-3.5 w-3.5 shrink-0" />
                  Joined{" "}
                  {new Date(profile.created_at).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              </div>
            </div>

            <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <StatCard
                icon={Tv}
                label="Total Series Tracked"
                value={profile.stats.total_series_tracked}
              />
              <StatCard
                icon={Film}
                label="Total Episodes Watched"
                value={profile.stats.total_episodes_watched}
              />
            </div>
          </section>

          <section className="mb-6">
            <h2 className="mb-3 text-sm font-semibold text-[var(--primary)]">
              Active Watch Checkpoints
            </h2>
            {profile.checkpoints.length === 0 ? (
              <p className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 text-sm text-[var(--text-muted)]">
                You haven&apos;t started tracking any anime yet.
              </p>
            ) : (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {profile.checkpoints.map((card) => (
                  <CheckpointCard key={card.anime_slug} card={card} />
                ))}
              </div>
            )}
          </section>

          <section className="mb-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[var(--primary)]">
              <Lock className="h-4 w-4 text-[var(--ferret)]" />
              Account Security
            </h2>
            <form
              onSubmit={handlePasswordSubmit}
              className="flex max-w-sm flex-col gap-3"
            >
              <input
                type="password"
                required
                minLength={8}
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                placeholder="Current password"
                disabled={isSavingPassword}
                className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
              />
              <input
                type="password"
                required
                minLength={8}
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                placeholder="New password (min 8 characters)"
                disabled={isSavingPassword}
                className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
              />

              {passwordError && (
                <p className="text-xs text-[var(--pink)]">{passwordError}</p>
              )}
              {passwordSuccess && (
                <p className="text-xs text-[var(--primary)]">
                  {passwordSuccess}
                </p>
              )}

              <button
                type="submit"
                disabled={isSavingPassword}
                className="self-start rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
              >
                {isSavingPassword ? "Updating..." : "Update Password"}
              </button>
            </form>
          </section>

          <section className="rounded-lg border border-[var(--pink)] bg-[var(--surface)] p-5">
            <h2 className="mb-1 text-sm font-semibold text-[var(--primary)]">
              Danger Zone
            </h2>
            <p className="mb-3 text-xs text-[var(--text-muted)]">
              Permanently delete your account and all associated watch progress.
              This cannot be undone.
            </p>
            {deleteError && (
              <p className="mb-3 text-xs text-[var(--pink)]">{deleteError}</p>
            )}
            <button
              type="button"
              onClick={() => setIsDeleteModalOpen(true)}
              className="rounded-md border border-[var(--pink)] px-4 py-2 text-sm font-medium text-[var(--pink)]"
            >
              Delete Account
            </button>
          </section>
        </>
      )}

      {isDeleteModalOpen && (
        <DeleteAccountModal
          onConfirm={handleConfirmDelete}
          onClose={() => setIsDeleteModalOpen(false)}
        />
      )}
    </main>
  );
}

export default ProfilePage;
