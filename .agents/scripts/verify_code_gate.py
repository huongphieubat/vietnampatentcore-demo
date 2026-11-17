#!/usr/bin/env python3
"""Kiểm chứng tự động 3 Trạm chất lượng cho Build App & Code (plan, milestone, final) kèm kiểm đồng bộ code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_TOOLS_DIR = os.environ.get("CODE_HANDOFF_TOOLS_DIR", "/shared/user/.gemini/code_handoff_tools")

PASS_STATUS_RE = re.compile(
    r"(?im)^\s*(?:[-*]|\d+\.)?\s*\*{0,2}(?:Kết quả|Trạng thái|Status)\*{0,2}\s*:\s*\*{0,2}PASS\b"
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


def extract_field_token(text: str, label: str) -> str:
    m = re.search(rf"(?m)^-\s*{re.escape(label)}\s*:\s*([A-Za-z0-9_]+)", text)
    return m.group(1) if m else ""


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
                if val and not (val.startswith("[") and val.endswith("]")):
                    targets.append(Path(val).as_posix().lstrip("./"))
            elif line.strip().startswith(("-", "## ")):
                break
    return targets


def check_audit_pass(audit_path: Path) -> str | None:
    if not audit_path.is_file():
        return f"Thiếu biên bản kiểm toán độc lập {audit_path.name}"
    txt = audit_path.read_text(encoding="utf-8")
    if NEED_SPLIT_RE.search(txt):
        return f"Biên bản {audit_path.name} đang mang mã NEED_SPLIT (bắt buộc chia nhỏ module cho subagent mới)"
    if COMPACTED_INVALID_RE.search(txt):
        return f"Biên bản {audit_path.name} bị vô hiệu do nén ngữ cảnh (COMPACTED_INVALID); bắt buộc chạy lại trên phiên sạch"
    if FAIL_STATUS_RE.search(txt):
        return f"Biên bản {audit_path.name} đang mang kết quả FAIL"
    if not PASS_STATUS_RE.search(txt):
        return f"Biên bản {audit_path.name} chưa có dòng 'Kết quả: PASS' hoặc 'Trạng thái: PASS'"
    return None


def latest_round_artifact(art_dir: Path, prefix: str, milestone: str, suffix: str = "") -> Path:
    tail = f"_{suffix}" if suffix else ""
    fixes = sorted(
        art_dir.glob(f"{prefix}_{milestone}{tail}_fix*.md"),
        key=lambda p: int(m.group(1)) if (m := re.search(r"_fix(\d+)\.md$", p.name)) else 0,
    )
    return fixes[-1] if fixes else (art_dir / f"{prefix}_{milestone}{tail}.md")


def run_base_checks(root: Path, allow_template: bool, handoff_flush: bool, extra_check_args: list[str]) -> list[str]:
    errors: list[str] = []
    checker = resolve_sibling_script(root, "check_code_handoff.py")
    cmd_args = [str(checker), "--root", str(root), "--quiet-ok"]
    if allow_template:
        cmd_args.append("--allow-template")
    if handoff_flush:
        cmd_args.append("--handoff-flush")
    cmd_args.extend(extra_check_args)
    proc = run_py(cmd_args, root)
    if proc.returncode != 0:
        for ln in (proc.stdout + "\n" + proc.stderr).splitlines():
            if ln.strip() and not ln.strip().startswith("WARN |"):
                errors.append(ln.strip())

    guard = resolve_sibling_script(root, "code_handoff_guard.py")
    if guard.is_file():
        g_proc = run_py([str(guard), "enforce", "--root", str(root), "--rollback", "--quiet-ok"], root)
        if g_proc.returncode != 0:
            for ln in (g_proc.stdout + "\n" + g_proc.stderr).splitlines():
                if ln.strip():
                    errors.append(ln.strip())
    return errors


def verify_plan_gate(root: Path, allow_template: bool, extra_check_args: list[str]) -> int:
    errors = run_base_checks(root, allow_template=allow_template, handoff_flush=True, extra_check_args=extra_check_args)
    handoff = root / ".handoff"
    art_dir = handoff / "artifacts"
    bb_path = handoff / "ledgers" / "plan_backbone.md"
    smap_path = handoff / "contracts" / "symbol_map.json"
    creg_path = handoff / "contracts" / "contracts_registry.json"

    if not smap_path.is_file():
        errors.append("Thiếu .handoff/contracts/symbol_map.json (chạy code_slicer.py index trước)")
    if not creg_path.is_file():
        errors.append("Thiếu .handoff/contracts/contracts_registry.json")

    if not (art_dir / "explore_M00.md").is_file():
        errors.append("Thiếu biên bản khảo sát kiến trúc .handoff/artifacts/explore_M00.md")
    audit_err = check_audit_pass(art_dir / "audit_M00.md")
    if audit_err:
        errors.append(audit_err)

    if not bb_path.is_file():
        errors.append("Thiếu .handoff/ledgers/plan_backbone.md")
    else:
        bb_text = bb_path.read_text(encoding="utf-8")
        if not allow_template and ("[CHUA_LAP_KE_HOACH]" in bb_text or "[Điền tên module/feature]" in bb_text):
            errors.append("plan_backbone.md vẫn còn chỗ trống mẫu chưa điền")
        data_rows = [
            ln for ln in bb_text.splitlines()
            if ln.strip().startswith("|") and not re.match(r"^\|[\s:-]+\|", ln.strip())
        ]
        if len(data_rows) < 2:
            errors.append("plan_backbone.md phải có tối thiểu 1 dòng cột mốc ngoài dòng tiêu đề")

    if errors:
        for e in errors:
            print(f"ERR | GATE1_PLAN | {e}")
        return 1
    print("GATE1_OK | symbol_map.json, contracts_registry.json, plan_backbone.md và audit_M00.md hợp lệ")
    return 0


def verify_milestone_gate(
    root: Path,
    expected_ms: str,
    allow_shrink: bool,
    run_tests: bool,
    extra_check_args: list[str],
) -> int:
    errors = run_base_checks(root, allow_template=False, handoff_flush=True, extra_check_args=extra_check_args)
    handoff = root / ".handoff"
    led_text = (handoff / "01_STATE_LEDGER.md").read_text(encoding="utf-8")
    milestone = expected_ms or extract_field_token(led_text, "Cột mốc đang mở")
    targets = extract_targets(led_text)
    art_dir = handoff / "artifacts"

    work_file = latest_round_artifact(art_dir, "work", milestone)
    if not work_file.is_file():
        errors.append(f"Thiếu biên bản thực thi {work_file.name}")

    layer_a = latest_round_artifact(art_dir, "audit", milestone, "layerA")
    layer_b = latest_round_artifact(art_dir, "audit", milestone, "layerB")
    audit_names: list[str] = []
    if layer_a.is_file() or layer_b.is_file():
        for lf in (layer_a, layer_b):
            err = check_audit_pass(lf)
            if err:
                errors.append(err)
            else:
                audit_names.append(lf.name)
    else:
        audit_file = latest_round_artifact(art_dir, "audit", milestone)
        audit_err = check_audit_pass(audit_file)
        if audit_err:
            errors.append(audit_err)
        else:
            audit_names.append(audit_file.name)

    for t in targets:
        tp = root / t
        if not tp.exists():
            errors.append(f"Tệp đích chưa được tạo trên đĩa: {t}")

    sync_tool = resolve_sibling_script(root, "verify_code_sync.py")
    sync_args = [str(sync_tool), "check", "--root", str(root)]
    if allow_shrink:
        sync_args.append("--allow-shrink")
    if run_tests:
        sync_args.append("--run-tests")
    s_proc = run_py(sync_args, root)
    if s_proc.returncode != 0:
        for ln in (s_proc.stdout + "\n" + s_proc.stderr).splitlines()[:10]:
            if ln.strip():
                errors.append(f"verify_code_sync: {ln.strip()}")

    if errors:
        for e in errors:
            print(f"ERR | GATE2_MILESTONE | {e}")
        return 1
    print(f"GATE2_OK | milestone={milestone} | audit={','.join(audit_names)} | sync=clean")
    return 0


def verify_final_gate(
    root: Path,
    allow_shrink: bool,
    extra_check_args: list[str],
) -> int:
    errors = run_base_checks(root, allow_template=False, handoff_flush=True, extra_check_args=extra_check_args)
    handoff = root / ".handoff"
    art_dir = handoff / "artifacts"
    c6_dir = handoff / "archive" / "c6_backups"
    led_text = (handoff / "01_STATE_LEDGER.md").read_text(encoding="utf-8")
    targets = extract_targets(led_text)

    if not targets:
        errors.append("Chưa khai báo danh sách tệp thành phẩm cuối trong M99")

    # CẤM gộp kiểm toán: bắt buộc 3 subagent độc lập SYNC (layerA), LOGIC/SEC (layerB), BUILD/UI (gate6)
    for req_audit in ("audit_M99_layerA.md", "audit_M99_layerB.md", "audit_M99_gate6.md"):
        err = check_audit_pass(art_dir / req_audit)
        if err:
            errors.append(err)

    pre_c6_manifest = c6_dir / "truoc_c6_manifest.json"
    if not pre_c6_manifest.is_file():
        errors.append("Thiếu bản chụp đối chứng trước Cổng 6 tại .handoff/archive/c6_backups/truoc_c6_manifest.json")

    hashes: list[str] = []
    for t in targets:
        tp = root / t
        if not tp.is_file():
            errors.append(f"Thiếu tệp thành phẩm cuối trên đĩa: {t}")
            continue
        hashes.append(f"{tp.name}:{hashlib.sha256(tp.read_bytes()).hexdigest()[:16]}")

    sync_tool = resolve_sibling_script(root, "verify_code_sync.py")
    sync_args = [str(sync_tool), "check", "--root", str(root), "--run-tests"]
    if allow_shrink:
        sync_args.append("--allow-shrink")
    s_proc = run_py(sync_args, root)
    if s_proc.returncode != 0:
        for ln in (s_proc.stdout + "\n" + s_proc.stderr).splitlines()[:12]:
            if ln.strip():
                errors.append(f"verify_code_sync(final): {ln.strip()}")

    if errors:
        for e in errors:
            print(f"ERR | GATE3_FINAL | {e}")
        return 1
    print(f"GATE3_OK | sync_and_tests=clean | sha256={','.join(hashes)}")
    return 0


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Kiểm chứng 3 trạm chất lượng cho Build App & Code")
    parser.add_argument("--root", default=".", help="Thư mục gốc dự án")
    parser.add_argument("--gate", required=True, choices=("plan", "milestone", "final"))
    parser.add_argument("--milestone", default="", help="Mã cột mốc kỳ vọng")
    parser.add_argument("--allow-shrink", action="store_true", help="Cho phép giảm >20% dòng khi chủ đích xóa code")
    parser.add_argument("--run-tests", action="store_true", help="Chạy kèm lệnh test ở cổng milestone")
    parser.add_argument("--skip-tool-hash", action="store_true", help="Bỏ qua kiểm tra SHA-256 công cụ")
    parser.add_argument("--allow-template", action="store_true", help="Cho phép mẫu khi kiểm thử M00")
    args = parser.parse_args()

    extra = ["--skip-tool-hash"] if args.skip_tool_hash else []
    root = Path(args.root).resolve()
    if args.gate == "plan":
        return verify_plan_gate(root, args.allow_template, extra)
    if args.gate == "milestone":
        return verify_milestone_gate(root, args.milestone, args.allow_shrink, args.run_tests, extra)
    return verify_final_gate(root, args.allow_shrink, extra)


if __name__ == "__main__":
    raise SystemExit(main())
