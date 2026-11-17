# BIÊN BẢN KIỂM TOÁN ĐỐI KHÁNG LỚP A - ĐỒNG BỘ LIÊN TỆP & HỢP ĐỒNG (`audit_M99_layerA.md`)

- Cột mốc: `M99` (Trạm 3 - `FINAL_AUDIT_A`)
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Kho nguồn đối chiếu: `huongphieubat/vietnam-patent-db` (commit `35d0ff1`) <-> Kho đích (trên nền commit `b84b040`)
- Vai trò kiểm toán: `CODE_AUDITOR_A` (`clean_code_auditor`, phiên ngữ cảnh sạch độc lập 100%)
- Kết quả: PASS

## 1. Kiểm chứng tất định hợp đồng & cú pháp (`verify_code_sync.py`)

- Lệnh chạy độc lập: `python3 -X utf8 /shared/user/.gemini/code_handoff_tools/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo`
- Đầu ra thực tế: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).
- Đối chiếu chi tiết:
  - `C01_SYNTAX`: `0` lỗi cú pháp HTML5 và `<script>` nội tuyến trên toàn bộ nhóm tệp giao diện.
  - `C03_TRUNCATION` & `C04_SHRINK_SABOTAGE`: `0` bình luận cắt cụt code máy sinh; `0` hiện tượng sụt giảm dòng bất thường (`index.html` = `5.042` dòng, `admin.html` = `4.447` dòng).
  - `dom_bindings` & `shared_symbols` (`contracts_registry.json`): Khớp 100% toàn bộ ID phần tử DOM (`#siteHeader`, `#brandHomeLink`, `#navBtn-search`, `#navBtn-assistant`, `#navBtn-insights`; `#headerSyncBadge`, `#kpiContainer`, `#tabBtn-search`, `#tabBtn-nlg`) và các hàm JS (`rebuildPatentLookupMaps`, `findDossierByApp`, `hydrateCatalogShardRows`; `rebuildAdminPatentLookupMap`, `findAdminPatentByApp`, `hydrateAdminCatalogShardRows`).

## 2. Đối chiếu đối xứng SHA-256 1-1 giữa `vietnam-patent-db` (`35d0ff1`) và `vietnampatentcore-demo`

Kiểm chứng độc lập bằng Python `hashlib.sha256` trên toàn bộ danh mục 7 tệp JSON (`catalog/`) và 5 tệp HTML (3 tệp gốc + 2 bản sao thư mục con):

| STT | Tệp nguồn (`vietnam-patent-db` `35d0ff1`) | Tệp đích (`vietnampatentcore-demo`) | Kích thước (bytes) | SHA-256 | Kết quả |
| ---: | :--- | :--- | ---: | :--- | :--- |
| 1 | `catalog/manifest.json` | `catalog/manifest.json` | `846` | `aaf6f1b81db915562518fac683e099a24d97a03ce7ef8fb233847f594c135a8e` | `MATCH` |
| 2 | `catalog/shard_0.json` | `catalog/shard_0.json` | `10.727.863` | `218f57b03397574acabb3439f7595966fbb2a85edbc5637ca7969103464c5d23` | `MATCH` |
| 3 | `catalog/shard_1.json` | `catalog/shard_1.json` | `18.216.001` | `94225ef506afc3f0f7761271cbb89feb00b6425177e2b512d3eeafd320048923` | `MATCH` |
| 4 | `catalog/shard_2.json` | `catalog/shard_2.json` | `13.554.102` | `09663650dcc784d76e2f3d4e465216523beedbb7b345360aeeaa004915209f35` | `MATCH` |
| 5 | `catalog/shard_3.json` | `catalog/shard_3.json` | `6.440.823` | `d83824c7965f5e142d51b3ae4b0d8fdfc723fa16cc29fb6a14c7aeb280820d6f` | `MATCH` |
| 6 | `catalog/shard_4.json` | `catalog/shard_4.json` | `7.064.165` | `afacd0b07edc8a138dc905b11369038a6c8cae84c272dc8296628a46fd9fdf37` | `MATCH` |
| 7 | `catalog/shard_5.json` | `catalog/shard_5.json` | `15.968.768` | `b43ed2f3f1e23050682d962580516633712e48ce9ee5a0df3737d5075f8d3f10` | `MATCH` |
| 8 | `index.html` | `index.html` | `393.089` | `49b7aa0dc19f85d792dce03197aae43e09eef36b2a8576181354c98b5f99f4f4` | `MATCH` |
| 9 | `vietnampatentcore_fullpage_embed.html` | `vietnampatentcore_fullpage_embed.html` | `393.089` | `49b7aa0dc19f85d792dce03197aae43e09eef36b2a8576181354c98b5f99f4f4` | `MATCH` |
| 10 | `index.html` | `full-page-embed/index.html` | `393.089` | `49b7aa0dc19f85d792dce03197aae43e09eef36b2a8576181354c98b5f99f4f4` | `MATCH` |
| 11 | `admin.html` | `admin.html` | `406.840` | `288c11c8258aaf951097ee799a83b52e16ae1bb06a5517852cf44e7292d7cace` | `MATCH` |
| 12 | `admin.html` | `admin/index.html` | `406.840` | `288c11c8258aaf951097ee799a83b52e16ae1bb06a5517852cf44e7292d7cace` | `MATCH` |

