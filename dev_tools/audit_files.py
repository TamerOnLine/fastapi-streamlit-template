#!/usr/bin/env python3
"""
audit_files.py — Practical project file auditor & cleaner for FastAPI + Streamlit + ReportLab resume projects.

What it does:
1) Builds a Python import graph starting from entry points:
   - api/main.py    (FastAPI backend)
   - streamlit/app.py (Streamlit frontend) — optional if missing
2) Adds side-effect imports from api/pdf_utils/blocks/__init__.py (block registry)
3) Parses layouts/*.json to collect required block_ids (so block files are preserved even if not directly imported)
4) Detects routers included via app.include_router(...) to keep their modules
5) Classifies files into: core, support, non_essential, generated
6) Writes project_file_roles.json and creates safe-delete scripts that move files to .trash/

Usage:
    python audit_files.py [--root .] [--dry-run]
"""
from __future__ import annotations
import ast
import argparse
import os
from pathlib import Path
from typing import Dict, Set, List, Tuple

ROOT_MARKERS = ["api", "streamlit", "themes", "layouts", "tools"]

def detect_repo_root(start: Path) -> Path:
    p = start.resolve()
    while p != p.parent:
        if any((p / m).exists() for m in ROOT_MARKERS):
            return p
        p = p.parent
    return start.resolve()

def module_name(root: Path, p: Path) -> str:
    rel = p.resolve().relative_to(root).with_suffix("")
    return ".".join(rel.parts)

def parse_imports(p: Path) -> Set[str]:
    try:
        src = p.read_text(encoding="utf-8")
    except Exception:
        return set()
    try:
        tree = ast.parse(src, filename=str(p))
    except Exception:
        return set()
    mods: Set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name:
                    mods.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                mods.add(n.module.split(".")[0])
    return mods

