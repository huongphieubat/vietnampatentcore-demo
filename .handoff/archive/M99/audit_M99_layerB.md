# BIÊN BẢN KIỂM TOÁN ĐỘC LẬP LỚP B (CODE_AUDITOR_B — M99)

- Mã cột mốc: `M99`
- Pha kiểm định: `FINAL_AUDIT_B`
- Vai trò kiểm toán: `CODE_AUDITOR_B` (Logic Nghiệp Vụ, Toàn Vẹn Dữ Liệu 6 Shard & Bảo Mật Client-Side)
- Dự án: `/home/antigravity/huongphieubat/vietnampatentcore-demo`
- Kết quả: PASS

---

## 1. Phạm vi & Bất biến Ngữ cảnh Sạch
- Phiên `clean_code_auditor` khởi tạo độc lập 100%, tuân thủ đọc lát cắt `<= 150–200 dòng/lượt` qua `code_slicer.py` và kiểm chứng dữ liệu bằng lệnh Python một dòng (`0` đọc tràn monolith, `0` sửa mã nguồn dự án, tách biệt hoàn toàn khỏi Lớp A và Cổng 6).
- Đối chiếu SHA-256 1-1 toàn bộ 12 tệp thành phẩm (`catalog/manifest.json`, `catalog/shard_0..5.json`, `index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html`, `admin.html`, `admin/index.html`) với nguồn `huongphieubat/vietnam-patent-db`: **`0` lệch (`1_TO_1_UPSTREAM_MISMATCHES = []`)**.
  - `catalog/manifest.json`: `c6f3e0219fd3f49e36005281c1750bbcce66257eaa584ecdc46009f8504fbe49`
  - `index.html` / `vietnampatentcore_fullpage_embed.html` / `full-page-embed/index.html`: `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce`
  - `admin.html` / `admin/index.html`: `2cb937192d2a391c8f5a766663880b117310391d0a19aaef5b0e48e70678ab50`

---

## 2. Kiểm toán Logic & Toàn vẹn Dữ liệu 6 Shard (`B10`, `B11`, `B12`)

| Mã kiểm | Hạng mục kiểm định độc lập trên `manifest.json` + `shard_0..5.json` | Số liệu thực đo | Đánh giá |
| :--- | :--- | :--- | :--- |
| **`B12`** | Tổng hồ sơ duy nhất, khớp `manifest.json` (`count` & `bytes` cả 6 shard), `0` trùng `application_no`, `100%` khớp `^[12]-\d{4}-\d{5}$` | `total_rows = 124.761`, `unique_apps = 124.761`, `dup_apps = 0`, `bad_format_apps = 0`, `shard_meta_mismatches = 0` (`B12 == 0`) | **PASS** |
| **`B10`** | Văn bằng cấp (`granted_count`), độ duy nhất `grant_no`, và kiểm chứng hồ sơ `1-2019-07346` không mang `grant_no` giả | `granted_count = 57.907` (`r[3] == 0`: `57.907`), `57.450` `grant_no` khác rỗng với `dup_grants_raw = 0` & `dup_grants_typed = 0`; hồ sơ `1-2019-07346` có `r[1] = ""`, `r[3] = 1` (`PUBLISHED`), `grant_date = ""` (`B10 == 0`) | **PASS** |
| **`B11`** | Quét toàn bộ chuỗi trong `manifest.json`, `shard_0..5.json` và 5 tệp HTML tìm ký tự PUA (`\uE000-\uF8FF`), dấu rời NFD (`\u0300-\u036F`), `\u0131` và lỗi TCVN3 (`hệ thèng`, `HƯ ` lỗi mã) | `PUA = 0`, `NFD = 0`, `\u0131 = 0`, `hệ thèng = 0`, lỗi TCVN3 `HƯ ` (`HƯ Nội`...) `= 0` (toàn bộ 28 cụm từ `HƯ ` độc lập đều là từ tiếng Việt hợp lệ: `HƯ HỎNG` (15), `HƯ HẠI` (6), `HƯ TỔN` (6), `[THẬN] HƯ TIÊN [PHÁT]` (1)) (`B11 == 0`) | **PASS** |

