# Nén tệp âm thanh WAV PCM bằng Huffman

Bài giải đầy đủ: **BAI_GIAI_AM_THANH.md**.

Python 3.12 trở lên, chỉ cần thư viện chuẩn. Đã chạy kiểm thử với Python 3.12.14.

```bash
python3 huffman_audio.py compress samples/sine_440hz_16bit_mono.wav audio.huf
python3 huffman_audio.py decompress audio.huf restored.wav
python3 -m unittest -v test_huffman_audio.py
python3 run_experiments.py
```

Tệp đầu ra của CLI phải chưa tồn tại. Tệp .huf là định dạng HAU1 tự thiết kế; giải nén thành WAV trước khi phát.

Huffman mã hóa mọi byte của tệp WAV, bao gồm cấu trúc và metadata; không chuyển đổi mẫu âm thanh. Phạm vi đầu vào: WAV PCM mà wave đọc được. Không phải trình chuyển đổi MP3/AAC.

Bốn mẫu trong samples được tổng hợp bằng run_experiments.py, không phải bản ghi thực tế. results.json lưu kết quả kích thước, tham số WAV, SHA-256 và so sánh byte. Không suy rộng tỷ lệ nén mẫu sang mọi bản ghi âm.

Đã đạt 9 nhóm kiểm thử, gồm 100 WAV PCM giả ngẫu nhiên. Chưa tải lên GitHub; cần bổ sung URL thật trong bài giải trước khi nộp.
