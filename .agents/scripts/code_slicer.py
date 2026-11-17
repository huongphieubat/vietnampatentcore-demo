#!/usr/bin/env python3
"""Lập chỉ mục ký hiệu đa ngôn ngữ (symbol_map.json) và chiếu lát ngữ cảnh <= 200 dòng cho Build App & Code."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

MAX_SLICE_LINES = 200
MONOLITH_LINE_THRESHOLD = 400
MONOLITH_BYTE_THRESHOLD = 40_000
CODE_CHARS_PER_TOKEN = 3.2

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
    ".mypy_cache",
}

INDEXABLE_EXTS = {
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
}

JS_FUNC_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(([^)]*)\)"
)
JS_CLASS_RE = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_$][A-Za-z0-9_$]*)")
JS_CONST_FN_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][A-Za-z0-9_$]*)\s*=>"
)
JS_IMPORT_RE = re.compile(
    r"""^\s*import\s+(?:.+?\s+from\s+)?['"]([^'"]+)['"]|require\(\s*['"]([^'"]+)['"]\s*\)"""
)
FETCH_API_RE = re.compile(r"""(?:fetch|axios\.(?:get|post|put|delete|patch))\(\s*[`'"]([^`'"]+)[`'"]""")
PY_ROUTE_RE = re.compile(
    r"""@(?:app|router|bp|api)\.(get|post|put|delete|patch|route)\(\s*[r`'"]+([^`'"]+)[`'"]"""
)
PY_PATH_ROUTE_RE = re.compile(r"""(?:path|parsed\.path)\s*(?:==|\.startswith\()\s*[`'"](/[^`'"]*)[`'"]""")
HTML_ID_RE = re.compile(r"""\bid\s*=\s*["']([A-Za-z0-9_.:-]+)["']""")
HTML_SCRIPT_OPEN_RE = re.compile(r"<script\b([^>]*)>", re.IGNORECASE)
HTML_SCRIPT_CLOSE_RE = re.compile(r"</script\s*>", re.IGNORECASE)
SQL_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?([A-Za-z0-9_]+)[`\"']?",
    re.IGNORECASE,
)
CSS_VAR_RE = re.compile(r"(--[A-Za-z0-9_-]+)\s*:")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(raw.encode("utf-8"))
    tmp.replace(path)


def estimate_code_tokens(text: str) -> int:
    if not text:
        return 0
    return int(math.ceil(len(text) / CODE_CHARS_PER_TOKEN))


def iter_source_files(root: Path) -> list[Path]:
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
                    if p.suffix.lower() in INDEXABLE_EXTS:
                        found.append(p)
            except OSError:
                continue
        stack.extend(reversed(subdirs))
    return found


def _format_py_args(args_node: ast.arguments) -> str:
    names = [a.arg for a in args_node.posonlyargs] + [a.arg for a in args_node.args]
    if args_node.vararg:
        names.append(f"*{args_node.vararg.arg}")
    names.extend(f"{a.arg}=*" for a in args_node.kwonlyargs)
    if args_node.kwarg:
        names.append(f"**{args_node.kwarg.arg}")
    return ", ".join(names)


def index_python_file(text: str) -> dict[str, object]:
    symbols: list[dict[str, object]] = []
    imports: list[dict[str, object]] = []
    routes: list[dict[str, object]] = []

    for idx, line in enumerate(text.splitlines(), 1):
        for rm in PY_ROUTE_RE.finditer(line):
            routes.append({"method": rm.group(1).upper(), "path": rm.group(2), "line": idx})
        for pm in PY_PATH_ROUTE_RE.finditer(line):
            routes.append({"method": "HANDLER", "path": pm.group(1), "line": idx})

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {
            "symbols": symbols,
            "imports": imports,
            "routes": routes,
            "syntax_error": f"L{exc.lineno}: {exc.msg}",
        }

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "names": [], "line": node.lineno})
        elif isinstance(node, ast.ImportFrom):
            mod = ("." * node.level) + (node.module or "")
            imports.append(
                {
                    "module": mod,
                    "names": [a.name for a in node.names],
                    "line": node.lineno,
                }
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            sig = f"{prefix} {node.name}({_format_py_args(node.args)})"
            symbols.append(
                {
                    "name": node.name,
                    "kind": "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                    "signature": sig,
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                }
            )
        elif isinstance(node, ast.ClassDef):
            methods: list[str] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
                    m_prefix = "async def" if isinstance(item, ast.AsyncFunctionDef) else "def"
                    symbols.append(
                        {
                            "name": f"{node.name}.{item.name}",
                            "kind": "method",
                            "signature": f"{m_prefix} {node.name}.{item.name}({_format_py_args(item.args)})",
                            "start_line": item.lineno,
                            "end_line": getattr(item, "end_lineno", item.lineno),
                        }
                    )
            symbols.append(
                {
                    "name": node.name,
                    "kind": "class",
                    "signature": f"class {node.name} [{', '.join(methods[:8])}]",
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                }
            )
    symbols.sort(key=lambda s: int(s["start_line"]))
    return {"symbols": symbols, "imports": imports, "routes": routes}


def _estimate_brace_end(lines: list[str], start_idx: int, max_scan: int = 400) -> int:
    depth = 0
    opened = False
    limit = min(len(lines), start_idx + max_scan)
    for idx in range(start_idx, limit):
        ln = lines[idx]
        for ch in ln:
            if ch == "{":
                depth += 1
                opened = True
            elif ch == "}":
                depth -= 1
                if opened and depth <= 0:
                    return idx + 1
    return min(len(lines), start_idx + 25)


def index_js_lines(lines: list[str], line_offset: int = 0) -> tuple[list[dict[str, object]], list[str], list[dict[str, object]]]:
    symbols: list[dict[str, object]] = []
    imports: list[str] = []
    api_calls: list[dict[str, object]] = []
    for i, line in enumerate(lines):
        lineno = line_offset + i + 1
        im = JS_IMPORT_RE.search(line)
        if im:
            mod = im.group(1) or im.group(2)
            if mod:
                imports.append(mod)
        for fm in FETCH_API_RE.finditer(line):
            api_calls.append({"path": fm.group(1), "line": lineno})

        m_fn = JS_FUNC_RE.match(line)
        if m_fn:
            end_ln = line_offset + _estimate_brace_end(lines, i)
            symbols.append(
                {
                    "name": m_fn.group(1),
                    "kind": "function",
                    "signature": f"function {m_fn.group(1)}({m_fn.group(2).strip()})",
                    "start_line": lineno,
                    "end_line": end_ln,
                }
            )
            continue
        m_cls = JS_CLASS_RE.match(line)
        if m_cls:
            end_ln = line_offset + _estimate_brace_end(lines, i)
            symbols.append(
                {
                    "name": m_cls.group(1),
                    "kind": "class",
                    "signature": f"class {m_cls.group(1)}",
                    "start_line": lineno,
                    "end_line": end_ln,
                }
            )
            continue
        m_cfn = JS_CONST_FN_RE.match(line)
        if m_cfn:
            end_ln = line_offset + _estimate_brace_end(lines, i)
            symbols.append(
                {
                    "name": m_cfn.group(1),
                    "kind": "arrow_fn",
                    "signature": f"const {m_cfn.group(1)} = (...) =>",
                    "start_line": lineno,
                    "end_line": end_ln,
                }
            )
    return symbols, imports, api_calls


def index_html_file(text: str) -> dict[str, object]:
    lines = text.splitlines()
    dom_ids: list[dict[str, object]] = []
    script_blocks: list[dict[str, object]] = []
    symbols: list[dict[str, object]] = []
    api_calls: list[dict[str, object]] = []

    in_script = False
    script_start = 0
    script_is_js = True
    buf: list[str] = []

    for idx, line in enumerate(lines, 1):
        if not in_script:
            for id_m in HTML_ID_RE.finditer(line):
                dom_ids.append({"id": id_m.group(1), "line": idx})
            open_m = HTML_SCRIPT_OPEN_RE.search(line)
            if open_m:
                attrs = open_m.group(1).lower()
                if "src=" not in attrs:
                    script_is_js = ("application/json" not in attrs and "application/ld+json" not in attrs)
                    if HTML_SCRIPT_CLOSE_RE.search(line):
                        script_blocks.append({"start_line": idx, "end_line": idx, "is_js": script_is_js})
                    else:
                        in_script = True
                        script_start = idx
                        buf = []
        else:
            if HTML_SCRIPT_CLOSE_RE.search(line):
                script_blocks.append({"start_line": script_start, "end_line": idx, "is_js": script_is_js})
                if script_is_js and buf:
                    s_syms, _, s_apis = index_js_lines(buf, line_offset=script_start)
                    symbols.extend(s_syms)
                    api_calls.extend(s_apis)
                in_script = False
                buf = []
            else:
                buf.append(line)
                for id_m in HTML_ID_RE.finditer(line):
                    dom_ids.append({"id": id_m.group(1), "line": idx})

    return {
        "symbols": symbols,
        "dom_ids": dom_ids[:300],
        "dom_id_count": len(dom_ids),
        "script_blocks": script_blocks,
        "api_calls": api_calls,
    }


def index_sql_file(text: str) -> dict[str, object]:
    tables: list[dict[str, object]] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        m = SQL_CREATE_TABLE_RE.search(line)
        if m:
            tname = m.group(1)
            end_ln = idx + 1
            cols: list[str] = []
            for j in range(idx + 1, min(len(lines), idx + 120)):
                s = lines[j].strip()
                if s.startswith(")") or s.endswith(");"):
                    end_ln = j + 1
                    break
                if s and not s.startswith(("--", "PRIMARY", "FOREIGN", "UNIQUE", "CONSTRAINT", "CHECK", "INDEX")):
                    col_tok = s.split()[0].strip("`\"',")
                    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", col_tok):
                        cols.append(col_tok)
            tables.append(
                {
                    "name": tname,
                    "columns": cols,
                    "start_line": idx + 1,
                    "end_line": end_ln,
                }
            )
    symbols = [
        {
            "name": t["name"],
            "kind": "sql_table",
            "signature": f"TABLE {t['name']} ({', '.join(t['columns'][:10])})",
            "start_line": t["start_line"],
            "end_line": t["end_line"],
        }
        for t in tables
    ]
    return {"symbols": symbols, "sql_tables": tables}


def index_css_file(text: str) -> dict[str, object]:
    css_vars = sorted(set(CSS_VAR_RE.findall(text)))
    return {"symbols": [], "css_variables": css_vars[:120]}


def build_symbol_map(root: Path) -> dict[str, object]:
    files_meta: dict[str, object] = {}
    monoliths: list[str] = []
    total_lines = 0
    total_tokens = 0
    total_symbols = 0

    for fp in iter_source_files(root):
        rel = fp.relative_to(root).as_posix()
        raw = fp.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        line_count = len(text.splitlines())
        tok_est = estimate_code_tokens(text)
        is_monolith = line_count > MONOLITH_LINE_THRESHOLD or len(raw) > MONOLITH_BYTE_THRESHOLD
        if is_monolith:
            monoliths.append(rel)

        ext = fp.suffix.lower()
        if ext == ".py":
            parsed = index_python_file(text)
        elif ext in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}:
            syms, imps, apis = index_js_lines(text.splitlines(), 0)
            parsed = {"symbols": syms, "imports": imps, "api_calls": apis}
        elif ext == ".html":
            parsed = index_html_file(text)
        elif ext == ".sql":
            parsed = index_sql_file(text)
        elif ext == ".css":
            parsed = index_css_file(text)
        else:
            parsed = {"symbols": []}

        sym_list = parsed.get("symbols", [])
        total_symbols += len(sym_list) if isinstance(sym_list, list) else 0
        total_lines += line_count
        total_tokens += tok_est

        files_meta[rel] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "lines": line_count,
            "est_tokens": tok_est,
            "monolith_slice_only": is_monolith,
            **parsed,
        }

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "root": root.as_posix(),
        "summary": {
            "indexed_files": len(files_meta),
            "total_lines": total_lines,
            "total_est_tokens": total_tokens,
            "total_symbols": total_symbols,
            "monolith_files_count": len(monoliths),
            "monolith_slice_only_files": monoliths,
        },
        "files": files_meta,
    }


