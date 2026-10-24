"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const groups = [
  {
    href: "/app",
    label: "Explore Locations",
    id: "explore",
    items: [
      ["locations-heading", "Location Rankings"],
      ["dayparts-heading", "DaypartDNA"],
      ["comparison-heading", "Compare Locations"],
    ],
  },
  {
    href: "/app/scenarios",
    label: "Test Changes",
    id: "scenarios",
    items: [
      ["builder-heading", "Scenario Builder"],
      ["infra-heading", "Future Infrastructure"],
      ["risk-heading", "FailFast"],
    ],
  },
  {
    href: "/app/portfolio",
    label: "Investment Plan",
    id: "portfolio",
    items: [
      ["portfolio-heading", "Budget Optimisation"],
      ["report-heading", "Investment Reports"],
    ],
  },
];

export default function WorkspaceNavigation({
  contentReady,
}: {
  contentReady: boolean;
}) {
  const pathname = usePathname();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    [pathname]: true,
  });
  const [anchor, setAnchor] = useState("");

  useEffect(() => {
    const syncHash = () => setAnchor(window.location.hash.slice(1));
    syncHash();
    setExpanded((previous) => ({ ...previous, [pathname]: true }));
    window.addEventListener("hashchange", syncHash);
    window.addEventListener("popstate", syncHash);
    return () => {
      window.removeEventListener("hashchange", syncHash);
      window.removeEventListener("popstate", syncHash);
    };
  }, [pathname]);

  // Revisit deep links after asynchronous project content becomes available.
  useEffect(() => {
    if (!contentReady || !anchor) return;
    const frame = requestAnimationFrame(() => {
      const target = document.getElementById(anchor);
      if (!target) return;
      target.setAttribute("tabindex", "-1");
      target.scrollIntoView({ block: "start" });
      target.focus({ preventScroll: true });
    });
    return () => cancelAnimationFrame(frame);
  }, [pathname, anchor, contentReady]);

  return (
    <nav className="workspace-navigation" aria-label="Investment workflow">
      {groups.map((group) => (
        <div className="workspace-nav-group" key={group.href}>
          <div className="workspace-nav-row">
            <Link
              href={group.href}
              aria-current={pathname === group.href ? "page" : undefined}
              onClick={() => {
                setAnchor("");
                setExpanded((previous) => ({
                  ...previous,
                  [group.href]: true,
                }));
              }}
            >
              {group.label}
            </Link>
            <button
              type="button"
              className="workspace-nav-toggle"
              aria-label={group.label + " features"}
              aria-expanded={!!expanded[group.href]}
              aria-controls={group.id + "-features"}
              onClick={() =>
                setExpanded((previous) => ({
                  ...previous,
                  [group.href]: !previous[group.href],
                }))
              }
            >
              <svg
                viewBox="0 0 16 16"
                width="14"
                height="14"
                aria-hidden="true"
              >
                <path
                  d="m5 6 3 3 3-3"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
          <ul
            id={group.id + "-features"}
            className="workspace-subnav"
            aria-label={group.label + " features"}
            hidden={!expanded[group.href]}
          >
            {group.items.map(([id, label]) => (
              <li key={id}>
                <Link
                  href={group.href + "#" + id}
                  aria-current={
                    pathname === group.href && anchor === id
                      ? "location"
                      : undefined
                  }
                  onClick={(event) => {
                    if (
                      event.metaKey ||
                      event.ctrlKey ||
                      event.shiftKey ||
                      event.altKey
                    )
                      return;
                    if (pathname === group.href) {
                      // Native fragment history plus explicit focus also supports repeated clicks.
                      event.preventDefault();
                      if (window.location.hash !== "#" + id)
                        window.history.pushState(null, "", "#" + id);
                      setAnchor(id);
                      const target = document.getElementById(id);
                      if (target) {
                        target.setAttribute("tabindex", "-1");
                        target.scrollIntoView({ block: "start" });
                        target.focus({ preventScroll: true });
                      }
                    }
                  }}
                >
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}
