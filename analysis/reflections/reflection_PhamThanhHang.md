# Báo cáo Cá nhân (Individual Reflection) - Hằng

**Vị trí:** Data & Retrieval Engineer

## 1. Tôi đã xây dựng cái gì?
Là người chịu trách nhiệm về mảng Data và Retrieval của dự án "AI Evaluation Factory", tôi đã độc lập thiết kế và xây dựng module sinh dữ liệu và đo lường nằm trong thư mục `data/` (Chi tiết tại file: `data/synthetic_gen.py`). Cụ thể:
- **Tự động sinh Golden Dataset:** Tạo ra 55 test cases chất lượng cao, chia làm 46 câu hỏi chuẩn hóa đa dạng ngữ cảnh và 9 câu "Hard Cases" (Adversarial, Edge Cases, Multi-turn, Technical Constraints). Bộ dữ liệu này được xuất tự động ra file `data/golden_set.jsonl`.
- **Hệ thống đo lường Retrieval Metric:** Viết các hàm toán học đo lường `Hit Rate` và `MRR` (Mean Reciprocal Rank) không phụ thuộc vào framework, đảm bảo đánh giá chính xác chất lượng của Vector DB trước khi đưa vào Evaluation Engine.

## 2. Giải quyết độ khó cốt lõi (Hard Problem) của hệ thống RAG
Trong quá trình đánh giá hệ thống RAG, sai lầm phổ biến nhất là chỉ đánh giá câu trả lời cuối cùng (Generation) mà bỏ qua khâu truy xuất (Retrieval). Nếu Retrieval lấy sai tài liệu, AI bị "Hallucination" (bịa chuyện) là hệ quả tất yếu. 

Công việc của tôi giải quyết bài toán cốt lõi: **"Làm sao biết Vector DB có đang trả về đúng tài liệu người dùng cần hay không, và độ ưu tiên của tài liệu đó như thế nào?"**
- **Sự khác biệt giữa MRR và Hit Rate:**
  - **Hit Rate (@K):** Đo lường xem tài liệu đúng (Ground Truth Chunk) có xuất hiện trong top K tài liệu truy xuất về hay không. Chỉ số này mang tính chất nhị phân (1 hoặc 0). Nó chỉ quan tâm đến việc "Có tìm thấy không?".
  - **MRR (Mean Reciprocal Rank):** Khắt khe hơn rất nhiều. MRR quan tâm đến **thứ hạng (rank)** của tài liệu đúng đầu tiên được tìm thấy. Công thức là `1/rank`. Nếu tài liệu đúng nằm ở top 1, điểm là 1.0; nếu nằm ở top 2, điểm tụt xuống 0.5. Trong thực tế, MRR cực kỳ quan trọng vì LLM bị ảnh hưởng bởi *Position Bias* (thiên vị vị trí - LLM thường chú ý đến các tài liệu nằm ở đầu phần ngữ cảnh). Do đó, việc đẩy tài liệu đúng lên top 1 (để có MRR cao) quan trọng hơn việc chỉ xuất hiện trong top 3.
- **Chiến lược Red Teaming:** Đưa các bẫy Prompt Injection, câu hỏi mập mờ, câu hỏi Out-of-Context vào Golden Dataset để ép hệ thống lộ ra điểm yếu (xem Agent có biết từ chối trả lời hay nói "Tôi không biết" khi thiếu dữ liệu không).

## 3. Khó khăn kỹ thuật gặp phải & Cách giải quyết
Trong quá trình code module này, tôi đã gặp phải một số vấn đề kỹ thuật và đã tự xử lý thành công:
- **Lỗi ánh xạ (Mapping) Chunk ID:** Khi tính Hit Rate ban đầu, logic thường trả về 0 dù tài liệu đúng đã được lấy về. 
  - *Giải quyết:* Tôi phát hiện ra vấn đề nằm ở cấu trúc mảng ID truyền vào bị lệch định dạng. Tôi đã thiết kế lại luồng JSONL, buộc `ground_truth_chunk_ids` phải là một mảng List chuẩn, đồng thời viết lại vòng lặp `for chunk_id in ground_truth_chunk_ids` so sánh chính xác tuyệt đối với mảng kết quả trả về từ Vector DB.
- **Thiếu sự đa dạng trong Test Cases (Data Leak):** Kịch bản ban đầu tự động sinh câu hỏi bằng vòng lặp rất máy móc. Điều này khiến bộ Test thiếu tính thực tế và độ "nhiễu".
  - *Giải quyết:* Tôi đã đập bỏ hàm sinh cơ bản, xây dựng lại hệ thống sinh dữ liệu ngẫu nhiên sử dụng `random.choice()`. Module mới sẽ trộn các danh từ, động từ và các ngữ cảnh chính sách khác nhau lại với nhau, tạo ra các câu query cực kỳ giống thật để đánh lừa Agent.

Qua module này, tôi đã nắm vững cách vận hành của bước Retrieval trong pipeline RAG, cũng như kỹ thuật tạo bộ Dataset "Red Teaming" để benchmark các giới hạn của AI.
