---
trigger: glob
globs: "**/.handoff/**"
description: Quy tắc đóng gói cột mốc code, làm mới symbol_map.json, xử lý NEED_SPLIT/COMPACTED_INVALID và cầu chì BLOCKED
---

# QUY TẮC ĐÓNG GÓI CỘT MỐC CODE & CẦU CHÌ NGẮT LỖI

## 1. Chu trình kiểm chứng tất định 0-token LLM
- Mọi lệnh Python chạy với `python3 -X utf8` cùng `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`.
- Bộ công cụ chuẩn đặt tại `/shared/user/.gemini/code_handoff_tools/` (hoặc `.agents/scripts/` trong repo).
- Trạm 1 (`M00`): Chạy `verify_code_gate.py --root <REPO> --gate plan` và chỉ gọi `close_code_milestone.py --root <REPO> --milestone M00 --user-approved` sau khi duyệt kế hoạch & hợp đồng.
- Trạm 2 (`M01..M98`): Chạy `close_code_milestone.py --root <REPO> --milestone <MA>` (tự động kiểm `code_handoff_guard.py enforce --rollback`, `verify_code_sync.py`, tái lập `symbol_map.json` và chụp snapshot mới).
- Trạm 3 (`M99`): Phải có bản chụp `.handoff/archive/c6_backups/truoc_c6_manifest.json` (`export_session_handoff.py --c6-backup`) và đủ 3 biên bản `PASS` từ 3 phiên subagent độc lập (`audit_M99_layerA.md`, `audit_M99_layerB.md`, `audit_M99_gate6.md`).

## 2. Xử lý `NEED_SPLIT`, `COMPACTED_INVALID`, Trần 200k và Cầu chì `BLOCKED`
- Nếu biên bản có `Kết quả: NEED_SPLIT` hoặc `COMPACTED_INVALID`: tự động chặn đóng mốc; Orchestrator rollback qua `code_handoff_guard.py enforce --rollback`, chia cột mốc thành `M01a`, `M01b` và mở subagent sạch mới.
- Nếu `audit_<MA>_fix2.md` báo `FAIL`: `check_code_handoff.py` tự động chuyển sổ cái sang `BLOCKED` để dừng vòng lặp sửa mù, trình người dùng quyết định.
- Khi `context_meter.json` đạt `>= 200.000 token`: `close_code_milestone.py` tự động chuyển cột mốc kế sang `HANDOFF_FLUSH` và xuất `.handoff/SESSION_HANDOFF_BUNDLE.md` để sang phiên mới.
