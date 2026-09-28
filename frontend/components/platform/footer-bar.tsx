/**
 * Platform Console Footer Bar — M9-C71
 *
 * The operations console must declare its own runtime boundary. An operator
 * looking at a status screen has to be able to tell, without inference, that the
 * screen is showing recorded facts and is not itself running analysis:
 *
 *   - Band A — read-only console: no mutation engine, no LLM call, no repository
 *     scan, no full verification run.
 *   - No AI — nothing on this surface is model-generated. Every status is
 *     reported by the backend.
 *
 * `platform-dashboard.spec.ts` certifies both statements ("renders footer bar").
 * Before M9-C71 the console had no footer bar at all: the only footer was the
 * sidebar's build label, which says nothing about what the console is allowed to
 * do at runtime.
 */

export function PlatformFooterBar() {
  return (
    <footer
      data-testid="platform-footer-bar"
      className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-1 border-t border-[var(--border-subtle)] bg-[var(--surface-base)] px-5 py-2 font-mono text-xs text-[var(--text-tertiary)]"
    >
      <span data-testid="platform-footer-band">M9-C57 Band A</span>
      <span data-testid="platform-footer-ai">No AI</span>
      <span className="ml-auto">Read-only console — no mutation, no LLM, no repository scan</span>
    </footer>
  );
}
