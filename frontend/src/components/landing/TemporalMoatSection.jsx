import { Clock, Database } from "lucide-react";

function TemporalMoatSection() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <div className="mx-auto mb-10 max-w-2xl text-center">
        <h2 className="text-2xl font-bold text-[var(--primary)] sm:text-3xl">
          Most anime databases only know what&apos;s true. AniFerret knows when.
        </h2>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-6">
          <div className="mb-3 flex items-center gap-2">
            <Database className="h-5 w-5 text-[var(--text-muted)]" />
            <h3 className="text-sm font-semibold text-[var(--text-muted)]">
              Existing Databases
            </h3>
          </div>
          <p className="text-sm text-[var(--text-muted)]">
            Store static facts — a character&apos;s bio, a faction&apos;s roster
            — as one flat block of text. Read it on Episode 1 or Episode 100,
            you see the exact same thing, spoilers included.
          </p>
        </div>

        <div className="rounded-lg border border-[var(--pink)] bg-[var(--surface-warm)] p-6">
          <div className="mb-3 flex items-center gap-2">
            <Clock className="h-5 w-5 text-[var(--ferret)]" />
            <h3 className="text-sm font-semibold text-[var(--primary)]">
              AniFerret&apos;s Temporal Facts
            </h3>
          </div>
          <p className="text-sm text-[var(--text)]">
            Every fact is stored as itself <em>plus</em> the exact episode it
            first becomes true in canon. Your dossier is generated fresh for
            your current episode — nothing you haven&apos;t earned yet ever
            reaches the screen.
          </p>
        </div>
      </div>
    </section>
  );
}

export default TemporalMoatSection;
