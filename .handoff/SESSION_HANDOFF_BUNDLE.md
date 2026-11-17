# GÓI BÀN GIAO LIÊN PHIÊN CHỐNG MẤT ĐỒNG BỘ CODE (SESSION_HANDOFF_BUNDLE)

- Thời điểm đóng gói: 2026-11-17T04:18:26+00:00
- Lý do bàn giao: Chạm ngưỡng khóa cứng 200k token — đóng gói sổ cái để mở phiên sạch mới
- Thư mục dự án: `/home/antigravity/huongphieubat/vietnampatentcore-demo`
- Nhánh Git: `main` | Token phiên vừa đóng: `6394 (GREEN_UNDER_170K)`

## 1. Lệnh Khởi Động Lại Trên Phiên Sạch Mới (Nạp < 1.500 token)
```bash
python3 -X utf8 /shared/user/.gemini/code_handoff_tools/check_code_handoff.py --root /home/antigravity/huongphieubat/vietnampatentcore-demo --reset-session-meter --token-report
python3 -X utf8 /shared/user/.gemini/code_handoff_tools/verify_code_sync.py check --root /home/antigravity/huongphieubat/vietnampatentcore-demo
```
Sau đó chỉ đọc: `.handoff/00_INVARIANTS.md`, `.handoff/01_STATE_LEDGER.md` và `.handoff/contracts/contracts_registry.json`.

## 2. Trạng Thái Sổ Cái Hiện Thời (Trích 01_STATE_LEDGER.md)
# SỔ CÁI TRẠNG THÁI ĐIỀU PHỐI CODE (01_STATE_LEDGER)

## 1. Con trỏ điều phối hiện thời
- Cột mốc đang mở: M00
- Pha hiện tại: PLAN_EXPLORE
- Dung lượng ngữ cảnh gần nhất: 0
- Trạng thái trần token: GREEN_UNDER_170K
- Hành động kế tiếp duy nhất: Chạy code_slicer.py index, gọi code_explorer khảo sát kiến trúc, khóa contracts_registry.json và lập plan_backbone.md

## 2. Đặc tả cột mốc đang thực thi
- Mã phiên hiện hành: M00
- Mục tiêu cột mốc: Lập chỉ mục ký hiệu symbol_map.json, khóa hợp đồng liên tệp contracts_registry.json và kế hoạch phân rã module M00
- Tệp đầu vào tham chiếu:
  - .handoff/00_INVARIANTS.md
  - .handoff/contracts/symbol_map.json
- Tệp đích được phép chạm (giới hạn từ 1 đến 5 tệp):
  - .handoff/ledgers/plan_backbone.md
  - .handoff/contracts/contracts_registry.json
  - .handoff/ledgers/decision_log.tsv
- Tệp bàn giao hoạt động:
  - Khảo sát: .handoff/artifacts/explore_M00.md -> Trạng thái: Chờ chạy
  - Kiểm định: .handoff/artifacts/audit_M00.md -> Trạng thái: Chờ chạy
- Tiêu chí nghiệm thu riêng:
  - Đã tạo symbol_map.json, khóa đầy đủ API/DB/DOM/Symbol contracts, mỗi cột mốc <= 1 module dọc (1..5 tệp), code_auditor phản biện PASS và người dùng duyệt

## 3. Sổ quyết định kiến trúc đã khóa (Locked Decisions)
- Chưa có quyết định khóa.

## 4. Hàng đợi cột mốc kế tiếp
- [ ] M01: [Điền module/tính năng thực thi đầu tiên sau khi duyệt M00] -> Phụ thuộc: M00 đạt PASS -> Phạm vi: [1..5 tệp đích].
- [ ] M99: Tích hợp toàn cục, kiểm toán tách 3 lớp độc lập (SYNC, LOGIC, BUILD_UI) và bàn giao -> Phụ thuộc: Các mốc trước PASS -> Phạm vi: [Entrypoints].

## 5. Chỉ mục cột mốc đã đóng gói
- Chưa có cột mốc đóng gói.

## 3. Tóm Tắt Hợp Đồng Đồng Bộ & Cảnh Báo Tệp Monolith
- Shared Symbols đã khóa: 0
- API Endpoints đã khóa: 0
- DB Tables đã khóa: 0
- DOM Bindings đã khóa: 3
- Test Commands: Chưa khai báo
- Tệp MONOLITH_SLICE_ONLY (CẤM view_file toàn bộ, bắt buộc qua code_slicer.py): admin.html, index.html, vietnampatentcore_fullpage_embed.html, admin/index.html, full-page-embed/index.html

## 4. Trạng Thái Git & Commit Gần Nhất
- Git status (`git status -s`):
  `?? .agents/`
  `?? .gitignore`
  `?? .handoff/`
  `?? GEMINI.md`
- Commit gần nhất:
  - `034f4bd feat(stage5): cập nhật 5 giai đoạn 1.024 điểm chốt & 90.458 hồ sơ UTF-8 sạch`
  - `77666cc feat(admin): connect Admin Console to 6-shard 90,458 clean NOIP catalog & purge TCVN3 fragments`
  - `635ef95 feat(portal): kết nối toàn bộ 91.802 văn bằng & đơn qua danh mục tĩnh 6 shard (0 MB PDF)`
  - `f49c97f chore(sync): đồng bộ snapshot 856/856 kỳ (91.802 hồ sơ CSDL Cục SHTT)`
  - `a2323bf chore(sync): cập nhật lịch đồng bộ tối ưu 20 phút/nhịp & 6.027 văn bằng Cục SHTT`
