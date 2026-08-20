# M9-C41 — Full Browser Matrix

**Status: CONDITIONAL** — chromium reproduced; 5 projects NOT CERTIFIED.

## Server Ownership (preserved, C38.6 / C41.18)

- Playwright owns port 3000 via `npm start` (`next start`, server mode). `reuseExistingServer: false`.
- Backend :8000 started/health-checked by `global-setup.ts`.
- **No second frontend server started during certification.**

## Matrix

| Project | Viewport | CI | Local | C41 Status |
|---------|----------|----|-------|------------|
| chromium | 1280×720 | ✓ | ✓ | REPRODUCED (213/7/13) |
| firefox | 1280×720 | ✓ | ✓ | NOT CERTIFIED |
| webkit | 1280×720 | ✓ | ✓ | NOT CERTIFIED |
| mobile-chrome | Pixel 5 | ✓ | ✓ | NOT CERTIFIED |
| mobile-safari | iPhone 12 | ✓ | ✓ | NOT CERTIFIED |
| tablet | iPad Pro | ✓ | ✓ | NOT CERTIFIED |

The CI matrix shards one project per job (`PLAYWRIGHT_PROJECT`) — the canonical browser environment. Local C41 prioritized defect forensics and reproduced **chromium only**. Per C41 §17, matrix reduction is forbidden; projects not executed are reported **NOT CERTIFIED** rather than falsely claimed green.
