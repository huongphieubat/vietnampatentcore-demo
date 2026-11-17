#!/usr/bin/env python3
"""Kiểm tra toàn vẹn .handoff/ cho Code, khóa cứng trần 200k-240k token trước compact, khóa SHA-256 công cụ và cầu chì BLOCKED."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

# Ngưỡng khóa cứng Ngân sách Ngữ cảnh trước khi hệ thống auto-compact (~256k token)
SOFT_WARN_TOKENS = 170_000
HARD_FREEZE_NEW_WORK_TOKENS = 200_000
ABSOLUTE_CEILING_TOKENS = 240_000

MAX_INVARIANTS_LINES = 120
MAX_LEDGER_LINES = 150
MAX_ARTIFACT_LINES = 300
MAX_ALWAYS_ON_TOKENS = 1800

VI_CHARS_PER_TOKEN = 2.2
CODE_CHARS_PER_TOKEN = 3.2

DEFAULT_SKILLS_DIR = os.environ.get("CODE_HANDOFF_SKILLS_DIR", "/shared/user/.gemini/skills")
DEFAULT_TOOLS_DIR = os.environ.get("CODE_HANDOFF_TOOLS_DIR", "/shared/user/.gemini/code_handoff_tools")

DEFAULT_CODE_SLICER_SHA256 = os.environ.get(
    "CODE_SLICER_SHA256",
    "c5172d7ff9164acbd647307c0b6f699565da41366e6fdaa4e3e6e49439e824da",
)
DEFAULT_VERIFY_SYNC_SHA256 = os.environ.get(
    "VERIFY_CODE_SYNC_SHA256",
    "ca4df883616c0cb329fb636e87b1394e650d77cab9c95825fe3cc5a194880b63",
)

VALID_PHASES = {
    "PLAN_EXPLORE",
    "PLAN_AUDIT",
    "PLAN_APPROVAL",
    "EXPLORE",
    "WORK",
    "AUDIT",
    "FIXING",
    "READY_TO_CLOSE",
    "FINAL_MERGE",
    "FINAL_AUDIT_A",
    "FINAL_AUDIT_B",
    "FINAL_GATE6",
    "HANDOFF_FLUSH",
    "READY_TO_DELIVER",
    "BLOCKED",
}
FLUSH_ALLOWED_PHASES = {"READY_TO_CLOSE", "HANDOFF_FLUSH", "READY_TO_DELIVER", "BLOCKED"}
REQUIRED_SECTIONS = ("## 1.", "## 2.", "## 3.", "## 4.", "## 5.")

PLACEHOLDER_RE = re.compile(
    r"\[(TEN_DU_AN|YYYY-MM-DD|Mô tả[^\]]*|Danh sách[^\]]*|Điền[^\]]*)\]"
)
ARTIFACT_NAME_RE = re.compile(
    r"^(?:explore|work|audit)_([A-Za-z0-9]+)(?:_part\d+)?(?:_(?:fix\d+|layerA|layerB|gate6))?\.md$"
)
FAIL_STATUS_RE = re.compile(
    r"(?im)^\s*(?:[-*]|\d+\.)?\s*\*{0,2}(?:Kết quả|Trạng thái|Status)\*{0,2}\s*:\s*\*{0,2}FAIL\b"
)
NEED_SPLIT_RE = re.compile(
    r"(?im)^\s*(?:[-*]|\d+\.)?\s*\*{0,2}(?:Kết quả|Trạng thái|Status)\*{0,2}\s*:\s*\*{0,2}NEED_SPLIT\b"
)
COMPACTED_INVALID_RE = re.compile(
    r"(?im)^\s*(?:[-*]|\d+\.)?\s*\*{0,2}(?:Kết quả|Trạng thái|Status)\*{0,2}\s*:\s*\*{0,2}COMPACTED(?:_INVALID)?\b"
)


def build_starter_invariants(project_id: str, slicer_sha: str, sync_sha: str) -> str:
    return f"""# RÀNG BUỘC BẤT BIẾN KIẾN TRÚC & ĐỒNG BỘ CODE (00_INVARIANTS)

- Mã dự án: {project_id}
- Phiên bản quy chuẩn: v1.0-code-antigravity
- Ngày khóa chuẩn: {date.today().isoformat()}
- Quyền chỉnh sửa: CẤM mọi subagent tự ý sửa tệp này; Orchestrator chỉ cập nhật khi duyệt Cổng Kiến trúc (M00) hoặc đổi yêu cầu.

## 1. Mục tiêu cốt lõi & Ranh giới phạm vi
- Đích đến sản phẩm: [Mô tả kiến trúc ứng dụng / tính năng cốt lõi]
- Thành phẩm bàn giao chính thức: [Danh sách entrypoints / gói build / dịch vụ]
- Ngoài phạm vi (Out of Scope): `/shared/user/.gemini/handoff_tools/`, `/shared/user/.gemini/skills/` (chỉ đọc, bảo toàn hệ thống SHTT)

