# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark (Agent V2 vs Agent V1)
- **Tổng số cases:** 52
- **Tỉ lệ Pass/Fail (V2):** 52 / 0 (Không có case nào điểm < 3.0)
- **Điểm RAGAS trung bình (V2):**
    - Faithfulness: 0.9200
    - Relevancy: 0.8800
    - Hit Rate: 0.9615
    - MRR: 0.9615
- **Điểm LLM-Judge trung bình (V2):** 4.50 / 5.0 (V1: 3.84 / 5.0)
- **Tổng chi phí Eval (V2):** $0.00733 (V1: $0.31460 - Giảm 97.67% nhờ tối ưu hóa mô hình và kích thước prompt)

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Hallucination | 2 | Retriever không lấy đúng context (Miss trong V2) |
| Incomplete | 1 | Prompt giới hạn độ dài câu trả lời quá mức |
| Tone Mismatch | 0 | Đã cải tiến prompt để đảm bảo sự chuyên nghiệp |

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)

### Case #1: Lỗi Retrieval đối với câu hỏi Edge Case du hành vũ trụ
1. **Symptom:** Agent không trả về thông tin phù hợp và trả lời từ chối.
2. **Why 1:** LLM không tìm thấy bất kỳ thông tin nào liên quan đến du hành vũ trụ trong context.
3. **Why 2:** Vector DB không truy xuất được chunk tài liệu nào có chứa từ khóa này.
4. **Why 3:** Tài liệu HR nội bộ không có chính sách du hành vũ trụ.
5. **Why 4:** Khách hàng hỏi ngoài phạm vi nghiệp vụ được thiết lập.
6. **Root Cause:** Đây là câu hỏi biên (Edge Case - Out of Context). Giải pháp là giữ nguyên câu trả lời "Tôi không biết" để tránh Hallucination, điều này hoàn toàn chính xác.

### Case #2: Điểm số thẩm định viên bị lệch giữa 2 Judge
1. **Symptom:** GPT-4o chấm 4 điểm, trong khi Claude-3.5 chấm 5 điểm.
2. **Why 1:** Claude đánh giá cao văn phong trôi chảy, GPT-4o khắt khe về độ chính xác tuyệt đối của thuật ngữ.
3. **Why 2:** Không có bộ rubric thống nhất và chi tiết cho từng khung điểm ở cấu hình Judge.
4. **Why 3:** Hệ thống prompt của Judge chỉ đưa ra tiêu chuẩn chấm chung chung.
5. **Root Cause:** Thiếu Guide-line (Evaluation Rubrics) cụ thể cho các thẩm định viên LLM.

### Case #3: Trễ (Latency) đột biến ở một số case RAG phức tạp
1. **Symptom:** Thời gian phản hồi vượt quá 0.5s ở Agent V1.
2. **Why 1:** Sử dụng model lớn gpt-4o cho các tác vụ xử lý đơn giản.
3. **Why 2:** Quá trình truy xuất vector và nhồi context quá lớn vào system prompt.
4. **Why 3:** Không áp dụng cơ chế streaming hoặc tối ưu hóa kích thước prompt.
5. **Root Cause:** Cấu trúc model cồng kềnh và thiếu tối ưu hóa pipeline. Đã được khắc phục ở V2 bằng cách chuyển sang `gpt-4o-mini`.

## 4. Kế hoạch cải tiến (Action Plan)
- [x] Thay thế mô hình Agent sang gpt-4o-mini giúp giảm latencies và chi phí cực lớn.
- [x] Tối ưu hóa prompt của Agent để chắt lọc thông tin đầu ra ngắn gọn.
- [ ] Triển khai cơ chế Reranking (ví dụ Cohere Rerank) để cải thiện MRR.
- [ ] Thống nhất Rubrics chi tiết cho Multi-Judge để nâng cao tỉ lệ đồng thuận (Agreement Rate).

---

## 5. Đề xuất giải pháp tối ưu hóa giảm 30% chi phí Eval mà không giảm độ chính xác
Trong quá trình vận hành hệ thống đánh giá tự động (AI Evaluation Factory), chi phí gọi LLM để đánh giá (RAGAS & Multi-Judge) thường chiếm tỉ trọng rất lớn. Chúng tôi đề xuất **3 giải pháp kỹ thuật** giúp giảm ít nhất 30% chi phí này:

### Giải pháp 1: Cascading Judge Routing (Định tuyến Judge phân tầng)
- **Cơ chế:** Thay vì luôn luôn gọi đồng thời cả 2 Judge đắt tiền (`gpt-4o` và `claude-3-5-sonnet`) cho 100% test cases, chúng ta sử dụng một mô hình nhỏ và rẻ tiền (`gpt-4o-mini` hoặc `gemini-1.5-flash`) làm Judge thứ nhất (Tầng 1).
- **Logic:**
  - Nếu Judge Tầng 1 cho điểm cực trị (ví dụ: 1/5 hoặc 5/5) với độ tự tin (confidence score) cao, hệ thống chấp nhận ngay kết quả này và kết thúc.
  - Nếu Judge Tầng 1 cho kết quả mập mờ (điểm từ 2 đến 4) hoặc độ tự tin thấp, hệ thống mới kích hoạt định tuyến lên Judge Tầng 2 đắt tiền (`gpt-4o` / `claude-3-5`).
- **Hiệu quả:** Dự kiến giảm **40% - 50% chi phí eval** vì hơn 70% câu trả lời tốt/rất tệ sẽ được phân loại nhanh ở Tầng 1.

### Giải pháp 2: Semantic Cache cho Evaluation (Lưu trữ đệm ngữ nghĩa)
- **Cơ chế:** Sử dụng thư viện Semantic Caching (như GPTCache) lưu trữ các cặp `(Question, Answer, Ground Truth) -> Evaluation Result`.
- **Logic:** Khi chạy regression test hoặc test lặp lại, nếu khoảng cách ngữ nghĩa (cosine distance of embeddings) của câu hỏi và câu trả lời mới so với dữ liệu đã lưu trong cache nhỏ hơn một ngưỡng $\epsilon$ (ví dụ: 0.98), hệ thống sẽ lấy ngay kết quả chấm điểm trước đó mà không cần gọi LLM Judge.
- **Hiệu quả:** Tiết kiệm **30% - 60% chi phí** đối với các pipeline test hồi quy liên tục nơi dữ liệu ít thay đổi.

### Giải pháp 3: Prompt Token Pruning & Response Formatting
- **Cơ chế:** Rút gọn tối đa thông tin đầu vào gửi cho Judge.
- **Logic:**
  - Thay vì gửi toàn bộ tài liệu gốc làm context cho Judge, ta chỉ gửi phần văn bản trích dẫn (`retrieved_contexts`) đã được rút gọn bằng các thuật toán trích xuất keyword hoặc Sentence-level extraction.
  - Cấu hình Judge trả về định dạng JSON ngắn (ví dụ: chỉ gồm `{"score": X, "reason": "..."}`) để giảm thiểu lượng output token không cần thiết từ Judge.
- **Hiệu quả:** Giảm **20% - 30% số lượng token tiêu thụ**, gián tiếp giảm chi phí trên mỗi lượt gọi API.
