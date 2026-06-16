# Báo cáo Thu hoạch Cá nhân (Individual Reflection Report)
**Họ và tên:** Nguyễn Đức Lãm (Lãm)  
**Vai trò:** DevOps Engineer & Analyst  

---

## 1. Tôi đã xây dựng những gì? (Engineering Contribution)

Trong bài Lab này, tôi chịu trách nhiệm thiết kế hệ thống gác cổng tự động (Auto-Gate) và đo lường tài nguyên tiêu thụ của hệ thống RAG. Các đóng góp cụ thể của tôi gồm:
* **Hệ thống Regression Release Gate:** Viết hàm quyết định tự động trong [analysis/regression.py](file:///c:/Users/LocND/Desktop/api/GroupA4-Lab14-AI-Evaluation-Benchmarking/analysis/regression.py) giúp tính toán % biến động (Delta) của tất cả chỉ số chất lượng, chi phí và thời gian trễ. Tích hợp trực tiếp logic này vào luồng chạy chính [main.py](file:///c:/Users/LocND/Desktop/api/GroupA4-Lab14-AI-Evaluation-Benchmarking/main.py).
* **Module đếm Token & Tính chi phí:** Viết cấu phần [cost_tracker.py](file:///c:/Users/LocND/Desktop/api/GroupA4-Lab14-AI-Evaluation-Benchmarking/engine/cost_tracker.py) ánh xạ bảng giá thực tế của `gpt-4o`, `gpt-4o-mini`, và `claude-3-5-sonnet` sang định dạng USD, đếm chính xác số lượng Input & Output Token tiêu thụ tại cả 3 tầng (Agent, RAGAS Evaluator, và Multi-Judge).
* **Xuất báo cáo chuẩn hóa:** Bảo đảm định dạng dữ liệu đầu ra khớp 100% với yêu cầu tự động hóa của script chấm điểm, xuất ra file [summary.json](file:///c:/Users/LocND/Desktop/api/GroupA4-Lab14-AI-Evaluation-Benchmarking/reports/summary.json) và [benchmark_results.json](file:///c:/Users/LocND/Desktop/api/GroupA4-Lab14-AI-Evaluation-Benchmarking/reports/benchmark_results.json).
* **Báo cáo tối ưu hóa chi phí:** Hoàn thiện [failure_analysis.md](file:///c:/Users/LocND/Desktop/api/GroupA4-Lab14-AI-Evaluation-Benchmarking/analysis/failure_analysis.md) với đề xuất 3 giải pháp kỹ thuật cụ thể giúp giảm chi phí Eval đi ít nhất 30% mà không giảm độ chính xác.

---

## 2. Giải quyết bài toán khó trong RAG (Technical Depth)

### Bài toán 1: Sự cân bằng (Trade-off) giữa Chi phí (Cost) và Chất lượng (Quality)
Khi vận hành một hệ thống RAG quy mô doanh nghiệp lớn, việc đánh giá liên tục (Continuous Evaluation) bằng các mô hình LLM lớn (`gpt-4o`, `claude-3-5`) rất tốn kém tiền bạc và thời gian (latency tăng cao). 
* **Giải pháp của tôi:** Thay vì sử dụng một mô hình duy nhất cho cả Agent và Judge, tôi đề xuất thiết kế **Cascading Judge Routing**. Nhờ việc đo lường chính xác lượng token tiêu thụ và quy đổi ra USD trong [cost_tracker.py](file:///c:/Users/LocND/Desktop/api/GroupA4-Lab14-AI-Evaluation-Benchmarking/engine/cost_tracker.py), tôi đã chứng minh được khi thay đổi từ Base V1 (`gpt-4o`) sang Optimized V2 (`gpt-4o-mini`), chi phí tổng thể giảm đi **63.79%** và thời gian phản hồi trung bình (latency) giảm **73.10%**, trong khi các chỉ số chất lượng chính (Hit Rate và Faithfulness) đều tăng trưởng dương (tương ứng **+13.33%** và **+12.20%**).
* **Bài học rút ra:** Không nhất thiết phải sử dụng LLM lớn nhất để đánh giá mọi lúc. Các tác vụ đánh giá có cấu trúc rõ ràng hoặc có rubrics phân tầng hoàn toàn có thể định tuyến về các model mini để tiết kiệm tối đa tài nguyên.

---

## 3. Lỗi phát sinh & Cách khắc phục (Problem Solving)

### Lỗi 1: UnicodeEncodeError trên terminal Windows (PowerShell)
* **Mô tả lỗi:** Khi tôi chạy script `check_lab.py` hoặc in kết quả benchmark ra màn hình, Python ném lỗi `UnicodeEncodeError: 'charmap' codec can't encode character...` do hệ thống Windows sử dụng cp1252 mã hóa mặc định, không hiển thị được ký tự tiếng Việt có dấu hoặc icon emoji.
* **Cách khắc phục:** Tôi cấu hình chạy Python thông qua cờ `-X utf8` (`python -X utf8 main.py`) để ép buộc Python sử dụng mã hóa UTF-8 chuẩn trên terminal Windows, loại bỏ hoàn toàn lỗi encoding này.

### Lỗi 2: KeyError khi đồng bộ hóa khóa Delta
* **Mô tả lỗi:** Khi tích hợp hàm so sánh, do thiết lập nhầm tên khóa cho chỉ số độ trễ (`latency_pct` thay vì `avg_latency_pct` để khớp với hàm định dạng dòng), hệ thống phát sinh lỗi `KeyError: 'avg_latency_pct'` làm gián đoạn luồng xuất báo cáo.
* **Cách khắc phục:** Tôi đã chuẩn hóa lại định dạng cấu trúc trả về của hàm `check_release_gate` trong [regression.py](file:///c:/Users/LocND/Desktop/api/GroupA4-Lab14-AI-Evaluation-Benchmarking/analysis/regression.py) để tất cả các tên khóa đo lường đều ánh xạ khớp 1-1 với thuộc tính của file báo cáo tổng hợp.

### Lỗi 3: Blocking trong Git do xung đột thư mục báo cáo `.gitignore`
* **Mô tả lỗi:** Theo mặc định, thư mục `reports/` bị loại bỏ trong `.gitignore`. Điều này dẫn đến việc chạy thành công ở local nhưng khi push lên Git, Repository sẽ bị thiếu các tệp `summary.json` và `benchmark_results.json` khiến script chấm điểm tự động đánh trượt điểm thủ tục.
* **Cách khắc phục:** Tôi đã sửa đổi `.gitignore` để bỏ qua việc loại trừ đối với định dạng tệp tin JSON trong thư mục báo cáo bằng cú pháp loại trừ phủ định `!reports/*.json`, vừa đảm bảo không commit rác thừa vừa đảm bảo có đầy đủ báo cáo nộp bài.
