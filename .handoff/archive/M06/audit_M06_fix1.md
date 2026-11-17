# BIÊN BẢN KIỂM ĐỊNH ĐỘC LẬP VÒNG M06_fix1 (`audit_M06_fix1.md`)

- Cột mốc: `M06` (`M06_fix1`)
- Dự án: `VIETNAMPATENTCORE_DEMO` (`/home/antigravity/huongphieubat/vietnampatentcore-demo`)
- Vai trò: `clean_code_auditor` (ngữ cảnh sạch độc lập)
- Kết quả: PASS

## 1. Kiểm tra đồng bộ hợp đồng & cú pháp (`verify_code_sync.py`)

- Lệnh thực thi: `python3 -X utf8 .agents/scripts/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo`
- Kết quả: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (`exit code = 0`).
- Xác nhận bảo toàn 100% `dom_bindings` và `js_handlers` đã khóa trong `.handoff/contracts/contracts_registry.json`:
  - `index.html` & `vietnampatentcore_fullpage_embed.html`: `#siteHeader`, `#brandHomeLink`, `#navBtn-search`, `#navBtn-assistant`, `#navBtn-insights`; `rebuildPatentLookupMaps`, `findDossierByApp`, `hydrateCatalogShardRows`.
  - `admin.html`: `#headerSyncBadge`, `#kpiContainer`, `#tabBtn-search`, `#tabBtn-nlg`; `rebuildAdminPatentLookupMap`, `findAdminPatentByApp`, `hydrateAdminCatalogShardRows`.
- Không phát hiện bình luận cắt cụt code hay tụt giảm dòng bất thường.

## 2. Đối chiếu SHA-256 bit-for-bit 12/12 tệp sản phẩm (`vietnampatentcore-demo` <-> `vietnam-patent-db`)

| STT | Tệp đích (`vietnampatentcore-demo`) | Tệp nguồn đối chiếu (`vietnam-patent-db`) | Kích thước (bytes) | SHA-256 | Kết quả |
| ---: | :--- | :--- | ---: | :--- | :--- |
| 1 | `admin.html` | `admin.html` | `410.640` | `2cb937192d2a391c8f5a766663880b117310391d0a19aaef5b0e48e70678ab50` | **KHỚP 100%** |
| 2 | `admin/index.html` | `admin.html` | `410.640` | `2cb937192d2a391c8f5a766663880b117310391d0a19aaef5b0e48e70678ab50` | **KHỚP 100%** |
| 3 | `index.html` | `index.html` | `394.047` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` | **KHỚP 100%** |
| 4 | `vietnampatentcore_fullpage_embed.html` | `vietnampatentcore_fullpage_embed.html` (`== index.html`) | `394.047` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` | **KHỚP 100%** |
| 5 | `full-page-embed/index.html` | `vietnampatentcore_fullpage_embed.html` (`== index.html`) | `394.047` | `ead021c74c39ab94b024f1b8983b08531c814b70466a71cfbcc6daa2e6b8f5ce` | **KHỚP 100%** |
| 6 | `catalog/manifest.json` | `catalog/manifest.json` | `846` | `c6f3e0219fd3f49e36005281c1750bbcce66257eaa584ecdc46009f8504fbe49` | **KHỚP 100%** |
| 7 | `catalog/shard_0.json` | `catalog/shard_0.json` | `10.065.469` | `dd89408810cd07e9d88e65a45c2a8ade51660294ddd2689b5bb618e4e0071b06` | **KHỚP 100%** |
| 8 | `catalog/shard_1.json` | `catalog/shard_1.json` | `16.995.032` | `11e2967d8c2392fe7b33dd144da2a29cad8a25c2fcc7f81ffb2a2c3e19790cd9` | **KHỚP 100%** |
| 9 | `catalog/shard_2.json` | `catalog/shard_2.json` | `14.721.478` | `1dbf73e46ea4d1393770d617024b63d945dcc98c49163287954c33ce61d14692` | **KHỚP 100%** |
| 10 | `catalog/shard_3.json` | `catalog/shard_3.json` | `5.573.467` | `cf919cc02f5b6a0dd1a8d14c3320f2e4714abf0032513ee1de5d747e7ae99828` | **KHỚP 100%** |
| 11 | `catalog/shard_4.json` | `catalog/shard_4.json` | `8.149.712` | `39a9525c0410e0c3cc595ddf36403dc6f7cdf673a94321498089ae3ca9dc30e0` | **KHỚP 100%** |
| 12 | `catalog/shard_5.json` | `catalog/shard_5.json` | `15.393.275` | `addd17fbff50da5e9aecc54e5f7214ccb2b0b4afd7b9b28c9262e471e1ac723f` | **KHỚP 100%** |

