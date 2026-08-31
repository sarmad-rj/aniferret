import { NavLink } from "react-router-dom";

const NAV_LINKS = [
  { label: "Discover", to: "/app/discover" },
  { label: "Dossiers", to: "/app/dossiers" },
  { label: "Lore Assistant", to: "/app/lore-assistant" },
  { label: "Watch Order", to: "/app/watch-order" },
];

function NavBar() {
  return (
    <nav className="border-b border-[var(--border)] bg-[var(--surface)] px-6 py-3">
      <ul className="flex gap-6">
        {NAV_LINKS.map((link) => (
          <li key={link.label}>
            <NavLink
              to={link.to}
              className={({ isActive }) =>
                `text-sm font-medium hover:text-[var(--primary)] ${
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
