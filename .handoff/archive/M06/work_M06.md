# BIÊN BẢN THỰC THI CỘT MỐC M06 (`work_M06.md`)

- Cột mốc: `M06`
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `code_worker` (ngữ cảnh sạch)
- Kết quả: PASS

## 1. Phạm vi 5 tệp đích đã thực thi (khóa cứng theo `01_STATE_LEDGER.md`)

Sao chép nguyên bản 1-1 (bit-for-bit) từ `/home/antigravity/huongphieubat/vietnam-patent-db/` sang `/home/antigravity/huongphieubat/vietnampatentcore-demo/` (tuyệt đối không chạm `catalog/*` hay tạo tệp lạ ngoài phạm vi):

| Tệp nguồn (`vietnam-patent-db`) | Tệp đích (`vietnampatentcore-demo`) | Kích thước (bytes) | Số dòng | SHA-256 (khớp 100% nguồn <-> đích) |
| :--- | :--- | ---: | ---: | :--- |
| `index.html` | `index.html` | `394.047` | `5.059` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` |
| `admin.html` | `admin.html` | `409.433` | `4.454` | `9ada4831c65064a1a8a6fb0cd50e79b2ffc2dd568100e45bb04bd71a0c45882f` |
| `admin.html` | `admin/index.html` | `409.433` | `4.454` | `9ada4831c65064a1a8a6fb0cd50e79b2ffc2dd568100e45bb04bd71a0c45882f` |
| `vietnampatentcore_fullpage_embed.html` | `vietnampatentcore_fullpage_embed.html` | `394.047` | `5.059` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` |
| `vietnampatentcore_fullpage_embed.html` | `full-page-embed/index.html` | `394.047` | `5.059` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` |

## 2. Kiểm chứng tất định bằng Python & `verify_code_sync.py`

1. **Kiểm tra đường dẫn nạp `catalog/manifest.json` tại thư mục con (`admin/index.html` & `full-page-embed/index.html`)**:
   - Đã đối chiếu trước khi ghi đè: bản hiện hữu ở `M03` giống hệt 1-1 `admin.html` và `vietnampatentcore_fullpage_embed.html` vì cả `resolveAdminStaticCatalogManifest()` (`admin.html:L1433`) và `resolveStaticCatalogManifest()` (`index.html:L4928-4930`) đều tự động duyệt mảng `["./catalog", "../catalog", "/catalog", "https://huongphieubat.github.io/vietnampatentcore-demo/catalog"]`. Do đó sao chép 1-1 bit-for-bit vừa khớp mã băm vừa bảo toàn 100% đường dẫn nạp shard ở thư mục con.
2. **Đối chiếu SHA-256, snapshot `1024/1024` kỳ, `124.761` hồ sơ & bản vá `B13`**:
   - Cả 5 tệp HTML khớp tuyệt đối 100% SHA-256 với `vietnam-patent-db`, chứa đầy đủ snapshot `1024/1024` kỳ, `124.761` hồ sơ (`manifest.json['total_dossiers'] = 124761`) và bản vá `B13` (làm sạch & chống XSS biểu thức tô sáng từ khóa, khóa giao thức `http:/https:` + `isOfficialNoipHost` + `win.opener = null`, đồng bộ bảng trạng thái `ADMIN_SHARD_STATUS` gồm `UNDER_SUBSTANTIVE_EXAM`, `TERMINATED`, `WITHDRAWN`).
   - Đã quét regex toàn văn cả 5 tệp HTML: `0` lần xuất hiện các con số cũ `130949`/`130.949` hoặc `98380`/`98.380`.
3. **Đối chiếu bảo toàn 100% SHA-256 của 7 tệp `catalog/` (chỉ đọc)**:
   - `catalog/manifest.json`: `c6f3e0219fd3f49e36005281c1750bbcce66257eaa584ecdc46009f8504fbe49`
   - `catalog/shard_0.json`: `dd89408810cd07e9d88e65a45c2a8ade51660294ddd2689b5bb618e4e0071b06`
   - `catalog/shard_1.json`: `11e2967d8c2392fe7b33dd144da2a29cad8a25c2fcc7f81ffb2a2c3e19790cd9`
   - `catalog/shard_2.json`: `1dbf73e46ea4d1393770d617024b63d945dcc98c49163287954c33ce61d14692`
   - `catalog/shard_3.json`: `cf919cc02f5b6a0dd1a8d14c3320f2e4714abf0032513ee1de5d747e7ae99828`
   - `catalog/shard_4.json`: `39a9525c0410e0c3cc595ddf36403dc6f7cdf673a94321498089ae3ca9dc30e0`
   - `catalog/shard_5.json`: `addd17fbff50da5e9aecc54e5f7214ccb2b0b4afd7b9b28c9262e471e1ac723f`
4. **Kiểm tra đồng bộ hợp đồng & cú pháp (`verify_code_sync.py`)**:
   - Lệnh: `python3 -X utf8 .agents/scripts/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo`
   - Nhật ký: `.handoff/logs/verify_M06.log`
   - Đầu ra: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).

## 3. Rủi ro đồng bộ ghi nhận cho cột mốc kế tiếp

- Không có rủi ro lệch hợp đồng, gãy đường dẫn tương đối `../catalog` hay cắt cụt mã nguồn (`0` lỗi; bảo toàn 100% DOM IDs & JS handlers trong `contracts_registry.json`).
- Toàn bộ 7 tệp `catalog/` (`124.761` hồ sơ sạch) và 5 tệp HTML bản `B13` (`1024/1024` kỳ) đã đồng bộ 1-1 hoàn chỉnh với `vietnam-patent-db`, sẵn sàng chuyển sang `audit_M06` và Trạm 3 (`M99`).
