# BIÊN BẢN THỰC THI CỘT MỐC M05 (`work_M05.md`)

- Cột mốc: `M05`
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `clean_code_worker` (ngữ cảnh sạch 100%)
- Kết quả: PASS

## 1. Phạm vi tệp đích đã thực thi (khóa cứng theo `01_STATE_LEDGER.md`)

Sao chép nguyên vẹn 1-1 (`cp`) từ `/tmp/rebuilt_portal_m06/catalog/` sang `/home/antigravity/huongphieubat/vietnampatentcore-demo/catalog/` (giữ nguyên 100% `/tmp/rebuilt_portal_m06/`):

| Tệp đích | Kích thước (bytes) | Số bản ghi | SHA-256 (khớp 100% nguồn <-> đích) |
| :--- | ---: | ---: | :--- |
| `catalog/shard_3.json` | `5.573.467` | `20.794` hồ sơ | `cf919cc02f5b6a0dd1a8d14c3320f2e4714abf0032513ee1de5d747e7ae99828` |
| `catalog/shard_4.json` | `8.149.712` | `20.794` hồ sơ | `39a9525c0410e0c3cc595ddf36403dc6f7cdf673a94321498089ae3ca9dc30e0` |
| `catalog/shard_5.json` | `15.393.275` | `20.791` hồ sơ | `addd17fbff50da5e9aecc54e5f7214ccb2b0b4afd7b9b28c9262e471e1ac723f` |

## 2. Kiểm chứng tổng hợp toàn bộ `catalog/manifest.json` + `catalog/shard_0..5.json`

1. **Quy mô & Khớp `manifest.json` 100%**:
   - Phân bổ 6 shard: `[20794, 20794, 20794, 20794, 20794, 20791]` -> Tổng cộng `124.761` hồ sơ (`20.794 * 5 + 20.791 == manifest.total_dossiers == 124761`).
   - Kích thước byte từng tệp `shard_0..5.json` khớp tuyệt đối cột `bytes` trong `catalog/manifest.json`.
   - Tổng số đơn duy nhất (`application_no`): `124.761` (`0` trùng số đơn).
2. **Kiểm chứng sạch lỗi `B10`..`B12` toàn bộ `124.761` hồ sơ**:
   - Ký tự PUA (`\uE000-\uF8FF` & Supplementary PUA): `0` (cả raw JSON/escape và chuỗi sau decode).
   - Dấu rời tổ hợp NFD (`\u0300-\u036F`): `0` (cả raw JSON/escape và chuỗi sau decode).
   - Ký tự dotless-i (`\u0131`): `0` (cả raw JSON/escape và chuỗi sau decode).
   - Định dạng `application_no` (`r[0]`) khớp `^[12]-\d{4}-\d{5}$`: `100%` (`124.761/124.761`, `bad_app = 0`).
   - Trùng số bằng `grant_no` (`r[1]` khác rỗng): `0` (`57.450/57.450` số bằng duy nhất trên shards).
3. **Kiểm tra đồng bộ mã nguồn (`verify_code_sync.py`)**:
   - Lệnh: `python3 -X utf8 /shared/user/.gemini/code_handoff_tools/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo`
   - Nhật ký: `.handoff/logs/verify_M05.log`
   - Đầu ra: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).

## 3. Rủi ro đồng bộ ghi nhận cho cột mốc kế tiếp

- Bộ dữ liệu `catalog/manifest.json` và toàn bộ 6 tệp `catalog/shard_0..5.json` (`124.761` hồ sơ sạch `B10`..`B12`) đã đồng bộ hoàn chỉnh 100%; cần thực thi tiếp cột mốc `M06` để đồng bộ 1-1 5 tệp HTML giao diện (`index.html`, `admin.html`, `admin/index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html`) bản sạch `B13` trước khi nghiệm thu `M99`.
- Không phát sinh bất kỳ thay đổi nào ngoài 3 tệp đích đã khóa trong `01_STATE_LEDGER.md`.
