import { useEffect, useId, useRef, useState } from "react";
import { Search } from "lucide-react";
import { useNavigate } from "react-router-dom";

// Light-background twin of AnimeSearchBar.jsx (that one is styled for the app
// Header's dark navy bar) — same combobox behavior, sized and colored for the
// hero's white/cream canvas instead. Selecting an anime here has nowhere to
// "select into" yet (there's no app shell on this page), so it navigates
// straight into that anime's dossier rather than lifting state to a parent.
function LandingSearchBar({ animeList }) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const containerRef = useRef(null);
  const listboxId = useId();
  const navigate = useNavigate();

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
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (anime) => {
    navigate(`/app/dossiers?anime=${anime.slug}`);
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
    }
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-sm">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
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
          placeholder="Search for an anime to start..."
          className="w-full rounded-md border border-[var(--border)] bg-[var(--surface)] py-2.5 pl-9 pr-3 text-sm text-[var(--text)] outline-none placeholder:text-[var(--text-muted)] focus:border-[var(--primary)]"
        />
      </div>

      {isOpen && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute left-0 top-full z-20 mt-1 max-h-64 w-full overflow-y-auto rounded-md border border-[var(--border)] bg-[var(--surface)] py-1 shadow-md"
        >
          {matches.length === 0 ? (
            <li className="px-3 py-1.5 text-sm text-[var(--text-muted)]">
              No matches
            </li>
          ) : (
            matches.map((anime, index) => (
              <li key={anime.slug} role="option" aria-selected={false}>
                <button
                  type="button"
                  onClick={() => handleSelect(anime)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                  className={`block w-full truncate px-3 py-1.5 text-left text-sm ${
                    index === highlightedIndex
                      ? "bg-[var(--surface-warm)] text-[var(--primary)]"
                      : "text-[var(--text)]"
                  }`}
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

export default LandingSearchBar;