---

## 3. Kiểm toán Bảo mật Client-Side (`B13`, URL Scheme, Tabnabbing, Secrets)

1. **Cưỡng chế Scheme `http(s):` & Whitelist Tên miền Cục SHTT**:
   - `normalizeNoipPdfUrl` (`index.html:L3032-L3054`, `admin.html:L1542-L1564`, cùng các bản sao embed/admin): Phân tích qua `new URL(u)`, chặn mọi giao thức ngoài `https:`/`http:` (`javascript:`, `data:`, `file:`, `vbscript:` trả về `""`), tự động nâng cấp `http:` lên `https:` cho `(www.)ipvietnam.gov.vn`, xóa tham số `download=true|1` và `hash`.
   - `isOfficialNoipHost` (`index.html:L3056-L3073`, `admin.html:L1566-L1583`): Khóa cứng danh sách trắng 5 tên miền chính thức của Cục SHTT (`ipvietnam.gov.vn`, `www.ipvietnam.gov.vn`, `wipopublish.ipvietnam.gov.vn`, `iplib.noip.gov.vn`, `iplib.ipvietnam.gov.vn`).
2. **Chống Reverse Tabnabbing & Kiểm tra `window.open`**:
   - `openFloatingNoipPdfWindow` (`index.html:L3097-L3118`, `admin.html:L1600-L1620`): Xác thực kép giao thức `/^https?:/i` và `isOfficialNoipHost(...)` trước khi mở cửa sổ; gán `if (win) win.opener = null;` cho popup và truyền `"noopener,noreferrer"` cho nhánh fallback `_blank`.
   - Toàn bộ các lời gọi `window.open` (`3` tại `index.html`, `2` tại `admin.html`) và toàn bộ thẻ `target="_blank"` trên cả 5 tệp HTML đều có `noopener` (`blank_no_noopener = 0`).
3. **Chống DOM XSS trên toàn bộ `.innerHTML` (`B13 == 0`)**:
   - Quét toàn bộ 5 tệp HTML: `0` điểm dùng `insertAdjacentHTML`, `.outerHTML =`, `document.write`, hoặc `eval(`.
   - Kiểm tra toàn bộ `36` điểm gán `.innerHTML` / `57` HTML template literals tại `index.html` (và 2 tệp embed) cùng `41` điểm gán `.innerHTML` / `63` HTML template literals tại `admin.html` (và `admin/index.html`): 100% trường dữ liệu động từ shard, API hoặc truy vấn người dùng đều được bọc qua `escapeHtmlAttr(...)` (kể cả hàm `highlightText` tại `index.html:L2876-L2900` thực hiện `escapeHtmlAttr` cả văn bản gốc lẫn token tìm kiếm trước khi chèn `<mark class="hl">`). Không có bất kỳ lỗ hổng chèn HTML/thuộc tính chưa thoát mã nào (`B13 == 0`).
4. **Rà quét Khóa Bí mật Tĩnh (Secrets Scan)**:
   - Quét mẫu khóa thực tế (`AIza...`, `sk-...`, `ghp_...`, `github_pat_...`, `AKIA...`, `xox...`, `PRIVATE KEY`) trên toàn bộ 5 tệp HTML và 7 tệp JSON catalog: **`0` khóa bí mật lộ lọt (`SECRET_HITS = []`)**.

---

## 4. Kết luận Kiểm toán Lớp B
- Toàn bộ tiêu chí logic dữ liệu 6 shard (`B10 == 0`, `B11 == 0`, `B12 == 0`) và bảo mật client-side trên 5 tệp HTML (`B13 == 0`, URL whitelist, chống tabnabbing, không lộ khóa bí mật) đều đạt tuyệt đối.
- Chấp thuận thông qua Lớp B (`PASS`) để chuyển sang bước nghiệm thu tiếp theo tại Trạm 3 (`M99`).
