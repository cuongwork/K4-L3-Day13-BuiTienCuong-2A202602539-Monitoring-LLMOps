# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên: Bùi Tiến Cường**
- **MSSV: 2A202602539**
- **Lớp:** K4-L3A
- **Repository URL: https://github.com/cuongwork/K4-L3-Day13-BuiTienCuong-2A202602539-Monitoring-LLMOps.git**
- **Commit SHA cuối:** Chưa chốt; điền SHA sau khi tạo commit cuối cùng.
- **Commit SHA cuối:** Lấy từ `HEAD` sau khi push; nộp cùng repository URL trên LMS.
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602539`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.txt` |
| Log validator | `evidence/02-log-validator.txt` |
| Dashboard validator | `evidence/03-dashboard-validator.txt` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.txt` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard overview image | `evidence/11-dashboard-overview.png` |
| Incident metric values | `evidence/12-incident-metric.txt` |
| Incident log | `evidence/13-incident-log.txt` |
| Incident trace | `evidence/14-incident-trace.txt` |
| Incident recovery | `evidence/15-incident-recovery.txt` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 (21 records; 20 thiếu required fields; 20 thiếu enrichment; 0 correlation IDs) | 100/100 (91 records; 0 thiếu fields/enrichment; 44 correlation IDs; 0 PII leaks) | Baseline CP0 chưa đạt là dự kiến vì TODO của CP1 chưa được triển khai. |
| `validate_dashboard.py` | Hợp lệ 6/6 panel | Hợp lệ 6/6 panel | Snapshot SVG được sinh từ 23 structured log records gần nhất; CP3 có snapshot riêng theo đúng challenge window. |
| `validate_dashboard.py` | Hợp lệ 6/6 panel | Hợp lệ 6/6 panel | Contract validator đạt đủ sáu panel; dashboard overview có ảnh PNG riêng. |
| `pytest` | 22 passed in 2.44s | 24 passed in 2.46s | Chạy bằng Python 3.12 và `--basetemp .pytest-tmp` do thư mục Temp mặc định bị lỗi quyền trên Windows. |
| Số traces hợp lệ | Workload mẫu gồm 10 request; tracing được bật | 54 root traces | Đếm qua Langfuse Observations API v2 trong project cá nhân sau CP3/recovery. |
| Số PII leak | 0 trong 21 log records | 0 trong 91 log records | Validator hiện tại không phát hiện PII. |
| Latency P95 / TTFT P95 | Không lưu baseline CP0 | CP3: 4081 / 50 ms | Đúng 5 challenge requests; ngưỡng challenge 2000 ms. |
| Retrieval success rate | Không lưu baseline CP0 | CP3: 100% (5/5); recovery: 100% (5/5) | Tất cả challenge/recovery response logs có `tool_success=true`. |

### Baseline CP0

- `/health`: `ok: true`, `tracing_enabled: true`, không có incident đang bật.
- Load test: 10/10 request trả HTTP 200 và tạo `data/logs.jsonl`.
- Correlation ID trong response đang là `MISSING`; đây là TODO thuộc CP1, chưa sửa tại CP0.
- Môi trường ban đầu dùng Python 3.14 nên không cài được dependency khóa `pydantic==2.11.4`; đã tạo lại `.venv` bằng Python 3.12 theo yêu cầu Python 3.11+ của bài.
- Evidence output: [`evidence/00-cp0-baseline.txt`](evidence/00-cp0-baseline.txt).

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa context ở đầu mỗi request, chỉ nhận header đúng `req-<8-hex>`; header sai hoặc thiếu được thay bằng ID sinh từ UUID. ID được bind vào structlog, lưu ở `request.state`, rồi trả qua `x-request-id`; thời gian xử lý trả qua `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model` và `env` được bind trước event `request_received`, nên dùng chung cho các log API trong request.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` chạy sau khi merge context nhưng trước `JsonlFileProcessor` và `JSONRenderer`. Processor scrub đệ quy mọi chuỗi trong dict/list/tuple, bao phủ cả payload và error metadata.
- **Cách kiểm chứng kết quả:** Workload tạo 12 correlation IDs; header hợp lệ `req-deadbeef` được giữ lại, header không hợp lệ được thay bằng ID đúng format. Validator đạt 100/100 và tìm kiếm raw email/điện thoại/CCCD/thẻ/hộ chiếu đều không còn trong log. Xem [`evidence/02-log-validator.txt`](evidence/02-log-validator.txt).

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Chạy workload bằng key project cá nhân, sau đó truy vấn Langfuse Observations API v2 theo tên root `lab-agent-run`; truy vấn hiện tại trả 54 root observations/trace IDs sau CP3 và recovery.
- **Cấu trúc root/retrieval/generation observations:** Root `lab-agent-run` loại AGENT có child `retrieval` loại RETRIEVER và `generation` loại GENERATION. Generation chứa model, prompt link, input/output/total tokens, total cost và TTFT; input/output chỉ lưu preview đã scrub.
- **Cách nối trace với log:** `correlation_id` được propagate vào metadata của cả ba observations và trùng ID trong structured log.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** version 1, labels `baseline` và `production` sau rollback.
- **Version/label candidate:** version 2, label `candidate`.
- **Trace ID của mỗi version:** baseline v1 `ca62d602d56910ee0fc62a80a9a74827`; candidate v2 `ac1b99002177dd70ea37a815807f9867`; production sau rollback v1 `975e920979bc2761be28402e028b73ee`.
- **Cách promote và rollback `production`:** Tạo v1 với baseline/production, tạo v2 candidate, chuyển `production` sang v2 qua Prompt Version API, rồi chuyển lại v1. Trace production cuối xác nhận prompt `day13-chat@1`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `config/dashboard.yaml` định nghĩa nguồn `data/logs.jsonl`, time range 60 phút, refresh mục tiêu 30 giây và sáu panel latency/TTFT, traffic, errors/retrieval, cost, tokens, quality. Contract validator đạt 6/6. Dashboard overview image: [`evidence/11-dashboard-overview.png`](evidence/11-dashboard-overview.png).
- **SLO và lý do chọn:** 99.5% request thành công trong 28 ngày phải có latency ≤ 3000 ms. Ngưỡng cao hơn baseline khoảng 0.4–1.6 giây nhưng đủ nhạy để phát hiện `rag_slow` cộng 2.5 giây.
- **Cách tính error budget:** 100% − 99.5% = 0.5%; cửa sổ 28 ngày có 40,320 phút nên budget là 201.6 phút, tương đương tối đa 50 bad events trên 10,000 request nếu traffic phân bố đều.
- **Ba alert và runbook tương ứng:** P95 latency > 3000 ms trong 5m; error rate > 2% trong 5m; mean quality < 0.75 trong 15m. Tất cả symptom-based, có severity, owner, Slack `#llmops-alerts` và runbook tại [`docs/alerts.md`](../docs/alerts.md).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1` (K4, incident `rag_slow`, feature `monitoring`).
- **Khoảng thời gian điều tra:** `2026-09-29T09:35:45.672553Z`–`2026-09-29T09:36:00.813561Z`, theo request đầu và response cuối trong structured log.
- **Triệu chứng từ metrics:** Challenge threshold là 2000 ms. Snapshot sau đúng 5 challenge requests ghi P50 2653 ms, P95/P99 4081 ms; cả 5 latency đều vượt ngưỡng, TTFT P95 là 50 ms và error breakdown rỗng. Xem [metric output](evidence/12-incident-metric.txt).
- **Log line và correlation ID liên quan:** `data/logs.jsonl:71`, `response_sent`, correlation ID `req-de1bb63f`, latency 4081 ms. Xem [incident log evidence](evidence/13-incident-log.txt).
- **Trace ID và span gây ảnh hưởng:** Trace `335133736374cd29fdf485b35210a968`, cùng correlation ID `req-de1bb63f`. Root `lab-agent-run` mất 4.082 s; child `retrieval` mất 2.501 s; `generation` mất 0.153 s. Có khoảng 1.427 s giữa retrieval kết thúc và generation bắt đầu; `resolve_prompt()` chạy trong đoạn này và trace ghi `prompt_source=langfuse`, nhưng không có span riêng để xác định chính xác phần thời gian đó. Xem [incident trace evidence](evidence/14-incident-trace.txt).
- **Root cause:** Challenge bật `rag_slow`; [app/mock_rag.py](../app/mock_rag.py) chèn `time.sleep(2.5)` trong retrieval. Độ trễ retrieval 2.501 s khớp với injected delay và tự nó vượt challenge threshold 2000 ms, giải thích việc cả 5 request đều vượt ngưỡng. Phần 1.427 s chưa được phân giải riêng, nên không quy nó cho retrieval.
- **Fix action:** Sau khi lưu evidence, tắt incident mô phỏng bằng `python scripts/inject_incident.py --disable`; `/health` xác nhận `rag_slow=false`. Chạy lại cùng challenge workload: 5/5 request HTTP 200, application latency 151–175 ms, đều dưới 2000 ms. Đây là recovery của mock challenge, không phải thay đổi production; xem [recovery evidence](evidence/15-incident-recovery.txt).
- **Preventive measure:** Với hệ thống thật, đặt alert cho retrieval-span P95 vượt 2000 ms, thêm timeout/fallback cho retrieval, và kiểm tra regression/load test có fault injection. Đây là khuyến nghị, chưa được triển khai hoặc kiểm chứng trong production.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Dùng `correlation_id` làm khóa nối log với trace và lọc đúng challenge window, thay vì suy root cause từ P95 tổng hợp có cả lượt recovery. PII scrub được đặt trước bước serialize/ghi file để không lưu raw PII.
- **Một lỗi/blocker đã gặp:** Lệnh `python` ban đầu dùng Python hệ thống không có `httpx`; Python trong `.venv` có dependency đúng nhưng API chưa chạy nên request injection bị từ chối. Khởi động API bằng interpreter của `.venv`, sau đó chạy lại script thành công.
- **Cách tìm nguyên nhân và xử lý:** `/metrics` cho thấy P95 4081 ms vượt challenge threshold 2000 ms; log `req-de1bb63f` trỏ tới trace tương ứng. Waterfall đo retrieval 2.501 s, khớp `time.sleep(2.5)` của incident `rag_slow`; tắt injection và chạy lại workload xác nhận 5/5 latency về 151–175 ms.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics phát hiện loại triệu chứng và khoảng thời gian; log cung cấp `correlation_id` của request bất thường; trace có cùng ID cho biết span nào tiêu thời gian. Trong trace này còn 1.427 s chưa được tách span nên không gán phần đó cho retrieval.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Version/label Langfuse giúp biết prompt nào phục vụ request và rollback về version đã biết; token/cost đo mức tiêu thụ; SLO đặt ngưỡng đánh giá latency/error và error budget. Đây là các tín hiệu vận hành, không thay thế việc kiểm tra trace.
- **Điều quan trọng nhất đã học:** P95 giúp phát hiện tail latency nhưng không tự chỉ ra nguyên nhân. Cần nối cùng request qua metric, log và trace; nếu waterfall còn khoảng không instrument thì ghi nhận đó là chưa rõ, không đoán.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Dashboard SVG là snapshot tĩnh, không tự refresh. Prompt resolution chưa có span riêng nên chưa phân giải được khoảng 1.427 s. Challenge là mock injection; chưa triển khai hoặc kiểm chứng production fix. Cần chốt commit SHA và xác nhận ảnh dashboard/Langfuse hiện có trước khi nộp.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** CP3 metric evidence là output text; chưa có ảnh dashboard runtime riêng cho CP3. Prompt resolution chưa có span riêng nên chưa phân giải được khoảng 1.427 s. Challenge là mock injection; chưa triển khai hoặc kiểm chứng production fix. Cần rà nội dung hiển thị của ảnh Langfuse trước khi nộp.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** CP3 metric evidence hiện là output text, chưa có screenshot dashboard runtime riêng. Prompt resolution chưa có span riêng nên chưa phân giải được khoảng 1.427 s. Challenge là mock injection; chưa triển khai hoặc kiểm chứng production fix. Cần rà ảnh evidence trước khi nộp.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả đường dẫn evidence trong report là tương đối và trỏ tới file hiện có.
- [x] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Chưa xác minh cài đặt sạch theo README; test và validators đã pass trong `.venv` hiện có.
- [ ] Đã rà toàn bộ ảnh/output để chắc không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
