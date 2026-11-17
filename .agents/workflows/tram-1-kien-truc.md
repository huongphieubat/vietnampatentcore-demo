---
description: Chạy Trạm 1 (M00) lập chỉ mục ký hiệu symbol_map.json, khóa hợp đồng liên tệp contracts_registry.json và phản biện kế hoạch trước khi code
---

Thực hiện Trạm 1 (Cổng Kiến trúc & Hợp đồng `M00`) cho yêu cầu build app / code hiện tại, TUYỆT ĐỐI chưa gọi `code_worker` viết code:
1. Chạy `python3 -X utf8 .agents/scripts/check_code_handoff.py --allow-template --token-report` xác nhận sổ cái đang ở `M00` (`PLAN_EXPLORE`, dưới trần 200k token) và chụp ảnh `python3 -X utf8 .agents/scripts/code_handoff_guard.py snapshot`.
2. Chạy `python3 -X utf8 .agents/scripts/code_slicer.py index --root .` để sinh `.handoff/contracts/symbol_map.json`, nhận diện toàn bộ tệp `MONOLITH_SLICE_ONLY`.
3. Gọi subagent `code_explorer` (ngữ cảnh sạch, `<= 15` lượt công cụ, đọc lát `<= 150–200 dòng/lượt` qua `code_slicer.py`) khảo sát kiến trúc hiện hữu, xuất `.handoff/artifacts/explore_M00.md` (`<= 300 dòng`) và điền các hợp đồng cốt lõi vào `.handoff/contracts/contracts_registry.json`. Chạy `code_handoff_guard.py enforce --rollback`.
4. Lập `.handoff/ledgers/plan_backbone.md` chia từng cột mốc `M01..M98` theo đúng 01 module/feature dọc khép kín (`1..5 tệp đích`, đầu vào `<= 1.200 dòng`), chuyển pha sang `PLAN_AUDIT`.
5. Gọi subagent `code_auditor` mới (`PLAN_AUDIT`, `<= 20` lượt công cụ, trả về `<= 350 token`) phản biện kiến trúc, kiểm va chạm tệp đích và tính đầy đủ hợp đồng -> xuất `.handoff/artifacts/audit_M00.md`. Nếu đạt `PASS`, chuyển pha sang `PLAN_APPROVAL`, trình người dùng duyệt trước khi điền `00_INVARIANTS.md` và chạy `close_code_milestone.py --milestone M00 --user-approved`.
