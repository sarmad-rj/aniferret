import { useState } from "react";
import { ChevronDown, LogOut, Plus, User } from "lucide-react";
import { Link } from "react-router-dom";
import logo from "../logo/AniFerret_Logo.png";
import AuthModal from "./AuthModal";
import { useAuth } from "../context/useAuth";

function Header({ animeList, selectedSlug, onSelectAnime, onOpenImport }) {
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const { user, isAuthenticated, logout } = useAuth();

  const handleAnimeChange = (event) => {
    onSelectAnime(event.target.value);
  };

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

      <div className="flex items-center gap-2">
        {animeList.length > 0 && (
          <select
            value={selectedSlug ?? ""}
            onChange={handleAnimeChange}
            className="rounded-md border border-[var(--primary-light)] bg-[var(--primary-light)] px-3 py-1.5 text-sm text-[var(--surface)]"
          >
            {animeList.map((anime) => (
              <option key={anime.slug} value={anime.slug}>
                {anime.title}
              </option>
            ))}
          </select>
        )}

        <button
          type="button"
          onClick={onOpenImport}
          className="inline-flex items-center gap-1 rounded-md border border-[var(--sky)] px-3 py-1.5 text-sm font-medium text-[var(--sky)]"
        >
          <Plus className="h-3.5 w-3.5" />
          Import
        </button>

        {isAuthenticated ? (
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsUserMenuOpen((previous) => !previous)}
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--primary-light)] bg-[var(--primary-light)] px-3 py-1.5 text-sm font-medium text-[var(--surface)]"
            >
              <User className="h-3.5 w-3.5" />
              {user?.display_name ?? user?.email}
              <ChevronDown className="h-3.5 w-3.5" />
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 top-full z-20 mt-1 w-40 rounded-md border border-[var(--border)] bg-[var(--surface)] py-1 shadow-md">
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
