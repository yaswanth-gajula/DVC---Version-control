import { NavLink } from "react-router-dom";

export default function Sidebar({ projectId }) {
  const base = `/p/${projectId}`;
  const links = [
    { to: base, label: "Overview", end: true },
    { to: `${base}/new`, label: "New version" },
    { to: `${base}/history`, label: "History" },
    { to: `${base}/git-log`, label: "Git log" },
  ];

  return (
    <nav className="w-44 shrink-0 border-r border-border py-6 pr-4">
      <ul className="space-y-1">
        {links.map((link) => (
          <li key={link.to}>
            <NavLink
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `block text-sm px-3 py-1.5 rounded transition-colors ${
                  isActive ? "bg-accentSoft text-accent font-medium" : "text-muted hover:text-ink hover:bg-bg"
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
