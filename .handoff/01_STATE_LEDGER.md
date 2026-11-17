# SỔ CÁI TRẠNG THÁI ĐIỀU PHỐI CODE (01_STATE_LEDGER)

## 1. Con trỏ điều phối hiện thời
- Cột mốc đang mở: NONE
- Pha hiện tại: READY_TO_DELIVER
- Dung lượng ngữ cảnh gần nhất: 34000
- Trạng thái trần token: GREEN_UNDER_170K
- Hành động kế tiếp duy nhất: Trình bày báo cáo đồng bộ thành phẩm & SHA-256 cho người dùng

## 2. Đặc tả cột mốc đang thực thi
- Mã phiên hiện hành: NONE
- Mục tiêu cột mốc: Đã hoàn tất toàn bộ hàng đợi cột mốc
- Tệp đích được phép chạm (giới hạn từ 1 đến 5 tệp):
  - .handoff/01_STATE_LEDGER.md

## 3. Sổ quyết định kiến trúc đã khóa (Locked Decisions)
- D01: Duy trì đồng bộ 1-1 catalog/manifest.json, catalog/shard_0..5.json, index.html, admin.html (-> admin/index.html) và vietnampatentcore_fullpage_embed.html (-> full-page-embed/index.html) từ vietnam-patent-db.

## 4. Hàng đợi cột mốc kế tiếp
- Không còn cột mốc chờ.

## 5. Chỉ mục cột mốc đã đóng gói
- Tiền-M00 (Phiên hiện tại): Đồng bộ `45616f4` (96.186 hồ sơ, 880/1024 kỳ) và nâng cấp lên 98.380 hồ sơ (889/1024 kỳ từ `7a05dc2`).
- [x] M00: Khóa kế hoạch đồng bộ 1-1 danh mục 6 shard và 5 tệp HTML từ vietnam-patent-db sang vietnampatentcore-demo sau khi làm sạch dữ liệu Giai đoạn 5 và kéo điểm chốt Marathon #44015228202 -> Tệp: .handoff/ledgers/plan_backbone.md, .handoff/contracts/contracts_registry.json, .handoff/ledgers/decision_log.tsv -> Lưu: .handoff/archive/M00/
- [x] M01: Đồng bộ `catalog/manifest.json` & `catalog/shard_0..2.json` từ `vietnam-patent-db` -> Tệp: catalog/manifest.json, catalog/shard_0.json, catalog/shard_1.json, catalog/shard_2.json -> Lưu: .handoff/archive/M01/
- [x] M02: Đồng bộ `catalog/shard_3..5.json` từ `vietnam-patent-db` -> Tệp: catalog/shard_3.json, catalog/shard_4.json, catalog/shard_5.json -> Lưu: .handoff/archive/M02/
- [x] M03: Đồng bộ 3 tệp gốc HTML + 2 bản sao thư mục con từ `vietnam-patent-db` -> Tệp: index.html, admin.html, admin/index.html, vietnampatentcore_fullpage_embed.html, full-page-embed/index.html -> Lưu: .handoff/archive/M03/
- [x] M04: Đồng bộ 1-1 `catalog/manifest.json` và `catalog/shard_0..2.json` bản sạch `B10`..`B13` từ `vietnam-patent-db`. -> Tệp: catalog/manifest.json, catalog/shard_0.json, catalog/shard_1.json, catalog/shard_2.json -> Lưu: .handoff/archive/M04/
- [x] M05: Đồng bộ 1-1 `catalog/shard_3..5.json` bản sạch `B10`..`B12` từ `vietnam-patent-db` -> Tệp: catalog/shard_3.json, catalog/shard_4.json, catalog/shard_5.json -> Lưu: .handoff/archive/M05/
- [x] M06: Đồng bộ 1-1 5 tệp HTML (`index.html`, `admin.html`, `admin/index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html`) bản sạch `B13` từ `vietnam-patent-db` -> Tệp: index.html, admin.html, admin/index.html, vietnampatentcore_fullpage_embed.html, full-page-embed/index.html -> Lưu: .handoff/archive/M06/
- [x] M99: Nghiệm thu lại 3 lớp độc lập (`CODE_AUDITOR_A`, `CODE_AUDITOR_B`, `CODE_AUDITOR_C6`) -> Tệp: catalog/manifest.json, index.html, admin.html, vietnampatentcore_fullpage_embed.html, full-page-embed/index.html -> Lưu: .handoff/archive/M99/
