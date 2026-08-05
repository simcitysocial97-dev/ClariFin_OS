#!/usr/bin/env bash
# .github/scripts/generate_release_notes.sh
# Generates RELEASE_NOTES.md for a tagged release.
# Invoked by the release workflow.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

VERSION="${1:-$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || echo 'unreleased')}"

cat > RELEASE_NOTES.md <<EOF
# Release ${VERSION}

Generated artifacts are ready for deployment.

## Assets
- Frontend distribution (frontend/.next)
- Release notes (RELEASE_NOTES.md)

## Verification
Run the release tag against the release verification profile to confirm
artifact integrity before deployment.
EOF

echo "RELEASE_NOTES.md generated for version ${VERSION}"
