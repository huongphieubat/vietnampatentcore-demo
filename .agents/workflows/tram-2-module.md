---
description: Thực thi và kiểm toán độc lập cột mốc module hiện hành tại Trạm 2 kèm khóa 1..5 tệp đích, kiểm đồng bộ hợp đồng và khóa trần 200k token
---

Thực hiện Trạm 2 cho cột mốc đang mở trong `.handoff/01_STATE_LEDGER.md`:
1. Kiểm tra ngân sách bằng `python3 -X utf8 .agents/scripts/check_code_handoff.py`: nếu phiên đã chạm `>= 200.000 token`, DỪNG NGAY việc mở module mới, chạy `export_session_handoff.py` và đề nghị chuyển phiên sạch.
2. Nếu dưới 200k token: khóa danh sách `1..5 tệp đích` cụ thể vào mục 2 của `01_STATE_LEDGER.md`, chuyển pha sang `WORK` và chạy `python3 -X utf8 .agents/scripts/code_handoff_guard.py snapshot`.
3. Gọi phiên subagent `code_worker` ngữ cảnh sạch mới (`<= 25` lượt công cụ, đọc lát qua `code_slicer.py slice`, cấm cắt cụt code AI) thực thi module bám sát `contracts_registry.json`, chạy `verify_code_sync.py check` đạt `SYNC_OK` và xuất `work_<MA>.md` (`<= 300 dòng`). Chạy ngay `code_handoff_guard.py enforce --rollback` và `check_code_handoff.py`.
4. Nếu subagent trả `NEED_SPLIT` hoặc `COMPACTED_INVALID`: hoàn nguyên bằng `code_handoff_guard.py enforce --rollback`, chia nhỏ cột mốc thành `Mxxa`, `Mxxb` và chạy trên phiên subagent sạch mới.
5. Chuyển pha sang `AUDIT`, chụp lại snapshot và gọi phiên subagent `code_auditor` mới kiểm toán độc lập -> xuất `audit_<MA>.md`. Nếu `PASS`, chạy `python3 -X utf8 .agents/scripts/close_code_milestone.py --milestone <MA>` (tự động tái lập `symbol_map.json` cho mốc kế tiếp). Nếu `FAIL` quá 2 vòng (`_fix2`), sổ cái tự khóa sang `BLOCKED`.
