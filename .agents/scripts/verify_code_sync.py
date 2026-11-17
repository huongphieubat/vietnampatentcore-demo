#!/usr/bin/env python3
"""Kiểm tra đồng bộ liên tệp, hợp đồng API/DB/DOM, cú pháp đa ngôn ngữ (kể cả JS nhúng HTML) và chống cắt cụt code AI."""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".handoff",
    ".agents",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
}

CHECKABLE_EXTS = {
    ".py",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".sql",
    ".json",
}

AI_LAZY_TRUNCATION_RE = re.compile(
    r"(?i)(?://|#|--|/\*|<!--)\s*\.\.\.\s*"
    r"(?:existing|rest\s+of|remaining|unchanged|previous|keep\s+existing|omitted|phần\s+còn\s+lại|giữ\s+nguyên)\s*"
    r"(?:code|lines|implementation|html|css|functions?|mã\s+nguồn)?"
)
MERGE_CONFLICT_RE = re.compile(r"^(?:<{7}\s|={7}\s*$|>{7}\s)")
SECRET_LEAK_RE = re.compile(
    r"(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{32,}|"
    r"AIzaSy[A-Za-z0-9_-]{33}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)
JS_REL_IMPORT_RE = re.compile(
    r"""^\s*(?:import|export)\s+(?:.+?\s+from\s+)?['"](\.\.?/[^'"]+)['"]|require\(\s*['"](\.\.?/[^'"]+)['"]\s*\)"""
)
HTML_SCRIPT_OPEN_RE = re.compile(r"<script\b([^>]*)>", re.IGNORECASE)
HTML_SCRIPT_CLOSE_RE = re.compile(r"</script\s*>", re.IGNORECASE)
HTML_ID_SET_RE = re.compile(r"""\bid\s*=\s*["']([A-Za-z0-9_.:-]+)["']""")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def iter_code_files(root: Path, only_files: list[str] | None = None) -> list[Path]:
    if only_files:
        out: list[Path] = []
        for rel in only_files:
            p = (root / rel).resolve()
            if p.is_file() and p.suffix.lower() in CHECKABLE_EXTS:
                out.append(p)
        return out

    found: list[Path] = []
    stack = [root]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError:
            continue
        subdirs: list[Path] = []
        for entry in entries:
            if entry.name in SKIP_DIRS:
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    subdirs.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    p = Path(entry.path)
                    ext = p.suffix.lower()
                    if ext in CHECKABLE_EXTS:
                        if ext == ".json" and entry.stat(follow_symlinks=False).st_size > 512 * 1024:
                            continue
                        found.append(p)
            except OSError:
                continue
        stack.extend(reversed(subdirs))
    return found


def _node_bin() -> str | None:
    return shutil.which("node")


def _check_js_syntax_with_node(js_code: str, is_module: bool = False) -> str | None:
    node = _node_bin()
    if not node:
        return None
    suffix = ".mjs" if is_module else ".js"
    with tempfile.NamedTemporaryFile("w", suffix=suffix, encoding="utf-8", delete=False) as tf:
        tf.write(js_code)
        tmp_path = Path(tf.name)
    try:
        proc = subprocess.run(
            [node, "--check", str(tmp_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        if proc.returncode != 0:
            err_lines = [ln.strip() for ln in (proc.stderr or proc.stdout).splitlines() if ln.strip()]
            return " | ".join(err_lines[:3])
        return None
    except subprocess.TimeoutExpired:
        return "node --check timeout"
    finally:
        tmp_path.unlink(missing_ok=True)


def check_file_syntax(fp: Path, rel: str, text: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    ext = fp.suffix.lower()

    if ext == ".py":
        try:
            ast.parse(text, filename=rel)
        except SyntaxError as exc:
            issues.append(
                {
                    "code": "C01_SYNTAX",
                    "severity": "ERROR",
                    "file": rel,
                    "location": f"L{exc.lineno or 1}",
                    "detail": f"Lỗi cú pháp Python: {exc.msg}",
                }
            )
    elif ext == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            issues.append(
                {
                    "code": "C01_SYNTAX",
                    "severity": "ERROR",
                    "file": rel,
                    "location": f"L{exc.lineno}",
                    "detail": f"Lỗi cú pháp JSON: {exc.msg}",
                }
            )
    elif ext in {".js", ".mjs", ".cjs"}:
        is_mod = ext == ".mjs" or bool(re.search(r"(?m)^\s*(?:import|export)\s+", text))
        err = _check_js_syntax_with_node(text, is_module=is_mod)
        if err:
            issues.append(
                {
                    "code": "C01_SYNTAX",
                    "severity": "ERROR",
                    "file": rel,
                    "location": "JS",
                    "detail": f"Lỗi cú pháp JavaScript: {err}",
                }
            )
    elif ext == ".html":
        script_block_re = re.compile(r"<script\b([^>]*)>(.*?)</script\s*>", re.IGNORECASE | re.DOTALL)
        for m in script_block_re.finditer(text):
            attrs = m.group(1).lower()
            inner = m.group(2)
            start_line = text.count("\n", 0, m.start()) + 1
            end_line = text.count("\n", 0, m.end()) + 1
            if "src=" in attrs:
                continue
            skip_block = any(
                t in attrs
                for t in (
                    "application/json",
                    "application/ld+json",
                    "importmap",
                    "text/template",
                    "text/x-template",
                    "text/babel",
                )
            )
            if skip_block or not inner.strip() or "{{" in inner or "{%" in inner:
                continue
            is_mod = 'type="module"' in attrs or "type='module'" in attrs
            padded_js = ("\n" * (start_line - 1)) + inner
            err = _check_js_syntax_with_node(padded_js, is_module=is_mod)
            if err:
                loc = f"L{start_line}" if start_line == end_line else f"L{start_line}-L{end_line}"
                issues.append(
                    {
                        "code": "C01_SYNTAX",
                        "severity": "ERROR",
                        "file": rel,
                        "location": loc,
                        "detail": f"Lỗi cú pháp <script> nội tuyến: {err}",
                    }
                )
        stripped_html = re.sub(r"<!--.*?-->", "", script_block_re.sub("", text), flags=re.DOTALL)
        dangling = HTML_SCRIPT_OPEN_RE.search(stripped_html)
        if dangling:
            unclosed_ln = stripped_html.count("\n", 0, dangling.start()) + 1
            issues.append(
                {
                    "code": "C01_SYNTAX",
                    "severity": "ERROR",
                    "file": rel,
                    "location": f"L{unclosed_ln}",
                    "detail": "Thẻ <script> mở nhưng không có thẻ đóng </script> (nghi ngờ file bị cắt cụt)",
                }
            )
    return issues


def _collect_py_module_exports(py_path: Path) -> set[str] | None:
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None
    exported: set[str] = set()
    has_star_reexport = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            exported.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    exported.add(t.id)
                elif isinstance(t, ast.Tuple):
                    for elt in t.elts:
                        if isinstance(elt, ast.Name):
                            exported.add(elt.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            exported.add(node.target.id)
        elif isinstance(node, ast.Import):
            for a in node.names:
                exported.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name == "*":
                    has_star_reexport = True
                else:
                    exported.add(a.asname or a.name)
    if has_star_reexport:
        return None
    return exported


def _resolve_local_py_module(root: Path, caller_dir: Path, module_name: str, level: int) -> Path | None:
    base = caller_dir
    if level > 0:
        for _ in range(level - 1):
            base = base.parent
        rel_parts = module_name.split(".") if module_name else []
        cand_bases = [base]
    else:
        if not module_name:
            return None
        rel_parts = module_name.split(".")
        cand_bases = [root, caller_dir]

    for b in cand_bases:
        target = b.joinpath(*rel_parts)
        py_file = target.with_suffix(".py")
        init_file = target / "__init__.py"
        if py_file.is_file() and root in py_file.resolve().parents:
            return py_file.resolve()
        if init_file.is_file() and root in init_file.resolve().parents:
            return init_file.resolve()
    return None


def check_cross_file_imports(root: Path, files: list[Path]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    export_cache: dict[Path, set[str] | None] = {}

    for fp in files:
        rel = fp.relative_to(root).as_posix()
        ext = fp.suffix.lower()
        text = fp.read_text(encoding="utf-8", errors="replace")

        if ext == ".py":
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in tree.body:
                if isinstance(node, ast.ImportFrom):
                    local_mod = _resolve_local_py_module(root, fp.parent, node.module or "", node.level)
                    if local_mod is None:
                        if node.level > 0:
                            issues.append(
                                {
                                    "code": "C02_IMPORT_SYNC",
                                    "severity": "ERROR",
                                    "file": rel,
                                    "location": f"L{node.lineno}",
                                    "detail": f"Relative import không tồn tại: '{'.' * node.level}{node.module or ''}'",
                                }
                            )
                        continue
                    if local_mod not in export_cache:
                        export_cache[local_mod] = _collect_py_module_exports(local_mod)
                    exports = export_cache[local_mod]
                    if exports is None:
                        continue
                    mod_rel = local_mod.relative_to(root).as_posix()
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        sub_mod = local_mod.parent / f"{alias.name}.py"
                        sub_pkg = local_mod.parent / alias.name / "__init__.py"
                        if alias.name not in exports and not sub_mod.is_file() and not sub_pkg.is_file():
                            issues.append(
                                {
                                    "code": "C02_IMPORT_SYNC",
                                    "severity": "ERROR",
                                    "file": rel,
                                    "location": f"L{node.lineno}",
                                    "detail": f"Mất đồng bộ import: '{alias.name}' không tồn tại trong {mod_rel}",
                                }
                            )
        elif ext in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}:
            for idx, line in enumerate(text.splitlines(), 1):
                m = JS_REL_IMPORT_RE.search(line)
                if not m:
                    continue
                imp_spec = m.group(1) or m.group(2)
                if not imp_spec:
                    continue
                clean_spec = imp_spec.split("?")[0].split("#")[0]
                cand_base = (fp.parent / clean_spec).resolve()
                candidates = [
                    cand_base,
                    *(cand_base.with_suffix(s) for s in (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".json", ".css")),
                    *(cand_base / f"index{s}" for s in (".js", ".ts", ".tsx", ".jsx")),
                ]
                if not any(c.is_file() for c in candidates):
                    issues.append(
                        {
                            "code": "C02_IMPORT_SYNC",
                            "severity": "ERROR",
                            "file": rel,
                            "location": f"L{idx}",
                            "detail": f"Import tương đối trỏ tới tệp không tồn tại: '{imp_spec}'",
                        }
                    )
    return issues


def check_contracts_registry(root: Path) -> list[dict[str, str]]:
    reg_path = root / ".handoff" / "contracts" / "contracts_registry.json"
    if not reg_path.is_file():
        return []
    try:
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [
            {
                "code": "C03_CONTRACT_DRIFT",
                "severity": "ERROR",
                "file": ".handoff/contracts/contracts_registry.json",
                "location": f"L{exc.lineno}",
                "detail": f"contracts_registry.json lỗi JSON: {exc.msg}",
            }
        ]

    issues: list[dict[str, str]] = []
    file_cache: dict[str, str] = {}

    def _read_rel(rel_p: str) -> str | None:
        if not rel_p:
            return None
        if rel_p in file_cache:
            return file_cache[rel_p]
        fp = root / rel_p
        if not fp.is_file():
            return None
        content = fp.read_text(encoding="utf-8", errors="replace")
        file_cache[rel_p] = content
        return content

    for sym in reg.get("shared_symbols", []):
        mfile = sym.get("module_file", "")
        sname = sym.get("symbol", "")
        req_params = sym.get("required_params", [])
        txt = _read_rel(mfile)
        if txt is None:
            issues.append(
                {
                    "code": "C03_CONTRACT_DRIFT",
                    "severity": "ERROR",
                    "file": mfile or "contracts_registry.json",
                    "location": "shared_symbols",
                    "detail": f"Tệp nguồn hợp đồng '{mfile}' không tồn tại cho ký hiệu '{sname}'",
                }
            )
            continue
        if mfile.endswith(".py"):
            exports = _collect_py_module_exports(root / mfile)
            if exports is not None and sname not in exports:
                issues.append(
                    {
                        "code": "C03_CONTRACT_DRIFT",
                        "severity": "ERROR",
                        "file": mfile,
                        "location": "shared_symbols",
                        "detail": f"Ký hiệu đã khóa '{sname}' bị mất hoặc đổi tên trong {mfile}",
                    }
                )
            elif req_params:
                try:
                    tree = ast.parse(txt)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == sname:
                            actual_args = {a.arg for a in node.args.args + node.args.kwonlyargs}
                            missing_p = [p for p in req_params if p not in actual_args]
                            if missing_p:
                                issues.append(
                                    {
                                        "code": "C03_CONTRACT_DRIFT",
                                        "severity": "ERROR",
                                        "file": mfile,
                                        "location": f"L{node.lineno}",
                                        "detail": f"Hàm '{sname}' mất tham số hợp đồng bắt buộc: {missing_p}",
                                    }
                                )
                            break
                except SyntaxError:
                    pass
        elif sname and sname not in txt:
            issues.append(
                {
                    "code": "C03_CONTRACT_DRIFT",
                    "severity": "ERROR",
                    "file": mfile,
                    "location": "shared_symbols",
                    "detail": f"Ký hiệu hợp đồng '{sname}' không còn xuất hiện trong {mfile}",
                }
            )

    for ep in reg.get("api_endpoints", []):
        route_path = ep.get("path", "")
        prod = ep.get("producer_file", "")
        consumers = ep.get("consumer_files", [])
        if prod:
            ptxt = _read_rel(prod)
            if ptxt is None or (route_path and route_path not in ptxt):
                issues.append(
                    {
                        "code": "C03_CONTRACT_DRIFT",
                        "severity": "ERROR",
                        "file": prod,
                        "location": "api_endpoints",
                        "detail": f"API endpoint đã khóa '{route_path}' không còn trong producer {prod}",
                    }
                )
        for cons in consumers:
            ctxt = _read_rel(cons)
            if ctxt is None or (route_path and route_path not in ctxt):
                issues.append(
                    {
                        "code": "C03_CONTRACT_DRIFT",
                        "severity": "ERROR",
                        "file": cons,
                        "location": "api_endpoints",
                        "detail": f"API endpoint đã khóa '{route_path}' mất đồng bộ tại consumer {cons}",
                    }
                )

    for tbl in reg.get("db_tables", []):
        sfile = tbl.get("schema_file", "")
        tname = tbl.get("table", "")
        cols = tbl.get("required_columns", [])
        stxt = _read_rel(sfile)
        if stxt is None or (tname and tname not in stxt):
            issues.append(
                {
                    "code": "C03_CONTRACT_DRIFT",
                    "severity": "ERROR",
                    "file": sfile or "contracts_registry.json",
                    "location": "db_tables",
                    "detail": f"Bảng CSDL đã khóa '{tname}' không tìm thấy trong {sfile}",
                }
            )
            continue
        for col in cols:
            if not re.search(rf"\b{re.escape(col)}\b", stxt):
                issues.append(
                    {
                        "code": "C03_CONTRACT_DRIFT",
                        "severity": "ERROR",
                        "file": sfile,
                        "location": f"table:{tname}",
                        "detail": f"Cột CSDL đã khóa '{tname}.{col}' bị thiếu trong {sfile}",
                    }
                )

    for dom in reg.get("dom_bindings", []):
        hfile = dom.get("html_file", "")
        eids = dom.get("element_ids", [])
        handlers = dom.get("js_handlers", [])
        js_file = dom.get("js_file", "") or hfile
        htxt = _read_rel(hfile)
        if htxt is None:
            issues.append(
                {
                    "code": "C03_CONTRACT_DRIFT",
                    "severity": "ERROR",
                    "file": hfile or "contracts_registry.json",
                    "location": "dom_bindings",
                    "detail": f"Tệp HTML '{hfile}' trong dom_bindings không tồn tại",
                }
            )
            continue
        found_ids = set(HTML_ID_SET_RE.findall(htxt))
        for eid in eids:
            if eid not in found_ids and f"'{eid}'" not in htxt and f'"{eid}"' not in htxt:
                issues.append(
                    {
                        "code": "C03_CONTRACT_DRIFT",
                        "severity": "ERROR",
                        "file": hfile,
                        "location": "dom_bindings",
                        "detail": f"DOM ID đã khóa '#{eid}' bị mất trong {hfile}",
                    }
                )
        jtxt = _read_rel(js_file) if js_file else htxt
        if jtxt is not None:
            for fn in handlers:
                if not re.search(rf"\b{re.escape(fn)}\b", jtxt):
                    issues.append(
                        {
                            "code": "C03_CONTRACT_DRIFT",
                            "severity": "ERROR",
                            "file": js_file,
                            "location": "dom_bindings",
                            "detail": f"JS handler đã khóa '{fn}' bị mất trong {js_file}",
                        }
                    )
    return issues


def check_hygiene_and_truncation(
    root: Path,
    files: list[Path],
    allow_shrink: bool,
    max_shrink_ratio: float,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    snap_manifest = root / ".handoff" / "archive" / "snapshots" / "current" / "manifest.json"
    old_files: dict[str, dict] = {}
    if snap_manifest.is_file():
        try:
            old_files = json.loads(snap_manifest.read_text(encoding="utf-8")).get("files", {})
        except Exception:
            old_files = {}

    for fp in files:
        rel = fp.relative_to(root).as_posix()
        raw = fp.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        lines = text.splitlines()

        for idx, ln in enumerate(lines, 1):
            if MERGE_CONFLICT_RE.match(ln):
                issues.append(
                    {
                        "code": "C05_MERGE_CONFLICT",
                        "severity": "ERROR",
                        "file": rel,
                        "location": f"L{idx}",
                        "detail": "Còn sót dấu xung đột git merge (<<<<<<< / ======= / >>>>>>>)",
                    }
                )
                break

        for idx, ln in enumerate(lines, 1):
            if AI_LAZY_TRUNCATION_RE.search(ln):
                issues.append(
                    {
                        "code": "C04_AI_TRUNCATION",
                        "severity": "ERROR",
                        "file": rel,
                        "location": f"L{idx}",
                        "detail": f"Phát hiện bình luận cắt bớt code kiểu máy sinh: {ln.strip()[:90]}",
                    }
                )
            sm = SECRET_LEAK_RE.search(ln)
            if sm and "EXAMPLE" not in ln.upper() and "PLACEHOLDER" not in ln.upper() and "SECRET_LEAK_RE" not in ln:
                issues.append(
                    {
                        "code": "C06_SECRET_LEAK",
                        "severity": "ERROR",
                        "file": rel,
                        "location": f"L{idx}",
                        "detail": f"Nghi ngờ lộ khóa bí mật cứng trong mã nguồn ({sm.group(0)[:12]}...)",
                    }
                )

        if not allow_shrink and rel in old_files:
            old_size = int(old_files[rel].get("size", 0))
            old_lines = int(old_files[rel].get("lines", 0))
            if old_lines >= 80 and len(lines) < int(old_lines * (1.0 - max_shrink_ratio)):
                issues.append(
                    {
                        "code": "C04_SHRINK_SABOTAGE",
                        "severity": "ERROR",
                        "file": rel,
                        "location": f"{old_lines}L->{len(lines)}L",
                        "detail": (
                            f"Tệp tụt đột ngột >{int(max_shrink_ratio * 100)}% số dòng "
                            f"({old_lines} -> {len(lines)} dòng); nghi ngờ ghi đè cắt cụt (dùng --allow-shrink nếu chủ đích xóa code)"
                        ),
                    }
                )
            elif old_lines == 0 and old_size >= 4096 and len(raw) < int(old_size * (1.0 - max_shrink_ratio)):
                issues.append(
                    {
                        "code": "C04_SHRINK_SABOTAGE",
                        "severity": "ERROR",
                        "file": rel,
                        "location": f"{old_size}B->{len(raw)}B",
                        "detail": (
                            f"Tệp tụt đột ngột >{int(max_shrink_ratio * 100)}% dung lượng "
                            f"({old_size} -> {len(raw)} bytes); nghi ngờ ghi đè cắt cụt"
                        ),
                    }
                )
    return issues


def run_test_commands(root: Path, extra_cmds: list[str]) -> list[dict[str, str]]:
    cmds = list(extra_cmds)
    reg_path = root / ".handoff" / "contracts" / "contracts_registry.json"
    if not cmds and reg_path.is_file():
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
            cmds = [str(c) for c in reg.get("test_commands", []) if str(c).strip()]
        except Exception:
            cmds = []

    if not cmds:
        return []

    log_dir = root / ".handoff" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "last_test_run.log"
    issues: list[dict[str, str]] = []
    log_chunks: list[str] = []

    for cmd in cmds:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        combined = (proc.stdout + "\n" + proc.stderr).strip()
        log_chunks.append(f"$ {cmd}\n[exit={proc.returncode}]\n{combined}\n")
        if proc.returncode != 0:
            tail = " | ".join(ln.strip() for ln in combined.splitlines()[-4:] if ln.strip())
            issues.append(
                {
                    "code": "C07_TEST_FAIL",
                    "severity": "ERROR",
                    "file": ".handoff/logs/last_test_run.log",
                    "location": f"exit={proc.returncode}",
                    "detail": f"Lệnh test '{cmd}' thất bại: {tail[:200]}",
                }
            )
    log_path.write_text("\n".join(log_chunks), encoding="utf-8")
    return issues


def cmd_self_test() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".handoff" / "contracts").mkdir(parents=True)
        (root / "db.py").write_text("def fetch_items(limit=10):\n    return []\n", encoding="utf-8")
        (root / "api.py").write_text(
            "from db import fetch_items\n\ndef handle():\n    return fetch_items(5)\n",
            encoding="utf-8",
        )
        (root / "index.html").write_text(
            "<!doctype html><html><body><div id='app-root'></div>"
            "<script>function renderApp() { return fetch('/api/items'); }</script></body></html>\n",
            encoding="utf-8",
        )
        (root / ".handoff" / "contracts" / "contracts_registry.json").write_text(
            json.dumps(
                {
                    "shared_symbols": [{"module_file": "db.py", "symbol": "fetch_items", "required_params": ["limit"]}],
                    "dom_bindings": [{"html_file": "index.html", "element_ids": ["app-root"], "js_handlers": ["renderApp"]}],
                }
            ),
            encoding="utf-8",
        )

        files = iter_code_files(root)
        clean_issues = (
            [i for f in files for i in check_file_syntax(f, f.relative_to(root).as_posix(), f.read_text("utf-8"))]
            + check_cross_file_imports(root, files)
            + check_contracts_registry(root)
            + check_hygiene_and_truncation(root, files, False, 0.2)
        )
        assert not clean_issues, f"Dự án sạch không được báo lỗi: {clean_issues}"

        # Gài lỗi mất đồng bộ import + cắt cụt AI + lỗi JS trong HTML + mất DOM ID
        (root / "api.py").write_text(
            "from db import nonexistent_fn\n# ... existing code ...\n",
            encoding="utf-8",
        )
        (root / "index.html").write_text(
            "<!doctype html><html><body><div id='wrong-id'></div><script>function broken( {</script></body></html>\n",
            encoding="utf-8",
        )
        files2 = iter_code_files(root)
        bad_issues = (
            [i for f in files2 for i in check_file_syntax(f, f.relative_to(root).as_posix(), f.read_text("utf-8"))]
            + check_cross_file_imports(root, files2)
            + check_contracts_registry(root)
            + check_hygiene_and_truncation(root, files2, False, 0.2)
        )
        codes = {i["code"] for i in bad_issues}
        assert "C02_IMPORT_SYNC" in codes, "Phải bắt được lỗi gãy import liên tệp"
        assert "C03_CONTRACT_DRIFT" in codes, "Phải bắt được lỗi mất DOM ID / JS handler đã khóa"
        assert "C04_AI_TRUNCATION" in codes, "Phải bắt được bình luận cắt cụt code kiểu AI"
        if _node_bin():
            assert "C01_SYNTAX" in codes, "Phải bắt được lỗi cú pháp JS nội tuyến trong HTML"

    print("SELF_TEST_OK | verify_code_sync.py | sai 0")
    return 0


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(
        description="Kiểm tra tất định đồng bộ code, hợp đồng liên tệp, cú pháp và vệ sinh bản giao"
    )
    parser.add_argument("action", nargs="?", default="check", choices=("check", "self-test", "tu-kiem"))
    parser.add_argument("--root", default=".", help="Thư mục gốc dự án")
    parser.add_argument("--files", nargs="*", default=[], help="Chỉ kiểm danh sách tệp cụ thể (tương đối từ root)")
    parser.add_argument("--run-tests", action="store_true", help="Chạy kèm các lệnh test trong contracts_registry.json")
    parser.add_argument("--test-cmd", action="append", default=[], help="Lệnh test bổ sung cần chạy")
    parser.add_argument("--allow-shrink", action="store_true", help="Cho phép tệp giảm >20% dòng khi chủ đích refactor xóa code")
    parser.add_argument("--max-shrink-ratio", type=float, default=0.20, help="Ngưỡng cảnh báo tụt dòng đột ngột (mặc định 0.20)")
    parser.add_argument("--json-out", default="", help="Ghi báo cáo chi tiết JSON ra tệp")
    args = parser.parse_args()

    if args.action in ("self-test", "tu-kiem"):
        return cmd_self_test()

    root = Path(args.root).resolve()
    files = iter_code_files(root, args.files if args.files else None)
    all_issues: list[dict[str, str]] = []

    for fp in files:
        rel = fp.relative_to(root).as_posix()
        txt = fp.read_text(encoding="utf-8", errors="replace")
        all_issues.extend(check_file_syntax(fp, rel, txt))

    all_issues.extend(check_cross_file_imports(root, files))
    all_issues.extend(check_contracts_registry(root))
    all_issues.extend(check_hygiene_and_truncation(root, files, args.allow_shrink, args.max_shrink_ratio))

    if args.run_tests or args.test_cmd:
        all_issues.extend(run_test_commands(root, args.test_cmd))

    report = {
        "root": root.as_posix(),
        "checked_files": len(files),
        "error_count": len(all_issues),
        "issues": all_issues,
    }
    if args.json_out:
        out_p = Path(args.json_out).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if all_issues:
        print(f"SYNC_FAIL | checked={len(files)} files | errors={len(all_issues)}")
        for item in all_issues[:30]:
            print(f"  - [{item['code']}] {item['file']}:{item['location']} -> {item['detail']}")
        if len(all_issues) > 30:
            print(f"  ... còn {len(all_issues) - 30} lỗi nữa (dùng --json-out để xem toàn bộ trên đĩa)")
        return 1

    print(f"SYNC_OK | checked={len(files)} files | errors=0 | contracts=clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
