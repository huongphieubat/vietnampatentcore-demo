# RÀNG BUỘC BẤT BIẾN KIẾN TRÚC & ĐỒNG BỘ CODE (00_INVARIANTS)

- Mã dự án: VIETNAMPATENTCORE_DEMO
- Phiên bản quy chuẩn: v1.0-code-antigravity
- Ngày khóa chuẩn: 2026-11-16
- Quyền chỉnh sửa: CẤM mọi subagent tự ý sửa tệp này; Orchestrator chỉ cập nhật khi duyệt Cổng Kiến trúc (M00) hoặc đổi yêu cầu.

## 1. Mục tiêu cốt lõi & Ranh giới phạm vi
- Đích đến sản phẩm: Bản phân phối GitHub Pages tĩnh (Static Portal, Admin Demo, Full-Page Embed & Sharded Catalog) đồng bộ 1-1 từ repo nguồn `huongphieubat/vietnam-patent-db`.
- Thành phẩm bàn giao chính thức: `index.html`, `admin.html`, `vietnampatentcore_fullpage_embed.html`, `admin/index.html`, `full-page-embed/index.html`, `catalog/manifest.json` & `catalog/shard_*.json`.
- Ngoài phạm vi (Out of Scope): `/shared/user/.gemini/handoff_tools/`, `/shared/user/.gemini/skills/` (chỉ đọc, bảo toàn hệ thống SHTT).

## 2. Ngân sách Ngữ cảnh Khóa cứng Trần 200k–240k Token (Anti-Compaction)
- Cảnh báo chuẩn bị chốt mốc: `170.000 token`
- Khóa cứng ngắt việc mới: `200.000 token` (từ 200k–240k chỉ được đóng gói sổ cái, hợp đồng và xuất `SESSION_HANDOFF_BUNDLE.md`)
- Trần ngắt cầu chì tuyệt đối: `240.000 token` (trước ngưỡng auto-compact ~256k của hệ thống)
- Ngân sách mỗi Subagent: Ngữ cảnh sạch mới 100%, đọc lát `<= 150–200 dòng/lượt` qua `code_slicer.py` (cả 5 tệp HTML đều là `MONOLITH_SLICE_ONLY` > 4.400 dòng), hủy kết quả nếu nén (`COMPACTED_INVALID`).

## 3. Hằng số Kỹ thuật & Khóa Mã băm Công cụ Đồng bộ
- Công cụ cắt lát ký hiệu: `/shared/user/.gemini/code_handoff_tools/code_slicer.py` (SHA-256: `c5172d7ff9164acbd647307c0b6f699565da41366e6fdaa4e3e6e49439e824da`)
- Công cụ kiểm đồng bộ code: `/shared/user/.gemini/code_handoff_tools/verify_code_sync.py` (SHA-256: `ca4df883616c0cb329fb636e87b1394e650d77cab9c95825fe3cc5a194880b63`)
- Sổ cái hợp đồng liên tệp: `.handoff/contracts/contracts_registry.json` & `.handoff/contracts/symbol_map.json`
- Môi trường chạy lệnh: `python3 -X utf8` với `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`

## 4. Ngăn xếp Công nghệ & Quy ước Bất biến
- Ngôn ngữ / Runtime: Static GitHub Pages (`.nojekyll`), Vanilla HTML5/CSS3/JS + Sharded JSON Catalog (`catalog/`).
- Quy ước đồng bộ: `index.html` <-> `vietnampatentcore_fullpage_embed.html` <-> `full-page-embed/index.html` và `admin.html` <-> `admin/index.html` phải khớp bản xuất từ `vietnam-patent-db`.

## 5. Lằn ranh đỏ Nghiệm thu (Hard Rejection Gates)
1. Vượt trần `200.000 token` mà vẫn mở cột mốc mới thay vì đóng gói bàn giao hoặc đẩy sang subagent sạch.
2. Đọc nguyên văn bất kỳ tệp HTML 400KB nào không qua `code_slicer.py`.
3. Lỗi cú pháp `<script>` nội tuyến trong HTML, lệch DOM ID/JS handler hoặc tụt `> 20%` dòng do cắt cụt code AI.
4. Sửa trực tiếp bản phân phối demo làm lệch khỏi nguồn `vietnam-patent-db` mà không đồng bộ hai chiều.
