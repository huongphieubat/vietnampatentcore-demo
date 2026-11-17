---
trigger: always_on
---

# KHÓA CỨNG TRẦN 200K–240K TOKEN CHO MỌI AGENT CODE (ANTI-COMPACTION)
- **Ngân sách 4 ngưỡng**: Cảnh báo `170.000 token`; **KHÓA CỨNG NGẮT VIỆC MỚI ở `200.000 token`**; vùng `200.000 – 240.000 token` chỉ dùng để đóng gói `.handoff/`, đồng bộ hợp đồng và xuất `SESSION_HANDOFF_BUNDLE.md`; trần ngắt tuyệt đối `240.000 token` (trước auto-compact ~256k).
- **Cấm đọc tràn tệp Monolith**: Orchestrator đọc `<= 150 dòng/lượt`, Subagent `<= 150–200 dòng/lượt`. Mọi tệp `MONOLITH_SLICE_ONLY` (`> 400 dòng` / `> 40KB`) bắt buộc cắt lát bằng `code_slicer.py search|slice`; cấm in log test/build dài ra ngữ cảnh (ghi vào `.handoff/logs/`).
- **Cầu dao chống Compact**: Subagent bị nén giữa chừng -> **HỦY KẾT QUẢ (`COMPACTED_INVALID`)**, cấm code từ trí nhớ tóm tắt, rollback và chạy lại trên phiên sạch. Luồng chính chạm 200k -> chạy `export_session_handoff.py` và mở phiên mới.