def load_or_build_map(root: Path, out_path: Path | None = None) -> dict[str, object]:
    target = out_path or (root / ".handoff" / "contracts" / "symbol_map.json")
    if target.is_file():
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            pass
    data = build_symbol_map(root)
    if (root / ".handoff").is_dir() or out_path is not None:
        atomic_write_json(target, data)
    return data


def cmd_index(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    out_path = Path(args.out).resolve() if args.out else (root / ".handoff" / "contracts" / "symbol_map.json")
    data = build_symbol_map(root)
    atomic_write_json(out_path, data)
    s = data["summary"]
    print(
        f"INDEX_OK | files={s['indexed_files']} | symbols={s['total_symbols']} | "
        f"lines={s['total_lines']} | repo_tokens~={s['total_est_tokens']} | "
        f"monoliths={s['monolith_files_count']} | out={out_path.as_posix()}"
    )
    if s["monolith_slice_only_files"]:
        print("MONOLITH_SLICE_ONLY (CẤM đọc toàn văn, bắt buộc dùng code_slicer.py slice):")
        for mf in s["monolith_slice_only_files"][:15]:
            finfo = data["files"][mf]
            print(f"  - {mf}: {finfo['lines']}L (~{finfo['est_tokens']} tok, {len(finfo.get('symbols', []))} symbols)")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    smap = load_or_build_map(root)
    q = args.query.lower().strip()
    hits: list[str] = []

    for rel, finfo in smap.get("files", {}).items():
        if q in rel.lower():
            hits.append(f"[FILE] {rel} ({finfo['lines']}L, ~{finfo['est_tokens']} tok, monolith={finfo['monolith_slice_only']})")
        for sym in finfo.get("symbols", []):
            if q in sym["name"].lower() or q in sym.get("signature", "").lower():
                hits.append(f"[{sym['kind'].upper()}] {rel}:L{sym['start_line']}-L{sym['end_line']} :: {sym['signature']}")
        for rt in finfo.get("routes", []):
            if q in rt["path"].lower():
                hits.append(f"[ROUTE] {rel}:L{rt['line']} :: {rt['method']} {rt['path']}")
        for dom in finfo.get("dom_ids", []):
            if q in dom["id"].lower():
                hits.append(f"[DOM_ID] {rel}:L{dom['line']} :: #{dom['id']}")
        for api in finfo.get("api_calls", []):
            if q in api["path"].lower():
                hits.append(f"[API_CALL] {rel}:L{api['line']} :: {api['path']}")

    if not hits:
        print(f"SEARCH_EMPTY | query='{args.query}' | 0 kết quả trong symbol_map.json")
        return 0

    limit = max(1, min(args.limit, 50))
    print(f"SEARCH_OK | query='{args.query}' | showing {min(len(hits), limit)}/{len(hits)} hits:")
    for h in hits[:limit]:
        print(f"  {h}")
    return 0


def _collect_related_contracts(root: Path, rel_file: str) -> list[str]:
    reg_path = root / ".handoff" / "contracts" / "contracts_registry.json"
    if not reg_path.is_file():
        return []
    try:
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    notes: list[str] = []
    for ep in reg.get("api_endpoints", []):
        files = [ep.get("producer_file", ""), *ep.get("consumer_files", [])]
        if rel_file in files:
            notes.append(f"API {ep.get('method', 'ANY')} {ep.get('path')} <-> {files}")
    for sym in reg.get("shared_symbols", []):
        files = [sym.get("module_file", ""), *sym.get("consumer_files", [])]
        if rel_file in files:
            notes.append(f"SYMBOL {sym.get('symbol')} in {sym.get('module_file')} -> consumers={sym.get('consumer_files', [])}")
    for dom in reg.get("dom_bindings", []):
        if rel_file in (dom.get("html_file"), dom.get("js_file")):
            notes.append(f"DOM #{', #'.join(dom.get('element_ids', [])[:8])} in {dom.get('html_file')}")
    return notes[:10]


def cmd_slice(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    target = (root / args.file).resolve()
    if not target.is_file():
        sys.stderr.write(f"ERR | Không tìm thấy tệp: {args.file}\n")
        return 1
    rel = target.relative_to(root).as_posix()
    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    total = len(lines)
    max_cap = max(20, min(args.max_lines, MAX_SLICE_LINES))

    start_ln = 1
    end_ln = min(total, max_cap)
    header_label = ""

    if args.symbol:
        smap = load_or_build_map(root)
        finfo = smap.get("files", {}).get(rel)
        if not finfo:
            smap = build_symbol_map(root)
            finfo = smap.get("files", {}).get(rel, {})
        q = args.symbol.strip()
        exact = [s for s in finfo.get("symbols", []) if s["name"] == q]
        partial = [s for s in finfo.get("symbols", []) if q.lower() in s["name"].lower()]
        chosen = exact[0] if exact else (partial[0] if partial else None)
        if not chosen:
            sys.stderr.write(f"ERR | Không tìm thấy ký hiệu '{q}' trong {rel}; thử lệnh search trước\n")
            return 1
        start_ln = max(1, int(chosen["start_line"]) - args.context)
        raw_end = min(total, int(chosen["end_line"]) + args.context)
        end_ln = min(raw_end, start_ln + max_cap - 1)
        header_label = f"symbol={chosen['name']} (gốc L{chosen['start_line']}-L{chosen['end_line']})"
    elif args.lines:
        m = re.match(r"^(\d+)\s*[:-]\s*(\d+)$", args.lines.strip())
        if not m:
            sys.stderr.write("ERR | Cú pháp --lines phải là START:END (ví dụ 120:260)\n")
            return 1
        start_ln = max(1, int(m.group(1)))
        req_end = min(total, int(m.group(2)))
        if req_end < start_ln:
            req_end = start_ln
        end_ln = min(req_end, start_ln + max_cap - 1)
        header_label = f"lines=L{start_ln}-L{end_ln} (yêu cầu L{start_ln}-L{req_end})"

    slice_lines = lines[start_ln - 1 : end_ln]
    slice_text = "\n".join(slice_lines)
    tok_est = estimate_code_tokens(slice_text)

    print(
        f"=== CODE SLICE | {rel} | L{start_ln}-L{end_ln}/{total}L | "
        f"count={len(slice_lines)}/{MAX_SLICE_LINES}L | ~{tok_est} tok | {header_label} ==="
    )
    contracts = _collect_related_contracts(root, rel)
    if contracts:
        print("[LOCKED CONTRACTS LIÊN QUAN]")
        for c in contracts:
            print(f"  * {c}")

    if start_ln > 25 and target.suffix.lower() == ".py":
        imp_lines = [
            f"  L{i}: {ln}"
            for i, ln in enumerate(lines[:35], 1)
            if ln.lstrip().startswith(("import ", "from "))
        ]
        if imp_lines:
            print("[IMPORTS ĐẦU TỆP]")
            for il in imp_lines[:10]:
                print(il)

    print("[NỘI DUNG LÁT CẮT]")
    for idx, content in enumerate(slice_lines, start=start_ln):
        print(f"{idx:5d}: {content}")

    if args.symbol and chosen and end_ln < int(chosen["end_line"]):
        print(
            f"[NEED_NEXT_SLICE] Ký hiệu dài vượt trần {max_cap} dòng; "
            f"đọc lát kế tiếp bằng: --file {rel} --lines {end_ln + 1}:{min(total, end_ln + max_cap)}"
        )
    return 0


def cmd_self_test() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "app.py").write_text(
            "import os\nfrom db import get_user\n\n@app.get('/api/users')\ndef list_users(limit: int = 10):\n    return get_user(limit)\n",
            encoding="utf-8",
        )
        big_html = ["<!doctype html><html><body><div id='search-box'></div><script>"]
        big_html.append("async function fetchPatents(q) { const r = await fetch('/api/users'); return r.json(); }")
        for i in range(420):
            big_html.append(f"const row_{i} = {i};")
        big_html.append("</script></body></html>")
        (root / "index.html").write_text("\n".join(big_html), encoding="utf-8")
        (root / "schema.sql").write_text(
            "CREATE TABLE patents (\n  id INTEGER PRIMARY KEY,\n  title TEXT NOT NULL\n);\n",
            encoding="utf-8",
        )

        smap = build_symbol_map(root)
        assert smap["summary"]["indexed_files"] == 3, "Phải index đủ 3 tệp"
        assert "index.html" in smap["summary"]["monolith_slice_only_files"], "Phải nhận diện monolith HTML"
        py_syms = [s["name"] for s in smap["files"]["app.py"]["symbols"]]
        assert "list_users" in py_syms, "Phải trích được hàm Python"
        html_syms = [s["name"] for s in smap["files"]["index.html"]["symbols"]]
        assert "fetchPatents" in html_syms, "Phải trích được hàm JS trong HTML"
        sql_syms = [s["name"] for s in smap["files"]["schema.sql"]["symbols"]]
        assert "patents" in sql_syms, "Phải trích được bảng SQL"

    print("SELF_TEST_OK | code_slicer.py | sai 0")
    return 0


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(
        description="Công cụ lập chỉ mục ký hiệu & cắt lát mã nguồn <= 200 dòng chống compact"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_idx = sub.add_parser("index", help="Quét codebase lập .handoff/contracts/symbol_map.json")
    p_idx.add_argument("--root", default=".", help="Thư mục gốc dự án")
    p_idx.add_argument("--out", default="", help="Đường dẫn xuất symbol_map.json tùy chọn")

    p_srch = sub.add_parser("search", help="Tìm ký hiệu, API route, bảng SQL hoặc DOM ID")
    p_srch.add_argument("--root", default=".", help="Thư mục gốc dự án")
    p_srch.add_argument("--query", required=True, help="Từ khóa ký hiệu / đường dẫn / ID")
    p_srch.add_argument("--limit", type=int, default=25, help="Số kết quả tối đa")

    p_slc = sub.add_parser("slice", help="Chiếu lát mã nguồn <= 200 dòng kèm hợp đồng liên quan")
    p_slc.add_argument("--root", default=".", help="Thư mục gốc dự án")
    p_slc.add_argument("--file", required=True, help="Đường dẫn tệp tương đối từ root")
    p_slc.add_argument("--symbol", default="", help="Tên hàm/class cần cắt lát")
    p_slc.add_argument("--lines", default="", help="Dải dòng START:END")
    p_slc.add_argument("--context", type=int, default=5, help="Số dòng đệm trên/dưới ký hiệu")
    p_slc.add_argument("--max-lines", type=int, default=MAX_SLICE_LINES, help="Trần dòng mỗi lát (<= 200)")

    sub.add_parser("self-test", help="Tự kiểm thử toàn vẹn công cụ")
    sub.add_parser("tu-kiem", help="Bí danh tiếng Việt của self-test")

    args = parser.parse_args()
    if args.cmd in ("self-test", "tu-kiem"):
        return cmd_self_test()
    if args.cmd == "index":
        return cmd_index(args)
    if args.cmd == "search":
        return cmd_search(args)
    return cmd_slice(args)


if __name__ == "__main__":
    raise SystemExit(main())
