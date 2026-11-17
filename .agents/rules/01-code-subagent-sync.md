---
trigger: always_on
---

# ĐỒNG BỘ HỢP ĐỒNG CODE & ĐIỀU PHỐI SUBAGENT 3 TRẠM (ZERO-DESYNC)
- **Hợp đồng đồng bộ trên đĩa**: Khóa cứng API routes, bảng/cột SQL, chữ ký hàm dùng chung và DOM ID tại `.handoff/contracts/contracts_registry.json` & `symbol_map.json`. Cấm dùng bình luận cắt cụt code (`// ... existing code ...`) hoặc làm tụt `> 20%` số dòng ngoài chủ đích.
- **Độ mịn mỗi Subagent**: Ngữ cảnh sạch mới 100% mỗi cột mốc (cấm tái sử dụng `idle`), xử lý đúng 01 module dọc (`1..5 tệp đích`), tối đa 15–25 lượt công cụ (`code_explorer` <=15, `code_auditor` <=20, `code_worker` <=25), trả về `<= 350 token`. Đầu vào `> 1.200 dòng` phải dừng trả `NEED_SPLIT`.
- **3 Trạm**: Trạm 1 (`M00`: `code_slicer.py index` -> khóa `contracts_registry.json` + `plan_backbone.md` -> `audit_M00.md`) -> Trạm 2 (`M01..M98`: `snapshot` -> `code_worker` -> `enforce --rollback` + `verify_code_sync.py` -> `code_auditor` -> `close_code_milestone.py`) -> Trạm 3 (`M99`: tách 3 subagent độc lập `layerA` Sync, `layerB` Logic/Sec, `gate6` Build/UI).
