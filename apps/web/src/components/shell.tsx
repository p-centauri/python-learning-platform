"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import {
  BookOpen,
  BookText,
  Bookmark,
  ChartNoAxesCombined,
  Anvil,
  Command,
  FlaskConical,
  FolderKanban,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Network,
  RotateCcw,
  Search,
  Sun,
  X,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { User } from "@/lib/types";
import { Loading, ErrorNotice } from "./ui";
import { SearchDialog } from "./search";

const UserContext = createContext<User | null>(null);
export function useUser() {
  return useContext(UserContext);
}
const navigation = [
  { label: "Overview", href: "/", icon: LayoutDashboard },
  { label: "My learning plan", href: "/plan", icon: BookOpen },
  { label: "Learning path", href: "/learn", icon: BookOpen },
  { label: "Practice lab", href: "/practice", icon: FlaskConical },
  { label: "Coding and SQL", href: "/coding", icon: FlaskConical },
  { label: "Spaced review", href: "/review", icon: RotateCcw },
  { label: "Portfolio projects", href: "/projects", icon: FolderKanban },
  { label: "Review workspace", href: "/project-reviews", icon: FolderKanban },
  { label: "Assessments", href: "/exams", icon: GraduationCap },
  { label: "Skill progress", href: "/progress", icon: ChartNoAxesCombined },
  { label: "Knowledge map", href: "/map", icon: Network },
  { label: "Bookmarks", href: "/bookmarks", icon: Bookmark },
  { label: "Glossary", href: "/glossary", icon: BookText },
  { label: "Account & evidence", href: "/account", icon: Command },
];
const navigationGroups = [
  { title: "Study", items: navigation.slice(0, 3) },
  { title: "Practice & evidence", items: navigation.slice(3, 10) },
  { title: "Library & account", items: navigation.slice(10) },
];
const mobileNavigation = [
  navigation[0],
  navigation[2],
  navigation[3],
  navigation[5],
];
function isActive(path: string, href: string) {
  return href === "/"
    ? path === "/"
    : path === href || path.startsWith(`${href}/`);
}

