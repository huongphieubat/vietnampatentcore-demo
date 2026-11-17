# BIÊN BẢN THỰC THI CỘT MỐC M02 (`work_M02.md`)

- Cột mốc: `M02`
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `code_worker` (ngữ cảnh sạch)
- Kết quả: PASS

## 1. Phạm vi tệp đích đã thực thi (khóa cứng theo `01_STATE_LEDGER.md`)

Sao chép nguyên vẹn 1-1 (`cp`) từ `/home/antigravity/huongphieubat/vietnam-patent-db/catalog/` sang `/home/antigravity/huongphieubat/vietnampatentcore-demo/catalog/`:

| Tệp đích | Kích thước (bytes) | Số mục / bản ghi | SHA-256 (khớp 100% nguồn <-> đích) |
| :--- | ---: | ---: | :--- |
| `catalog/shard_3.json` | `6.440.823` | `21.825` hồ sơ | `d83824c7965f5e142d51b3ae4b0d8fdfc723fa16cc29fb6a14c7aeb280820d6f` |
| `catalog/shard_4.json` | `7.064.165` | `21.825` hồ sơ | `afacd0b07edc8a138dc905b11369038a6c8cae84c272dc8296628a46fd9fdf37` |
| `catalog/shard_5.json` | `15.968.768` | `21.824` hồ sơ | `b43ed2f3f1e23050682d962580516633712e48ce9ee5a0df3737d5075f8d3f10` |

## 2. Kiểm chứng tất định bằng Python & `verify_code_sync.py`

1. **Đối chiếu SHA-256 & tổng hồ sơ toàn bộ 6 shard (`shard_0..5.json`)**:
   - Khớp 100% SHA-256 và dung lượng byte (`bytes`) trên cả 3 tệp `shard_3..5.json` giữa nguồn `vietnam-patent-db/catalog/` và đích `vietnampatentcore-demo/catalog/`, khớp tuyệt đối với bảng `shards` trong `catalog/manifest.json`.
   - Số lượng bản ghi theo từng shard tại `vietnampatentcore-demo/catalog/`: `shard_0=21.825`, `shard_1=21.825`, `shard_2=21.825`, `shard_3=21.825`, `shard_4=21.825`, `shard_5=21.824`.
   - Tổng số hồ sơ 6 shard: `21.825 * 5 + 21.824 = 130.949 == manifest.json['total_dossiers']` (`130949`).
2. **Kiểm tra đồng bộ mã nguồn (`verify_code_sync.py`)**:
   - Lệnh: `python3 -X utf8 .agents/scripts/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo --allow-shrink`
   - Nhật ký: `.handoff/logs/verify_M02.log`
   - Đầu ra: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).

## 3. Rủi ro đồng bộ ghi nhận cho cột mốc kế tiếp

- Bộ dữ liệu `catalog/manifest.json` và đủ 6 shard `catalog/shard_0..5.json` (`130.949` hồ sơ) đã đồng bộ hoàn chỉnh 100%.
- Bước kế tiếp (`M03`): đồng bộ 5 tệp HTML giao diện (`index.html`, `admin.html`, `admin/index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html`) từ `vietnam-patent-db` để hiển thị khớp số liệu mới.
- Không phát sinh bất kỳ chỉnh sửa nào ngoài 3 tệp đích đã khóa của `M02`.
