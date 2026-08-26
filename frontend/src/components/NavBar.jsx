const NAV_LINKS = ["Discover", "Dossiers", "Lore Assistant", "Watch Order"];

function NavBar() {
  return (
    <nav className="border-b border-[var(--border)] bg-[var(--surface)] px-6 py-3">
      <ul className="flex gap-6">
        {NAV_LINKS.map((label) => (
          <li key={label}>
            <a
              href="#"
              className="text-sm font-medium text-[var(--text-muted)] hover:text-[var(--primary)]"
            >
              {label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export default NavBar;
