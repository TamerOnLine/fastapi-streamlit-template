#!/usr/bin/env python3
"""
audit_files_pro.py — Practical auditor for FastAPI + Streamlit + ReportLab projects.

Features:
1) Static import graph from entry points:
   - api/main.py
   - streamlit/app.py (optional)
2) Keeps PDF blocks referenced via:
   - layouts/*.json block_id values
   - api/pdf_utils/blocks/__init__.py side-effect imports
3) Keeps api/routes/* if included via app.include_router(...)
4) Optional runtime coverage merge: --coverage-xml coverage.xml
5) Classifies into: core, support, non_essential, generated
6) (Optional) Build a clean deployable copy with only core + config/assets: --make-clean-build

Outputs:
- project_file_roles.json
- helper scripts: run_coverage_fastapi.*, hit_endpoints.*
"""

from __future__ import annotations
import argparse, ast, json, os, xml.etree.ElementTree as ET, shutil
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
    return [p for p in root.rglob("*.py")
            if ".venv" not in p.parts and "site-packages" not in p.parts and ".trash" not in p.parts]

def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def blocks_from_layouts(root: Path) -> Set[str]:
    req: Set[str] = set()
    layout_dir = root / "layouts"
    if not layout_dir.exists():
        return req
    for p in layout_dir.glob("*.json"):
        data = read_json(p) or {}
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
    p = root / "api" / "pdf_utils" / "blocks" / "__init__.py"
    mods: Set[str] = set()
    if not p.exists(): return mods
    try:
        src = p.read_text(encoding="utf-8")
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

def routers_from_api_main(root: Path) -> bool:
    """Return True if app.include_router is used -> keep api/routes/*."""
    p = root / "api" / "main.py"
    if not p.exists():
        return False
    try:
        src = p.read_text(encoding="utf-8"); tree = ast.parse(src, filename=str(p))
    except Exception:
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "include_router":
            return True
    return False

def build_import_graph(root: Path) -> Tuple[Dict[str, Set[str]], Dict[str, Path]]:
    files = collect_py_files(root)
    by_mod = {module_name(root, p): p for p in files}
    edges: Dict[str, Set[str]] = {m: set() for m in by_mod}
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
        if m in seen: return
        seen.add(m)
        for n in edges.get(m, ()): dfs(n)
    for e in entries:
        if e in edges: dfs(e)
    return seen

def read_coverage_xml(path: Path, root: Path) -> Set[Path]:
    executed: Set[Path] = set()
    try:
        tree = ET.parse(path)
    except Exception:
        return executed
    for cls in tree.findall(".//class"):
        filename = cls.get("filename") or ""
        if not filename: continue
        p = (root / filename).resolve()
        if p.exists(): executed.add(p)
    return executed