## 3. Kiểm định lát cắt `.innerHTML` & `escapeHtmlAttr(...)` trên `admin.html` và `admin/index.html`

Đã cắt lát qua `code_slicer.py slice` (`<= 200 dòng/lượt`) trên `admin.html` và `admin/index.html` (`4.454` dòng, `237` điểm gọi `escapeHtmlAttr(...)`, `41` vị trí `.innerHTML`):

- **`L1531-L1539` (`escapeHtmlAttr`)**: Đã sửa điều kiện rỗng thành `if (val === null || val === undefined || val === false) return "";` (bảo toàn số `0`) và thoát đầy đủ `&`, `"`, `'`, `<`, `>`.
- **`L1688-L1689`**: `c.claim_number`, `(c.parent_claim_numbers || []).join(", ")`, `c.claim_text_vi` đều đã bọc `escapeHtmlAttr(...)`.
- **`L3243-L3258`**: Toàn bộ trường đối chứng (`m.citation_category`, `m.application_no`, `m.grant_no`, `m.title_vi`, `m.rrf_hybrid_score`, `m.vector_cosine_similarity`, `m.lexical_bm25_score`, `m.citation_assessment`, `f.feature_id`, `f.prior_art_claim_element`, `f.overlap_assessment`) đều đã bọc `escapeHtmlAttr(...)`.
- **`L3334-L3349`**: `data.application_no`, `data.grant_no`, `streamPdfUrl`, `dl.substantive_exam_deadline`, `dl.expected_publication_date`, `dl.expiration_date` đều đã bọc `escapeHtmlAttr(...)`.
- **`L3398-L3434`**: Toàn bộ trường hàng đợi khuyết & bảng nhật ký ETL (`m.application_no`, `cmask`, `m.detected_source`, `f`, `m.missing_reason`, `m.detected_at`, `m.priority_level`, `l.created_at`, `l.triggered_by`, `l.gazette_issues_scanned`, `l.monthly_portal_period`, `l.new_patents_added`, `l.fulltext_specs_parsed`) đều đã bọc `escapeHtmlAttr(...)`.
- **`L3602-L3612`**: `ov.completed_checkpoints ?? 1024`, `ov.total_checkpoints || 1024`, `ov.jobs_per_day_at_current_cadence || 2520`, `etaS1Label`, `etaAllLabel` đều đã bọc `escapeHtmlAttr(...)`.
- **`L4102-L4110` & `L4244-L4252`**: Toàn bộ trường bảng Công báo và Thương mại hóa (bao gồm `g.summary_note || ''` tại `L4110` và `p.commercialization_note || ''` tại `L4252`) đều đã bọc `escapeHtmlAttr(...)`.
- **`L4312-L4424`**: Toàn bộ danh mục MCP, bảng khóa API, nhật ký Telemetry và banner tạo khóa mới (`t.name`, `t.quota_cost`, `t.description`, `k.*`, `l.*`, `ck.plaintext_api_key_shown_once`, `ck.stored_sha256_hash`) đều đã bọc `escapeHtmlAttr(...)`.

## 4. Kết luận & Rủi ro đồng bộ

- Toàn bộ mục tiêu sửa lỗi `M06_fix1` đạt chuẩn 100%, không phát sinh chỉnh sửa ngoài phạm vi tệp đích của `01_STATE_LEDGER.md`.
- Không còn rủi ro tồn đọng; đủ điều kiện đóng cột mốc `M06` và tiến vào nghiệm thu Trạm 3 (`M99`).
