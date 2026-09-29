# Alert runbooks

Các alert dưới đây dựa trên triệu chứng người dùng/SLO. Kênh chung là Slack
`#llmops-alerts`; mọi thao tác mitigation phải được ghi lại cùng correlation ID mẫu.

## High request latency

- **Severity / duration:** warning trong 5 phút.
- **Điều kiện:** P95 của `response_sent.latency_ms` lớn hơn SLO 3000 ms.
- **Ảnh hưởng:** người dùng phải chờ lâu ở phần đuôi phân phối dù average có thể bình thường.
- **Ba bước đầu:** (1) xác nhận time range và P95/TTFT; (2) lọc log chậm, lấy correlation ID; (3) mở trace cùng ID và so sánh retrieval/generation.
- **Mitigation:** giảm concurrency, tạm dùng retrieval cache hoặc rollback prompt nếu generation tăng bất thường.
- **Owner:** `llm-platform-oncall`.

## Elevated request error rate

- **Severity / duration:** critical trong 5 phút.
- **Điều kiện:** `request_failed / request_received * 100 > 2%`.
- **Ảnh hưởng:** hơn 2% request không trả được câu trả lời.
- **Ba bước đầu:** (1) phân loại theo `error_type`; (2) lấy correlation ID của request lỗi; (3) mở trace và kiểm tra observation lỗi gần nhất.
- **Mitigation:** bật fallback an toàn, giảm traffic tới dependency lỗi và rollback thay đổi gần nhất.
- **Owner:** `llm-platform-oncall`.

## Degraded answer quality

- **Severity / duration:** warning trong 15 phút.
- **Điều kiện:** mean `response_sent.quality_score` thấp hơn 0.75.
- **Ảnh hưởng:** request vẫn thành công nhưng câu trả lời có thể thiếu liên quan hoặc thiếu context.
- **Ba bước đầu:** (1) so sánh quality theo prompt version; (2) kiểm tra retrieval success/doc count; (3) xem trace mẫu và output preview đã scrub.
- **Mitigation:** rollback label `production` về prompt baseline và chuyển request thiếu context sang fallback.
- **Owner:** `ai-quality-oncall`.
