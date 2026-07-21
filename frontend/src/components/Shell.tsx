import Link from "next/link";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:p-3 focus:text-black">
        Aller au contenu
      </a>

      {/* Barre de titre applicative */}
      <header className="sticky top-0 z-30 border-b border-line bg-surface/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-8">
          <Link href="/diagnostics/new" className="flex min-h-12 items-center gap-3 rounded-md">
            <span aria-hidden="true" className="grid h-10 w-10 place-items-center rounded-md bg-primary font-black text-canvas shadow-[0_0_16px_rgba(245,165,36,.35)]">
              ◈
            </span>
            <span className="leading-tight">
              <strong className="block text-[15px] font-extrabold tracking-wide">DiagPilot</strong>
              <span className="text-[11px] uppercase tracking-[.18em] text-muted">Assistant diagnostic · Atelier</span>
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 rounded-md border border-line bg-panel px-3 py-2 font-mono text-[11px] uppercase tracking-wider text-slate-300 sm:inline-flex">
              <span className="led" aria-hidden="true" />
              Système prêt
            </span>
            <Link className="btn-primary" href="/diagnostics/new">Nouveau diagnostic</Link>
          </div>
        </div>

        {/* Bandeau mode démonstration */}
        <div className="border-t border-line/70 bg-amber-950/25">
          <div className="mx-auto flex max-w-7xl items-center gap-2 px-4 py-1.5 font-mono text-[11px] uppercase tracking-wider text-amber-300/90 md:px-8">
            <span className="led-amber led" aria-hidden="true" />
            Mode démonstration — données non contractuelles, aucune commande de calculateur
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 md:px-8">
        {children}
      </main>

      {/* Barre de statut */}
      <footer className="border-t border-line bg-panel">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-2.5 font-mono text-[11px] text-muted md:px-8">
          <span className="flex items-center gap-2">
            <span className="led led-muted" aria-hidden="true" />
            Aide à la décision · aucun remplacement de pièce sans contrôle de confirmation
          </span>
          <span className="uppercase tracking-wider">DiagPilot v0.1 · le jugement professionnel reste indispensable</span>
        </div>
      </footer>
    </div>
  );
}
