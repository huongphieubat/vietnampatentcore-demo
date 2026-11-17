# BIÊN BẢN KIỂM ĐỊNH ĐỘC LẬP CỘT MỐC M06 (`audit_M06.md`)

- Cột mốc: `M06`
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `clean_code_auditor` (`CODE_AUDITOR_A` + xác minh bản vá `B13` trên ngữ cảnh sạch)
- Kết quả: PASS

## 1. Kiểm tra đồng bộ hợp đồng & cú pháp (`verify_code_sync.py`)

- Lệnh thực thi: `python3 -X utf8 .agents/scripts/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo`
- Kết quả: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).
- Toàn bộ ràng buộc `dom_bindings` trong `.handoff/contracts/contracts_registry.json` (`#siteHeader`, `#brandHomeLink`, `#navBtn-search`, `#navBtn-assistant`, `#navBtn-insights`, `#headerSyncBadge`, `#kpiContainer`, `#tabBtn-search`, `#tabBtn-nlg`) và các hàm xử lý JS (`rebuildPatentLookupMaps`, `findDossierByApp`, `hydrateCatalogShardRows`, `rebuildAdminPatentLookupMap`, `findAdminPatentByApp`, `hydrateAdminCatalogShardRows`) được bảo toàn 100%, không cắt cụt code.

## 2. Đối chiếu SHA-256 bit-for-bit giữa `vietnampatentcore-demo` và `vietnam-patent-db`

### 2.1. Nhóm 5 tệp HTML thành phẩm M06
| Nhóm | Tệp kiểm tra | Bytes | Dòng | SHA-256 | Kết quả |
| :--- | :--- | ---: | ---: | :--- | :--- |
| Portal / Embed | `vietnampatentcore-demo/index.html`<br>`vietnampatentcore-demo/vietnampatentcore_fullpage_embed.html`<br>`vietnampatentcore-demo/full-page-embed/index.html`<br>`vietnam-patent-db/index.html`<br>`vietnam-patent-db/vietnampatentcore_fullpage_embed.html` | `394.047` | `5.059` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` | **KHỚP 100%** |
| Admin | `vietnampatentcore-demo/admin.html`<br>`vietnampatentcore-demo/admin/index.html`<br>`vietnam-patent-db/admin.html` | `409.433` | `4.454` | `9ada4831c65064a1a8a6fb0cd50e79b2ffc2dd568100e45bb04bd71a0c45882f` | **KHỚP 100%** |

### 2.2. Nhóm 7 tệp `catalog/` (`total_dossiers = 124.761`, tổng dòng 6 shard = `124.761`)
| Tệp `catalog/` | SHA-256 (`vietnampatentcore-demo` == `vietnam-patent-db`) | Kết quả |
| :--- | :--- | :--- |
| `catalog/manifest.json` | `c6f3e0219fd3f49e36005281c1750bbcce66257eaa584ecdc46009f8504fbe49` | **KHỚP 100%** |
| `catalog/shard_0.json` | `dd89408810cd07e9d88e65a45c2a8ade51660294ddd2689b5bb618e4e0071b06` | **KHỚP 100%** |
| `catalog/shard_1.json` | `11e2967d8c2392fe7b33dd144da2a29cad8a25c2fcc7f81ffb2a2c3e19790cd9` | **KHỚP 100%** |
| `catalog/shard_2.json` | `1dbf73e46ea4d1393770d617024b63d945dcc98c49163287954c33ce61d14692` | **KHỚP 100%** |
| `catalog/shard_3.json` | `cf919cc02f5b6a0dd1a8d14c3320f2e4714abf0032513ee1de5d747e7ae99828` | **KHỚP 100%** |
| `catalog/shard_4.json` | `39a9525c0410e0c3cc595ddf36403dc6f7cdf673a94321498089ae3ca9dc30e0` | **KHỚP 100%** |
| `catalog/shard_5.json` | `addd17fbff50da5e9aecc54e5f7214ccb2b0b4afd7b9b28c9262e471e1ac723f` | **KHỚP 100%** |

## 3. Kiểm định lát cắt mã nguồn (`code_slicer.py slice`) & JSON Snapshot

1. **`SYNC_SCHEDULE_INITIAL_SNAPSHOT` & tẩy sạch số liệu cũ**:
   - Đã giải mã trực tiếp đối tượng JSON `SYNC_SCHEDULE_INITIAL_SNAPSHOT` trên cả 5 tệp HTML (`index.html:L2127`, `admin.html:L3447` và các bản sao): `updated_at = "2026-11-17 17:06:42"`, `completed_checkpoints == 1024`, `total_checkpoints == 1024`, `total_patents_in_db == 124761`.
   - Quét regex toàn văn 5 tệp HTML với mẫu `130[.,]?949|98[.,]?380`: **`0` lần xuất hiện**.
2. **Bản vá bảo mật & đồng bộ enum `B13`**:
   - `ADMIN_SHARD_STATUS` (`admin.html:L1276`) đủ 7 trạng thái `["GRANTED", "PUBLISHED", "PENDING", "UNDER_SUBSTANTIVE_EXAM", "REFUSED", "TERMINATED", "WITHDRAWN"]`, đồng bộ 100% với `SHARD_STATUS` trong `index.html` và bao phủ toàn bộ chỉ số trạng thái `[0..5]` trong `shard_0..5.json`.
   - Khóa giao thức `http:`/`https:` kết hợp danh sách trắng tên miền Cục SHTT `isOfficialNoipHost()` (`index.html:L3040-3065, L3097-3103`; `admin.html:L1566-1583, L1600-1604`).
   - Chống reverse-tabnabbing: `try { if (win) win.opener = null; } catch (e) {}` kèm fallback `noopener,noreferrer` (`index.html:L3112-3114`; `admin.html:L1614-1618`).
   - Thoát ký tự HTML/thuộc tính động: `escapeHtmlAttr()` (`index.html:L2838-2845` với `142` điểm gọi; `admin.html:L1531-1539` với `165` điểm gọi).
3. **Đường dẫn nạp `catalog/manifest.json` tại gốc và thư mục con**:
   - `resolveStaticCatalogManifest()` (`index.html:L4926-4944`) và `resolveAdminStaticCatalogManifest()` (`admin.html:L1428-1447`) đều thử tuần tự `["./catalog", "../catalog", "/catalog", "https://huongphieubat.github.io/vietnampatentcore-demo/catalog"]` và trả về `{ base, manifest }`, đảm bảo nạp đúng `manifest.json` và `shard_0..5.json` cả ở gốc (`/index.html`, `/admin.html`, `/vietnampatentcore_fullpage_embed.html`) lẫn thư mục con (`/admin/index.html`, `/full-page-embed/index.html`).

## 4. Kết luận & Rủi ro tồn đọng

- Không phát hiện lỗi mất đồng bộ hợp đồng, lệch mã băm hay gãy đường dẫn tương đối `../catalog`.
- Ghi chú nhỏ không chặn nghiệm thu (upstream note): `escapeHtmlAttr` dùng `String(str || "")` / `if (!val) return ""` nên nếu truyền trực tiếp số `0` chưa chuỗi hóa sẽ trả về `""`; hiện tại khớp 1-1 với `vietnam-patent-db` đúng quy ước bất biến `D01`.
- Đủ điều kiện đóng cột mốc `M06` và chuyển sang Trạm 3 (`M99`).
