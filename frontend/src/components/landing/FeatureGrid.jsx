import {
  GitCompare,
  Lock,
  Network,
  Repeat,
  ShieldAlert,
  Users,
} from "lucide-react";
import FeatureCard from "./FeatureCard";

const DIFFERENTIATORS = [
  {
    number: "01",
    tag: "Spoiler Protection",
    title: "Progress-Gated Retrieval",
    description:
      "Set your episode, and every dossier, roster, and answer filters itself to only what's true by then. Nothing ahead of your progress ever reaches the screen.",
    icon: Lock,
  },
  {
    number: "02",
    tag: "Spoiler Protection",
    title: "Uniform Refusal Engine",
    description:
      "Ask about a locked twist and ask a nonsense question — you get the exact same answer either way, so the refusal itself can never give the twist away.",
    icon: ShieldAlert,
  },
  {
    number: "03",
    tag: "Social",
    title: "Group Mode",
    description:
      "Watching with friends at different episodes? Group Mode locks everyone's dossier to whoever's furthest behind, automatically.",
    icon: Users,
  },
  {
    number: "04",
    tag: "Rewatch",
    title: "Foreshadowing Index",
    description:
      "Finished the show? Flip the ledger around and see every setup next to the payoff it was quietly building toward, episode by episode.",
    icon: Repeat,
  },
  {
    number: "05",
    tag: "Developer / MCP",
    title: "Machine-Queryable Dossiers",
    description:
      "Faction hierarchies and character rosters are exposed as structured, progress-gated tools over a standalone MCP server.",
    icon: Network,
  },
  {
    number: "06",
    tag: "Data Integrity",
    title: "Source-Conflict Surfacing",
    description:
      "When Jikan, AniList, and wiki sources disagree, AniFerret shows you the disagreement — with provider tags — instead of quietly picking one.",
    icon: GitCompare,
  },
];

function FeatureGrid() {
  return (
    <section
      id="features"
      className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6"
    >
      <div className="mx-auto mb-10 max-w-2xl text-center">
        <h2 className="text-2xl font-bold text-[var(--primary)] sm:text-3xl">
          Six differentiators, built on one moat
        </h2>
        <p className="mt-2 text-sm text-[var(--text-muted)]">
          Everything below runs on the same progress-gated engine — nothing here
          is a bolt-on feature.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {DIFFERENTIATORS.map((feature) => (
          <FeatureCard key={feature.number} {...feature} />
        ))}
      </div>
    </section>
  );
}

export default FeatureGrid;
