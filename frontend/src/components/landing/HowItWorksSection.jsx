import { Eye, MapPin, MessageCircle, Sparkles } from "lucide-react";

const STEPS = [
  {
    icon: MapPin,
    title: "Set your episode checkpoint",
    description:
      "Drag the progress slider to exactly where you are — first episode or five hundred episodes in.",
  },
  {
    icon: Sparkles,
    title: "Browse dossiers filtered to what you've seen",
    description:
      "Character bios, factions, bounties, and lore ledgers all regenerate for that exact checkpoint, nothing more.",
  },
  {
    icon: MessageCircle,
    title: "Ask the Lore Assistant anything",
    description:
      "Our Gemini-powered chat only ever draws from facts you've already unlocked — ask about a future twist and it stays silent.",
  },
  {
    icon: Eye,
    title: "Finished the show? Flip on Rewatch Mode",
    description:
      "The Foreshadowing Index reveals every hint next to the payoff it was quietly setting up, episode by episode.",
  },
];

function HowItWorksSection() {
  return (
    <section
      id="how-it-works"
      className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6"
    >
      <div className="mx-auto mb-10 max-w-2xl text-center">
        <h2 className="text-2xl font-bold text-[var(--primary)] sm:text-3xl">
          How it works
        </h2>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((step, index) => (
          <div key={step.title} className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--primary)] text-xs font-bold text-[var(--surface)]">
                {index + 1}
              </span>
              <step.icon className="h-4 w-4 text-[var(--ferret)]" />
            </div>
            <h3 className="text-sm font-semibold text-[var(--text)]">
              {step.title}
            </h3>
            <p className="text-xs text-[var(--text-muted)]">
              {step.description}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default HowItWorksSection;