## 3. Kiểm toán đồng bộ Schema mảng vị trí `r[0..21]` (+ `r[22]`) và bộ giải nén JS

- **Toàn vẹn Manifest & Shards**: `manifest.json` (`schema_version = "2026.8-compact-v1"`) khớp tuyệt đối kích thước byte và số dòng của cả 6 shard (`21.825 x 5 + 21.824 = 130.949` hồ sơ; `granted_count = 66.306` khớp đếm `r[3] == 0`; `public_domain_count = 8.466` khớp đếm `r[8] == 2`).
- **Độ dài mảng nén**: Dải độ dài thực tế trên `130.949` bản ghi là `18..23` phần tử (18 trường cốt lõi `r[0..17]` luôn có mặt; các trường đuôi `r[18..22]` lược bỏ khi rỗng để tối ưu dung lượng).
- **Đối xứng giải nén (`index.html:L2743-L2808` & `admin.html:L1359-L1425`)**:
  - `r[0]` (`application_no`), `r[1]` (`grant_no`), `r[2]` (`patent_type`: `0/1`), `r[3]` (`status_group`: `0..5`), `r[4..7]` (`filing/publication/grant/expiration_date`), `r[8]` (`fto_status`: `0..2`), `r[9]` (`commercialization_status`: `0..4`), `r[10]` (`applicant_country`: `0="VN"`, `1="INTL"/"FOREIGN"`, hoặc mã ISO), `r[11]` (`applicant_type`: `0..4`), `r[12]` (`title_vi`), `r[13]` (`applicant_name`), `r[14]` (`ipc_codes` list), `r[15]` (`fulltext_pdf_url` nén tiền tố `~` charCode `126`), `r[16]` (`monthly_release_period`), `r[17]` (`gazette_issue_no`), `r[18]` (`abstract_vi`), `r[19]` (`special_filter_flags` tách dấu phẩy), `r[20]` (`inventors` list), `r[21]` (`representative`), `r[22]` (`commercialization_note`).
  - Mọi chỉ số đuôi `r[18..22]` khi vắng mặt đều được bọc fallback an toàn (`|| ""`, `Array.isArray(...) ? ... : []`), không phát sinh `TypeError` trên bất kỳ bản ghi 18–22 cột nào.

## 4. Kiểm toán đường dẫn tương đối nạp `catalog/` từ thư mục gốc và thư mục con

- **Nhóm Portal & Embed** (`index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html` — `resolveStaticCatalogManifest` tại `L4909-L4927`): Dò tuần tự `candidates = ["./catalog", "../catalog", "/catalog", "https://huongphieubat.github.io/vietnampatentcore-demo/catalog"]`, trả về `{ base, manifest }` và nạp từng shard qua `${base}/${sh.file}` (`sh.file = "shard_0.json".."shard_5.json"`).
- **Nhóm Admin** (`admin.html`, `admin/index.html` — `resolveAdminStaticCatalogManifest` tại `L1427-L1446` & `catalogPromise` tại `L2422-L2464`): Trên HTTP(S) dò `["./catalog", "../catalog", "/catalog"]` kèm fallback URL tuyệt đối GitHub Pages, nạp shard qua `${base}/${sh.file}`.
- **Kết luận đường dẫn**:
  - Tại thư mục gốc (`/index.html`, `/admin.html`, `/vietnampatentcore_fullpage_embed.html`): Khớp ngay ứng viên số 1 `"./catalog/manifest.json"` và `"./catalog/shard_*.json"`.
  - Tại thư mục con (`/admin/`, `/admin/index.html`, `/full-page-embed/`, `/full-page-embed/index.html`): Ứng viên `"./catalog/manifest.json"` trả HTTP 404 được bỏ qua an toàn (`if (!res.ok) continue;`) và khớp chính xác ở ứng viên số 2 `"../catalog/manifest.json"` cùng `"../catalog/shard_*.json"`. Không có bất kỳ lệch đường dẫn fetch nào.

## 5. Rủi ro đồng bộ & Ghi chú kỹ thuật

- **Mức độ rủi ro mất đồng bộ**: `0` (Không phát hiện lỗi đồng bộ liên tệp, lệch schema hay đứt gãy đường dẫn).
- **Ghi chú thông tin (Non-blocking)**: Khi mở từ thư mục con `/admin/` hoặc `/full-page-embed/`, trình duyệt thực hiện 01 probe `"./catalog/manifest.json"` (404 có chủ đích) trước khi nạp thành công `"../catalog/manifest.json"`; đồng thời `r[10] === 1` ánh xạ nhãn hiển thị `"INTL"` ở Portal và `"FOREIGN"` ở Admin nhưng giữ nguyên `filing_origin = "PCT_NATIONAL"` đồng nhất.
