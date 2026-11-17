#!/usr/bin/env python3
"""Đóng gói nguyên tử cột mốc code, tự động tái lập symbol_map.json cho cột mốc kế tiếp và chụp snapshot mới."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MAX_LEDGER_LINES = 150
KEEP_RECENT_CLOSED = 10
DEFAULT_TOOLS_DIR = os.environ.get("CODE_HANDOFF_TOOLS_DIR", "/shared/user/.gemini/code_handoff_tools")

QUEUE_ITEM_RE = re.compile(r"^-\s*\[\s*\]\s*(M\d+[A-Za-z0-9]*)\s*:\s*(.+)$")
DECISION_ID_RE = re.compile(r"\[D(\d+)")
ARTIFACT_MS_RE = re.compile(r"^(?:explore|work|audit)_([A-Za-z0-9]+)(?:_.*)?\.md$")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def utf8_env() -> dict[str, str]:
    return {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def run_py(args_list: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-X", "utf8", *args_list],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=utf8_env(),
    )


def resolve_sibling_script(root: Path, script_name: str) -> Path:
    local_p = root / ".agents" / "scripts" / script_name
    if local_p.is_file():
        return local_p.resolve()
    here_p = Path(__file__).resolve().parent / script_name
    if here_p.is_file():
        return here_p
    return (Path(DEFAULT_TOOLS_DIR) / script_name).resolve()


def atomic_write_lf(path: Path, text: str) -> None:
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    if not norm.endswith("\n"):
        norm += "\n"
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(norm.encode("utf-8"))
    tmp.replace(path)


def extract_field(text: str, label: str) -> str:
    m = re.search(rf"(?m)^-\s*{re.escape(label)}\s*:\s*(.+)$", text)
    return m.group(1).strip() if m else ""


def extract_targets(ledger_text: str) -> list[str]:
    targets: list[str] = []
    in_block = False
    for line in ledger_text.splitlines():
        if re.match(r"^-\s*Tệp đích được phép chạm", line):
            in_block = True
            continue
        if in_block:
            if re.match(r"^\s{2,}-\s+", line):
                val = re.sub(r"^\s{2,}-\s+", "", line).strip().strip("`")
                if val:
                    targets.append(val)
            elif line.strip().startswith(("-", "## ")):
                break
    return targets


def split_ledger_sections(text: str) -> tuple[list[str], dict[int, list[str]]]:
    header: list[str] = []
    sections: dict[int, list[str]] = {1: [], 2: [], 3: [], 4: [], 5: []}
    cur = 0
    for line in text.splitlines():
        m = re.match(r"^##\s+([1-5])\.", line)
        if m:
            cur = int(m.group(1))
            sections[cur].append(line)
        elif cur == 0:
            header.append(line)
        else:
            sections[cur].append(line)
    return header, sections


def render_ledger(header: list[str], sections: dict[int, list[str]]) -> str:
    blocks = ["\n".join(header).strip()]
    for idx in range(1, 6):
        blocks.append("\n".join(sections[idx]).strip())
    return "\n\n".join(b for b in blocks if b) + "\n"


def parse_queue_payload(raw_desc: str) -> tuple[str, list[str]]:
    parts = [p.strip() for p in raw_desc.split("->")]
    goal = parts[0] if parts else raw_desc.strip()
    targets: list[str] = []
    for p in parts[1:]:
        if ":" in p and "Phạm vi" in p:
            _, rhs = p.split(":", 1)
            for item in rhs.split(","):
                cleaned = item.strip().rstrip(".").strip("`")
                if cleaned:
                    targets.append(cleaned)
    return goal, targets


def _current_meter_summary(handoff_dir: Path, arg_tokens: str) -> tuple[str, str]:
    meter_p = handoff_dir / "context_meter.json"
    if arg_tokens and arg_tokens.isdigit():
        tok_num = int(arg_tokens)
    elif meter_p.is_file():
        try:
            d = json.loads(meter_p.read_text(encoding="utf-8"))
            tok_num = int(d.get("effective_session_tokens", 0))
        except Exception:
            tok_num = 0
    else:
        tok_num = 0

    if tok_num >= 200_000:
        tier = "HARD_FREEZE_200K_240K"
    elif tok_num >= 170_000:
        tier = "WARN_170K_200K"
    else:
        tier = "GREEN_UNDER_170K"
    return str(tok_num), tier


def build_active_sections(
    next_ms: str,
    next_goal: str,
    next_targets: list[str],
    tok_str: str,
    tier_str: str,
    next_action: str,
) -> tuple[list[str], list[str]]:
    freeze_mode = tier_str == "HARD_FREEZE_200K_240K"

    if next_ms == "NONE":
        sec1 = [
            "## 1. Con trỏ điều phối hiện thời",
            "- Cột mốc đang mở: NONE",
            "- Pha hiện tại: READY_TO_DELIVER",
            f"- Dung lượng ngữ cảnh gần nhất: {tok_str}",
            f"- Trạng thái trần token: {tier_str}",
            f"- Hành động kế tiếp duy nhất: {next_action or 'Trình bày báo cáo đồng bộ thành phẩm & SHA-256 cho người dùng'}",
        ]
        sec2 = [
            "## 2. Đặc tả cột mốc đang thực thi",
            "- Mã phiên hiện hành: NONE",
            "- Mục tiêu cột mốc: Đã hoàn tất toàn bộ hàng đợi cột mốc",
            "- Tệp đích được phép chạm (giới hạn từ 1 đến 5 tệp):",
            "  - .handoff/01_STATE_LEDGER.md",
        ]
        return sec1, sec2

    phase = "HANDOFF_FLUSH" if freeze_mode else ("FINAL_MERGE" if next_ms == "M99" else "EXPLORE")
    if freeze_mode:
        default_action = (
            f"ĐÃ CHẠM TRẦN 200K ({tok_str} token): Cấm mở {next_ms} trên luồng này! "
            f"Chạy export_session_handoff.py và tiếp tục {next_ms} ở phiên sạch mới."
        )
    elif next_ms == "M99":
        default_action = (
            "Chạy FINAL_MERGE tích hợp & test toàn cục, chụp truoc_c6_manifest.json, rồi tách 3 subagent độc lập "
            "FINAL_AUDIT_A (Sync), FINAL_AUDIT_B (Logic/Sec) và FINAL_GATE6 (Build/UI)"
        )
    else:
        default_action = f"Khóa danh sách 1..5 tệp đích cụ thể của {next_ms}, chụp snapshot và gọi code_worker ngữ cảnh sạch"

    target_lines = [f"  - {t}" for t in (next_targets[:5] if next_targets else ["[Điền đường dẫn tệp đích 1..5]"])]
    sec1 = [
        "## 1. Con trỏ điều phối hiện thời",
        f"- Cột mốc đang mở: {next_ms}",
        f"- Pha hiện tại: {phase}",
        f"- Dung lượng ngữ cảnh gần nhất: {tok_str}",
        f"- Trạng thái trần token: {tier_str}",
        f"- Hành động kế tiếp duy nhất: {next_action or default_action}",
    ]
    sec2 = [
        "## 2. Đặc tả cột mốc đang thực thi",
        f"- Mã phiên hiện hành: {next_ms}",
        f"- Mục tiêu cột mốc: {next_goal or f'Thực thi module {next_ms}'}",
        "- Tệp đầu vào tham chiếu:",
        "  - .handoff/00_INVARIANTS.md",
        "  - .handoff/contracts/contracts_registry.json",
        "  - .handoff/contracts/symbol_map.json",
        "- Tệp đích được phép chạm (giới hạn từ 1 đến 5 tệp):",
        *target_lines,
        "- Tệp bàn giao hoạt động:",
        f"  - Thực thi: .handoff/artifacts/work_{next_ms}.md -> Trạng thái: Chờ chạy",
        f"  - Kiểm định: .handoff/artifacts/audit_{next_ms}.md -> Trạng thái: Chờ chạy",
    ]
    return sec1, sec2


def close_milestone(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    handoff = root / ".handoff"
    led_path = handoff / "01_STATE_LEDGER.md"
    art_dir = handoff / "artifacts"
    arc_root = handoff / "archive"

    if not led_path.is_file():
        print("ERR | Không tìm thấy .handoff/01_STATE_LEDGER.md")
        return 1

    led_text = led_path.read_text(encoding="utf-8")
    current_ms = extract_field(led_text, "Cột mốc đang mở").split()[0]
    milestone = args.milestone or current_ms

    if milestone in ("NONE", ""):
        print("ERR | Không có cột mốc nào đang mở để đóng")
        return 1
    if current_ms != milestone:
        print(f"ERR | Cột mốc đang mở '{current_ms}' khác với yêu cầu '{milestone}'")
        return 1
    if milestone == "M00" and not args.user_approved:
        print("ERR | Đóng M00 bắt buộc có cờ --user-approved sau khi người dùng duyệt kiến trúc")
        return 1

    gate_type = "plan" if milestone == "M00" else ("final" if milestone == "M99" else "milestone")
    verifier = resolve_sibling_script(root, "verify_code_gate.py")
    v_args = [str(verifier), "--root", str(root), "--gate", gate_type]
    if gate_type == "milestone":
        v_args.extend(["--milestone", milestone])
    if args.allow_shrink:
        v_args.append("--allow-shrink")
    if args.run_tests:
        v_args.append("--run-tests")
    if args.skip_tool_hash:
        v_args.append("--skip-tool-hash")

    v_proc = run_py(v_args, root)
    if v_proc.returncode != 0:
        print((v_proc.stdout + "\n" + v_proc.stderr).strip())
        return 1

    ms_arc_dir = arc_root / milestone
    if ms_arc_dir.exists():
        print(f"ERR | Thư mục lưu trữ .handoff/archive/{milestone} đã tồn tại")
        return 1

    matched_artifacts = [
        p for p in sorted(art_dir.glob("*.md"))
        if (m := ARTIFACT_MS_RE.match(p.name)) and m.group(1) == milestone
    ]

    targets = extract_targets(led_text)
    goal = extract_field(led_text, "Mục tiêu cột mốc")
    sha_records: list[str] = []
    for t in targets:
        tp = root / Path(t.strip("`"))
        if tp.is_file():
            sha_records.append(f"{tp.name}:{hashlib.sha256(tp.read_bytes()).hexdigest()[:16]}")

    tok_str, tier_str = _current_meter_summary(handoff, args.context_tokens)

    manifest_lines = [
        f"# HỒ SƠ ĐÓNG GÓI CỘT MỐC CODE {milestone}",
        "",
        f"- Thời điểm đóng gói: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- Trạm kiểm soát đã qua: {gate_type.upper()}",
        f"- Mục tiêu module: {goal}",
        f"- Token phiên lúc đóng: {tok_str} ({tier_str})",
        f"- Tệp đích đã chạm: {', '.join(targets)}",
        f"- Biên bản lưu trữ: {', '.join(p.name for p in matched_artifacts)}",
    ]
    if milestone == "M00":
        manifest_lines.append("- Phê duyệt kiến trúc: ĐÃ XÁC NHẬN (--user-approved)")
    if sha_records:
        manifest_lines.append(f"- SHA-256 xuất xưởng: {', '.join(sha_records)}")

    header, sections = split_ledger_sections(led_text)
    if args.decision:
        sec3_body = [ln for ln in sections[3][1:] if ln.strip() and "Chưa có quyết định" not in ln]
        existing_nums = [int(m.group(1)) for ln in sec3_body if (m := DECISION_ID_RE.search(ln))]
        next_num = max(existing_nums, default=0) + 1
        for dec in args.decision:
            sec3_body.append(f"- [D{next_num:02d} - {milestone}]: {dec.strip()}")
            next_num += 1
        sections[3] = [sections[3][0], *sec3_body]

    next_ms, next_goal, next_targets = "NONE", "", []
    new_sec4 = [sections[4][0]]
    popped = False
    for ln in sections[4][1:]:
        if not popped and (qm := QUEUE_ITEM_RE.match(ln.strip())):
            next_ms = qm.group(1)
            next_goal, next_targets = parse_queue_payload(qm.group(2))
            popped = True
            continue
        if ln.strip():
            new_sec4.append(ln)
    if len(new_sec4) == 1:
        new_sec4.append("- Không còn cột mốc chờ.")
    sections[4] = new_sec4

    sections[1], sections[2] = build_active_sections(
        next_ms=next_ms,
        next_goal=next_goal,
        next_targets=next_targets,
        tok_str=tok_str,
        tier_str=tier_str,
        next_action=args.next_action,
    )

    closed_items = [ln for ln in sections[5][1:] if ln.strip() and "Chưa có cột mốc" not in ln]
    clean_goal = goal if not goal.startswith("[") else f"Hoàn tất {milestone}"
    closed_items.append(
        f"- [x] {milestone}: {clean_goal} -> Tệp: {', '.join(targets)} -> Lưu: .handoff/archive/{milestone}/"
    )
    sections[5] = [sections[5][0], *closed_items]

    rendered = render_ledger(header, sections)
    overflow_items: list[str] = []
    if len(rendered.splitlines()) > MAX_LEDGER_LINES and len(closed_items) > KEEP_RECENT_CLOSED:
        overflow_items = closed_items[:-KEEP_RECENT_CLOSED]
        sections[5] = [sections[5][0], *closed_items[-KEEP_RECENT_CLOSED:]]
        rendered = render_ledger(header, sections)

    final_lines = len(rendered.splitlines())
    if args.dry_run:
        print(f"DRY_RUN | close={milestone} | next={next_ms} | ledger={final_lines}/{MAX_LEDGER_LINES}L")
        return 0

    ms_arc_dir.mkdir(parents=True, exist_ok=False)
    atomic_write_lf(ms_arc_dir / "manifest.md", "\n".join(manifest_lines))
    if milestone == "M00":
        for lock_name, rel_src in (
            ("plan_backbone_locked.md", handoff / "ledgers" / "plan_backbone.md"),
            ("contracts_registry_locked.json", handoff / "contracts" / "contracts_registry.json"),
        ):
            if rel_src.is_file():
                (ms_arc_dir / lock_name).write_bytes(rel_src.read_bytes())

    for f in matched_artifacts:
        (ms_arc_dir / f.name).write_bytes(f.read_bytes())
        f.unlink()

    if overflow_items:
        history_path = arc_root / "ledger_history.md"
        prefix = "" if history_path.exists() else "# LỊCH SỬ CỘT MỐC CODE ĐÃ ĐÓNG GÓI\n\n"
        with history_path.open("a", encoding="utf-8") as hf:
            hf.write(prefix + "\n".join(overflow_items) + "\n")

    atomic_write_lf(led_path, rendered)

    # Tự động cập nhật symbol_map.json để cột mốc kế tiếp đồng bộ 100% chữ ký mới nhất!
    slicer = resolve_sibling_script(root, "code_slicer.py")
    if slicer.is_file():
        run_py([str(slicer), "index", "--root", str(root)], root)

    guard = resolve_sibling_script(root, "code_handoff_guard.py")
    if guard.is_file():
        run_py([str(guard), "snapshot", "--root", str(root), "--quiet-ok"], root)

    # Nếu chạm 200k token, tự động xuất luôn SESSION_HANDOFF_BUNDLE.md
    exporter = resolve_sibling_script(root, "export_session_handoff.py")
    if tier_str == "HARD_FREEZE_200K_240K" and exporter.is_file():
        run_py([str(exporter), "--root", str(root)], root)

    sha_note = f" | {sha_records[0]}" if sha_records else ""
    print(
        f"OK | closed={milestone} | next={next_ms} | tok={tok_str}({tier_str}) | "
        f"symbol_map=refreshed | ledger={final_lines}/{MAX_LEDGER_LINES}L{sha_note}"
    )
    return 0


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Đóng gói nguyên tử cột mốc code & làm mới symbol_map.json")
    parser.add_argument("--root", default=".", help="Thư mục gốc dự án")
    parser.add_argument("--milestone", default="", help="Mã cột mốc cần đóng")
    parser.add_argument("--decision", action="append", default=[], help="Quyết định kiến trúc khóa vào mục 3")
    parser.add_argument("--context-tokens", default="", help="Cập nhật số token phiên hiện tại (ví dụ 145000)")
    parser.add_argument("--next-action", default="", help="Ghi đè hành động kế tiếp")
    parser.add_argument("--allow-shrink", action="store_true", help="Cho phép giảm >20% dòng khi chủ đích xóa code")
    parser.add_argument("--run-tests", action="store_true", help="Chạy kèm test khi đóng mốc")
    parser.add_argument("--skip-tool-hash", action="store_true", help="Bỏ qua kiểm tra SHA-256 công cụ")
    parser.add_argument("--user-approved", action="store_true", help="Xác nhận người dùng đã duyệt M00")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử không ghi đĩa")
    args = parser.parse_args()
    return close_milestone(args)


if __name__ == "__main__":
    raise SystemExit(main())