def collect_py_files(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.py") if ".venv" not in p.parts and "site-packages" not in p.parts]

def read_json(p: Path):
    import json
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def blocks_from_layouts(root: Path) -> Set[str]:
    req: Set[str] = set()
    for p in (root / "layouts").glob("*.json"):
        data = read_json(p) or {}
        # Layout item could be list of blocks or dicts with block_id
        def walk(x):
            if isinstance(x, dict):
                bid = x.get("block_id")
                if isinstance(bid, str):
                    req.add(bid.strip())
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for it in x:
                    walk(it)
        walk(data)
    return {b for b in req if b}

def blocks_from_blocks_init(root: Path) -> Set[str]:
    """Parse api/pdf_utils/blocks/__init__.py and extract modules imported there."""
    p = root / "api" / "pdf_utils" / "blocks" / "__init__.py"
    mods: Set[str] = set()
    if not p.exists():
        return mods
    try:
        src = p.read_text(encoding="utf-8")
    except Exception:
        return mods
    try:
        tree = ast.parse(src, filename=str(p))
    except Exception:
        return mods
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.endswith(".blocks"):
            for a in n.names:
                if a.name != "*":
                    mods.add(a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name and ".blocks." in a.name:
                    mods.add(a.name.split(".")[-1])
    return mods

def routers_from_api_main(root: Path) -> Set[str]:
    """Try to find included routers to keep their modules."""
    p = root / "api" / "main.py"
    keep: Set[str] = set()
    if not p.exists():
        return keep
    try:
        src = p.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(p))
    except Exception:
        return keep
    # naive: look for app.include_router(NAME)
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "include_router":
            # record the file where routers likely live (api/routes/*)
            keep.add("api.routes")
    return keep

def build_import_graph(root: Path) -> Tuple[Dict[str, Set[str]], Dict[str, Path]]:
    files = collect_py_files(root)
    by_mod = {module_name(root, p): p for p in files}
    edges: Dict[str, Set[str]] = {m: set() for m in by_mod}
    # Build loose edges: if import token matches prefix of a module path
    for m, p in by_mod.items():
        tokens = parse_imports(p)
        for tok in tokens:
            for target in by_mod:
                if target.startswith(tok):
                    edges[m].add(target)
    return edges, by_mod

def reachable_from(entries: List[str], edges: Dict[str, Set[str]]) -> Set[str]:
    seen: Set[str] = set()
    def dfs(m: str):
        if m in seen:
            return
        seen.add(m)
        for n in edges.get(m, ()):
            dfs(n)
    for e in entries:
        if e in edges:
            dfs(e)
    return seen

def classify_files(root: Path) -> Dict[str, dict]:
    edges, by_mod = build_import_graph(root)
    entries = []
    if (root / "api" / "main.py").exists():
        entries.append(module_name(root, root / "api" / "main.py"))
    if (root / "streamlit" / "app.py").exists():
        entries.append(module_name(root, root / "streamlit" / "app.py"))

    reach = reachable_from(entries, edges)

    # Keep block modules mentioned in layouts
    block_ids = blocks_from_layouts(root)
    # map block_id -> file path if exists under api/pdf_utils/blocks/{block_id}.py
    for bid in block_ids:
        p = root / "api" / "pdf_utils" / "blocks" / f"{bid}.py"
        if p.exists():
            reach.add(module_name(root, p))

    # Keep explicit imports from blocks/__init__.py
    for mod_tail in blocks_from_blocks_init(root):
        p = root / "api" / "pdf_utils" / "blocks" / f"{mod_tail}.py"
        if p.exists():
            reach.add(module_name(root, p))

    # Keep routers folder if included
    for mod in routers_from_api_main(root):
        # include all modules under api/routes
        for p in (root / "api" / "routes").glob("*.py"):
            reach.add(module_name(root, p))

    roles: Dict[str, dict] = {}

    def add_role(p: Path, role: str, reason: str):
        rel = p.resolve().relative_to(root).as_posix()
        info = roles.setdefault(rel, {"role": role, "reasons": set()})
        # escalate: core > support > non_essential > generated
        order = {"core": 3, "support": 2, "non_essential": 1, "generated": 0}
        if order[role] > order[info["role"]]:
            info["role"] = role
        info["reasons"].add(reason)

    # Classify .py
    for m, p in by_mod.items():
        if m in reach:
            add_role(p, "core", "reachable from entry-points / layouts / registry")
        else:
            # heuristics: tools, debug, scripts
            if "tools" in p.parts or "debug" in p.name or p.name.endswith("_test.py"):
                add_role(p, "support", "dev tool or debug script")
            else:
                add_role(p, "support", "unreachable Python module (double-check before removal)")

    # Classify non-code
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        rel = p.resolve().relative_to(root).as_posix()
        if rel in roles:
            continue
        if any(rel.startswith(x) for x in ["outputs/", "profiles/"]) or rel.endswith(".pdf"):
            add_role(p, "generated", "runtime output or saved profile")
        elif rel.startswith(("themes/", "layouts/")) and p.suffix.lower() == ".json":
            add_role(p, "core", "required configuration (themes/layouts)")
        elif p.name in (".gitignore", "LICENSE", "README.md", "env-info.txt", "requirements.txt"):
            add_role(p, "non_essential", "documentation or meta")
        else:
            # assets like fonts/icons used by PDF are core
            if "api/pdf_utils/assets" in rel:
                add_role(p, "core", "font/icon asset")
            else:
                add_role(p, "non_essential", "not code and not clearly required")

    # Convert reasons to list
    for v in roles.values():
        v["reasons"] = sorted(v["reasons"])

    return roles

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root (defaults to current dir)")
    ap.add_argument("--dry-run", action="store_true", help="Do not write scripts, just show report")
    args = ap.parse_args()

    root = detect_repo_root(Path(args.root))
    roles = classify_files(root)

    out_json = root / "project_file_roles.json"
    out_json.write_text(json.dumps(roles, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[✓] Wrote {out_json}")

    # Prepare safe-delete lists
    trash_candidates = [p for p, meta in roles.items()
                        if meta["role"] in ("non_essential", "support") and not p.endswith(".json")]
    # Do not delete core or config; we only move to .trash/
    bash = root / "safe_delete.sh"
    ps1  = root / "safe_delete.ps1"
    bash.write_text("#!/usr/bin/env bash\nset -euo pipefail\nTRASH=.trash\nmkdir -p \"$TRASH\"\n" +
                    "\n".join([f'mkdir -p \"$TRASH/$(dirname \\"{p}\\")\"; mv -v \"{p}\" \"$TRASH/{p}\" || true' for p in trash_candidates]) +
                    "\necho \"Moved candidates to $TRASH (nothing permanently deleted).\"\n", encoding="utf-8")
    ps1.write_text("New-Item -ItemType Directory -Force -Path .trash | Out-Null\n" +
                   "\n".join([f'$dest = ".trash/{p}".Replace("/", "\\\\"); $dir = Split-Path $dest; New-Item -ItemType Directory -Force -Path $dir | Out-Null; Move-Item -Force -Path "{p}" -Destination $dest -ErrorAction SilentlyContinue' for p in trash_candidates]) +
                   "\nWrite-Host 'Moved candidates to .trash (nothing permanently deleted).'\n", encoding="utf-8")

    if not args.dry_run:
        print(f"[✓] Wrote {bash}")
        print(f"[✓] Wrote {ps1}")
    else:
        print("[i] Dry-run: scripts not written")

if __name__ == "__main__":
    main()
