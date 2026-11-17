# BIÊN BẢN KIỂM TOÁN ĐỘC LẬP CỘT MỐC M04 (`audit_M04.md`)

- Cột mốc: `M04`
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `clean_code_auditor` (`CODE_AUDITOR_A` — phiên ngữ cảnh sạch 100%)
- Kết quả: PASS

## 1. Đối chiếu SHA-256 & Kích thước 4 Tệp Đích (`1-1`)

Đối chiếu trực tiếp bằng `hashlib.sha256` giữa `/home/antigravity/huongphieubat/vietnampatentcore-demo/catalog/`, `/tmp/rebuilt_portal_m06/catalog/` và biên bản `work_M04.md`:

| Tệp đích | Bytes | Bản ghi | SHA-256 thực tế | Khớp nguồn & `work_M04.md` |
| :--- | ---: | ---: | :--- | :---: |
| `catalog/manifest.json` | `846` | `6` shards (`124.761` hồ sơ) | `c6f3e0219fd3f49e36005281c1750bbcce66257eaa584ecdc46009f8504fbe49` | `100%` (`True`) |
| `catalog/shard_0.json` | `10.065.469` | `20.794` hồ sơ | `dd89408810cd07e9d88e65a45c2a8ade51660294ddd2689b5bb618e4e0071b06` | `100%` (`True`) |
| `catalog/shard_1.json` | `16.995.032` | `20.794` hồ sơ | `11e2967d8c2392fe7b33dd144da2a29cad8a25c2fcc7f81ffb2a2c3e19790cd9` | `100%` (`True`) |
| `catalog/shard_2.json` | `14.721.478` | `20.794` hồ sơ | `1dbf73e46ea4d1393770d617024b63d945dcc98c49163287954c33ce61d14692` | `100%` (`True`) |

## 2. Kiểm chứng Bất biến Dữ liệu (`manifest.json` & `shard_0..2.json`)

1. **Trường khóa `catalog/manifest.json`**:
   - `schema_version = "2026.8-compact-v1"`, `generated_at = "2026-11-17"`, `shard_count = 6`.
   - `total_dossiers = 124761`, `granted_count = 57907`, `published_count = 65275`, `pending_count = 1577`, `public_domain_count = 8385`, `verified_pdf_count = 44323`.
   - `binary_pdf_storage_mb = 0.0`.
   - Khai báo `count` và `bytes` của `shard_0..2.json` trong `manifest.json` khớp 100% tệp vật lý trên đĩa.
2. **Chất lượng dữ liệu `catalog/shard_0..2.json` (`B10`..`B13`)**:
   - Đối chiếu cấu trúc cột qua `code_slicer.py slice --file index.html --symbol hydrateCatalogShardRows`: `r[0]` là `appNo`, `r[1]` là `grantNo`.
   - Tổng số bản ghi `shard_0..2.json`: `20.794 + 20.794 + 20.794 = 62.382` hồ sơ (`row_widths = 18..23`).
   - Ký tự PUA (`\uE000-\uF8FF`, `\U000F0000-\U0010FFFF`): `0` (cả raw JSON và toàn bộ chuỗi sau decode).
   - Dấu tổ hợp NFD (`\u0300-\u036F`): `0` (cả raw JSON và toàn bộ chuỗi sau decode).
   - Số đơn `r[0]` khớp `^[12]-\d{4}-\d{5}$`: `62.382/62.382` (`100%`), duy nhất `100%` (`uniq = 62.382`, `dup = 0`).
   - Số bằng `r[1]` (`grant_no`): `57.450` bản ghi có số bằng, duy nhất `57.450/57.450` (`dup = 0`, `0` trùng `grant_no`).

## 3. Kiểm tra Đồng bộ Hợp đồng Mã nguồn (`verify_code_sync.py`)

- Lệnh thực thi: `python3 -X utf8 /shared/user/.gemini/code_handoff_tools/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo`
- Kết quả: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).

## 4. Rủi ro Đồng bộ & Khuyến nghị Điều phối

- Tạm thời tồn tại chênh lệch thế hệ dữ liệu giữa `manifest.json` + `shard_0..2.json` (mốc `124.761` hồ sơ) và `shard_3..5.json` + 5 tệp HTML (chờ `M05`, `M06`).
- Đủ điều kiện đóng mốc `M04` và chuyển sang thực thi `M05` -> `M06` -> `M99`.
