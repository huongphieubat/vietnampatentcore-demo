#!/usr/bin/env python3
"""Cưỡng chế phạm vi 1..5 tệp đích, chụp ảnh chống cắt cụt code, hoàn nguyên nguyên tử & khóa trần 200k-240k token qua Hook."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

HARD_FREEZE_NEW_WORK_TOKENS = 200_000
ABSOLUTE_CEILING_TOKENS = 240_000

READ_ONLY_PROJECT_PHASES = {
    "PLAN_EXPLORE",
    "PLAN_AUDIT",
    "PLAN_APPROVAL",
    "EXPLORE",
    "AUDIT",
    "READY_TO_CLOSE",
    "FINAL_AUDIT_A",
    "FINAL_AUDIT_B",
    "HANDOFF_FLUSH",
    "READY_TO_DELIVER",
    "BLOCKED",
}
SCOPED_WRITE_PHASES = {"WORK", "FIXING", "FINAL_MERGE", "FINAL_GATE6"}

SKIP_TOP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
}
BACKUP_EXTS = {
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
    ".yml",
    ".yaml",
    ".toml",
    ".sh",
    ".md",
    ".tsv",
    ".txt",
}
MAX_BACKUP_FILE_BYTES = 2 * 1024 * 1024
PROTECTED_DIRS = (
    "/shared/user/.gemini/handoff_tools",
    "/shared/user/.gemini/shtt_automation/kho",
)


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def extract_token(text: str, label: str) -> str:
    m = re.search(rf"(?m)^-\s*{re.escape(label)}\s*:\s*([A-Za-z0-9_]+)", text)
    return m.group(1) if m else ""


def extract_locked_targets(text: str) -> list[str]:
    targets: list[str] = []
    in_block = False
    for line in text.splitlines():
        if re.match(r"^-\s*Tệp đích được phép chạm", line):
            in_block = True
            continue
        if in_block:
            if re.match(r"^\s{2,}-\s+", line):
                val = re.sub(r"^\s{2,}-\s+", "", line).strip().strip("`")
                if val and not (val.startswith("[") and val.endswith("]")):
                    targets.append(Path(val).as_posix().lstrip("./"))
            elif line.strip().startswith(("-", "## ")):
                break
    return targets


def _scandir_walk_files(base: Path) -> list[tuple[Path, os.stat_result]]:
    out: list[tuple[Path, os.stat_result]] = []
    stack = [base]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError:
            continue
        dirs_to_visit: list[Path] = []
        for de in entries:
            if de.name in SKIP_TOP_DIRS:
                continue
            try:
                if de.is_dir(follow_symlinks=False):
                    dirs_to_visit.append(Path(de.path))
                elif de.is_file(follow_symlinks=False):
                    out.append((Path(de.path), de.stat(follow_symlinks=False)))
            except OSError:
                continue
        stack.extend(reversed(dirs_to_visit))
    return out


def iter_tracked_project_files(root: Path) -> list[tuple[Path, os.stat_result]]:
    results: list[tuple[Path, os.stat_result]] = []
    for entry in sorted(root.iterdir()):
        name = entry.name
        if name in SKIP_TOP_DIRS:
            continue
        if name == ".handoff":
            for sub_name in ("00_INVARIANTS.md", "01_STATE_LEDGER.md", "SESSION_HANDOFF_BUNDLE.md"):
                sp = entry / sub_name
                if sp.is_file():
                    results.append((sp, sp.stat()))
            for sub_dir in ("ledgers", "contracts"):
                sd = entry / sub_dir
                if sd.is_dir():
                    results.extend(_scandir_walk_files(sd))
            continue
        if name == ".agents":
            for sub in ("hooks.json", "rules", "agents", "scripts", "workflows"):
                sp = entry / sub
                if sp.is_file():
                    results.append((sp, sp.stat()))
                elif sp.is_dir():
                    results.extend(_scandir_walk_files(sp))
            continue
        if entry.is_file():
            results.append((entry, entry.stat()))
        elif entry.is_dir():
            results.extend(_scandir_walk_files(entry))
    return results


def snapshot_dir(root: Path) -> Path:
    return root / ".handoff" / "archive" / "snapshots" / "current"


def log_mutation(root: Path, record: dict) -> None:
    arc_dir = root / ".handoff" / "archive"
    arc_dir.mkdir(parents=True, exist_ok=True)
    with (arc_dir / "mutation_log.jsonl").open("a", encoding="utf-8") as lf:
        lf.write(json.dumps(record, ensure_ascii=False) + "\n")


def _should_store_bytes(fp: Path, size: int) -> bool:
    if size > MAX_BACKUP_FILE_BYTES:
        return False
    ext = fp.suffix.lower()
    if ext == ".json" and size > 512 * 1024:
        return False
    return ext in BACKUP_EXTS


def cmd_snapshot(root: Path, quiet: bool = False) -> int:
    handoff_dir = root / ".handoff"
    if not handoff_dir.exists():
        sys.stderr.write("ERR | Thiếu thư mục .handoff/ để chụp snapshot\n")
        return 1

    led_path = handoff_dir / "01_STATE_LEDGER.md"
    led_text = led_path.read_text(encoding="utf-8") if led_path.exists() else ""
    allowed = extract_locked_targets(led_text)

    snap = snapshot_dir(root)
    files_store = snap / "files"
    if snap.exists():
        shutil.rmtree(snap)
    files_store.mkdir(parents=True, exist_ok=True)

    manifest_files: dict[str, dict] = {}
    backed_up = 0
    for fp, st in iter_tracked_project_files(root):
        rel = fp.relative_to(root).as_posix()
        rec: dict[str, object] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns, "lines": 0}
        if _should_store_bytes(fp, st.st_size):
            data = fp.read_bytes()
            rec["sha256"] = hashlib.sha256(data).hexdigest()
            rec["lines"] = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
            rec["stored"] = True
            dest = files_store / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            backed_up += 1
        else:
            rec["sha256"] = ""
            rec["stored"] = False
        manifest_files[rel] = rec

    meta = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "milestone": extract_token(led_text, "Cột mốc đang mở"),
        "phase": extract_token(led_text, "Pha hiện tại"),
        "allowed_targets": allowed,
        "files": manifest_files,
    }
    (snap / "manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not quiet:
        print(f"OK | snapshot={len(manifest_files)} files (backed_up={backed_up})")
    return 0


def _read_session_tokens(root: Path) -> int:
    meter_path = root / ".handoff" / "context_meter.json"
    if not meter_path.is_file():
        return 0
    try:
        data = json.loads(meter_path.read_text(encoding="utf-8"))
        return int(data.get("effective_session_tokens", 0))
    except Exception:
        return 0


def _bump_meter_bytes(root: Path, byte_count: int) -> None:
    meter_path = root / ".handoff" / "context_meter.json"
    if not meter_path.is_file() or byte_count <= 0:
        return
    try:
        data = json.loads(meter_path.read_text(encoding="utf-8"))
        added = int(math.ceil(byte_count / 3.2))
        data["accumulated_work_tokens"] = int(data.get("accumulated_work_tokens", 0)) + added
        data["effective_session_tokens"] = max(
            int(data.get("effective_session_tokens", 0)),
            int(data.get("startup_tokens", 0)) + int(data["accumulated_work_tokens"]),
        )
        data["tool_events"] = int(data.get("tool_events", 0)) + 1
        meter_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass


def check_path_permission(
    rel_path: str,
    milestone: str,
    phase: str,
    allowed_targets: list[str],
    raw_abs_path: str = "",
    session_tokens: int = 0,
) -> str | None:
    if raw_abs_path:
        try:
            abs_p = Path(raw_abs_path).resolve()
            for prot in PROTECTED_DIRS:
                pp = Path(prot).resolve()
                if abs_p == pp or pp in abs_p.parents:
                    return f"Cấm chạm vào hạ tầng bảo vệ bên SHTT ({abs_p})"
        except OSError:
            pass

    if not rel_path:
        return None

    # Cho phép ghi nội bộ trong .handoff/ để đóng gói sổ cái kể cả khi chạm 200k-240k
    if (
        rel_path.startswith(".handoff/archive/")
        or rel_path.startswith(".handoff/artifacts/")
        or rel_path.startswith(".handoff/logs/")
        or rel_path in (".handoff/01_STATE_LEDGER.md", ".handoff/SESSION_HANDOFF_BUNDLE.md", ".handoff/context_meter.json")
    ):
        return None

    # Kiểm tra trần token cứng trước khi cho sửa bất kỳ tệp code dự án nào!
    if session_tokens >= ABSOLUTE_CEILING_TOKENS:
        return (
            f"CHẶN CỨNG TRẦN TUYỆT ĐỐI 240K ({session_tokens} token): "
            f"Cấm sửa tệp dự án ({rel_path}); chạy export_session_handoff.py và mở phiên mới ngay!"
        )
    if session_tokens >= HARD_FREEZE_NEW_WORK_TOKENS and not rel_path.startswith(".handoff/"):
        return (
            f"CHẶN CỨNG TRẦN 200K ({session_tokens} token): Vùng 200k–240k chỉ cho phép ghi sổ cái .handoff/ "
            f"để đóng gói bàn giao, cấm sửa trực tiếp tệp code ({rel_path})!"
        )

    if rel_path == ".handoff/00_INVARIANTS.md":
        if milestone not in ("M00", ""):
            return f"Cấm sửa 00_INVARIANTS.md sau khi đã khóa M00 (đang ở {milestone})"
        return None
    if rel_path.startswith(".handoff/ledgers/") or rel_path.startswith(".handoff/contracts/"):
        if rel_path == ".handoff/ledgers/plan_backbone.md" and milestone not in ("M00", ""):
            return f"Cấm sửa plan_backbone.md sau khi đã khóa M00 (đang ở {milestone})"
        return None
    if rel_path.startswith(".agents/"):
        return f"Cấm tự ý sửa cấu hình hệ thống ({rel_path}) trong phiên thực thi"

    if milestone == "M00" or phase.startswith("PLAN_"):
        return f"Chặn bởi Cổng Kiến trúc ({milestone} - {phase}): cấm sửa code ({rel_path}) khi chưa duyệt M00"
    if phase in READ_ONLY_PROJECT_PHASES:
        return f"Cấm ghi tệp code ({rel_path}) khi sổ cái đang ở pha chỉ đọc {phase}"
    if phase in SCOPED_WRITE_PHASES:
        if not allowed_targets:
            return f"Pha {phase} chưa khóa danh sách Tệp đích được phép chạm trong 01_STATE_LEDGER.md"
        if rel_path not in allowed_targets:
            return f"Chạm tệp ngoài phạm vi cột mốc ({rel_path}); chỉ cấp phép: {', '.join(allowed_targets)}"
        return None
    return f"Pha không xác định ({phase}): từ chối ghi {rel_path}"


def cmd_enforce(root: Path, rollback: bool, quiet_ok: bool = False) -> int:
    snap = snapshot_dir(root)
    manifest_path = snap / "manifest.json"
    if not manifest_path.exists():
        if not quiet_ok:
            print("WARN | Chưa có snapshot trước cột mốc; bỏ qua đối chiếu diff")
        return 0

    meta = json.loads(manifest_path.read_text(encoding="utf-8"))
    old_files: dict[str, dict] = meta.get("files", {})
    files_store = snap / "files"

    led_path = root / ".handoff" / "01_STATE_LEDGER.md"
    led_text = led_path.read_text(encoding="utf-8") if led_path.exists() else ""
    milestone = extract_token(led_text, "Cột mốc đang mở") or str(meta.get("milestone", ""))
    phase = extract_token(led_text, "Pha hiện tại") or str(meta.get("phase", ""))
    allowed = extract_locked_targets(led_text)
    sess_tok = _read_session_tokens(root)

    current_map: dict[str, tuple[Path, os.stat_result]] = {
        fp.relative_to(root).as_posix(): (fp, st) for fp, st in iter_tracked_project_files(root)
    }

    violations: list[tuple[str, str, str]] = []
    for rel, (fp, st) in sorted(current_map.items()):
        if rel not in old_files:
            reason = check_path_permission(rel, milestone, phase, allowed, str(fp), sess_tok)
            if reason:
                violations.append(("CREATED", rel, reason))
        else:
            old_rec = old_files[rel]
            changed = False
            if old_rec.get("sha256"):
                if st.st_size != old_rec["size"] or st.st_mtime_ns != old_rec["mtime_ns"]:
                    changed = hashlib.sha256(fp.read_bytes()).hexdigest() != old_rec["sha256"]
            else:
                changed = st.st_size != old_rec["size"] or st.st_mtime_ns != old_rec["mtime_ns"]
            if changed:
                reason = check_path_permission(rel, milestone, phase, allowed, str(fp), sess_tok)
                if reason:
                    violations.append(("MODIFIED", rel, reason))

    for rel in sorted(old_files):
        if rel not in current_map:
            reason = check_path_permission(rel, milestone, phase, allowed, str(root / rel), sess_tok)
            if reason:
                violations.append(("DELETED", rel, reason))

    if not violations:
        if not quiet_ok:
            print(f"OK | guard_enforce=clean | milestone={milestone} | phase={phase}")
        return 0

    for kind, rel, reason in violations:
        rolled_back = False
        target_p = root / rel
        backup_p = files_store / rel
        if rollback:
            if kind == "CREATED" and target_p.exists():
                target_p.unlink()
                parent = target_p.parent
                while parent != root and parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
                rolled_back = True
            elif kind in ("MODIFIED", "DELETED") and backup_p.exists():
                target_p.parent.mkdir(parents=True, exist_ok=True)
                target_p.write_bytes(backup_p.read_bytes())
                rolled_back = True

        log_mutation(
            root,
            {
                "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
                "source": "enforce",
                "kind": kind,
                "path": rel,
                "milestone": milestone,
                "phase": phase,
                "rolled_back": rolled_back,
                "reason": reason,
            },
        )
        action_note = "ĐÃ HOÀN NGUYÊN" if rolled_back else "CHƯA HOÀN NGUYÊN"
        sys.stderr.write(f"ERR | {action_note} [{kind}] {rel} -> {reason}\n")
    return 2


def parse_hook_payload(raw_stdin: str) -> tuple[str, str, int]:
    if not raw_stdin.strip():
        return "unknown", "", 0
    try:
        payload = json.loads(raw_stdin)
    except Exception:
        return "unparsed", "", len(raw_stdin)

    payload_bytes = len(raw_stdin.encode("utf-8", errors="ignore"))
    tool_call = payload.get("toolCall")
    if isinstance(tool_call, dict):
        t_name = str(tool_call.get("name") or "unknown")
        t_args = tool_call.get("args") or {}
        if isinstance(t_args, dict):
            for key in ("Path", "path", "TargetFile", "target_file", "file_path", "AbsolutePath"):
                val = t_args.get(key)
                if isinstance(val, str) and val.strip():
                    return t_name, val.strip(), payload_bytes
        return t_name, "", payload_bytes

    t_name = str(payload.get("tool_name") or payload.get("tool") or "unknown")
    t_input = payload.get("tool_input") or payload.get("input") or payload.get("args") or {}
    if isinstance(t_input, dict):
        for key in ("Path", "path", "TargetFile", "target_file", "file_path", "AbsolutePath"):
            val = t_input.get(key)
            if isinstance(val, str) and val.strip():
                return t_name, val.strip(), payload_bytes
    return t_name, "", payload_bytes


def normalize_rel(root: Path, raw_path: str) -> str:
    if not raw_path:
        return ""
    p = Path(raw_path)
    abs_p = p.resolve() if p.is_absolute() else (root / p).resolve()
    try:
        return abs_p.relative_to(root).as_posix()
    except ValueError:
        return ""


def cmd_hook(root: Path, mode: str) -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    tool_name, raw_path, payload_bytes = parse_hook_payload(raw)
    rel_path = normalize_rel(root, raw_path)

    led_path = root / ".handoff" / "01_STATE_LEDGER.md"
    led_text = led_path.read_text(encoding="utf-8") if led_path.exists() else ""
    milestone = extract_token(led_text, "Cột mốc đang mở")
    phase = extract_token(led_text, "Pha hiện tại")
    allowed = extract_locked_targets(led_text)
    sess_tok = _read_session_tokens(root)

    reason = (
        check_path_permission(rel_path, milestone, phase, allowed, raw_path, sess_tok)
        if (rel_path or raw_path)
        else None
    )
    log_mutation(
        root,
        {
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "source": mode,
            "tool": tool_name,
            "path": rel_path or raw_path,
            "session_tokens": sess_tok,
            "decision": "deny" if reason else "allow",
            "reason": reason or "",
        },
    )

    if mode == "hook-pre":
        if reason:
            sys.stdout.write(json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False))
        else:
            sys.stdout.write(json.dumps({"decision": "allow"}))
        sys.stdout.flush()
        return 0

    _bump_meter_bytes(root, payload_bytes)
    if reason:
        cmd_enforce(root, rollback=True, quiet_ok=True)
    sys.stdout.write("{}")
    sys.stdout.flush()
    return 0


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Chụp ảnh phạm vi, hoàn nguyên tức thời & khóa trần 200k-240k token")
    parser.add_argument("action", choices=("snapshot", "enforce", "hook-pre", "hook-post"))
    parser.add_argument("--root", default=".", help="Thư mục gốc dự án")
    parser.add_argument("--rollback", action="store_true", help="Tự động xóa/hoàn nguyên tệp vi phạm phạm vi")
    parser.add_argument("--quiet-ok", action="store_true", help="Ẩn dòng thông báo khi sạch")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.action == "snapshot":
        return cmd_snapshot(root, quiet=args.quiet_ok)
    if args.action == "enforce":
        return cmd_enforce(root, rollback=args.rollback, quiet_ok=args.quiet_ok)
    return cmd_hook(root, args.action)


if __name__ == "__main__":
    raise SystemExit(main())
