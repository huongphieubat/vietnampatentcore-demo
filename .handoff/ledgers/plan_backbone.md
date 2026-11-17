# XƯƠNG SỐNG KIẾN TRÚC & PHÂN RÃ MODULE CHỐNG MẤT ĐỒNG BỘ (M00)

Trạng thái: DA_LAP_KE_HOACH_DONG_BO_DEMO

| Mã mốc | Module / Tính năng dọc khép kín | Hợp đồng liên tệp khóa cứng (API / DB / Symbol / DOM ID) | Rủi ro đồng bộ & Kiểm thử tất định | Tệp đích (1..5 tệp) |
|---|---|---|---|---|
| M01 | Đồng bộ danh mục tĩnh `catalog/manifest.json` + `catalog/shard_0..2.json` sạch lỗi Giai đoạn 5 từ `vietnam-patent-db` | `catalog/manifest.json` (`schema_version=2026.8-compact-v1`, `binary_pdf_storage_mb=0.0`) | Kiểm khớp SHA-256 1-1 `manifest.json` & `shard_0..2.json` với nguồn `vietnam-patent-db` | `catalog/manifest.json`, `catalog/shard_0.json`, `catalog/shard_1.json`, `catalog/shard_2.json` |
| M02 | Đồng bộ nốt `catalog/shard_3..5.json` sạch lỗi Giai đoạn 5 từ `vietnam-patent-db` | `catalog/shard_3..5.json` khớp `manifest.json` | Kiểm khớp SHA-256 1-1 `shard_3..5.json` và tổng số dòng hồ sơ trên toàn 6 shard | `catalog/shard_3.json`, `catalog/shard_4.json`, `catalog/shard_5.json` |
| M03 | Đồng bộ 5 tệp giao diện HTML (`index.html`, `admin.html`, `admin/index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html`) | DOM IDs & JS handlers trong `contracts_registry.json` | `verify_code_sync.py check` đạt `SYNC_OK` và khớp SHA-256 1-1 với nguồn | `index.html`, `admin.html`, `admin/index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html` |
| M99 | Nghiệm thu thành phẩm tách 3 lớp độc lập (`CODE_AUDITOR_A`, `CODE_AUDITOR_B`, `CODE_AUDITOR_C6`) khi hoàn tất 1024/1024 kỳ | Toàn bộ `contracts_registry.json` (`0 MB` binary PDF) | `export_session_handoff.py --c6-backup` + 3 biên bản `PASS` độc lập | `index.html`, `admin.html`, `vietnampatentcore_fullpage_embed.html` |