## 2. Ngân sách Ngữ cảnh Khóa cứng Trần 200k–240k Token (Anti-Compaction)
- Cảnh báo chuẩn bị chốt mốc: `170.000 token`
- Khóa cứng ngắt việc mới: `200.000 token` (từ 200k–240k chỉ được đóng gói sổ cái, hợp đồng và xuất `SESSION_HANDOFF_BUNDLE.md`)
- Trần ngắt cầu chì tuyệt đối: `240.000 token` (trước ngưỡng auto-compact ~256k của hệ thống)
- Ngân sách mỗi Subagent: Ngữ cảnh sạch mới 100%, đọc lát `<= 150–200 dòng/lượt` qua `code_slicer.py`, đầu vào `<= 1.200 dòng` (`NEED_SPLIT`), hủy kết quả nếu nén (`COMPACTED_INVALID`).

## 3. Hằng số Kỹ thuật & Khóa Mã băm Công cụ Đồng bộ
- Công cụ cắt lát ký hiệu: `/shared/user/.gemini/code_handoff_tools/code_slicer.py` (SHA-256: `{slicer_sha}`)
- Công cụ kiểm đồng bộ code: `/shared/user/.gemini/code_handoff_tools/verify_code_sync.py` (SHA-256: `{sync_sha}`)
- Sổ cái hợp đồng liên tệp: `.handoff/contracts/contracts_registry.json` & `.handoff/contracts/symbol_map.json`
- Môi trường chạy lệnh: `python3 -X utf8` với `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`

## 4. Ngăn xếp Công nghệ & Quy ước Bất biến
- Ngôn ngữ / Runtime: [Điền phiên bản Python / Node.js / DB / Framework]
- Quy ước đồng bộ: Cấm đổi chữ ký hàm, API route, cột SQL hoặc DOM ID đã khóa trong `contracts_registry.json` nếu chưa cập nhật hợp đồng.

## 5. Lằn ranh đỏ Nghiệm thu (Hard Rejection Gates)
1. Vượt trần `200.000 token` mà vẫn mở cột mốc mới thay vì đóng gói bàn giao hoặc đẩy sang subagent sạch.
2. Đọc nguyên văn tệp `MONOLITH_SLICE_ONLY` (`> 400 dòng` / `> 40KB`) không qua `code_slicer.py`.
3. Mất đồng bộ import, lệch `contracts_registry.json`, lỗi cú pháp JS/Python/HTML hoặc tụt `> 20%` dòng do cắt cụt code AI.
4. Chạm tệp ngoài danh sách `1..5 tệp đích` trong `01_STATE_LEDGER.md` hoặc gộp 3 lớp kiểm toán M99 vào 1 subagent.
"""


STARTER_LEDGER = """# SỔ CÁI TRẠNG THÁI ĐIỀU PHỐI CODE (01_STATE_LEDGER)

## 1. Con trỏ điều phối hiện thời
- Cột mốc đang mở: M00
- Pha hiện tại: PLAN_EXPLORE
- Dung lượng ngữ cảnh gần nhất: 0
- Trạng thái trần token: GREEN_UNDER_170K
- Hành động kế tiếp duy nhất: Chạy code_slicer.py index, gọi code_explorer khảo sát kiến trúc, khóa contracts_registry.json và lập plan_backbone.md

## 2. Đặc tả cột mốc đang thực thi
- Mã phiên hiện hành: M00
- Mục tiêu cột mốc: Lập chỉ mục ký hiệu symbol_map.json, khóa hợp đồng liên tệp contracts_registry.json và kế hoạch phân rã module M00
- Tệp đầu vào tham chiếu:
  - .handoff/00_INVARIANTS.md
  - .handoff/contracts/symbol_map.json
- Tệp đích được phép chạm (giới hạn từ 1 đến 5 tệp):
  - .handoff/ledgers/plan_backbone.md
  - .handoff/contracts/contracts_registry.json
  - .handoff/ledgers/decision_log.tsv
- Tệp bàn giao hoạt động:
  - Khảo sát: .handoff/artifacts/explore_M00.md -> Trạng thái: Chờ chạy
  - Kiểm định: .handoff/artifacts/audit_M00.md -> Trạng thái: Chờ chạy
- Tiêu chí nghiệm thu riêng:
  - Đã tạo symbol_map.json, khóa đầy đủ API/DB/DOM/Symbol contracts, mỗi cột mốc <= 1 module dọc (1..5 tệp), code_auditor phản biện PASS và người dùng duyệt

## 3. Sổ quyết định kiến trúc đã khóa (Locked Decisions)
- Chưa có quyết định khóa.

