# BIÊN BẢN THỰC THI CỘT MỐC M01 (`work_M01.md`)

- Cột mốc: `M01`
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `code_worker` (ngữ cảnh sạch)
- Kết quả: PASS

## 1. Phạm vi tệp đích đã thực thi (khóa cứng theo `01_STATE_LEDGER.md`)

Sao chép nguyên vẹn 1-1 (`cp`) từ `/home/antigravity/huongphieubat/vietnam-patent-db/catalog/` sang `/home/antigravity/huongphieubat/vietnampatentcore-demo/catalog/`:

| Tệp đích | Kích thước (bytes) | Số mục / bản ghi | SHA-256 (khớp 100% nguồn <-> đích) |
| :--- | ---: | ---: | :--- |
| `catalog/manifest.json` | `846` | `6` shards (`130.949` hồ sơ) | `aaf6f1b81db915562518fac683e099a24d97a03ce7ef8fb233847f594c135a8e` |
| `catalog/shard_0.json` | `10.727.863` | `21.825` hồ sơ | `218f57b03397574acabb3439f7595966fbb2a85edbc5637ca7969103464c5d23` |
| `catalog/shard_1.json` | `18.216.001` | `21.825` hồ sơ | `94225ef506afc3f0f7761271cbb89feb00b6425177e2b512d3eeafd320048923` |
| `catalog/shard_2.json` | `13.554.102` | `21.825` hồ sơ | `09663650dcc784d76e2f3d4e465216523beedbb7b345360aeeaa004915209f35` |

## 2. Kiểm chứng tất định bằng Python & `verify_code_sync.py`

1. **Đối chiếu SHA-256 & trường khóa `manifest.json`**:
   - Khớp 100% SHA-256 trên cả 4 tệp giữa `vietnam-patent-db/catalog/` và `vietnampatentcore-demo/catalog/`.
   - `schema_version`: `"2026.8-compact-v1"`, `generated_at`: `"2026-11-17"`, `shard_count`: `6`.
   - `total_dossiers == 130949` (`granted_count: 66306`, `published_count: 63367`, `pending_count: 1274`, `public_domain_count: 8466`, `verified_pdf_count: 44323`).
   - `binary_pdf_storage_mb == 0.0`.
2. **Kiểm tra đồng bộ mã nguồn (`verify_code_sync.py`)**:
   - Lệnh: `python3 -X utf8 /home/antigravity/huongphieubat/vietnampatentcore-demo/.agents/scripts/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo --allow-shrink`
   - Nhật ký: `.handoff/logs/verify_M01.log`
   - Đầu ra: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).

## 3. Rủi ro đồng bộ ghi nhận cho cột mốc kế tiếp

- `catalog/manifest.json` đã trỏ sang bộ 6 shard mới (`130.949` hồ sơ); các shard còn lại (`catalog/shard_3.json`, `catalog/shard_4.json`, `catalog/shard_5.json`) và 5 tệp HTML giao diện sẽ được đồng bộ nối tiếp tại `M02` và `M03` theo đúng `01_STATE_LEDGER.md`.
- Không phát sinh sửa đổi ngoài 4 tệp đích đã khóa.
