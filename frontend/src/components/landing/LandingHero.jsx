import { Film } from "lucide-react";
import CtaButton from "./CtaButton";
import LandingSearchBar from "./LandingSearchBar";

function LandingHero({ animeList }) {
  const covers = animeList.slice(0, 2);

  return (
    <section className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 sm:px-6 lg:min-h-[calc(100vh-4.5rem)] lg:flex-row lg:items-center lg:justify-center lg:gap-10 lg:py-0">
      <div className="flex flex-1 flex-col gap-4">
        <span className="w-fit rounded-full bg-[var(--pink-light)] px-3 py-1 text-xs font-semibold text-[var(--primary)]">
          A Temporal Knowledge Platform
        </span>
        <h1 className="text-3xl font-bold leading-tight text-[var(--primary)] sm:text-4xl lg:text-5xl">
          Anime lore, revealed exactly when you&apos;re ready for it.
        </h1>
        <p className="max-w-xl text-base text-[var(--text-muted)] sm:text-lg">
          AniFerret adds a fourth dimension to the anime database — time. Every
          character, faction, and plot fact is locked to the exact episode
          it&apos;s safe to know, so a wiki, a friend, or your own curiosity can
          never spoil you again.
        </p>
        <div className="flex flex-col items-start gap-3 pt-2">
          <LandingSearchBar animeList={animeList} />
          <CtaButton href="#how-it-works" variant="outline-primary">
            See How It Works
          </CtaButton>
        </div>
      </div>

      <div className="grid flex-1 grid-cols-2 gap-4 sm:gap-6">
        {covers.length > 0
          ? covers.map((anime) => (
              <img
                key={anime.slug}
                src={anime.cover_image_url}
                alt={anime.title}
                className="aspect-[2/3] w-full rounded-md object-cover shadow-sm"
              />
            ))
          : ["one", "two"].map((placeholderKey) => (
              <div
                key={placeholderKey}
                className="flex aspect-[2/3] w-full items-center justify-center rounded-md border border-[var(--border)] bg-[var(--surface-warm)]"
              >
                <Film className="h-8 w-8 text-[var(--ferret)]" />
              </div>
            ))}
      </div>
    </section>
  );
}

export default LandingHero;