def classify_files(root: Path, coverage_xml: Path | None) -> Dict[str, dict]:
    edges, by_mod = build_import_graph(root)
    entries = []
    if (root / "api" / "main.py").exists():
        entries.append(module_name(root, root / "api" / "main.py"))
    if (root / "streamlit" / "app.py").exists():
        entries.append(module_name(root, root / "streamlit" / "app.py"))
    reach = reachable_from(entries, edges)

    # Keep blocks from layouts + explicit in blocks/__init__.py
    for bid in blocks_from_layouts(root):
        p = root / "api" / "pdf_utils" / "blocks" / f"{bid}.py"
        if p.exists(): reach.add(module_name(root, p))
    for mod_tail in blocks_from_blocks_init(root):
        p = root / "api" / "pdf_utils" / "blocks" / f"{mod_tail}.py"
        if p.exists(): reach.add(module_name(root, p))

    # Keep all api/routes if routers used
    if routers_from_api_main(root):
        for p in (root / "api" / "routes").glob("*.py"):
            reach.add(module_name(root, p))

    executed_paths: Set[Path] = set()
    if coverage_xml and coverage_xml.exists():
        executed_paths = read_coverage_xml(coverage_xml, root)

    roles: Dict[str, dict] = {}
    def add_role(p: Path, role: str, reason: str):
        rel = p.resolve().relative_to(root).as_posix()
        info = roles.setdefault(rel, {"role": role, "reasons": set()})
        order = {"core": 3, "support": 2, "non_essential": 1, "generated": 0}
        if order[role] > order[info["role"]]:
            info["role"] = role
        info["reasons"].add(reason)

    # Classify .py files
    for m, p in by_mod.items():
        if m in reach:
            add_role(p, "core", "reachable from entry-points / layouts / registry")
        else:
            # dev tools / tests heuristics
            if "tools" in p.parts or "debug" in p.name or p.name.endswith("_test.py"):
                add_role(p, "support", "dev tool or debug/test script")
            else:
                add_role(p, "support", "unreachable Python module (static graph)")
        if p in executed_paths:
            add_role(p, "core", "executed at runtime (coverage)")

    # Non-code files
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
        elif "api/pdf_utils/assets" in rel:
            add_role(p, "core", "font/icon asset")
        elif p.name in (".gitignore","LICENSE","README.md","env-info.txt","requirements.txt"):
            add_role(p, "non_essential", "documentation or meta")
        else:
            add_role(p, "non_essential", "not code and not clearly required")

    # normalize reasons
    for v in roles.values():
        v["reasons"] = sorted(v["reasons"])
    return roles

def write_helpers(root: Path):
    (root / "hit_endpoints.ps1").write_text(
        'Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/healthz | Out-Null\n'
        'Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/docs    | Out-Null\n'
        'Write-Host "Endpoints hit."', encoding="utf-8"
    )
    (root / "hit_endpoints.sh").write_text(
        '#!/usr/bin/env bash\ncurl -s http://127.0.0.1:8000/healthz > /dev/null\n'
        'curl -s http://127.0.0.1:8000/docs    > /dev/null\necho "Endpoints hit."', encoding="utf-8"
    )
    (root / "run_coverage_fastapi.ps1").write_text(
        'coverage run -m uvicorn api.main:app --host 127.0.0.1 --port 8000', encoding="utf-8"
    )
    (root / "run_coverage_fastapi.sh").write_text(
        '#!/usr/bin/env bash\ncoverage run -m uvicorn api.main:app --host 127.0.0.1 --port 8000', encoding="utf-8"
    )

def make_clean_build(root: Path, roles: Dict[str, dict], out_dir: Path):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def should_copy(rel: str, meta: dict) -> bool:
        if meta["role"] == "core":
            return True
        # keep config / assets explicitly (already marked core above, but just in case)
        if rel.startswith(("themes/", "layouts/")) and rel.endswith(".json"):
            return True
        if "api/pdf_utils/assets" in rel:
            return True
        return False

    for rel, meta in roles.items():
        src = root / rel
        if not src.exists():
            continue
        if should_copy(rel, meta):
            dst = out_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # always copy requirements & README if exist
    for name in ("requirements.txt", "README.md", "LICENSE"):
        p = root / name
        if p.exists():
            dst = out_dir / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root")
    ap.add_argument("--coverage-xml", default="", help="Path to coverage.xml (Cobertura)")
    ap.add_argument("--make-clean-build", action="store_true", help="Create clean_build/ with only core+config+assets")
    args = ap.parse_args()

    root = detect_repo_root(Path(args.root))
    cov_xml = Path(args.coverage_xml) if args.coverage_xml else None

    roles = classify_files(root, cov_xml)
    out_json = root / "project_file_roles.json"
    out_json.write_text(json.dumps(roles, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[✓] Wrote {out_json}")

    write_helpers(root)
    print("[✓] Wrote helper scripts: run_coverage_fastapi.*, hit_endpoints.*")

    if args.make_clean_build:
        out_dir = root / "clean_build"
        make_clean_build(root, roles, out_dir)
        print(f"[✓] Built clean bundle at: {out_dir}")

if __name__ == "__main__":
    main()
