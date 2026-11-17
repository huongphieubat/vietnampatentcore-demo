# SỔ CÁI TRẠNG THÁI ĐIỀU PHỐI CODE (01_STATE_LEDGER)

## 1. Con trỏ điều phối hiện thời
- Cột mốc đang mở: M00
- Pha hiện tại: HANDOFF_FLUSH
- Dung lượng ngữ cảnh gần nhất: 205000
- Trạng thái trần token: HARD_FREEZE_200K_240K
- Hành động kế tiếp duy nhất: Mở phiên chat sạch mới, chạy check_code_handoff.py --reset-session-meter và tiếp tục đồng bộ catalog/* + 5 tệp HTML từ vietnam-patent-db sau khi Marathon #44015228202 hoàn tất các lát quét Giai đoạn 5 tiếp theo

## 2. Đặc tả cột mốc đang thực thi
- Mã phiên hiện hành: M00_HANDOFF_DEMO_SYNC
- Mục tiêu cột mốc: Đồng bộ kho tĩnh GitHub Pages / Google Sites với điểm chốt 889/1024 kỳ (98.380 hồ sơ: 56.700 bằng cấp, 40.404 đơn công bố, 833 hết hạn công cộng) và xuất gói bàn giao liên phiên SESSION_HANDOFF_BUNDLE.md
- Tệp đầu vào tham chiếu:
  - .handoff/00_INVARIANTS.md
  - .handoff/SESSION_HANDOFF_BUNDLE.md
  - .handoff/contracts/contracts_registry.json
- Tệp đích được phép chạm (giới hạn từ 1 đến 5 tệp):
  - .handoff/ledgers/plan_backbone.md
  - .handoff/contracts/contracts_registry.json
  - .handoff/ledgers/decision_log.tsv
- Tệp bàn giao hoạt động:
  - Khảo sát: .handoff/artifacts/explore_M00.md -> Trạng thái: Chờ phiên sạch mới (nếu sửa giao diện HTML/JS)
  - Kiểm định: .handoff/artifacts/audit_M00.md -> Trạng thái: Chờ phiên sạch mới
- Tiêu chí nghiệm thu riêng:
  - Đồng bộ khớp 100% manifest.json (98.380 hồ sơ, 0.0 MB binary storage), verify_code_sync.py đạt SYNC_OK (0 lỗi)

## 3. Sổ quyết định kiến trúc đã khóa (Locked Decisions)
- D01: Duy trì đồng bộ 1-1 catalog/manifest.json, catalog/shard_0..5.json, index.html, admin.html (-> admin/index.html) và vietnampatentcore_fullpage_embed.html (-> full-page-embed/index.html) từ vietnam-patent-db.

## 4. Hàng đợi cột mốc kế tiếp
- [ ] M01: Đồng bộ lô `catalog/*` và 5 tệp `.html` tiếp theo từ `vietnam-patent-db` sau khi Marathon `#44015228202` quét tiếp `CB361 -> CB001`.
- [ ] M99: Kiểm toán giao diện & Cổng 6 (`CODE_AUDITOR_A`, `CODE_AUDITOR_B`, `CODE_AUDITOR_C6`) khi hoàn tất 1024/1024 kỳ.

## 5. Chỉ mục cột mốc đã đóng gói
- Tiền-M00 (Phiên hiện tại): Đồng bộ `45616f4` (96.186 hồ sơ, 880/1024 kỳ) và nâng cấp lên 98.380 hồ sơ (889/1024 kỳ từ `7a05dc2`).
