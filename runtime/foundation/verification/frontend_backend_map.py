"""Frontend-to-Backend API endpoint consumer mapper.

Scans the frontend codebase for API endpoint references and builds a
bidirectional map between backend endpoints and the frontend files that
consume them.  Supports hooks, components, app pages, capability hooks,
and the generated API client.

Scan patterns:
  - apiFetch('/api/...', ...)
  - apiFetch(`  /api/...`, ...)
  - apiFetchJson('/api/...')
  - fetch('/api/...', ...)
  - useQuery({ queryFn: () => apiFetchJson('/api/...'), ... })

Dynamic segments such as ${id} are normalized to :param so that
/api/loans/${id} and /api/loans/123 are both mapped to /api/loans/:param.

Results are cached to runtime/generated/frontend-backend-map.json and
only recomputed when any scanned source file's mtime changes.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Regex patterns for endpoint extraction
# ---------------------------------------------------------------------------

# Matches string/template-literal arguments to known fetch functions.
# Captures the URL portion after the opening quote/backtick.
FETCH_CALL_RE = re.compile(
    r"""(?:apiFetch|apiFetchJson|fetch)\s*\(\s*(?:[`'"])([^`'"]+)(?:[`'"])""",
    re.IGNORECASE,
)

# Standalone URL string literals starting with /api/ or /platform/
# Used as fallback for indirect references (e.g. variable assignment then call).
URL_LITERAL_RE = re.compile(
    r"""['"`]/((?:api|platform)/[^`"'\\\s\$\}\]\)]+)['"`]""",
    re.IGNORECASE,
)

# Template-literal URLs containing ${...} substitutions
TEMPLATE_URL_RE = re.compile(
    r"""`(/(?:api|platform)/[^`]+)`""",
)

# Lines that are imports — skip them entirely.
IMPORT_LINE_RE = re.compile(r"^\s*import\s+")

# Lines that are comments (single-line // or block-comment continuation *)
COMMENT_LINE_RE = re.compile(r"^\s*(?://.*|/\*|\*)\s*$")


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

# Pattern that matches ${...} expressions inside template literals.
_DOLLAR_BRACE_RE = re.compile(r"\$\{([^}]+)\}")

# Trailing query-string portion to strip when building the normalised key.
_QUERY_STRIP_RE = re.compile(r"\?[^\s`'\"]*$")


def _strip_query(path: str) -> str:
    """Remove trailing query-string from a raw path."""
    return _QUERY_STRIP_RE.sub("", path)


def _normalize_template_vars(path: str) -> str:
    """Replace ${anything} with :param so dynamic paths converge."""
    return _DOLLAR_BRACE_RE.sub(":param", path)


def _normalize_path(raw: str) -> str:
    """Return a normalised endpoint key for a raw URL string."""
    p = _strip_query(raw)
    p = _normalize_template_vars(p)
    # Collapse trailing slashes (but keep the leading slash).
    p = p.rstrip("/") or p
    return p


def _is_import_line(line: str) -> bool:
    return bool(IMPORT_LINE_RE.match(line)) or "from '" in line or 'from "' in line


def _is_comment_line(line: str) -> bool:
    if bool(COMMENT_LINE_RE.match(line)):
        return True
    # Also skip lines that are entirely an inline block comment.
    stripped = line.strip()
    if stripped.startswith("/*") and stripped.endswith("*/"):
        return True
    return False


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ConsumerInfo:
    """Metadata about who consumes a given backend endpoint."""

    endpoint: str
    hook_files: List[str] = field(default_factory=list)
    component_files: List[str] = field(default_factory=list)
    total_references: int = 0
    last_scanned: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Scan configuration
# ---------------------------------------------------------------------------

_HOOK_DIRS = [
    Path("frontend/lib/hooks"),
    Path("frontend/lib/capabilities"),
    Path("frontend/lib/api"),
]

_COMPONENT_DIRS = [
    Path("frontend/components"),
    Path("frontend/app"),
]

_ALL_SCAN_DIRS = _HOOK_DIRS + _COMPONENT_DIRS

_GENERATED_CACHE_PATH = Path("runtime/generated/frontend-backend-map.json")


class FrontendBackendMapper:
    """Scans the frontend codebase and maps backend endpoints to consumers."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root) if root is not None else Path(".")
        self._cache_path = self.root / _GENERATED_CACHE_PATH
        self._file_mtimes: Dict[str, float] = {}
        self._consumer_map: Dict[str, ConsumerInfo] = {}
        self._load_cache_if_valid()

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def _load_cache_if_valid(self) -> None:
        if not self._cache_path.exists():
            return
        try:
            data = json.loads(self._cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        cached_mtimes: Dict[str, float] = data.get("_mtimes", {})
        if cached_mtimes != self._compute_all_mtimes():
            return

        self._file_mtimes = cached_mtimes
        raw_map: Dict[str, dict] = data.get("consumer_map", {})
        self._consumer_map = {
            ep: ConsumerInfo(**info) for ep, info in raw_map.items()
        }

    def _persist_cache(self) -> None:
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict = {
            "_mtimes": self._file_mtimes,
            "consumer_map": {
                ep: info.to_dict() for ep, info in self._consumer_map.items()
            },
        }
        self._cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _compute_all_mtimes(self) -> Dict[str, float]:
        mtimes: Dict[str, float] = {}
        for fp in self._iter_source_files():
            try:
                mtimes[str(fp)] = fp.stat().st_mtime
            except OSError:
                pass
        return mtimes

    # ------------------------------------------------------------------
    # Source-file enumeration
    # ------------------------------------------------------------------

    def _iter_source_files(self) -> List[Path]:
        files: List[Path] = []
        seen: Set[str] = set()
        for d in _ALL_SCAN_DIRS:
            base = self.root / d
            if not base.exists():
                continue
            for root_dir, _, fnames in os.walk(base):
                for fname in fnames:
                    if fname.endswith((".ts", ".tsx")):
                        fp = Path(root_dir) / fname
                        key = str(fp.resolve())
                        if key not in seen:
                            seen.add(key)
                            files.append(fp)
        return sorted(files)

    # ------------------------------------------------------------------
    # Line-level extraction
    # ------------------------------------------------------------------

    def _extract_paths_from_file(self, filepath: Path) -> List[str]:
        """Return a list of normalised endpoint keys found in *filepath*."""
        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return []

        endpoints: List[str] = []
        for line in text.splitlines():
            if _is_import_line(line) or _is_comment_line(line):
                continue
            # Template-literal URLs (backtick strings containing /api/ or /platform/).
            for m in TEMPLATE_URL_RE.finditer(line):
                raw = m.group(1)
                if "/api/" in raw or "/platform/" in raw:
                    endpoints.append(_normalize_path(raw))
            # Quoted-string URL arguments to fetch functions.
            for m in FETCH_CALL_RE.finditer(line):
                raw = m.group(1)
                if raw.startswith("/api/") or raw.startswith("/platform/"):
                    endpoints.append(_normalize_path(raw))
            # Standalone URL literals (not inside a function call).
            for m in URL_LITERAL_RE.finditer(line):
                raw = "/" + m.group(1)  # group(1) omits the leading slash
                if "/api/" in raw or "/platform/" in raw:
                    endpoints.append(_normalize_path(raw))

        return list(dict.fromkeys(endpoints))  # deduplicate, preserve order

    # ------------------------------------------------------------------
    # Classifiers
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_file(filepath: Path) -> str:
        """Return 'hook' or 'component' based on file location."""
        strpath = str(filepath)
        if any(d in strpath for d in ("lib/hooks", "lib/capabilities", "lib/api")):
            return "hook"
        if any(d in strpath for d in ("components", "app/")):
            return "component"
        return "other"

    # ------------------------------------------------------------------
    # Public scanning API
    # ------------------------------------------------------------------

    def scan_frontend_hooks(self) -> Dict[str, List[Path]]:
        """Return endpoint → list of hook-source files mapping."""
        result: Dict[str, List[Path]] = {}
        for fp in self._iter_source_files():
            if self._classify_file(fp) != "hook":
                continue
            for ep in self._extract_paths_from_file(fp):
                result.setdefault(ep, []).append(fp)
        return result

    def scan_frontend_components(self) -> Dict[str, List[Path]]:
        """Return endpoint → list of component/page-source files mapping."""
        result: Dict[str, List[Path]] = {}
        for fp in self._iter_source_files():
            if self._classify_file(fp) != "component":
                continue
            for ep in self._extract_paths_from_file(fp):
                result.setdefault(ep, []).append(fp)
        return result

    def build_consumer_map(self) -> Dict[str, ConsumerInfo]:
        """Build (or reload) the full endpoint→ConsumerInfo map."""
        need_rebuild = False
        current_mtimes = self._compute_all_mtimes()
        if current_mtimes != self._file_mtimes:
            need_rebuild = True
            self._file_mtimes = current_mtimes

        if need_rebuild or not self._consumer_map:
            hook_map = self.scan_frontend_hooks()
            comp_map = self.scan_frontend_components()
            all_endpoints: Set[str] = set(hook_map) | set(comp_map)

            new_map: Dict[str, ConsumerInfo] = {}
            for ep in all_endpoints:
                hooks = hook_map.get(ep, [])
                comps = comp_map.get(ep, [])
                new_map[ep] = ConsumerInfo(
                    endpoint=ep,
                    hook_files=[str(f) for f in hooks],
                    component_files=[str(f) for f in comps],
                    total_references=len(hooks) + len(comps),
                    last_scanned=time.time(),
                )
            self._consumer_map = new_map
            self._persist_cache()

        return self._consumer_map

    def get_consumers_for_endpoint(self, endpoint: str) -> List[Path]:
        """Return all frontend files consuming *endpoint*."""
        info = self.build_consumer_map().get(endpoint)
        if info is None:
            return []
        files: List[Path] = []
        for p in info.hook_files:
            files.append(Path(p))
        for p in info.component_files:
            files.append(Path(p))
        return files

    def get_endpoints_for_file(self, file_path: Path) -> List[str]:
        """Return all normalised endpoints referenced by *file_path*."""
        if not file_path.is_absolute():
            file_path = self.root / file_path
        endpoints = self._extract_paths_from_file(file_path)
        # Cross-reference against the built map to only return known endpoints.
        known = set(self.build_consumer_map().keys())
        return [ep for ep in endpoints if ep in known]
