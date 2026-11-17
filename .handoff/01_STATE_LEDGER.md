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
