# BIÊN BẢN KIỂM TOÁN ĐỘC LẬP LỚP B — M99 (`FINAL_AUDIT_B`)

- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò kiểm toán: `CODE_AUDITOR_B` (Logic nghiệp vụ SHTT, Điều kiện biên dữ liệu & Bảo mật tĩnh)
- Cột mốc: `M99` (`FINAL_AUDIT_B`)
- Kết quả: FAIL

---

## 1. Phạm vi & Phương pháp kiểm định (Ngữ cảnh sạch 100%)
- **Sổ cái & Hợp đồng**: `.handoff/00_INVARIANTS.md`, `.handoff/01_STATE_LEDGER.md`, `.handoff/contracts/contracts_registry.json`, `catalog/manifest.json`.
- **Toàn bộ dữ liệu Catalog (`130.949` hồ sơ)**: Quét tất định bằng Python một dòng trên `catalog/shard_0.json` .. `catalog/shard_5.json` (`21.825 × 5 + 21.824 = 130.949` hồ sơ, `130.949` `application_no` duy nhất, `0` trùng lặp).
- **Mã nguồn Frontend Monolith**: Tra cứu và cắt lát `<= 150 dòng/lượt` qua `code_slicer.py` kết hợp quét AST/regex tĩnh trên `index.html` (`5.042` dòng), `admin.html` (`4.447` dòng) và toàn bộ cây thư mục dự án (không đọc `audit_M99_layerA.md`).

---

## 2. Kết quả kiểm toán chi tiết theo hạng mục

### 2.1. Logic dữ liệu & Điều kiện biên SHTT (`catalog/shard_0..5.json`)
| Hạng mục | Kết quả | Số liệu thực đo & Bằng chứng |
| :--- | :---: | :--- |
| **Tổng số hồ sơ & Khóa chính** | **PASS** | `130.949` hồ sơ khớp `manifest.json`; `130.949` số đơn duy nhất (`0` trùng). |
| **`B04` (Số bằng giả mạo Tập A)** | **PASS** | **`0` lỗi**: `0/63.365` hồ sơ `status_code=1` (và `0/64.643` hồ sơ chưa cấp bằng) có `patent_no` số trần 4–6 chữ số hay bất kỳ `grant_no` nào. *(Ghi chú thông tin: `2.354` hồ sơ `status_code=0` `GRANTED` đang để `grant_no=""` chờ cập nhật số bằng).* |
| **`B05` (Sót tiền tố INID `(71)-(76)`)** | **PASS** | **`0` lỗi**: Không lọt nhãn `(71)..(76)` vào `applicant_name` (`r[13]`), `inventors` (`r[20]`) hay `representative` (`r[21]`). |
| **`B06` (Ký tự bẩn / PUA / NFD)** | **FAIL** | `0` control char / `\uFFFD`, **nhưng còn sót `554` hồ sơ chứa ký tự PUA (`\uE000-\uF8FF`)** chưa ánh xạ sang Unicode chuẩn (553 hồ sơ chứa glyph Symbol/Wingdings `\uF000-\uF0FF` như `\uf0a3`, `\uf06d`, `\uf061` tại `1-2018-01565`, `1-2019-00698`, `1-2018-03239`, `1-2018-03093`, `1-2019-01659`; 1 hồ sơ PUA ngoài `\uF000-\uF0FF`) và **`4` hồ sơ sót dấu tổ hợp rời NFD/CP1258 (`\u0300`)** tại `1-2020-06280`, `1-2020-06276`, `1-2020-06278`, `1-2020-06274`. |
| **`D02` (Chuẩn hóa số đơn `^[12]-\d{4}-\d{5}$`)** | **FAIL** | `0` đơn KDCN (`3-`) hoặc Nhãn hiệu (`4-`); **nhưng có `78` hồ sơ lệch chuẩn 5 chữ số cuối** (`69` đơn 7 chữ số dạng `d-dddd-ddddddd` do dư số `0` đầu như `1-2016-0008651`, `1-2016-0008616`, `1-2016-0006312`, `1-2015-0056570`; `9` đơn 6 chữ số `d-dddd-dddddd`). Khi người dùng tra chuẩn `1-2016-08651` sẽ không khớp. |
| **Phân loại trạng thái & `public_domain`** | **FAIL** | Số lượng raw trong shard khớp `manifest.json`: `r[3]=0` (`66.306` granted) + `r[3]∈{1,3}` (`63.365 + 2 = 63.367` published/under_exam) + `r[3]=2` (`1.274` pending) + `r[3]∈{4,5}` (`1 + 1 = 2` refused/terminated) = `130.949`; `fto_code=2` (`public_domain`) = **`8.466`** khớp 100%. **Tuy nhiên `admin.html:L1275` khai báo `ADMIN_SHARD_STATUS = ["GRANTED", "PUBLISHED", "PENDING", "REFUSED", "WITHDRAWN", "EXPIRED"]` lệch chỉ số `3..5` so với `index.html:L2650` (`["GRANTED", "PUBLISHED", "PENDING", "UNDER_SUBSTANTIVE_EXAM", "REFUSED", "TERMINATED", ...]`)**, làm 2 đơn thẩm định nội dung (`1-2023-01980`, `1-2022-02740`) bị gán sai thành `REFUSED` và đơn `2-2024-00612` (`r[3]=4`) bị gán sai thành `WITHDRAWN`. |

