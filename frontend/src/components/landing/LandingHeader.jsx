import { useState } from "react";
import { Menu, X } from "lucide-react";
import { Link } from "react-router-dom";
import logo from "../../logo/AniFerret_Logo.png";
import CtaButton from "./CtaButton";

const ANCHOR_LINKS = [
  { label: "Features", href: "#features" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Anime", href: "#anime" },
];

function LandingHeader() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLinkClick = () => {
    setIsMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-10 bg-[var(--primary)] px-4 py-3 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to="/" className="flex items-center gap-2">
          <img
            src={logo}
            alt="AniFerret logo"
            className="h-11 w-11 rounded-full"
          />
          <span className="text-xl font-bold text-[var(--surface)]">
            AniFerret
          </span>
        </Link>

        <nav className="hidden items-center gap-6 sm:flex">
          {ANCHOR_LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-sm font-medium text-[var(--sky)] hover:text-[var(--surface)]"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <CtaButton to="/app" variant="outline">
            Enter AniFerret
          </CtaButton>

          <button
            type="button"
            onClick={() => setIsMenuOpen((previous) => !previous)}
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
            className="flex h-9 w-9 items-center justify-center rounded-md text-[var(--sky)] sm:hidden"
          >
            {isMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      {isMenuOpen && (
        <nav className="mt-3 flex flex-col gap-3 border-t border-[var(--primary-light)] pt-3 sm:hidden">
          {ANCHOR_LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              onClick={handleLinkClick}
              className="py-1 text-sm font-medium text-[var(--sky)] hover:text-[var(--surface)]"
            >
              {link.label}
            </a>
          ))}
        </nav>
      )}
    </header>
  );
}

export default LandingHeader;
