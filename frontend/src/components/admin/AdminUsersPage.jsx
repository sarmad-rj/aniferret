import { useState } from "react";
import { BadgeCheck, Search, ShieldCheck, Trash2 } from "lucide-react";
import { useAuth } from "../../context/useAuth";
import useAdminUsers from "../../hooks/useAdminUsers";
import {
  bulkDeleteAdminUsers,
  deleteAdminUser,
  verifyAdminUser,
} from "../../lib/api";
import ConfirmDeleteModal from "./ConfirmDeleteModal";

function AdminUsersPage() {
  const [pendingUserId, setPendingUserId] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [pendingDelete, setPendingDelete] = useState(null);

  const { token, user: currentAdmin } = useAuth();
  const { users, isLoading, error: fetchError, refetch } = useAdminUsers(token);

  const trimmedQuery = searchQuery.trim().toLowerCase();
  const visibleUsers = trimmedQuery
    ? users.filter(
        (rowUser) =>
          rowUser.email.toLowerCase().includes(trimmedQuery) ||
          (rowUser.display_name ?? "").toLowerCase().includes(trimmedQuery),
      )
    : users;

  // The admin's own row is never selectable -- deleting yourself has no re-auth
  // step here, unlike the Profile page's password-confirmed flow, so it's blocked
  // both server-side and by never offering the checkbox in the first place.
  const selectableVisibleUsers = visibleUsers.filter(
    (rowUser) => rowUser.id !== currentAdmin?.id,
  );
  const visibleSelectedCount = selectableVisibleUsers.filter((rowUser) =>
    selectedIds.has(rowUser.id),
  ).length;
  const areAllVisibleSelected =
    selectableVisibleUsers.length > 0 &&
    visibleSelectedCount === selectableVisibleUsers.length;

  const toggleSelected = (userId) => {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      if (next.has(userId)) {
        next.delete(userId);
      } else {
        next.add(userId);
      }
      return next;
    });
  };

  const toggleSelectAllVisible = () => {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      if (areAllVisibleSelected) {
        selectableVisibleUsers.forEach((rowUser) => next.delete(rowUser.id));
      } else {
        selectableVisibleUsers.forEach((rowUser) => next.add(rowUser.id));
      }
      return next;
    });
  };

  const handleVerify = async (targetUser) => {
    setActionError(null);
    setPendingUserId(targetUser.id);
    try {
      await verifyAdminUser(token, targetUser.id);
      await refetch();
    } catch {
      setActionError(
        `Could not verify "${targetUser.email}". Please try again.`,
      );
    } finally {
      setPendingUserId(null);
    }
  };

  const handleConfirmDelete = async () => {
    // No catch here on purpose: a total failure should propagate to
    // ConfirmDeleteModal's own inline error and keep the modal open. A partial
    // bulk failure still counts as a completed action (some rows did get
    // deleted), so that closes the modal and surfaces a summary on the page.
    if (pendingDelete.type === "single") {
      await deleteAdminUser(token, pendingDelete.targetUser.id);
      await refetch();
      setPendingDelete(null);
      setActionError(null);
    } else {
      const result = await bulkDeleteAdminUsers(token, pendingDelete.ids);
      await refetch();
      setSelectedIds(new Set());
      setPendingDelete(null);
      setActionError(
        result.failed.length > 0
          ? `${result.deleted_ids.length} deleted, ${result.failed.length} could not be deleted.`
          : null,
      );
    }
  };

  return (
    <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold text-[var(--primary)]">
          User Management
        </h1>
        {selectedIds.size > 0 && (
          <button
            type="button"
            onClick={() =>
              setPendingDelete({ type: "bulk", ids: Array.from(selectedIds) })
            }
            className="inline-flex items-center gap-1.5 rounded-md border border-[var(--pink)] px-3 py-1.5 text-sm font-medium text-[var(--pink)]"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Delete Selected ({selectedIds.size})
          </button>
        )}
      </div>

      {(fetchError || actionError) && (
        <p className="mb-4 rounded-lg border border-[var(--pink)] bg-[var(--pink-light)] p-4 text-sm text-[var(--primary)]">
          {actionError ?? "Could not load users."}
        </p>
      )}

      {!isLoading && users.length > 0 && (
        <div className="relative mb-4 max-w-xs">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search by email or name..."
            aria-label="Search users"
            className="w-full rounded-md border border-[var(--border)] bg-[var(--surface)] py-1.5 pl-8 pr-3 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)]"
          />
        </div>
      )}

      {isLoading ? (
        <div className="h-40 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface-warm)]" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-[var(--border)] bg-[var(--surface)]">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-xs uppercase tracking-wide text-[var(--text-muted)]">
                <th className="w-8 px-4 py-3">
                  {selectableVisibleUsers.length > 0 && (
                    <input
                      type="checkbox"
                      checked={areAllVisibleSelected}
                      onChange={toggleSelectAllVisible}
                      aria-label="Select all users"
                    />
                  )}
                </th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Display Name</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Joined</th>
                <th className="px-4 py-3">Series Tracked</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {visibleUsers.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-6 text-center text-[var(--text-muted)]"
                  >
                    {users.length === 0
                      ? "No users yet."
                      : "No users match your search."}
                  </td>
                </tr>
              ) : (
                visibleUsers.map((rowUser) => {
                  const isSelf = rowUser.id === currentAdmin?.id;
                  const isPending = pendingUserId === rowUser.id;

                  return (
                    <tr
                      key={rowUser.id}
                      className="border-b border-[var(--border)] last:border-0"
                    >
                      <td className="px-4 py-3">
                        {!isSelf && (
                          <input
                            type="checkbox"
                            checked={selectedIds.has(rowUser.id)}
                            onChange={() => toggleSelected(rowUser.id)}
                            aria-label={`Select ${rowUser.email}`}
                          />
                        )}
                      </td>
                      <td className="px-4 py-3 font-medium text-[var(--text)]">
                        {rowUser.email}
                      </td>
                      <td className="px-4 py-3 text-[var(--text-muted)]">
                        {rowUser.display_name ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1.5">
                          {rowUser.is_verified ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-[var(--pink-light)] px-2 py-0.5 text-xs font-medium text-[var(--primary)]">
                              <BadgeCheck className="h-3 w-3 text-[var(--pink)]" />
                              Verified
                            </span>
                          ) : (
                            <span className="inline-flex items-center rounded-full border border-[var(--border)] px-2 py-0.5 text-xs font-medium text-[var(--text-muted)]">
                              Unverified
                            </span>
                          )}
                          {rowUser.is_admin && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-[var(--sky)]/25 px-2 py-0.5 text-xs font-medium text-[var(--primary)]">
                              <ShieldCheck className="h-3 w-3" />
                              Admin
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-[var(--text-muted)]">
                        {new Date(rowUser.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-[var(--text-muted)]">
                        {rowUser.tracked_series_count}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-3">
                          {!rowUser.is_verified && (
                            <button
                              type="button"
                              onClick={() => handleVerify(rowUser)}
                              disabled={isPending}
                              className="text-xs font-medium text-[var(--primary)] underline disabled:opacity-50"
                            >
                              Mark Verified
                            </button>
                          )}
                          {!isSelf && (
                            <button
                              type="button"
                              onClick={() =>
                                setPendingDelete({
                                  type: "single",
                                  targetUser: rowUser,
                                })
                              }
                              disabled={isPending}
                              aria-label={`Delete ${rowUser.email}`}
                              className="text-[var(--pink)] disabled:opacity-50"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      )}

      {pendingDelete?.type === "single" && (
        <ConfirmDeleteModal
          title="Delete User"
          description={`Delete "${pendingDelete.targetUser.email}"? This removes their account and all watch progress.`}
          onConfirm={handleConfirmDelete}
          onClose={() => setPendingDelete(null)}
        />
      )}
      {pendingDelete?.type === "bulk" && (
        <ConfirmDeleteModal
          title="Delete Selected Users"
          description={`Delete ${pendingDelete.ids.length} users? This removes their accounts and all watch progress.`}
          onConfirm={handleConfirmDelete}
          onClose={() => setPendingDelete(null)}
        />
      )}
    </main>
  );
}

export default AdminUsersPage;
