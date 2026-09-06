import { NavLink } from "react-router-dom";

const NAV_LINKS = [
  { label: "Discover", to: "/app/discover" },
  { label: "Dossiers", to: "/app/dossiers" },
  { label: "Lore Assistant", to: "/app/lore-assistant" },
  { label: "Watch Order", to: "/app/watch-order" },
];

function NavBar() {
  return (
    <nav className="border-b border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 sm:px-6 sm:py-3">
      <ul className="flex gap-4 overflow-x-auto sm:gap-6">
        {NAV_LINKS.map((link) => (
          <li key={link.label} className="shrink-0">
            <NavLink
              to={link.to}
              className={({ isActive }) =>
                `whitespace-nowrap text-xs font-medium hover:text-[var(--primary)] sm:text-sm ${
                  isActive
                    ? "text-[var(--primary)]"
                    : "text-[var(--text-muted)]"
                }`
              }
            >
              {link.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export default NavBar;
