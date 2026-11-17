# BIÊN BẢN KIỂM TOÁN ĐỘC LẬP CỘT MỐC M05 (`audit_M05.md`)

- Cột mốc: `M05`
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `clean_code_auditor` (ngữ cảnh sạch 100%, độc lập đối kháng)
- Kết quả: PASS

## 1. Đối chiếu 1-1 SHA-256 & Kích thước 3 tệp đích (`catalog/shard_3..5.json`)

Đối chiếu trực tiếp bằng Python `hashlib.sha256` giữa kho đích, nguồn `/tmp/rebuilt_portal_m06/catalog/` và biên bản `.handoff/artifacts/work_M05.md`:

| Tệp đích | Kích thước (bytes) | Số bản ghi | SHA-256 thực tế | Khớp `/tmp/rebuilt_portal_m06/catalog/` | Khớp `work_M05.md` |
| :--- | ---: | ---: | :--- | :---: | :---: |
| `catalog/shard_3.json` | `5.573.467` | `20.794` | `cf919cc02f5b6a0dd1a8d14c3320f2e4714abf0032513ee1de5d747e7ae99828` | `100%` (`True`) | `100%` (`True`) |
| `catalog/shard_4.json` | `8.149.712` | `20.794` | `39a9525c0410e0c3cc595ddf36403dc6f7cdf673a94321498089ae3ca9dc30e0` | `100%` (`True`) | `100%` (`True`) |
| `catalog/shard_5.json` | `15.393.275` | `20.791` | `addd17fbff50da5e9aecc54e5f7214ccb2b0b4afd7b9b28c9262e471e1ac723f` | `100%` (`True`) | `100%` (`True`) |

## 2. Kiểm chứng toàn vẹn `catalog/manifest.json` + `catalog/shard_0..5.json` (`B10`..`B12`)

Kiểm tra độc lập bằng Python một dòng trên cả chuỗi sau giải mã JSON và văn bản JSON thô (`raw` + `\uXXXX` escape):

- **Tổng số hồ sơ & Khớp `manifest.json`**: `124.761` hồ sơ (`[20794, 20794, 20794, 20794, 20794, 20791]`), khớp 100% `manifest.total_dossiers = 124761` và khớp tuyệt đối cột `bytes` của cả 6 shard `[10065469, 16995032, 14721478, 5573467, 8149712, 15393275]`.
- **Tính duy nhất & Định dạng `application_no`**: `124.761 / 124.761` số đơn duy nhất (`0` trùng); `100%` khớp biểu thức `^[12]-\d{4}-\d{5}$` (`BAD_APP = 0`).
- **Tính duy nhất `grant_no`**: `57.450 / 57.450` số bằng khác rỗng duy nhất (`DUP_GRANTS = 0`, `WS_PADDED_GRANTS = 0`).
- **Sạch lỗi mã hóa ký tự (`B10`..`B12`)**:
  - Ký tự PUA (`\uE000-\uF8FF`, Supplementary PUA): `0` (`PUA = 0`, `RAW_ESC_PUA = 0`).
  - Dấu tổ hợp rời NFD (`\u0300-\u036F`): `0` (`NFD = 0`, `RAW_ESC_NFD = 0`).
  - Ký tự dotless-i (`\u0131`): `0` (`DOTLESS_I = 0`, `RAW_ESC_DOTI = 0`).

## 3. Kiểm tra đồng bộ hợp đồng mã nguồn (`verify_code_sync.py`)

- Lệnh thực thi: `python3 -X utf8 /shared/user/.gemini/code_handoff_tools/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo`
- Kết quả đầu ra: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).

## 4. Rủi ro đồng bộ & Khuyến nghị chuyển tiếp

- Cả 7 tệp dữ liệu `catalog/manifest.json` và `catalog/shard_0..5.json` đã đồng bộ hoàn chỉnh 1-1 (`124.761` hồ sơ sạch `B10`..`B12`).
- Cần tiếp tục đóng gói `M05` và thực thi `M06` để đồng bộ 1-1 5 tệp HTML giao diện (`index.html`, `admin.html`, `admin/index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html`) bản sạch `B13` trước khi nghiệm thu `M99`.
