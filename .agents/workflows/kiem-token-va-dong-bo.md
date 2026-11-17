---
description: Đo lường ngân sách trần 200k-240k token, kiểm tra đồng bộ hợp đồng code (verify_code_sync.py) và chỉ mục ký hiệu hiện thời
---

Chạy liên tiếp 2 lệnh kiểm tra tất định qua `run_command`:
1. `python3 -X utf8 .agents/scripts/check_code_handoff.py --root . --allow-template --token-report` (hoặc gọi từ `/shared/user/.gemini/code_handoff_tools/check_code_handoff.py`)
2. `python3 -X utf8 .agents/scripts/verify_code_sync.py check --root .`

Báo cáo gọn trong 5 dòng: cột mốc & pha hiện tại, số token phiên so với ngưỡng khóa việc mới `200.000 token` (trần tuyệt đối `240.000 token`), kết quả đồng bộ hợp đồng/cú pháp (`SYNC_OK` hay danh sách lỗi), danh sách tệp `MONOLITH_SLICE_ONLY` và hành động kế tiếp (nếu `>= 200k token`, xuất ngay `SESSION_HANDOFF_BUNDLE.md`).
