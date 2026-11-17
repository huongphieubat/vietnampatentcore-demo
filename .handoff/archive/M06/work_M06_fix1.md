# BIÊN BẢN THỰC THI VÒNG SỬA LỖI M06_fix1 (`work_M06_fix1.md`)

- Cột mốc: `M06` (`M06_fix1`)
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `clean_code_worker` (ngữ cảnh sạch)
- Kết quả: PASS

## 1. Phạm vi tệp đích đã thực thi (khóa cứng theo `01_STATE_LEDGER.md`)

Sao chép nguyên bản 1-1 (bit-for-bit) `/home/antigravity/huongphieubat/vietnam-patent-db/admin.html` (bản `M08_fix1`) sang `admin.html` và `admin/index.html` của `/home/antigravity/huongphieubat/vietnampatentcore-demo/`, đồng thời bảo toàn nguyên vẹn 3 tệp HTML còn lại (`index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html`) và không chạm `catalog/*`:

| Tệp nguồn (`vietnam-patent-db`) | Tệp đích (`vietnampatentcore-demo`) | Thao tác ở `M06_fix1` | Kích thước (bytes) | Số dòng | SHA-256 (khớp 100% nguồn <-> đích) |
| :--- | :--- | :--- | ---: | ---: | :--- |
| `admin.html` | `admin.html` | Cập nhật 1-1 | `410.640` | `4.454` | `2cb937192d2a391c8f5a766663880b117310391d0a19aaef5b0e48e70678ab50` |
| `admin.html` | `admin/index.html` | Cập nhật 1-1 | `410.640` | `4.454` | `2cb937192d2a391c8f5a766663880b117310391d0a19aaef5b0e48e70678ab50` |
| `index.html` | `index.html` | Giữ nguyên | `394.047` | `5.059` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` |
| `vietnampatentcore_fullpage_embed.html` | `vietnampatentcore_fullpage_embed.html` | Giữ nguyên | `394.047` | `5.059` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` |
| `vietnampatentcore_fullpage_embed.html` | `full-page-embed/index.html` | Giữ nguyên | `394.047` | `5.059` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` |

## 2. Kiểm chứng tất định 12 tệp (5 HTML + 7 `catalog/*`) & `verify_code_sync.py`

1. **Đối chiếu bit-for-bit 7 tệp `catalog/*` (chỉ đọc, khớp 100% với `vietnam-patent-db`)**:
   - `catalog/manifest.json` (`846` bytes): `c6f3e0219fd3f49e36005281c1750bbcce66257eaa584ecdc46009f8504fbe49`
   - `catalog/shard_0.json` (`10.065.469` bytes): `dd89408810cd07e9d88e65a45c2a8ade51660294ddd2689b5bb618e4e0071b06`
   - `catalog/shard_1.json` (`16.995.032` bytes): `11e2967d8c2392fe7b33dd144da2a29cad8a25c2fcc7f81ffb2a2c3e19790cd9`
   - `catalog/shard_2.json` (`14.721.478` bytes): `1dbf73e46ea4d1393770d617024b63d945dcc98c49163287954c33ce61d14692`
   - `catalog/shard_3.json` (`5.573.467` bytes): `cf919cc02f5b6a0dd1a8d14c3320f2e4714abf0032513ee1de5d747e7ae99828`
   - `catalog/shard_4.json` (`8.149.712` bytes): `39a9525c0410e0c3cc595ddf36403dc6f7cdf673a94321498089ae3ca9dc30e0`
   - `catalog/shard_5.json` (`15.393.275` bytes): `addd17fbff50da5e9aecc54e5f7214ccb2b0b4afd7b9b28c9262e471e1ac723f`
2. **Kiểm tra đồng bộ hợp đồng & cú pháp (`verify_code_sync.py`)**:
   - Lệnh: `python3 -X utf8 .agents/scripts/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo`
   - Nhật ký: `.handoff/logs/verify_M06_fix1.log`
   - Đầu ra: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).

## 3. Rủi ro đồng bộ ghi nhận cho cột mốc kế tiếp

- `0` lỗi cú pháp `<script>` nội tuyến, `0` vi phạm cắt cụt code, bảo toàn 100% DOM IDs (`headerSyncBadge`, `kpiContainer`, `tabBtn-search`, `tabBtn-nlg`) và JS handlers (`rebuildAdminPatentLookupMap`, `findAdminPatentByApp`, `hydrateAdminCatalogShardRows`) đã khóa trong `contracts_registry.json`.
- Toàn bộ 5 tệp HTML và 7 tệp `catalog/*` trên `vietnampatentcore-demo` khớp 100% bit-for-bit với `vietnam-patent-db`, sẵn sàng chuyển sang `audit_M06_fix1` và Trạm 3 (`M99`).
