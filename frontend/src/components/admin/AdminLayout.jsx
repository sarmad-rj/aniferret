import {
  Film,
  LayoutDashboard,
  Loader2,
  LogOut,
  ShieldAlert,
  Users,
} from "lucide-react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../context/useAuth";
import AdminLoginForm from "./AdminLoginForm";

const NAV_LINKS = [
  { label: "Overview", to: "/admin/overview", icon: LayoutDashboard },
  { label: "Anime", to: "/admin/anime", icon: Film },
  { label: "Users", to: "/admin/users", icon: Users },
  { label: "Data Integrity", to: "/admin/data-integrity", icon: ShieldAlert },
];

function AdminLayout() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--background)]">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--primary)]" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AdminLoginForm />;
  }

  if (!user?.is_admin) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[var(--background)] p-4 text-center">
        <p className="text-sm text-[var(--text)]">
          This account does not have admin access.
        </p>
        <button
          type="button"
          onClick={logout}
          className="rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--surface)]"
        >
          Sign Out
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--background)]">
      <aside className="flex h-full w-48 shrink-0 flex-col gap-1 overflow-y-auto border-r border-[var(--border)] bg-[var(--surface)] p-4">
        <Link
          to="/"
          className="mb-4 px-2 text-sm font-bold text-[var(--primary)]"
        >
          AniFerret Admin
        </Link>

        {NAV_LINKS.map(({ label, to, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-md px-2 py-2 text-sm font-medium ${
                isActive
                  ? "bg-[var(--primary)] text-[var(--surface)]"
                  : "text-[var(--text)] hover:bg-[var(--surface-warm)]"
              }`
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}

        <button
          type="button"
          onClick={logout}
          className="mt-auto flex items-center gap-2 rounded-md px-2 py-2 text-left text-sm font-medium text-[var(--text-muted)] hover:bg-[var(--surface-warm)]"
        >
          <LogOut className="h-4 w-4 shrink-0" />
          Sign Out
        </button>
      </aside>

      <div className="h-full min-w-0 flex-1 overflow-y-auto overflow-x-auto">
        <Outlet />
      </div>
    </div>
  );
}

export default AdminLayout;
