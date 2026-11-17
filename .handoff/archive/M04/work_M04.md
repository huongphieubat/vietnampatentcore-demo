# BIÊN BẢN THỰC THI CỘT MỐC M04 (`work_M04.md`)

- Cột mốc: `M04`
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `clean_code_worker` (ngữ cảnh sạch 100%)
- Kết quả: PASS

## 1. Phạm vi tệp đích đã thực thi (khóa cứng theo `01_STATE_LEDGER.md`)

Sao chép nguyên vẹn 1-1 (`cp`) từ `/tmp/rebuilt_portal_m06/catalog/` sang `/home/antigravity/huongphieubat/vietnampatentcore-demo/catalog/`:

| Tệp đích | Kích thước (bytes) | Số mục / bản ghi | SHA-256 (khớp 100% nguồn <-> đích) |
| :--- | ---: | ---: | :--- |
| `catalog/manifest.json` | `846` | `6` shards (`124.761` hồ sơ) | `c6f3e0219fd3f49e36005281c1750bbcce66257eaa584ecdc46009f8504fbe49` |
| `catalog/shard_0.json` | `10.065.469` | `20.794` hồ sơ | `dd89408810cd07e9d88e65a45c2a8ade51660294ddd2689b5bb618e4e0071b06` |
| `catalog/shard_1.json` | `16.995.032` | `20.794` hồ sơ | `11e2967d8c2392fe7b33dd144da2a29cad8a25c2fcc7f81ffb2a2c3e19790cd9` |
| `catalog/shard_2.json` | `14.721.478` | `20.794` hồ sơ | `1dbf73e46ea4d1393770d617024b63d945dcc98c49163287954c33ce61d14692` |

## 2. Kiểm chứng tất định bằng Python & `verify_code_sync.py`

1. **Đối chiếu SHA-256 & trường khóa `manifest.json`**:
   - Khớp 1-1 SHA-256 trên cả 4 tệp giữa `/tmp/rebuilt_portal_m06/catalog/` và `/home/antigravity/huongphieubat/vietnampatentcore-demo/catalog/`.
   - `schema_version`: `"2026.8-compact-v1"`, `generated_at`: `"2026-11-17"`, `shard_count`: `6`.
   - `total_dossiers == 124761` (`granted_count: 57907`, `published_count: 65275`, `pending_count: 1577`, `public_domain_count: 8385`, `verified_pdf_count: 44323`).
   - `binary_pdf_storage_mb == 0.0`.
2. **Kiểm chứng sạch lỗi `B10`..`B12` trên `shard_0..2.json` (`62.382` hồ sơ)**:
   - Ký tự PUA (`\uE000-\uF8FF`, Supplementary PUA): `0` (cả raw JSON và chuỗi sau decode).
   - Dấu tổ hợp NFD (`\u0300-\u036F`): `0` (cả raw JSON và chuỗi sau decode).
   - Định dạng số đơn `^[12]-\d{4}-\d{5}$`: đạt `100%` (`62.382/62.382` bản ghi, `bad_app = 0`).
3. **Kiểm tra đồng bộ mã nguồn (`verify_code_sync.py`)**:
   - Lệnh: `python3 -X utf8 /shared/user/.gemini/code_handoff_tools/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo`
   - Nhật ký: `.handoff/logs/verify_M04.log`
   - Đầu ra: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).

## 3. Rủi ro đồng bộ ghi nhận cho cột mốc kế tiếp

- `catalog/manifest.json` và `catalog/shard_0..2.json` đã cập nhật sang bộ `124.761` hồ sơ sạch `B10`..`B13`; cần thực thi nối tiếp `M05` (`catalog/shard_3..5.json`) và `M06` (5 tệp HTML giao diện) để đồng bộ trọn vẹn 6 shard và KPI giao diện trước khi nghiệm thu `M99`.
- Không phát sinh bất kỳ chỉnh sửa nào ngoài 4 tệp đích đã khóa trong `01_STATE_LEDGER.md`.
