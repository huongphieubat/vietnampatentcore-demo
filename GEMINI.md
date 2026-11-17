# QUY CHUẨN BUILD APP & CODE CHỐNG COMPACT (TRẦN CỨNG 200K–240K TOKEN)

1. **Khóa cứng trần ngữ cảnh trước Compact**:
   - Nạp và tuân thủ skill `kiem-soat-chat-luong-code`.
   - Cảnh báo ở `170.000 token`; **KHÓA CỨNG NGẮT VIỆC MỚI ở `200.000 token`**; dải `200.000 – 240.000 token` chỉ dùng để đóng gói `.handoff/` và xuất `SESSION_HANDOFF_BUNDLE.md` (trần ngắt tuyệt đối `240.000 token`, trước ngưỡng auto-compact ~256k).
2. **Cấm đọc tràn tệp Monolith & Cấm viết tắt cắt cụt code**:
   - Orchestrator đọc tối đa `<= 150 dòng/lượt`; Subagent đọc tối đa `<= 150–200 dòng/lượt`.
   - Mọi tệp gắn cờ `MONOLITH_SLICE_ONLY` (`> 400 dòng` / `> 40KB`) bắt buộc tra cứu và cắt lát bằng `python3 -X utf8 .agents/scripts/code_slicer.py search|slice`.
   - Cấm tuyệt đối dùng bình luận cắt bớt (`// ... existing code ...`, `# ... rest of code ...`) hoặc làm tụt `> 20%` số dòng ngoài chủ đích.
3. **Đồng bộ Đa Tác Tử trên Đĩa**:
   - Mọi API endpoint, bảng/cột SQL, chữ ký hàm dùng chung và DOM ID khóa cứng tại `.handoff/contracts/contracts_registry.json` & `symbol_map.json`.
   - Trước và sau mỗi subagent: chạy `code_handoff_guard.py snapshot` -> `invoke_subagent` (ngữ cảnh sạch mới) -> `code_handoff_guard.py enforce --rollback` -> `verify_code_sync.py check` -> `check_code_handoff.py`.
   - Subagent quá tải (`> 1.200 dòng` đầu vào) phải dừng trả `NEED_SPLIT`; bị compact giữa chừng bị hủy kết quả (`COMPACTED_INVALID`).
