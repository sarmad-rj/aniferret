import logo from "../logo/AniFerret_Logo.png";

function Header({ animeList, selectedSlug, onSelectAnime }) {
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
    </header>
  );
}

export default Header;