### 2.2. Bảo mật Frontend tĩnh (`index.html`, `admin.html` & toàn kho)
| Hạng mục | Kết quả | Bằng chứng kỹ thuật |
| :--- | :---: | :--- |
| **Secrets / API Keys / Private Keys** | **PASS** | **`0` lộ lọt**: Quét toàn bộ tệp nguồn trong kho xác nhận `0` API key, token hay khóa bí mật cứng. |
| **Thẻ `<a target="_blank">` (`noopener`)** | **PASS** | `index.html` (`5/5`) và `admin.html` (`3/3`) đều có đủ `rel="noopener noreferrer"`. |
| **Kiểm soát URL PDF (`http:`/`https:`)** | **FAIL** | Dữ liệu shard sạch (`0/44.359` URL sai scheme). Tuy nhiên trong mã JS: (1) `normalizeNoipPdfUrl` (`index.html:L3022-L3043`, `admin.html:L1541-L1562`) không chặn scheme ngoài `http:`/`https:` (trả nguyên `javascript:...` / `data:...` qua `parsed.toString()`); (2) `isOfficialNoipHost` (`index.html:L3045-L3060`, `admin.html:L1564-L1579`) chỉ kiểm `hostname` mà không kiểm `parsed.protocol === "http:" \|\| parsed.protocol === "https:"`; (3) Nhánh popup chính `openFloatingNoipPdfWindow` (`index.html:L3091-L3095`, `admin.html:L1603-L1607`) mở `window.open` không kèm `noopener,noreferrer` trong `windowFeatures` và không chặn URL ngoài `^https?:`. |
| **Escape HTML chống DOM-XSS (`innerHTML`)** | **FAIL** | Cả hai tệp có `escapeHtmlAttr` (`index.html:L2838`, `admin.html:L1530`), nhưng vẫn còn nhiều biểu thức `${...}` nội suy trực tiếp trường dữ liệu sáng chế (`p.title_vi`, `p.applicant_name`, `p.application_no`, `p.grant_no`, `p.gazette_issue_no`) không bọc hàm escape trước khi đổ vào `.innerHTML` (`index.html:L2678-L2725` — `28` điểm; `admin.html:L1307-L1346` — `56` điểm), gây nguy cơ DOM-XSS hoặc vỡ giao diện khi tên sáng chế chứa ký tự `<` / `>` (như `<0,5%`). |

---

## 3. Yêu cầu khắc phục bắt buộc trước khi duyệt `PASS`
1. **Chuẩn hóa dữ liệu gốc & xuất lại `shard_0..5.json`** (đồng bộ từ `vietnam-patent-db`):
   - `D02`: Chuẩn hóa `78` số đơn dư chữ số (`^[12]-\d{4}-0+(\d{5})$` -> `\1`, kiểm tra va chạm khóa trước khi gộp).
   - `B06`: Ánh xạ bảng mã PUA Symbol (`\uF000-\uF0FF` -> Unicode toán/Hy Lạp chuẩn), loại bỏ PUA rác còn sót trên `554` hồ sơ và chuẩn hóa `unicodedata.normalize("NFC", ...)` cho `4` hồ sơ dính dấu tổ hợp rời.
2. **Đồng bộ ánh xạ trạng thái tại `admin.html:L1275` (và `admin/index.html`)**:
   - Sửa `ADMIN_SHARD_STATUS` khớp 1-1 với `SHARD_STATUS_BY_INT` của `index.html:L2650` cho các mã `3, 4, 5`.
3. **Khóa cứng bảo mật URL & XSS trên `index.html`, `admin.html` và các bản sao embed/admin**:
   - Trong `normalizeNoipPdfUrl` & `isOfficialNoipHost`: bắt buộc kiểm tra `parsed.protocol === "https:" || parsed.protocol === "http:"` (từ chối trả `""` với mọi scheme khác như `javascript:`, `data:`, `ftp:`). Thêm `noopener,noreferrer` vào `windowFeatures` của `openFloatingNoipPdfWindow`.
   - Bọc `escapeHtml` / `escapeHtmlAttr` cho toàn bộ trường văn bản hồ sơ trước khi nối vào chuỗi `.innerHTML`.
