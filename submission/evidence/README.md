# Evidence cá nhân

Đặt ảnh hoặc output text dùng để chấm vào thư mục này. Danh sách đầy đủ xem tại [docs/SUBMISSION.md](../../docs/SUBMISSION.md).

Tên file gợi ý:

```text
01-pytest.txt
02-log-validator.txt
03-dashboard-validator.txt
04-structured-log.png
05-pii-redaction.txt
06-trace-list.png
07-trace-waterfall.png
08-trace-metadata.png
09-prompt-versions.png
10-prompt-rollback.png
11-dashboard-overview.png
12-incident-metric.png
13-incident-log.png
14-incident-trace.png
15-incident-recovery.png
```

Có thể dùng `.txt` cho output của tests/validators. Có thể tách dashboard thành nhiều ảnh nếu một ảnh không đọc rõ.

Evidence CP3 trong repository này là các trích xuất text đã lược bỏ nội dung query: metric từ API, log từ `data/logs.jsonl`, observations từ Langfuse API và kết quả recovery. Đây là output thật, không phải ảnh chụp UI.
Evidence `04`, `05` và `13` lấy từ terminal hoặc `data/logs.jsonl`. Ảnh `06`–`10`, `14` lấy từ project Langfuse cá nhân `day13-k4-l3a-<MSSV>` và nên nhìn thấy tên project. Không mở/chụp trang API Keys.

Từ `submission/REPORT.md`, dẫn ảnh bằng đường dẫn tương đối:

```markdown
![Trace waterfall](evidence/07-trace-waterfall.png)
```

Không commit secret, API key, PII thô hoặc evidence của học viên/lớp khác.
