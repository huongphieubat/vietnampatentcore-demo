# BIÊN BẢN KIỂM TOÁN ĐỐI KHÁNG LỚP A — TRẠM 3 (`audit_M99_layerA.md`)

- Cột mốc: `M99` (Pha `FINAL_AUDIT_A` — Trạm 3)
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `CODE_AUDITOR_A` (`clean_code_auditor` ngữ cảnh sạch độc lập — Lớp A: Đồng bộ Hợp đồng & Chống Cắt Cụt Code)
- Kết quả: PASS

## 1. Kiểm chứng Tất định `verify_code_sync.py` & Cú pháp `<script>` Nội tuyến

- Lệnh thực thi: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python3 -X utf8 .agents/scripts/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo`
- Kết quả đầu ra: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).
- Kiểm tra độc lập cú pháp JavaScript nội tuyến bằng `node --check` trên cả **5/5 tệp HTML** (`index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html`, `admin.html`, `admin/index.html`): `js_errs = 0`, `truncs = 0` (không có bất kỳ bình luận cắt cụt code `// ... existing code ...`, `# ... rest of code ...`, `/* ... unchanged ... */`, `<!-- ... -->` hay hiện tượng tụt dòng).

## 2. Kiểm tra Đồng bộ Hợp đồng Liên tệp (`contracts_registry.json` & Sharded Catalog)

### 2.1. Ràng buộc DOM IDs & JS Handlers trên 5/5 tệp HTML
- Nhóm Portal & Embed (`index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html` — `5.059` dòng, `394.047` bytes):
  - Đủ 5/5 DOM IDs: `#siteHeader`, `#brandHomeLink`, `#navBtn-search`, `#navBtn-assistant`, `#navBtn-insights` (`miss_ids = []`).
  - Đủ 3/3 JS handlers: `rebuildPatentLookupMaps()` (`L2656`), `findDossierByApp(appNo)` (`L2668`), `hydrateCatalogShardRows(rows, targetList, seenApps)` (`L2743`) (`miss_fns = []`).
- Nhóm Admin (`admin.html`, `admin/index.html` — `4.454` dòng, `410.640` bytes):
  - Đủ 4/4 DOM IDs: `#headerSyncBadge`, `#kpiContainer`, `#tabBtn-search`, `#tabBtn-nlg` (`miss_ids = []`).
  - Đủ 3/3 JS handlers: `rebuildAdminPatentLookupMap()` (`L1282`), `findAdminPatentByApp(appNo)` (`L1291`), `hydrateAdminCatalogShardRows(rows, targetList, seenApps)` (`L1360`) (`miss_fns = []`).

### 2.2. Đồng bộ Schema `catalog/manifest.json` <-> `shard_0..5.json` <-> Trình đọc JS
- `catalog/manifest.json` (`schema_version: "2026.8-compact-v1"`):
  - `total_dossiers = 124761` khớp chính xác tổng bản ghi thực tế trên `shard_0..5.json` (`20.794 × 5 + 20.791 = 124.761`).
  - `granted_count = 57907` khớp chính xác số hồ sơ có `r[3] == 0` (`GRANTED`) trên `shard_0..5.json` (`57.907`).
  - `shards[0..5]` khớp 100% cả tên tệp, `count` và `bytes` thực tế trên đĩa; trình nạp `index.html:L4935-L4984` và `admin.html:L1438-L1441, L2432-L2439` đọc đúng `manifest.shards` và `manifest.total_dossiers`.
- Đồng bộ ánh xạ mã nguyên giữa Portal (`index.html:L2650-L2653`) và Admin (`admin.html:L1276-L1279`):
  - `SHARD_STATUS_BY_INT` == `ADMIN_SHARD_STATUS` (**7 phần tử**): `['GRANTED', 'PUBLISHED', 'PENDING', 'UNDER_SUBSTANTIVE_EXAM', 'REFUSED', 'TERMINATED', 'WITHDRAWN']` (mã thực tế `r[3]` trong shard thuộc tập `[0, 1, 2, 3, 4, 5]`, nằm gọn trong miền `0..6`).
  - `SHARD_FTO_BY_INT` == `ADMIN_SHARD_FTO` (**3 phần tử**), `SHARD_COMM_BY_INT` == `ADMIN_SHARD_COMM` (**5 phần tử**), `SHARD_APPTYPE_BY_INT` == `ADMIN_SHARD_APPTYPE` (**5 phần tử**).
  - Bố cục tuple `r[0..22]` (độ dài thực tế `18..23` cột tùy trường tùy chọn cuối) khớp 100% giữa dữ liệu `shard_0..5.json`, `hydrateCatalogShardRows` và `hydrateAdminCatalogShardRows`.

## 3. Đối chiếu 12/12 Tệp Sản phẩm Khớp 100% SHA-256 với `vietnam-patent-db`

| STT | Tệp đích (`vietnampatentcore-demo`) | Tệp nguồn (`vietnam-patent-db`) | Bytes | SHA-256 (`MATCH = True`) |
| --: | :--- | :--- | ---: | :--- |
| 1 | `catalog/manifest.json` | `catalog/manifest.json` | `846` | `c6f3e0219fd3f49e36005281c1750bbcce66257eaa584ecdc46009f8504fbe49` |
| 2 | `catalog/shard_0.json` | `catalog/shard_0.json` | `10.065.469` | `dd89408810cd07e9d88e65a45c2a8ade51660294ddd2689b5bb618e4e0071b06` |
| 3 | `catalog/shard_1.json` | `catalog/shard_1.json` | `16.995.032` | `11e2967d8c2392fe7b33dd144da2a29cad8a25c2fcc7f81ffb2a2c3e19790cd9` |
| 4 | `catalog/shard_2.json` | `catalog/shard_2.json` | `14.721.478` | `1dbf73e46ea4d1393770d617024b63d945dcc98c49163287954c33ce61d14692` |
| 5 | `catalog/shard_3.json` | `catalog/shard_3.json` | `5.573.467` | `cf919cc02f5b6a0dd1a8d14c3320f2e4714abf0032513ee1de5d747e7ae99828` |
| 6 | `catalog/shard_4.json` | `catalog/shard_4.json` | `8.149.712` | `39a9525c0410e0c3cc595ddf36403dc6f7cdf673a94321498089ae3ca9dc30e0` |
| 7 | `catalog/shard_5.json` | `catalog/shard_5.json` | `15.393.275` | `addd17fbff50da5e9aecc54e5f7214ccb2b0b4afd7b9b28c9262e471e1ac723f` |
| 8 | `index.html` | `index.html` | `394.047` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` |
| 9 | `vietnampatentcore_fullpage_embed.html` | `vietnampatentcore_fullpage_embed.html` | `394.047` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` |
| 10 | `full-page-embed/index.html` | `vietnampatentcore_fullpage_embed.html` | `394.047` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` |
| 11 | `admin.html` | `admin.html` | `410.640` | `2cb937192d2a391c8f5a766663880b117310391d0a19aaef5b0e48e70678ab50` |
| 12 | `admin/index.html` | `admin.html` | `410.640` | `2cb937192d2a391c8f5a766663880b117310391d0a19aaef5b0e48e70678ab50` |

## 4. Kết luận Lớp A (`CODE_AUDITOR_A`)

- Đạt `PASS` tuyệt đối ở Lớp A (0 lỗi cú pháp, 0 lệch hợp đồng DOM/JS/Shard, 12/12 tệp khớp SHA-256 bit-for-bit với repo nguồn, không chạm sửa bất kỳ tệp mã nguồn dự án nào). Đủ điều kiện chuyển sang phiên độc lập `CODE_AUDITOR_B`.
