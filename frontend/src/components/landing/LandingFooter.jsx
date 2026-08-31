import logo from "../../logo/AniFerret_Logo.png";

const FOOTER_LINKS = ["Discover", "Dossiers", "Lore Assistant", "Watch Order"];

function LandingFooter() {
  return (
    <footer className="bg-[var(--primary)] px-4 py-8 sm:px-6">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 sm:flex-row sm:justify-between">
        <div className="flex items-center gap-2">
          <img
            src={logo}
            alt="AniFerret logo"
            className="h-8 w-8 rounded-full"
          />
          <span className="text-sm font-bold text-[var(--surface)]">
            AniFerret
          </span>
        </div>

        <ul className="flex flex-wrap items-center justify-center gap-5">
          {FOOTER_LINKS.map((label) => (
            <li key={label}>
              <span className="text-xs font-medium text-[var(--sky)]">
                {label}
              </span>
            </li>
          ))}
        </ul>

        <p className="text-xs text-[var(--text-muted)]">
          &copy; {new Date().getFullYear()} AniFerret. Spoiler-safe, by design.
        </p>
      </div>
    </footer>
  );
}

export default LandingFooter;
