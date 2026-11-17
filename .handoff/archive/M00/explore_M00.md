# BIÊN BẢN KHẢO SÁT KIẾN TRÚC ĐỒNG BỘ DEMO (explore_M00)

- **Kết quả**: PASS
- **Trạng thái kho đích**: `huongphieubat/vietnampatentcore-demo` đang ở mốc `98.380` hồ sơ (`889/1024` kỳ), `0.0 MB` lưu trữ PDF nhị phân, đã khóa `symbol_map.json` (`5` tệp monolith HTML) và `contracts_registry.json`.
- **Tệp `MONOLITH_SLICE_ONLY` (`5` tệp)**: `index.html`, `admin.html`, `admin/index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html`.
- **Chiến lược đồng bộ 1-1 chống vi phạm phạm vi `<= 5` tệp/mốc**:
  1. `M01` (`4` tệp): Đồng bộ `catalog/manifest.json`, `catalog/shard_0.json`, `catalog/shard_1.json`, `catalog/shard_2.json` sau khi `vietnam-patent-db` hoàn tất làm sạch `B04`/`B05`/`B06` và kéo điểm chốt Marathon `#44015228202` mới nhất.
  2. `M02` (`3` tệp): Đồng bộ `catalog/shard_3.json`, `catalog/shard_4.json`, `catalog/shard_5.json`.
  3. `M03` (`5` tệp): Đồng bộ `index.html`, `admin.html` (`-> admin/index.html`), `vietnampatentcore_fullpage_embed.html` (`-> full-page-embed/index.html`), kiểm chứng `verify_code_sync.py check` đạt `SYNC_OK`.
  4. `M99` (`3` tệp): Nghiệm thu 3 lớp độc lập khi hoàn tất `1024/1024` kỳ.
