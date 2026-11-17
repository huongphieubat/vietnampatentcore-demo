# BIÊN BẢN KIỂM TOÁN KẾ HOẠCH & HỢP ĐỒNG ĐỒNG BỘ (audit_M00)

- Kết quả: PASS
- Vai trò kiểm toán: `PLAN_AUDIT` (Trạm 1 — Cổng Kiến trúc `M00`)
- Kho kiểm định: `/home/antigravity/huongphieubat/vietnampatentcore-demo`
- Mã phiên sổ cái: `M00_DEMO_SYNC_PLAN` (`GREEN_UNDER_170K`)

## 1. Kiểm chứng tất định 0-Token LLM
- Lệnh `verify_code_sync.py check`: `SYNC_OK | checked=6 files | errors=0 | contracts=clean` (exit code `0`).
- Chỉ mục `symbol_map.json`: Hợp lệ, phủ đủ `5/5` tệp HTML gắn cờ `MONOLITH_SLICE_ONLY`:
  - `index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html`: `5.042` dòng, `72` ký hiệu/tệp.
  - `admin.html`, `admin/index.html`: `4.447` dòng, `97` ký hiệu/tệp.
- Hiện trạng `catalog/manifest.json`: `schema_version=2026.8-compact-v1`, `binary_pdf_storage_mb=0.0`.

## 2. Thẩm định độ mịn `plan_backbone.md` & Chống va chạm ghi tệp
| Mã mốc | Số tệp đích | Trần `1..5` tệp | Đánh giá độ mịn, phụ thuộc & va chạm |
|---|---:|---|---|
| `M01` | 4 | ĐẠT | `catalog/manifest.json`, `catalog/shard_0..2.json` — độc lập tệp với `M02`, `M03`. |
| `M02` | 3 | ĐẠT | `catalog/shard_3..5.json` — nối tiếp tuần tự sau `M01`, không giao tệp đích với `M01`. |
| `M03` | 5 | ĐẠT | `index.html`, `admin.html`, `admin/index.html`, `vietnampatentcore_fullpage_embed.html`, `full-page-embed/index.html` — vừa khít trần 5 tệp. |
| `M99` | 3 | ĐẠT | Nghiệm thu tách đủ 3 subagent độc lập (`CODE_AUDITOR_A`, `CODE_AUDITOR_B`, `CODE_AUDITOR_C6`) kèm `truoc_c6_manifest.json`. |

- **Đồ thị phụ thuộc**: Tuyến tính một chiều `M00 -> M01 -> M02 -> M03 -> M99`; **0** phụ thuộc vòng; **0** xung đột ghi song song giữa các cột mốc Trạm 2 (`M01`, `M02`, `M03` tách rời hoàn toàn tập tệp đích).

## 3. Thẩm định `contracts_registry.json` & Bất biến `00_INVARIANTS.md`
- `contracts_registry.json` khóa cứng `dom_bindings` cho 3 tệp gốc (`index.html`, `vietnampatentcore_fullpage_embed.html`, `admin.html`) với đầy đủ `element_ids` và `js_handlers` nạp shard (`rebuildPatentLookupMaps`, `findDossierByApp`, `hydrateCatalogShardRows`, `rebuildAdminPatentLookupMap`, `findAdminPatentByApp`, `hydrateAdminCatalogShardRows`).
- Phù hợp kiến trúc Static GitHub Pages (`.nojekyll`, không có backend API động hay bảng SQL nội bộ nên `api_endpoints=[]`, `db_tables=[]` là chính xác).

## 4. Cảnh báo Rủi ro Đồng bộ & Điều kiện Cưỡng chế cho Trạm 2 – Trạm 3
1. **Rủi ro lệch tạm thời giữa `M01` và `M02`**: Sau `M01`, `manifest.json` đã lên bản mới trong khi `shard_3..5.json` chờ `M02`. Bắt buộc chạy liền mạch `M01 -> M02` trước khi xuất bản/push và chỉ kiểm tổng số hồ sơ toàn cục 6 shard tại cuối `M02`.
2. **Chống chạm cầu dao `NEED_SPLIT` ở `M03`**: Cả 5 tệp HTML đều `> 4.400` dòng (`MONOLITH_SLICE_ONLY`) và các tệp `shard_*.json` là dữ liệu lớn. Subagent `M01..M03` cấm `view_file` toàn văn; bắt buộc đồng bộ nhị phân 1-1 từ `vietnam-patent-db`, đối chiếu SHA-256 bằng Python và cắt lát `<= 150–200` dòng qua `code_slicer.py` khi kiểm tra.
3. **Bất biến bản sao thư mục con (`admin/index.html`, `full-page-embed/index.html`)**: Hiện `contracts_registry.json` kiểm `dom_bindings` trên 3 tệp gốc; ở `M03` và `M99` bắt buộc cưỡng chế kiểm SHA-256 khớp 1-1 giữa `admin.html <-> admin/index.html` và `vietnampatentcore_fullpage_embed.html <-> full-page-embed/index.html` (nếu `M99` phát sinh sửa lỗi trên HTML thì phải mở rộng danh sách tệp đích trong `01_STATE_LEDGER.md` bao gồm cả 2 tệp mirror, tối đa 5 tệp).

## 5. Kết luận Cổng Kiến trúc (Trạm 1)
- Đủ điều kiện đóng `M00` và chuyển sang thực thi `M01` khi nguồn `vietnam-patent-db` sẵn sàng.