export function Shell({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [menu, setMenu] = useState(false);
  const [search, setSearch] = useState(false);
  const [dark, setDark] = useState(false);
  const [mobile, setMobile] = useState(false);
  const sidebar = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const path = usePathname();
  const router = useRouter();
  useEffect(() => {
    const media = window.matchMedia("(max-width: 960px)");
    function update() {
      setMobile(media.matches);
      if (!media.matches) setMenu(false);
    }
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    if (!menu || !mobile) return;
    const previous = document.activeElement as HTMLElement | null;
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const focusables = () =>
      Array.from(
        sidebar.current?.querySelectorAll<HTMLElement>(
          "a[href], button:not(:disabled), input, [tabindex='0']",
        ) || [],
      ).filter((el) => el.getClientRects().length);
    focusables()[0]?.focus();
    function keyboard(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        setMenu(false);
      }
      if (event.key === "Tab") {
        const items = focusables();
        const first = items[0];
        const last = items.at(-1);
        if (!first || !last) return;
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        } else if (!sidebar.current?.contains(document.activeElement)) {
          event.preventDefault();
          first.focus();
        }
      }
    }
    document.addEventListener("keydown", keyboard);
    return () => {
      document.body.style.overflow = oldOverflow;
      document.removeEventListener("keydown", keyboard);
      if (previous?.isConnected) previous.focus();
    };
  }, [menu, mobile]);
  useEffect(() => {
    api<User>("/auth/me")
      .then(setUser)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) router.replace("/login");
        else setError(e.message);
      });
  }, [router]);
  useEffect(() => {
    const saved = localStorage.getItem("academy-theme") === "dark";
    setDark(saved);
    document.documentElement.dataset.theme = saved ? "dark" : "light";
  }, []);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (
        (e.metaKey || e.ctrlKey) &&
        e.key === "k" &&
        !/^\/exams\/\d+$/.test(path)
      ) {
        e.preventDefault();
        setMenu(false);
        setSearch((v) => !v);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [path]);
  useEffect(() => {
    setMenu(false);
  }, [path]);
  async function logout() {
    try {
      await api("/auth/logout", "POST");
      router.replace("/login");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  function theme() {
    const next = !dark;
    setDark(next);
    localStorage.setItem("academy-theme", next ? "dark" : "light");
    document.documentElement.dataset.theme = next ? "dark" : "light";
  }
  if (!user)
    return (
      <main id="main-content" tabIndex={-1} className="auth-loading">
        {error ? (
          <ErrorNotice message={error} retry={() => window.location.reload()} />
        ) : (
          <Loading />
        )}
      </main>
    );
  const isExam = /^\/exams\/\d+$/.test(path);
  return (
    <UserContext.Provider value={user}>
      <div className={`workspace ${isExam ? "exam-workspace" : ""}`}>
        {!isExam && (
          <>
            <button
              className={`sidebar-overlay ${menu ? "visible" : ""}`}
              aria-label="Close navigation"
              onClick={() => setMenu(false)}
            />
            <aside
              ref={sidebar}
              id="academy-sidebar"
              role={menu && mobile ? "dialog" : undefined}
              aria-modal={menu && mobile ? true : undefined}
              aria-label={menu && mobile ? "Workspace navigation" : undefined}
              className={`sidebar ${menu ? "mobile-open" : ""}`}
            >
              {menu && mobile && (
                <button
                  className="icon-button"
                  onClick={() => setMenu(false)}
                  aria-label="Close navigation menu"
                >
                  <X size={20} />
                </button>
              )}
              <Link className="brand" href="/">
                <span className="brand-mark">
                  <Anvil size={22} />
                </span>
                <span>
                  forge<span className="brand-dot">.</span>
                  <small>BACKEND & AI ACADEMY</small>
                </span>
              </Link>
              <nav aria-label="Main navigation">
                {navigationGroups.map((group) => (
                  <div className="nav-group" key={group.title}>
                    <p className="nav-caption">{group.title}</p>
                    {group.items.map(({ label, href, icon: Icon }) => (
                      <Link
                        key={href}
                        className={isActive(path, href) ? "active" : ""}
                        href={href}
                        aria-current={isActive(path, href) ? "page" : undefined}
                      >
                        <Icon size={18} />
                        {label}
                      </Link>
                    ))}
                  </div>
                ))}
              </nav>
              <div className="sidebar-bottom">
                <div className="profile">
                  <span className="avatar">
                    {user.name.slice(0, 2).toUpperCase()}
                  </span>
                  <div>
                    {user.name}
                    <small>Personal workspace</small>
                  </div>
                  <button
                    className="icon-button"
                    onClick={logout}
                    aria-label="Sign out"
                  >
                    <LogOut size={16} />
                  </button>
                </div>
              </div>
            </aside>
          </>
        )}
        <div
          className="workspace-main"
          inert={mobile && menu ? true : undefined}
        >
          <header className="topbar">
            {isExam ? (
              <Link href="/exams" className="text-link">
                ← Exit & resume later
              </Link>
            ) : (
              <>
                <button
                  ref={menuButton}
                  className="icon-button mobile-menu"
                  onClick={() => setMenu(!menu)}
                  aria-label="Open navigation"
                  aria-expanded={menu}
                  aria-controls="academy-sidebar"
                >
                  {menu ? <X size={20} /> : <Menu size={20} />}
                </button>
                <div className="breadcrumb">
                  Workspace <span>/</span>{" "}
                  <strong>
                    {navigation.find((n) => isActive(path, n.href))?.label ||
                      "Lesson"}
                  </strong>
                </div>
                <button
                  className="top-search"
                  aria-label="Search anything"
                  onClick={() => {
                    setMenu(false);
                    setSearch(true);
                  }}
                >
                  <Search size={16} />
                  <span>Search anything</span>
                  <kbd>⌘ K</kbd>
                </button>
              </>
            )}
            <button
              className="icon-button"
              onClick={theme}
              aria-label={
                dark ? "Switch to light theme" : "Switch to dark theme"
              }
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </header>
          <main id="main-content" tabIndex={-1} className="main-content">
            {error && <ErrorNotice message={error} />} {children}
          </main>
          <footer className="workspace-footer">
            <span>Forge · Backend & AI Engineering Academy</span>
            <Link href="/account">Your account & evidence</Link>
          </footer>
          {!isExam && (
            <nav className="mobile-dock" aria-label="Quick navigation">
              {mobileNavigation.map(({ label, href, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  aria-label={label}
                  aria-current={isActive(path, href) ? "page" : undefined}
                >
                  <Icon size={20} aria-hidden="true" />
                  <span>
                    {
                      {
                        Overview: "Home",
                        "Learning path": "Learn",
                        "Practice lab": "Practice",
                        "Spaced review": "Review",
                      }[label]
                    }
                  </span>
                </Link>
              ))}
              <button
                onClick={() => setMenu(true)}
                aria-label="Open all navigation"
                aria-expanded={menu}
                aria-controls="academy-sidebar"
              >
                <Menu size={20} aria-hidden="true" />
                <span>More</span>
              </button>
            </nav>
          )}
        </div>
        {!isExam && (
          <SearchDialog open={search} onClose={() => setSearch(false)} />
        )}
      </div>
    </UserContext.Provider>
  );
}
