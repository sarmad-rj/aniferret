import { useEffect, useId, useRef, useState } from "react";
import { Search } from "lucide-react";

function AnimeSearchBar({ animeList, selectedSlug, onSelectAnime }) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const containerRef = useRef(null);
  const listboxId = useId();

  const selectedAnime =
    animeList.find((anime) => anime.slug === selectedSlug) ?? null;
  const trimmedQuery = query.trim().toLowerCase();
  const matches = trimmedQuery
    ? animeList.filter((anime) =>
        anime.title.toLowerCase().includes(trimmedQuery),
      )
    : animeList;

  useEffect(() => {
    function handleClickOutside(event) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target)
      ) {
        setIsOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (anime) => {
    onSelectAnime(anime.slug);
    setQuery("");
    setIsOpen(false);
    setHighlightedIndex(0);
  };

  const handleChange = (event) => {
    setQuery(event.target.value);
    setIsOpen(true);
    setHighlightedIndex(0);
  };

  const handleKeyDown = (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setIsOpen(true);
      setHighlightedIndex((previous) =>
        Math.min(previous + 1, matches.length - 1),
      );
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlightedIndex((previous) => Math.max(previous - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      const match = matches[highlightedIndex];
      if (match) {
        handleSelect(match);
      }
    } else if (event.key === "Escape") {
      setIsOpen(false);
      setQuery("");
    }
  };

  return (
    <div ref={containerRef} className="relative w-[9rem] sm:w-56">
      <div className="relative">
        <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--sky)]" />
        <input
          type="text"
          role="combobox"
          aria-expanded={isOpen}
          aria-controls={listboxId}
          aria-autocomplete="list"
          aria-label="Search anime"
          value={query}
          onChange={handleChange}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={selectedAnime?.title ?? "Search anime..."}
          className="w-full rounded-md border border-[var(--primary-light)] bg-[var(--primary-light)] py-1.5 pl-7 pr-2 text-sm text-[var(--surface)] outline-none placeholder:text-[var(--sky)]"
        />
      </div>

      {isOpen && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute left-0 top-full z-20 mt-1 max-h-64 w-full min-w-[12rem] overflow-y-auto rounded-md border border-[var(--border)] bg-[var(--surface)] py-1 shadow-md"
        >
          {matches.length === 0 ? (
            <li className="px-3 py-1.5 text-sm text-[var(--text-muted)]">
              No matches
            </li>
          ) : (
            matches.map((anime, index) => (
              <li
                key={anime.slug}
                role="option"
                aria-selected={anime.slug === selectedSlug}
              >
                <button
                  type="button"
                  onClick={() => handleSelect(anime)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                  className={`block w-full truncate px-3 py-1.5 text-left text-sm ${
                    index === highlightedIndex
                      ? "bg-[var(--surface-warm)] text-[var(--primary)]"
                      : "text-[var(--text)]"
                  } ${anime.slug === selectedSlug ? "font-semibold" : ""}`}
                >
                  {anime.title}
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}

export default AnimeSearchBar;
