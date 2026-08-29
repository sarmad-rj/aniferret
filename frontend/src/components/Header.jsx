import { Plus } from "lucide-react";
import logo from "../logo/AniFerret_Logo.png";

function Header({ animeList, selectedSlug, onSelectAnime, onOpenImport }) {
  const handleAnimeChange = (event) => {
    onSelectAnime(event.target.value);
  };

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 bg-[var(--primary)] px-4 py-3 sm:px-6">
      <div className="flex items-center gap-2">
        <img
          src={logo}
          alt="AniFerret logo"
          className="h-11 w-11 rounded-full"
        />
        <span className="text-xl font-bold text-[var(--surface)]">
          AniFerret
        </span>
      </div>

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
      </div>
    </header>
  );
}

export default Header;