## 4. Hàng đợi cột mốc kế tiếp
- [ ] M01: [Điền module/tính năng thực thi đầu tiên sau khi duyệt M00] -> Phụ thuộc: M00 đạt PASS -> Phạm vi: [1..5 tệp đích].
- [ ] M99: Tích hợp toàn cục, kiểm toán tách 3 lớp độc lập (SYNC, LOGIC, BUILD_UI) và bàn giao -> Phụ thuộc: Các mốc trước PASS -> Phạm vi: [Entrypoints].

## 5. Chỉ mục cột mốc đã đóng gói
- Chưa có cột mốc đóng gói.
"""

STARTER_PLAN_BACKBONE = """# XƯƠNG SỐNG KIẾN TRÚC & PHÂN RÃ MODULE CHỐNG MẤT ĐỒNG BỘ (M00)

Trạng thái: [CHUA_LAP_KE_HOACH]

| Mã mốc | Module / Tính năng dọc khép kín | Hợp đồng liên tệp khóa cứng (API / DB / Symbol / DOM ID) | Rủi ro đồng bộ & Kiểm thử tất định | Tệp đích (1..5 tệp) |
|---|---|---|---|---|
| [M01] | [Điền tên module/feature] | [Điền chữ ký hàm / route / bảng SQL / DOM ID] | [Điền lệnh verify_code_sync.py / pytest] | [đường/dẫn/tệp] |
"""

STARTER_CONTRACTS_JSON = {
    "schema_version": "1.0",
    "description": "Sổ cái khóa cứng hợp đồng liên tệp chống mất đồng bộ giữa các Agent/Subagent",
    "shared_symbols": [],
    "api_endpoints": [],
    "db_tables": [],
    "dom_bindings": [],
    "env_variables": [],
    "test_commands": [],
}

LEDGER_TEMPLATES: dict[str, str] = {
    "plan_backbone.md": STARTER_PLAN_BACKBONE,
    "decision_log.tsv": "ma\tnguon_phat_hien\tvi_tri\ttom_tat\tquyet_dinh\tcan_cu\tcommit_hoac_sha\n",
    "bug_ledger.tsv": "ma\tloai_loi\tnguon_goc\tfile_vi_tri\ttom_tat\tbien_phap_chan_tai_nguon\n",
}

EXPECTED_TSV_HEADERS: dict[str, list[str]] = {
    "decision_log.tsv": ["ma", "nguon_phat_hien", "vi_tri", "tom_tat", "quyet_dinh", "can_cu", "commit_hoac_sha"],
    "bug_ledger.tsv": ["ma", "loai_loi", "nguon_goc", "file_vi_tri", "tom_tat", "bien_phap_chan_tai_nguon"],
}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def atomic_write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    if not norm.endswith("\n"):
        norm += "\n"
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(norm.encode("utf-8"))
    tmp.replace(path)


def estimate_vi_tokens(text: str) -> int:
    return int(math.ceil(len(text) / VI_CHARS_PER_TOKEN)) if text else 0


def estimate_mixed_tokens(text: str) -> int:
    return int(math.ceil(len(text) / ((VI_CHARS_PER_TOKEN + CODE_CHARS_PER_TOKEN) / 2.0))) if text else 0


def parse_frontmatter(md_text: str) -> tuple[dict[str, str], str]:
    if not md_text.startswith("---"):
        return {}, md_text
    parts = md_text.split("---", 2)
    if len(parts) < 3:
        return {}, md_text
    fm_raw, body = parts[1], parts[2]
    meta: dict[str, str] = {}
    current_key = ""
    for line in fm_raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m:
            current_key = m.group(1)
            meta[current_key] = m.group(2).strip().strip('"').strip("'")
        elif current_key and line.startswith(("  ", "\t")) and not line.lstrip().startswith("-"):
            meta[current_key] = (meta[current_key] + " " + line.strip()).strip()
    return meta, body


def resolve_tool_path(root: Path, tool_filename: str, cli_override: str = "", env_var: str = "") -> Path | None:
    override = cli_override.strip() or (os.environ.get(env_var, "").strip() if env_var else "")
    if override:
        return Path(override).expanduser().resolve()
    candidates = [
        root / ".agents" / "scripts" / tool_filename,
        Path(__file__).resolve().parent / tool_filename,
        Path(DEFAULT_TOOLS_DIR) / tool_filename,
    ]
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    return None


def measure_startup_tokens(root: Path, skills_dir_override: str = "") -> dict[str, object]:
    always_on_items: list[tuple[str, int, int]] = []
    glob_rule_items: list[tuple[str, int, int]] = []
    agent_items: list[tuple[str, int, int]] = []
    skill_items: list[tuple[str, int, int]] = []

    gemini_md = root / "GEMINI.md"
    if gemini_md.is_file():
        txt = gemini_md.read_text(encoding="utf-8")
        always_on_items.append(("GEMINI.md", len(txt), estimate_vi_tokens(txt)))

    rules_dir = root / ".agents" / "rules"
    if not rules_dir.is_dir():
        fb = Path(__file__).resolve().parent / "rules"
        if fb.is_dir():
            rules_dir = fb
    if rules_dir.is_dir():
        for rp in sorted(rules_dir.glob("*.md")):
            txt = rp.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(txt)
            trig = fm.get("trigger", "always_on")
            if trig == "always_on":
                clean_body = body.strip()
                always_on_items.append((f"rules/{rp.name}", len(clean_body), estimate_vi_tokens(clean_body)))
            else:
                desc_str = f"{rp.name}: {fm.get('description', '')} ({fm.get('globs', '')})"
                glob_rule_items.append((f"rules/{rp.name} [{trig}]", len(desc_str), estimate_vi_tokens(desc_str)))

    agents_dir = root / ".agents" / "agents"
    if not agents_dir.is_dir():
        fb_a = Path(__file__).resolve().parent / "agents"
        if fb_a.is_dir():
            agents_dir = fb_a
    if agents_dir.is_dir():
        for ap in sorted(agents_dir.glob("*.md")):
            fm, _ = parse_frontmatter(ap.read_text(encoding="utf-8"))
            line_injected = f"- {fm.get('name', ap.stem)}: {fm.get('description', '')}"
            agent_items.append((f"agents/{ap.name}", len(line_injected), estimate_vi_tokens(line_injected)))

    skills_dir = Path(skills_dir_override).resolve() if skills_dir_override else Path(DEFAULT_SKILLS_DIR)
    if skills_dir.is_dir():
        for sd in sorted(skills_dir.iterdir()):
            if not sd.is_dir():
                continue
            sp = sd / "SKILL.md"
            if sp.is_file():
                fm, _ = parse_frontmatter(sp.read_text(encoding="utf-8"))
                injected = f"- {fm.get('name', sd.name)} ({sp}): {fm.get('description', '')}"
                skill_items.append((f"skills/{sd.name}/SKILL.md", len(injected), estimate_vi_tokens(injected)))

    always_on_tok = sum(x[2] for x in always_on_items)
    glob_tok = sum(x[2] for x in glob_rule_items)
    agent_tok = sum(x[2] for x in agent_items)
    skill_tok = sum(x[2] for x in skill_items)
    return {
        "always_on_tokens": always_on_tok,
        "glob_pointer_tokens": glob_tok,
        "agents_meta_tokens": agent_tok,
        "skills_meta_tokens": skill_tok,
        "total_startup_tokens": always_on_tok + glob_tok + agent_tok + skill_tok,
        "always_on_items": always_on_items,
        "glob_rule_items": glob_rule_items,
        "agent_items": agent_items,
        "skill_items": skill_items,
    }


def _probe_transcript_tokens() -> int:
    tp_env = os.environ.get("ANTIGRAVITY_TRANSCRIPT_PATH", "").strip()
    candidates: list[Path] = []
    if tp_env:
        candidates.append(Path(tp_env))
    conv_id = os.environ.get("ANTIGRAVITY_CONVERSATION_ID", "").strip()
    if conv_id:
        base = Path.home() / ".gemini" / "jetski" / "brain" / conv_id / ".system_generated" / "logs"
        candidates.extend([base / "transcript_full.jsonl", base / "transcript.jsonl"])
    for c in candidates:
        if c.is_file():
            try:
                return int(math.ceil(c.stat().st_size / 3.0))
            except OSError:
                pass
    return 0


def load_or_update_context_meter(
    handoff_dir: Path,
    startup_tokens: int,
    ledger_text: str,
    add_tokens: int = 0,
    set_tokens: int | None = None,
    reset_meter: bool = False,
) -> dict[str, object]:
    meter_path = handoff_dir / "context_meter.json"
    meter: dict[str, object] = {
        "session_started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "startup_tokens": startup_tokens,
        "accumulated_work_tokens": 0,
        "tool_events": 0,
    }
    if meter_path.is_file() and not reset_meter:
        try:
            loaded = json.loads(meter_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                meter.update(loaded)
        except Exception:
            pass

    meter["startup_tokens"] = startup_tokens
    if set_tokens is not None:
        meter["accumulated_work_tokens"] = max(0, set_tokens - startup_tokens)
    elif add_tokens > 0:
        meter["accumulated_work_tokens"] = int(meter.get("accumulated_work_tokens", 0)) + add_tokens
        meter["tool_events"] = int(meter.get("tool_events", 0)) + 1

    # Đọc thông số ghi trong 01_STATE_LEDGER.md nếu lớn hơn
    led_tok = 0
    m = re.search(r"(?m)^-\s*Dung lượng ngữ cảnh gần nhất\s*:\s*([0-9][0-9_.,]*)", ledger_text)
    if m:
        digits = re.sub(r"[^0-9]", "", m.group(1))
        if digits:
            led_tok = int(digits)

    transcript_tok = _probe_transcript_tokens()
    computed = startup_tokens + int(meter.get("accumulated_work_tokens", 0))
    effective = max(computed, led_tok, transcript_tok)

    if effective >= ABSOLUTE_CEILING_TOKENS:
        tier = "ABORT_OVER_240K"
    elif effective >= HARD_FREEZE_NEW_WORK_TOKENS:
        tier = "HARD_FREEZE_200K_240K"
    elif effective >= SOFT_WARN_TOKENS:
        tier = "WARN_170K_200K"
    else:
        tier = "GREEN_UNDER_170K"

    meter["effective_session_tokens"] = effective
    meter["ledger_recorded_tokens"] = led_tok
    meter["transcript_probed_tokens"] = transcript_tok
    meter["ceiling_tier"] = tier
    meter["thresholds"] = {
        "soft_warn": SOFT_WARN_TOKENS,
        "hard_freeze_new_work": HARD_FREEZE_NEW_WORK_TOKENS,
        "absolute_abort_ceiling": ABSOLUTE_CEILING_TOKENS,
    }
    meter["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")

    if handoff_dir.is_dir():
        atomic_write_lf(meter_path, json.dumps(meter, ensure_ascii=False, indent=2))
    return meter


def extract_field_token(text: str, label: str) -> str:
    m = re.search(rf"(?m)^-\s*{re.escape(label)}\s*:\s*([A-Za-z0-9_]+)", text)
    return m.group(1) if m else ""


def extract_target_files(ledger_text: str) -> list[str]:
    targets: list[str] = []
    in_targets = False
    for line in ledger_text.splitlines():
        if re.match(r"^-\s*Tệp đích được phép chạm", line):
            in_targets = True
            continue
        if in_targets:
            if re.match(r"^\s{2,}-\s+", line):
                item = re.sub(r"^\s{2,}-\s+", "", line).strip().strip("`")
                if item:
                    targets.append(item)
            elif line.strip().startswith(("-", "## ")):
                break
    return targets


def trip_circuit_breaker_to_blocked(led_path: Path, led_text: str, reason_note: str) -> str:
    updated = re.sub(
        r"(?m)^(-\s*Pha hiện tại\s*:\s*)[A-Za-z0-9_]+",
        lambda m: f"{m.group(1)}BLOCKED",
        led_text,
        count=1,
    )
    updated = re.sub(
        r"(?m)^(-\s*Hành động kế tiếp duy nhất\s*:\s*).*$",
        lambda m: f"{m.group(1)}{reason_note}",
        updated,
        count=1,
    )
    atomic_write_lf(led_path, updated)
    return updated


def init_workspace(
    handoff_dir: Path,
    project_id: str,
    reset: bool,
    slicer_sha: str,
    sync_sha: str,
) -> int:
    (handoff_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (handoff_dir / "archive" / "c6_backups").mkdir(parents=True, exist_ok=True)
    (handoff_dir / "contracts").mkdir(parents=True, exist_ok=True)
    (handoff_dir / "ledgers").mkdir(parents=True, exist_ok=True)
    (handoff_dir / "logs").mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    for fname, body in LEDGER_TEMPLATES.items():
        fpath = handoff_dir / "ledgers" / fname
        if reset or not fpath.exists():
            atomic_write_lf(fpath, body)
            created.append(f"ledgers/{fname}")

    contracts_path = handoff_dir / "contracts" / "contracts_registry.json"
    if reset or not contracts_path.exists():
        atomic_write_lf(contracts_path, json.dumps(STARTER_CONTRACTS_JSON, ensure_ascii=False, indent=2))
        created.append("contracts/contracts_registry.json")

    inv_path = handoff_dir / "00_INVARIANTS.md"
    led_path = handoff_dir / "01_STATE_LEDGER.md"
    if reset or not inv_path.exists():
        atomic_write_lf(inv_path, build_starter_invariants(project_id, slicer_sha, sync_sha))
        created.append("00_INVARIANTS.md")
    if reset or not led_path.exists():
        atomic_write_lf(led_path, STARTER_LEDGER)
        created.append("01_STATE_LEDGER.md")

    if reset:
        for art in (handoff_dir / "artifacts").glob("*.md"):
            art.unlink()

    tok_info = measure_startup_tokens(handoff_dir.parent)
    load_or_update_context_meter(
        handoff_dir,
        int(tok_info["total_startup_tokens"]),
        led_path.read_text(encoding="utf-8"),
        reset_meter=True,
    )
    status = ",".join(created) if created else "already_exists"
    print(f"OK | init={handoff_dir.as_posix()} | updated={status}")
    return 0


def validate_workspace(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    handoff_dir = root / ".handoff"
    inv_path = handoff_dir / "00_INVARIANTS.md"
    led_path = handoff_dir / "01_STATE_LEDGER.md"
    art_dir = handoff_dir / "artifacts"
    arc_dir = handoff_dir / "archive"
    contracts_dir = handoff_dir / "contracts"
    ledgers_dir = handoff_dir / "ledgers"

    missing = [p.name for p in (inv_path, led_path, art_dir, arc_dir, contracts_dir, ledgers_dir) if not p.exists()]
    if missing:
        print(f"ERR | Thiếu cấu trúc .handoff ({', '.join(missing)}); chạy kèm cờ --init")
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    if not args.skip_tool_hash:
        tool_specs = [
            ("code_slicer.py", args.slicer_script, "CODE_SLICER_SCRIPT", args.slicer_sha256),
            ("verify_code_sync.py", args.sync_script, "VERIFY_CODE_SYNC_SCRIPT", args.sync_sha256),
        ]
        for fname, cli_p, env_p, exp_hash in tool_specs:
            tp = resolve_tool_path(root, fname, cli_p, env_p)
            if tp is None or not tp.is_file():
                errors.append(f"Không tìm thấy công cụ bắt buộc {fname}")
            else:
                act_hash = hashlib.sha256(tp.read_bytes()).hexdigest()
                if act_hash != exp_hash:
                    errors.append(
                        f"Lệch mã băm SHA-256 của {tp}: thực tế={act_hash[:16]} != kỳ vọng={exp_hash[:16]}"
                    )

    inv_text = inv_path.read_text(encoding="utf-8")
    inv_lines = len(inv_text.splitlines())
    if inv_lines > MAX_INVARIANTS_LINES:
        errors.append(f"00_INVARIANTS.md vượt trần ({inv_lines}/{MAX_INVARIANTS_LINES} dòng)")

    led_text = led_path.read_text(encoding="utf-8")
    led_lines = len(led_text.splitlines())
    if led_lines > MAX_LEDGER_LINES:
        errors.append(f"01_STATE_LEDGER.md vượt trần ({led_lines}/{MAX_LEDGER_LINES} dòng)")

    for sec in REQUIRED_SECTIONS:
        if sec not in led_text:
            errors.append(f"01_STATE_LEDGER.md thiếu phân mục bắt buộc '{sec}'")

    milestone = extract_field_token(led_text, "Cột mốc đang mở")
    phase = extract_field_token(led_text, "Pha hiện tại")
    session_id = extract_field_token(led_text, "Mã phiên hiện hành")

    if not milestone:
        errors.append("Không đọc được 'Cột mốc đang mở' trong mục 1")
    if phase not in VALID_PHASES:
        errors.append(f"Pha hiện tại '{phase}' không hợp lệ")

    # Cầu chì fix2
    if milestone and milestone != "NONE":
        fix2_audit = art_dir / f"audit_{milestone}_fix2.md"
        if fix2_audit.is_file() and FAIL_STATUS_RE.search(fix2_audit.read_text(encoding="utf-8")):
            if phase != "BLOCKED":
                led_text = trip_circuit_breaker_to_blocked(
                    led_path,
                    led_text,
                    f"Cầu chì {fix2_audit.name} báo FAIL; đã khóa sang BLOCKED chờ người dùng phân xử",
                )
                phase = "BLOCKED"
                errors.append(f"Cầu chì ngắt lỗi kích hoạt tại {fix2_audit.name}: đã chuyển sang BLOCKED")
            else:
                errors.append(f"Sổ cái đang BLOCKED do {fix2_audit.name} báo FAIL")

    if milestone and milestone not in {"M00", "NONE"}:
        if not (arc_dir / "M00" / "manifest.md").exists():
            errors.append(f"Chưa khóa Cổng Kiến trúc M00 (thiếu .handoff/archive/M00/manifest.md); cấm mở {milestone}")
        if PLACEHOLDER_RE.search(inv_text):
            errors.append("00_INVARIANTS.md còn chỗ trống mẫu chưa điền khi đã qua M00")
    elif not args.allow_template and PLACEHOLDER_RE.search(inv_text):
        errors.append("00_INVARIANTS.md còn chỗ trống mẫu chưa điền")

    if milestone and milestone != "NONE":
        if not session_id.startswith(milestone):
            errors.append(f"Mã phiên '{session_id}' lệch với cột mốc đang mở '{milestone}'")
        targets = extract_target_files(led_text)
        if not (1 <= len(targets) <= 5):
            errors.append(f"Số tệp đích được phép chạm ({len(targets)}) nằm ngoài khoảng 1..5")
        strict_phases = {"WORK", "AUDIT", "FIXING", "FINAL_MERGE", "FINAL_AUDIT_A", "FINAL_AUDIT_B", "FINAL_GATE6"}
        if phase in strict_phases and not args.allow_template:
            if any(t.startswith("[") and t.endswith("]") for t in targets):
                errors.append(f"Pha {phase} bắt buộc khóa đường dẫn tệp đích cụ thể thay vì mẫu")

    contracts_reg = contracts_dir / "contracts_registry.json"
    if not contracts_reg.is_file():
        errors.append("Thiếu .handoff/contracts/contracts_registry.json")
    else:
        try:
            json.loads(contracts_reg.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"contracts_registry.json lỗi cú pháp JSON tại L{exc.lineno}: {exc.msg}")

    for req_ledger in LEDGER_TEMPLATES:
        lp = ledgers_dir / req_ledger
        if not lp.exists():
            errors.append(f"Thiếu sổ bắt buộc .handoff/ledgers/{req_ledger}")
        elif req_ledger in EXPECTED_TSV_HEADERS:
            lines = lp.read_text(encoding="utf-8").splitlines()
            exp_cols = EXPECTED_TSV_HEADERS[req_ledger]
            if not lines or [c.strip() for c in lines[0].split("\t")] != exp_cols:
                errors.append(f"Tiêu đề cột {req_ledger} lệch chuẩn: kỳ vọng {exp_cols}")

    for art in sorted(art_dir.glob("*.md")):
        art_txt = art.read_text(encoding="utf-8")
        art_line_count = len(art_txt.splitlines())
        if art_line_count > MAX_ARTIFACT_LINES:
            errors.append(f"{art.name} vượt trần ({art_line_count}/{MAX_ARTIFACT_LINES} dòng)")
        m = ARTIFACT_NAME_RE.match(art.name)
        if not m:
            errors.append(f"Tên tệp '{art.name}' sai quy ước explore|work|audit_<ma>[_partN][_fixN|_layerA|_layerB|_gate6].md")
        elif milestone and milestone != "NONE" and m.group(1) != milestone:
            errors.append(f"Tệp biên bản mồ côi '{art.name}' khác cột mốc đang mở '{milestone}'")
        if NEED_SPLIT_RE.search(art_txt):
            errors.append(f"Subagent báo NEED_SPLIT tại {art.name}: bắt buộc chia nhỏ cột mốc (Mxxa, Mxxb) trên phiên sạch")
        if COMPACTED_INVALID_RE.search(art_txt):
            errors.append(
                f"Subagent bị compact giữa chừng tại {art.name} (COMPACTED_INVALID): vô hiệu hóa kết quả, bắt buộc rollback & chạy lại trên phiên sạch"
            )

    # Đo lường & cưỡng chế Trần Token 170k / 200k / 240k
    tok_info = measure_startup_tokens(root, args.skills_dir)
    always_on_tok = int(tok_info["always_on_tokens"])
    if always_on_tok > MAX_ALWAYS_ON_TOKENS:
        errors.append(f"Quy tắc always_on vượt ngân sách ({always_on_tok}/{MAX_ALWAYS_ON_TOKENS} token)")

    meter = load_or_update_context_meter(
        handoff_dir=handoff_dir,
        startup_tokens=int(tok_info["total_startup_tokens"]),
        ledger_text=led_text,
        add_tokens=args.add_tokens,
        set_tokens=args.set_tokens,
        reset_meter=args.reset_session_meter,
    )
    eff_tok = int(meter["effective_session_tokens"])
    tier = str(meter["ceiling_tier"])

    if eff_tok >= ABSOLUTE_CEILING_TOKENS:
        errors.append(
            f"VƯỢT TRẦN TUYỆT ĐỐI 240K ({eff_tok}/{ABSOLUTE_CEILING_TOKENS} token): "
            f"DỪNG KHẨN CẤP trước ngưỡng auto-compact! Chạy export_session_handoff.py và mở phiên sạch mới ngay."
        )
    elif eff_tok >= HARD_FREEZE_NEW_WORK_TOKENS:
        if not args.handoff_flush and phase not in FLUSH_ALLOWED_PHASES:
            errors.append(
                f"CHẠM TRẦN KHÓA CỨNG 200K ({eff_tok}/{HARD_FREEZE_NEW_WORK_TOKENS} token, pha={phase}): "
                f"CẤM mở hoặc chạy việc mới trên luồng này! Vùng 200k–240k chỉ dùng để đóng gói sổ cái "
                f"(chuyển sang HANDOFF_FLUSH / READY_TO_CLOSE hoặc gọi export_session_handoff.py)."
            )
        else:
            warnings.append(
                f"Đang trong vùng đệm đóng gói 200k–240k ({eff_tok} token): hoàn tất ghi sổ và mở phiên mới ngay."
            )
    elif eff_tok >= SOFT_WARN_TOKENS:
        warnings.append(
            f"Cảnh báo tiệm cận trần 200k ({eff_tok}/{HARD_FREEZE_NEW_WORK_TOKENS} token): "
            f"không mở rộng phạm vi, chuẩn bị đóng cột mốc hiện tại."
        )

    if args.token_report:
        print("=== BÁO CÁO NGÂN SÁCH NGỮ CẢNH CODE (TRẦN CỨNG 200K - ĐỆM ĐÓNG GÓI 240K) ===")
        for group_label, key in (
            ("ALWAYS_ON (GEMINI.md + always_on rules)", "always_on_items"),
            ("GLOB RULES POINTERS", "glob_rule_items"),
            ("SUBAGENTS METADATA", "agent_items"),
            ("SKILLS YAML FRONTMATTER", "skill_items"),
        ):
            items = tok_info[key]
            print(f"[{group_label}] ({len(items)} mục)")
            for path_str, chars, toks in items[:15]:
                print(f"  - {path_str}: {chars} ký tự (~{toks} token)")
            if len(items) > 15:
                print(f"  ... và {len(items) - 15} mục khác")
        print(
            f"TOKEN ĐẦU PHIÊN: {tok_info['total_startup_tokens']} tok "
            f"(always_on={always_on_tok}/{MAX_ALWAYS_ON_TOKENS}) | "
            f"PHIÊN HIỆN TẠI: {eff_tok} tok | TRẠNG THÁI: {tier} "
            f"[Warn={SOFT_WARN_TOKENS}, FreezeNewWork={HARD_FREEZE_NEW_WORK_TOKENS}, AbortCeiling={ABSOLUTE_CEILING_TOKENS}]"
        )

    for w in warnings:
        print(f"WARN | {w}")

    if errors:
        for err in errors:
            print(f"ERR | {err}")
        return 3 if eff_tok >= ABSOLUTE_CEILING_TOKENS else (2 if eff_tok >= HARD_FREEZE_NEW_WORK_TOKENS else 1)

    if not args.quiet_ok:
        print(
            f"OK | milestone={milestone} | phase={phase} | "
            f"session_tok={eff_tok}/{HARD_FREEZE_NEW_WORK_TOKENS} (max={ABSOLUTE_CEILING_TOKENS}, tier={tier}) | "
            f"inv={inv_lines}/{MAX_INVARIANTS_LINES}L | ledger={led_lines}/{MAX_LEDGER_LINES}L"
        )
    return 0


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(
        description="Kiểm tra sổ cái .handoff/ cho Code & cưỡng chế trần cứng 200k–240k token trước compact"
    )
    parser.add_argument("--root", default=".", help="Thư mục gốc dự án")
    parser.add_argument("--init", action="store_true", help="Khởi tạo cấu trúc .handoff nếu chưa có")
    parser.add_argument("--reset", action="store_true", help="Đặt lại sổ cái sạch về M00")
    parser.add_argument("--project-id", default="APP_CODE_PROJECT", help="Mã dự án khởi tạo")
    parser.add_argument("--skills-dir", default="", help="Ghi đè thư mục skills khi đo token")
    parser.add_argument("--slicer-script", default="", help="Ghi đè đường dẫn code_slicer.py")
    parser.add_argument("--sync-script", default="", help="Ghi đè đường dẫn verify_code_sync.py")
    parser.add_argument("--slicer-sha256", default=DEFAULT_CODE_SLICER_SHA256, help="SHA-256 kỳ vọng của code_slicer.py")
    parser.add_argument("--sync-sha256", default=DEFAULT_VERIFY_SYNC_SHA256, help="SHA-256 kỳ vọng của verify_code_sync.py")
    parser.add_argument("--skip-tool-hash", action="store_true", help="Bỏ qua kiểm tra SHA-256 công cụ")
    parser.add_argument("--allow-template", action="store_true", help="Cho phép chỗ trống mẫu khi đang ở M00")
    parser.add_argument("--handoff-flush", action="store_true", help="Cho phép chạy thao tác đóng gói bàn giao trong dải 200k–240k")
    parser.add_argument("--add-tokens", type=int, default=0, help="Cộng thêm token tiêu thụ vào bộ đếm phiên")
    parser.add_argument("--set-tokens", type=int, default=None, help="Đặt trực tiếp tổng token phiên hiện tại")
    parser.add_argument("--reset-session-meter", action="store_true", help="Đặt lại bộ đếm token phiên khi mở phiên chat mới")
    parser.add_argument("--quiet-ok", action="store_true", help="Chỉ in khi có lỗi hoặc cảnh báo")
    parser.add_argument("--token-report", action="store_true", help="In chi tiết bảng đo ngân sách token")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.init or args.reset:
        return init_workspace(
            handoff_dir=root / ".handoff",
            project_id=args.project_id,
            reset=args.reset,
            slicer_sha=args.slicer_sha256,
            sync_sha=args.sync_sha256,
        )
    return validate_workspace(args)


if __name__ == "__main__":
    raise SystemExit(main())
