import { Link } from "react-router-dom";
import heroImage from "../assets/atlas-hero.svg";
import PageBackdrop from "../components/PageBackdrop";
import BrandMark from "../components/BrandMark";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg flex flex-col relative">
      <PageBackdrop variant="landing" />
      <header className="border-b border-border bg-surface">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
          <h1 className="brand-lockup text-lg font-semibold tracking-tight"><BrandMark />DVC Atlas</h1>
          <div className="flex items-center gap-3 text-sm">
            <Link to="/login" className="text-muted hover:text-ink transition-colors">
              Sign in
            </Link>
            <Link
              to="/signup"
              className="bg-accent text-white rounded px-3 py-1.5 font-medium hover:bg-accent/90 transition-colors"
            >
              Sign up
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1 flex items-center">
        <div className="landing-hero max-w-5xl mx-auto px-6 py-20 w-full relative">
          <span className="font-mono text-xs text-accent border border-accent/20 bg-accentSoft rounded px-2 py-1">
            DATA VERSION CONTROL
          </span>
          <h2 className="text-4xl font-semibold tracking-tight mt-4 max-w-2xl">
            Data version control that stores what actually changed.
          </h2>
          <p className="text-muted mt-4 max-w-xl leading-relaxed">
            Naive versioning stores a full copy of your data every time you
            save. This system chunks and hashes your files, so storage grows
            with distinct content — not with how many versions you've saved.
            Real Git history underneath, every version.
          </p>
          <div className="flex items-center gap-3 mt-8">
            <Link
              to="/signup"
              className="bg-accent text-white rounded px-5 py-2.5 font-medium hover:bg-accent/90 transition-colors"
            >
              Get started
            </Link>
            <Link
              to="/login"
              className="border border-border rounded px-5 py-2.5 font-medium hover:bg-surface transition-colors"
            >
              Sign in
            </Link>
          </div>

          <img className="landing-hero-visual" src={heroImage} alt="" aria-hidden="true" />

          <div className="grid grid-cols-3 gap-4 mt-16 max-w-3xl">
            <div className="border border-border bg-surface rounded-md p-4">
              <div className="text-sm font-medium">Content-addressed storage</div>
              <p className="text-xs text-muted mt-1">
                Files are chunked and hashed; unchanged chunks are never stored twice.
              </p>
            </div>
            <div className="border border-border bg-surface rounded-md p-4">
              <div className="text-sm font-medium">Real Git history</div>
              <p className="text-xs text-muted mt-1">
                Every save is a genuine commit — inspect it with git log.
              </p>
            </div>
            <div className="border border-border bg-surface rounded-md p-4">
              <div className="text-sm font-medium">Naive vs. dedup, measured</div>
              <p className="text-xs text-muted mt-1">
                A live chart compares the naive baseline against real storage savings.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}