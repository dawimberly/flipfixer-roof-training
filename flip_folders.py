"""Find other Flip Fixer / flpfx folders on this machine so ingest can scan them too."""

from __future__ import annotations

from pathlib import Path

# Names people actually put on Desktop copies of the shop (typos included).
FOLDER_HINTS = (
    "flpfx",
    "flpfxr",
    "flpfxt",
    "flpfixer",
    "flipfixer",
    "flip-fixer",
    "theflipfixer",
    "the-flip-fixer",
)

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".cache",
    ".cursor",
    "AppData",
    "site-packages",
}


def _normalized_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def looks_like_flip_folder(name: str) -> bool:
    compact = _normalized_name(name)
    if not compact:
        return False
    if any(_normalized_name(hint) in compact for hint in FOLDER_HINTS):
        return True
    return "fixer" in compact and ("flip" in compact or "flp" in compact)


def default_search_roots(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    candidates = [
        home / "Desktop",
        home / "Downloads",
        home / "Documents",
        home / "OneDrive" / "Desktop",
        home / "OneDrive" / "Downloads",
        home / "OneDrive" / "Documents",
        home / "OneDrive",
    ]
    return [path for path in candidates if path.exists()]


def discover_flip_folders(
    home: Path | None = None,
    extra_roots: list[Path] | None = None,
) -> list[Path]:
    """Return unique existing folders whose names look like Flip Fixer copies."""
    home = home or Path.home()
    roots = list(default_search_roots(home))
    if extra_roots:
        roots.extend(extra_roots)
    found: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        try:
            children = list(root.iterdir())
        except OSError:
            continue
        for child in children:
            if not child.is_dir():
                continue
            if child.name in SKIP_DIR_NAMES:
                continue
            if not looks_like_flip_folder(child.name):
                continue
            resolved = child.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            found.append(child)
    return found


def ingest_roots(
    home: Path | None = None,
    extra_roots: list[Path] | None = None,
) -> list[Path]:
    """Desktop-style roots plus any Flip Fixer / flpfx folders sitting next to them."""
    home = home or Path.home()
    roots = default_search_roots(home)
    for folder in discover_flip_folders(home, extra_roots=extra_roots):
        if folder not in roots:
            roots.append(folder)
    return roots
