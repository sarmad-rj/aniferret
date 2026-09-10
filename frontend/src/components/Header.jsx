import { useState } from "react";
import {
  ChevronDown,
  FileUp,
  LayoutDashboard,
  LogOut,
  UserCircle2,
} from "lucide-react";
import { Link } from "react-router-dom";
import logo from "../logo/AniFerret_Logo.png";
import AnimeSearchBar from "./AnimeSearchBar";
import AuthModal from "./AuthModal";
import ImportMalModal from "./ImportMalModal";
import { useAuth } from "../context/useAuth";

function Header({
  animeList,
  selectedSlug,
  onSelectAnime,
  onWatchProgressImported,
}) {
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isImportMalModalOpen, setIsImportMalModalOpen] = useState(false);

  const { user, token, isAuthenticated, logout } = useAuth();

  const handleSignOut = () => {
    setIsUserMenuOpen(false);
    logout();
  };

  const avatarInitial = (user?.display_name ?? user?.email ?? "?")
    .charAt(0)
    .toUpperCase();

  return (
    <header className="flex flex-nowrap items-center justify-between gap-2 bg-[var(--primary)] px-4 py-3 sm:gap-3 sm:px-6">
      <Link to="/" className="flex shrink-0 items-center gap-2">
        <img
          src={logo}
          alt="AniFerret logo"
          className="h-8 w-8 rounded-full sm:h-11 sm:w-11"
        />
        <span className="hidden text-xl font-bold text-[var(--surface)] sm:inline">
          AniFerret
        </span>
      </Link>

      <div className="flex flex-nowrap items-center gap-2">
        {animeList.length > 0 && (
          <AnimeSearchBar
            animeList={animeList}
            selectedSlug={selectedSlug}
            onSelectAnime={onSelectAnime}
          />
        )}

        {isAuthenticated ? (
          <div className="relative shrink-0">
            <button
              type="button"
              onClick={() => setIsUserMenuOpen((previous) => !previous)}
              aria-label="Account menu"
              className="inline-flex items-center gap-1 rounded-full border border-[var(--primary-light)] bg-[var(--primary-light)] p-1 pr-1.5 text-sm font-medium text-[var(--surface)]"
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--sky)] text-xs font-bold text-[var(--primary)]">
                {avatarInitial}
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
                <button
                  type="button"
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    setIsImportMalModalOpen(true);
                  }}
                  className="flex w-full items-center gap-1.5 px-3 py-1.5 text-left text-sm text-[var(--text)] hover:bg-[var(--surface-warm)]"
                >
                  <FileUp className="h-3.5 w-3.5" />
                  Import MAL
                </button>
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

      {isImportMalModalOpen && (
        <ImportMalModal
          token={token}
          onImportSuccess={onWatchProgressImported}
          onClose={() => setIsImportMalModalOpen(false)}
        />
      )}
    </header>
  );
}

export default Header;
