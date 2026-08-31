import { Film } from "lucide-react";
import { Link } from "react-router-dom";

function AnimeCoverCard({ anime, linkTo }) {
  return (
    <Link
      to={linkTo}
      className="flex flex-col overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface)] transition-shadow hover:shadow-md"
    >
      {anime.cover_image_url ? (
        <img
          src={anime.cover_image_url}
          alt={anime.title}
          className="h-48 w-full object-cover object-top"
        />
      ) : (
        <div className="flex h-48 w-full items-center justify-center bg-[var(--surface-warm)]">
          <Film className="h-8 w-8 text-[var(--ferret)]" />
        </div>
      )}

      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-sm font-semibold text-[var(--text)]">
            {anime.title}
          </h3>
          {anime.score != null && (
            <span className="shrink-0 rounded-md border border-[var(--border)] bg-[var(--surface-warm)] px-2 py-1 text-xs font-semibold text-[var(--primary)]">
              {anime.score.toFixed(2)}
            </span>
          )}
        </div>

        {anime.genres?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {anime.genres.map((genre) => (
              <span
                key={genre}
                className="rounded-full bg-[var(--sky)]/25 px-2.5 py-1 text-xs font-medium text-[var(--primary)]"
              >
                {genre}
              </span>
            ))}
          </div>
        )}

        <p className="mt-auto text-xs font-medium text-[var(--ferret)]">
          Explore Dossier &rarr;
        </p>
      </div>
    </Link>
  );
}

export default AnimeCoverCard;
