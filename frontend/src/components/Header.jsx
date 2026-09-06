import { useState } from "react";
import {
  ChevronDown,
  LayoutDashboard,
  LogOut,
  User,
  UserCircle2,
} from "lucide-react";
import { Link } from "react-router-dom";
import logo from "../logo/AniFerret_Logo.png";
import AnimeSearchBar from "./AnimeSearchBar";
import AuthModal from "./AuthModal";
import { useAuth } from "../context/useAuth";

function Header({ animeList, selectedSlug, onSelectAnime }) {
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const { user, isAuthenticated, logout } = useAuth();

  const handleSignOut = () => {
    setIsUserMenuOpen(false);
    logout();
  };

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 bg-[var(--primary)] px-4 py-3 sm:px-6">
      <Link to="/" className="flex items-center gap-2">
        <img
          src={logo}
          alt="AniFerret logo"
          className="h-11 w-11 rounded-full"
        />
        <span className="text-xl font-bold text-[var(--surface)]">
          AniFerret
        </span>
      </Link>

      <div className="flex flex-wrap items-center gap-2">
        {animeList.length > 0 && (
          <AnimeSearchBar
            animeList={animeList}
            selectedSlug={selectedSlug}
            onSelectAnime={onSelectAnime}
          />
        )}

        {isAuthenticated ? (
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsUserMenuOpen((previous) => !previous)}
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--primary-light)] bg-[var(--primary-light)] px-3 py-1.5 text-sm font-medium text-[var(--surface)]"
            >
              <User className="h-3.5 w-3.5 shrink-0" />
              <span className="max-w-[7rem] truncate sm:max-w-[12rem]">
                {user?.display_name ?? user?.email}
              </span>
              <ChevronDown className="h-3.5 w-3.5 shrink-0" />
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 top-full z-20 mt-1 w-40 rounded-md border border-[var(--border)] bg-[var(--surface)] py-1 shadow-md">
                <Link
                  to="/app/profile"
                  onClick={() => setIsUserMenuOpen(false)}
                  className="flex w-full items-center gap-1.5 px-3 py-1.5 text-left text-sm text-[var(--text)] hover:bg-[var(--surface-warm)]"
                >
                  <UserCircle2 className="h-3.5 w-3.5" />
                  My Profile
                </Link>
                {user?.is_admin && (
                  <Link
                    to="/admin"
                    onClick={() => setIsUserMenuOpen(false)}
                    className="flex w-full items-center gap-1.5 px-3 py-1.5 text-left text-sm text-[var(--text)] hover:bg-[var(--surface-warm)]"
                  >
                    <LayoutDashboard className="h-3.5 w-3.5" />
                    Admin Dashboard
                  </Link>
                )}
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="flex w-full items-center gap-1.5 px-3 py-1.5 text-left text-sm text-[var(--text)] hover:bg-[var(--surface-warm)]"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setIsAuthModalOpen(true)}
            className="rounded-md bg-[var(--surface)] px-3 py-1.5 text-sm font-medium text-[var(--primary)]"
          >
            Sign In
          </button>
        )}
      </div>

      {isAuthModalOpen && (
        <AuthModal onClose={() => setIsAuthModalOpen(false)} />
      )}
    </header>
  );
}

export default Header;
