---
description: Chạy Trạm 3 (M99) hợp nhất thành phẩm và kiểm toán độc lập tách 3 lớp (CODE_AUDITOR_A đồng bộ, CODE_AUDITOR_B logic/bảo mật, CODE_AUDITOR_C6 build/UI)
---

Thực hiện Trạm 3 (`M99`) nghiệm thu thành phẩm code cuối cùng (TUYỆT ĐỐI CẤM gộp 3 lớp kiểm toán vào chung 1 subagent):
1. Ở pha `FINAL_MERGE`, chạy `code_handoff_guard.py snapshot`, gọi phiên `code_worker` sạch tích hợp toàn cục, chạy bộ test & `verify_code_sync.py check --run-tests`, xuất `work_M99.md`, rồi chạy `code_handoff_guard.py enforce --rollback`.
2. Tạo bản chụp đối chứng trước Cổng 6 bằng `python3 -X utf8 .agents/scripts/export_session_handoff.py --root . --c6-backup --reason "M99 Pre-Gate6 Snapshot"`.
3. Chuyển sang `FINAL_AUDIT_A`, gọi phiên `code_auditor` độc lập (`CODE_AUDITOR_A`) kiểm **Đồng bộ hợp đồng liên tệp, imports, API/DB/DOM bindings & chống cắt cụt code** -> xuất `.handoff/artifacts/audit_M99_layerA.md`.
4. Chuyển sang `FINAL_AUDIT_B`, gọi phiên `code_auditor` độc lập mới (`CODE_AUDITOR_B`) kiểm **Logic nghiệp vụ, race condition, bảo mật (XSS/SQLi/Auth/Secrets) & độ phủ test** -> xuất `.handoff/artifacts/audit_M99_layerB.md`.
5. Chuyển sang `FINAL_GATE6`, gọi phiên `code_auditor` độc lập mới (`CODE_AUDITOR_C6`) kiểm **Build/Bundle/UI thành phẩm sạch, không còn xung đột merge hay log rác** -> xuất `.handoff/artifacts/audit_M99_gate6.md`.
6. Chạy `python3 -X utf8 .agents/scripts/close_code_milestone.py --milestone M99` xác thực cả 3 biên bản và SHA-256 xuất xưởng.
