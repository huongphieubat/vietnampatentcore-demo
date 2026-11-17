#!/usr/bin/env python3
"""Xuất gói bàn giao liên phiên (.handoff/SESSION_HANDOFF_BUNDLE.md <= 180 dòng) khi chạm trần 200k token hoặc chuyển phiên."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _git_summary(root: Path) -> tuple[str, list[str], list[str]]:
    branch = "non-git"
    status_lines: list[str] = []
    recent_commits: list[str] = []
    if not (root / ".git").exists():
        return branch, status_lines, recent_commits
    try:
        b = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(root), capture_output=True, text=True, timeout=5)
        if b.returncode == 0:
            branch = b.stdout.strip()
        s = subprocess.run(["git", "status", "-s"], cwd=str(root), capture_output=True, text=True, timeout=5)
        if s.returncode == 0:
            status_lines = [ln.rstrip() for ln in s.stdout.splitlines()[:20] if ln.strip()]
        lg = subprocess.run(["git", "log", "-n", "5", "--oneline"], cwd=str(root), capture_output=True, text=True, timeout=5)
        if lg.returncode == 0:
            recent_commits = [ln.strip() for ln in lg.stdout.splitlines() if ln.strip()]
    except Exception:
        pass
    return branch, status_lines, recent_commits


def export_bundle(root: Path, reason: str, create_c6_backup: bool = False) -> int:
    handoff = root / ".handoff"
    led_path = handoff / "01_STATE_LEDGER.md"
    inv_path = handoff / "00_INVARIANTS.md"
    creg_path = handoff / "contracts" / "contracts_registry.json"
    smap_path = handoff / "contracts" / "symbol_map.json"
    meter_path = handoff / "context_meter.json"

    if not led_path.is_file():
        sys.stderr.write("ERR | Thiếu .handoff/01_STATE_LEDGER.md\n")
        return 1

    led_lines = led_path.read_text(encoding="utf-8").splitlines()
    branch, git_status, commits = _git_summary(root)

    tok_info = "0"
    if meter_path.is_file():
        try:
            m = json.loads(meter_path.read_text(encoding="utf-8"))
            tok_info = f"{m.get('effective_session_tokens', 0)} ({m.get('ceiling_tier', 'UNKNOWN')})"
        except Exception:
            pass

    contracts_summary: list[str] = []
    if creg_path.is_file():
        try:
            creg = json.loads(creg_path.read_text(encoding="utf-8"))
            contracts_summary.append(f"- Shared Symbols đã khóa: {len(creg.get('shared_symbols', []))}")
            contracts_summary.append(f"- API Endpoints đã khóa: {len(creg.get('api_endpoints', []))}")
            contracts_summary.append(f"- DB Tables đã khóa: {len(creg.get('db_tables', []))}")
            contracts_summary.append(f"- DOM Bindings đã khóa: {len(creg.get('dom_bindings', []))}")
            contracts_summary.append(f"- Test Commands: {', '.join(creg.get('test_commands', [])) or 'Chưa khai báo'}")
        except Exception:
            pass

    monoliths: list[str] = []
    if smap_path.is_file():
        try:
            smap = json.loads(smap_path.read_text(encoding="utf-8"))
            monoliths = smap.get("summary", {}).get("monolith_slice_only_files", [])[:12]
        except Exception:
            pass

    if create_c6_backup:
        c6_dir = handoff / "archive" / "c6_backups"
        c6_dir.mkdir(parents=True, exist_ok=True)
        c6_hashes: dict[str, str] = {}
        if smap_path.is_file():
            try:
                smap = json.loads(smap_path.read_text(encoding="utf-8"))
                for rel_f in smap.get("files", {}):
                    fp = root / rel_f
                    if fp.is_file():
                        c6_hashes[rel_f] = hashlib.sha256(fp.read_bytes()).hexdigest()
            except Exception:
                pass
        (c6_dir / "truoc_c6_manifest.json").write_text(
            json.dumps(
                {
                    "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "branch": branch,
                    "file_sha256": c6_hashes,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    out_lines = [
        "# GÓI BÀN GIAO LIÊN PHIÊN CHỐNG MẤT ĐỒNG BỘ CODE (SESSION_HANDOFF_BUNDLE)",
        "",
        f"- Thời điểm đóng gói: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- Lý do bàn giao: {reason}",
        f"- Thư mục dự án: `{root.as_posix()}`",
        f"- Nhánh Git: `{branch}` | Token phiên vừa đóng: `{tok_info}`",
        "",
        "## 1. Lệnh Khởi Động Lại Trên Phiên Sạch Mới (Nạp < 1.500 token)",
        "```bash",
        f"python3 -X utf8 /shared/user/.gemini/code_handoff_tools/check_code_handoff.py --root {root.as_posix()} --reset-session-meter --token-report",
        f"python3 -X utf8 /shared/user/.gemini/code_handoff_tools/verify_code_sync.py check --root {root.as_posix()}",
        "```",
        "Sau đó chỉ đọc: `.handoff/00_INVARIANTS.md`, `.handoff/01_STATE_LEDGER.md` và `.handoff/contracts/contracts_registry.json`.",
        "",
        "## 2. Trạng Thái Sổ Cái Hiện Thời (Trích 01_STATE_LEDGER.md)",
        *[ln for ln in led_lines[:45]],
        "",
        "## 3. Tóm Tắt Hợp Đồng Đồng Bộ & Cảnh Báo Tệp Monolith",
        *(contracts_summary or ["- Chưa có hợp đồng."]),
        f"- Tệp MONOLITH_SLICE_ONLY (CẤM view_file toàn bộ, bắt buộc qua code_slicer.py): {', '.join(monoliths) or 'Không có'}",
        "",
        "## 4. Trạng Thái Git & Commit Gần Nhất",
        "- Git status (`git status -s`):",
        *([f"  `{s}`" for s in git_status] or ["  (Working tree clean)"]),
        "- Commit gần nhất:",
        *([f"  - `{c}`" for c in commits] or ["  - (Chưa có commit)"]),
    ]

    bundle_path = handoff / "SESSION_HANDOFF_BUNDLE.md"
    bundle_path.write_text("\n".join(out_lines[:175]) + "\n", encoding="utf-8")
    inv_sha = hashlib.sha256(inv_path.read_bytes()).hexdigest()[:12] if inv_path.is_file() else "none"
    print(
        f"HANDOFF_BUNDLE_OK | path={bundle_path.as_posix()} | lines={min(len(out_lines), 175)} | "
        f"inv_sha={inv_sha} | c6_backup={create_c6_backup}"
    )
    return 0


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Đóng gói bàn giao liên phiên chống mất đồng bộ code")
    parser.add_argument("--root", default=".", help="Thư mục gốc dự án")
    parser.add_argument(
        "--reason",
        default="Chạm ngưỡng khóa cứng 200k token — đóng gói sổ cái để mở phiên sạch mới",
        help="Lý do xuất gói bàn giao",
    )
    parser.add_argument(
        "--c6-backup",
        action="store_true",
        help="Tạo kèm bản chụp truoc_c6_manifest.json trước Cổng 6 (M99)",
    )
    args = parser.parse_args()
    return export_bundle(Path(args.root).resolve(), args.reason, args.c6_backup)


if __name__ == "__main__":
    raise SystemExit(main())
