# BÀI KIỂM TRA GIỮA KỲ – MÔN THUẬT TOÁN NÂNG CAO
## Đề tài: Nén không mất mát tệp âm thanh WAV PCM bằng mã Huffman

**Loại dữ liệu được chọn:** tệp âm thanh.  
**Phạm vi triển khai:** tệp WAV PCM chưa nén mà thư viện wave của Python đọc được.  
**Ngôn ngữ:** Python 3; kiểm thử bằng Python 3.12.14, chỉ dùng thư viện chuẩn.  
**Trạng thái GitHub:** chưa tải mã lên GitHub, chưa có URL thật. Cần bổ sung trước khi nộp.

## 1. Cơ sở tài liệu và mục tiêu

Đề “BÀI KIỂM TRA GIỮA KỲ.pdf”, trang 1 yêu cầu vận dụng Huffman Codes và Data Compression, chọn một trong ba loại dữ liệu; trình bày thuật toán, tính O, Ω, Θ, đánh giá độ phức tạp; mã nguồn tải lên GitHub và ghi liên kết trong bài. Bài này chọn duy nhất **tệp âm thanh**.

Cơ sở thuật toán là mục 15.3 “Huffman codes” trong *Introduction to Algorithms*, Fourth Edition, Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein, MIT Press, 2022. Tài liệu người học đã cung cấp có tên Algorithms2022.pdf; phần đã đối chiếu nằm ở trang PDF 570–579. Bài áp dụng nguyên lý mã tiền tố, min-heap, lựa chọn tham lam và cấu trúc con tối ưu trong mục này. Các định nghĩa O, Ω, Θ theo chương 3.

Tài liệu kỹ thuật âm thanh bổ sung được kiểm tra từ nguồn chính thức: Microsoft Learn về WAVEFORMATEX và tài liệu Python 3.12 về wave. Hai nguồn này dùng để giải thích tham số PCM và cách đọc WAV, không dùng thay nguồn lý thuyết Huffman. Danh mục liên kết ở cuối bài.

**Mục tiêu:** tạo tệp nén từ một tệp WAV PCM, sau đó giải nén để thu lại chính xác toàn bộ tệp WAV gốc, bao gồm dữ liệu âm thanh và thông tin đi kèm. Đây là nén không mất mát.

Định dạng HAU1, mã Python, ví dụ minh họa và các mẫu âm thanh trong gói bài là phần triển khai tự xây dựng. Không trình bày chúng như kết quả có sẵn trong giáo trình. Không có bản ghi giọng nói hoặc nhạc thực tế do người học cung cấp; toàn bộ mẫu âm thanh thực nghiệm được tổng hợp bằng chương trình.

## 2. Kiến thức cần dùng về âm thanh số

PCM biểu diễn tín hiệu âm thanh bằng các giá trị mẫu số. Các tham số cần phân biệt:

| Thuật ngữ | Ý nghĩa trong bài |
|---|---|
| Tần số lấy mẫu R | Số thời điểm lấy mẫu mỗi giây trên mỗi kênh, đơn vị Hz |
| Số kênh C | Mono: 1 kênh; stereo: 2 kênh |
| Độ rộng mẫu q | Số byte dùng để lưu một giá trị mẫu của một kênh |
| Frame | Tập giá trị mẫu của tất cả các kênh tại cùng một thời điểm |
| Byte | Đơn vị 8 bit; một mẫu PCM 16 bit chiếm 2 byte |

Với PCM có độ rộng mẫu nguyên byte, N frame chiếm N×C×q byte dữ liệu âm thanh. Thời lượng là N/R giây. Trong ví dụ 1 giây, 16.000 Hz, mono, 16 bit:

N = 16.000; C = 1; q = 2 ⇒ dữ liệu PCM = 16.000×1×2 = 32.000 byte.

Tệp WAV mẫu do chương trình tạo có thêm 44 byte cấu trúc WAV cơ bản nên tổng cộng 32.044 byte. **Không khẳng định mọi tệp WAV đều có header 44 byte:** tệp khác có thể có thêm các chunk/thông tin mở rộng.

### Đơn vị mà Huffman mã hóa

Bài này áp dụng Huffman lên **từng byte của toàn bộ tệp WAV**, không coi mỗi mẫu PCM 16 bit là một ký hiệu Huffman. Do đó:

- Mỗi ký hiệu có giá trị từ 0 đến 255; bảng ký hiệu có tối đa 256 phần tử.
- Hai byte của một mẫu PCM 16 bit được xử lý như hai byte riêng biệt.
- Byte thuộc cấu trúc WAV và metadata cũng được nén, giúp khôi phục nguyên tệp.
- Không đổi tần số lấy mẫu, không giảm độ rộng mẫu, không loại bỏ kênh, không làm tròn lại tín hiệu khi nén.

Cách làm này là một bộ nén Huffman theo byte áp dụng cho tệp âm thanh, chưa phải một codec chuyên khai thác tương quan giữa các mẫu âm thanh.

## 3. a) Trình bày thuật toán

### 3.1. Ý tưởng Huffman

Đếm số lần xuất hiện của mỗi byte. Dùng các tần suất này xây dựng cây nhị phân; mỗi lá chứa một byte. Gán nhánh trái là 0, nhánh phải là 1. Chuỗi bit trên đường đi từ gốc đến lá là mã của byte đó.

Huffman tạo mã tiền tố: không có từ mã nào là tiền tố của một từ mã khác. Vì vậy, quá trình giải mã xác định được từng ký hiệu mà không cần dấu phân cách.

Đặt f(c) là tần suất của byte c và l(c) là độ dài mã. Số bit của phần dữ liệu mã hóa là:

**B = Σ f(c)×l(c).**

Huffman tối thiểu hóa tổng này trong lớp mã nhị phân tiền tố mã hóa từng ký hiệu độc lập với tần suất đã biết. Tính tối ưu này không có nghĩa là tốt nhất trong mọi thuật toán nén âm thanh hoặc luôn giảm kích thước toàn bộ tệp.

### 3.2. Các bước nén WAV

1. Đọc tệp WAV dưới dạng byte.
2. Dùng wave để đọc tham số và xác nhận kiểu PCM được hỗ trợ; kiểm tra đủ số byte PCM tương ứng số frame khai báo. Không dùng wave để ghi lại tệp gốc.
3. Đếm tần suất tất cả byte của tệp, kể cả phần cấu trúc WAV.
4. Tạo một nút lá cho mỗi byte có tần suất dương; tạo min-heap theo tần suất.
5. Lấy hai nút nhỏ nhất x, y; ghép thành nút cha có tần suất f(x)+f(y); đưa nút cha trở lại heap. Lặp đến khi còn một nút gốc.
6. Duyệt cây để sinh bảng mã; thay từng byte gốc bằng mã tương ứng.
7. Đóng gói các bit thành byte và ghi tệp nén HAU1 với phần thông tin phụ để dựng lại cây.

Quy tắc khi hòa tần suất: các lá được tạo theo giá trị byte tăng dần, mỗi nút có số thứ tự tạo duy nhất. Heap so sánh tần suất trước, số thứ tự sau. Bên nén và giải nén dùng cùng quy tắc để tái tạo cùng cây.

```text
HUFFMAN(F):
    Q ← min-heap các nút lá có tần suất dương trong F
    nếu Q rỗng: trả về cây rỗng
    trong khi |Q| > 1:
        x ← EXTRACT_MIN(Q)
        y ← EXTRACT_MIN(Q)
        z ← nút có trái=x, phải=y, freq=x.freq+y.freq
        INSERT(Q, z)
    trả về nút duy nhất còn lại

COMPRESS_WAV(D):
    kiểm tra D là WAV PCM được hỗ trợ
    F ← đếm tần suất tất cả byte trong D
    T ← HUFFMAN(F)
    C ← sinh bảng mã từ T
    P ← mã hóa và đóng gói bit của D theo C
    trả về header_HAU1(F) cùng P
```

### 3.3. Tệp nén và cách giải nén

Định dạng **HAU1** là định dạng minh họa do bài làm thiết kế, không phải định dạng codec âm thanh tiêu chuẩn. Có thể đặt tên tệp đầu ra là audio.wav.huf. Tệp .huf không phát trực tiếp như WAV; phải giải nén trước.

| Thành phần HAU1 | Kích thước |
|---|---:|
| Dấu nhận dạng HAU1 | 4 byte |
| Số byte phân biệt k | 2 byte |
| Mỗi mục tần suất | 1 byte giá trị + 8 byte tần suất |
| Dữ liệu mã hóa đã đóng gói | ceil(B/8) byte |

Các số nguyên trong header HAU1 được ghi big-endian; byte của tệp WAV gốc được giữ nguyên như đầu vào, không chuyển đổi thứ tự byte của mẫu âm thanh. Mỗi tần suất trong định dạng phải nhỏ hơn 2^64.

**Kích thước toàn bộ tệp nén: S_nén = 6 + 9k + ceil(B/8) byte.**

Phân biệt hai phần: cấu trúc WAV gốc nằm bên trong dữ liệu được mã hóa; header HAU1 nằm bên ngoài và phục vụ bộ giải nén Huffman. Không nhầm chúng là một header.

Giải nén:

1. Kiểm tra HAU1, đọc k và bảng tần suất.
2. Tái tạo cây theo cùng quy tắc; tính B từ bảng mã và tần suất.
3. Kiểm tra kích thước payload và bit đệm; chỉ đọc đúng B bit hữu ích.
4. Từ gốc, gặp 0 đi trái, gặp 1 đi phải. Gặp lá thì xuất byte và trở lại gốc.
5. Kiểm tra tần suất byte đầu ra khớp bảng tần suất.
6. Kiểm tra dữ liệu khôi phục được đọc là WAV PCM rồi ghi nguyên byte ra tệp .wav.

Tệp WAV có 0 frame vẫn có cấu trúc WAV; nó không phải tệp 0 byte. Giao diện nén âm thanh từ chối tệp 0 byte vì không phải WAV. Lõi Huffman vẫn được kiểm thử riêng với dữ liệu rỗng và dữ liệu một ký hiệu; trường hợp một ký hiệu dùng từ mã 0 dài 1 bit.

### 3.4. Ví dụ tính tay gắn với âm thanh

Xét riêng một đoạn PCM mono 8 bit có 8 giá trị mẫu biểu diễn bằng 8 byte:

**128, 128, 128, 128, 129, 129, 130, 131.**

Đây là ví dụ nhỏ tự xây dựng để tính tay, chưa phải một tệp WAV hoàn chỉnh vì chưa bao gồm cấu trúc WAV.

| Giá trị byte | Tần suất | Mã Huffman | Số bit đóng góp |
|---|---:|---|---:|
| 128 | 4 | 0 | 4 |
| 129 | 2 | 10 | 4 |
| 130 | 1 | 110 | 3 |
| 131 | 1 | 111 | 3 |
| Tổng | 8 | | 14 |

Các lần ghép theo quy tắc của chương trình: (130,131) có tổng tần suất 2; ghép byte 129 với nhóm này được 4; ghép byte 128 với nhóm còn lại được 8.

Chuỗi mã là **00001010110111**, dài 14 bit so với 8×8=64 bit của đoạn PCM gốc. Đóng gói cần 2 byte, gồm 14 bit hữu ích và 2 bit đệm.

Nếu chỉ mã hóa riêng 8 byte này bằng lõi HAU1 thì cần 6+9×4+2=44 byte. Vì vậy, giảm số bit payload không đồng nghĩa giảm tổng dung lượng sau khi cộng header. Ví dụ này không thay thế thực nghiệm nén các tệp WAV đầy đủ ở mục 6.

### 3.5. Tính đúng và tính tối ưu

**Bảo toàn dữ liệu:** mã tiền tố cho phép tách dãy bit thành các ký hiệu duy nhất. Cây được tái dựng nhất quán, số bit hữu ích được xác định; mỗi byte được khôi phục đúng theo thứ tự ban đầu. Vì bộ nén không biến đổi mẫu và không ghi lại cấu trúc WAV, đầu ra giải nén phải trùng toàn bộ byte với đầu vào khi tệp nén không bị thay đổi.

**Lựa chọn tham lam:** bổ đề 15.2 trong tài liệu chỉ ra tồn tại một cây tối ưu có hai ký hiệu tần suất nhỏ nhất là hai lá anh em ở độ sâu lớn nhất. Vì vậy có thể ghép hai ký hiệu nhỏ nhất trước mà vẫn giữ được nghiệm tối ưu.

**Cấu trúc con tối ưu:** gộp hai ký hiệu x, y thành z với f(z)=f(x)+f(y). Nếu cây cho bài toán rút gọn tối ưu thì mở z thành hai con x, y cho cây tối ưu của bài toán ban đầu. Chi phí tăng đúng f(x)+f(y). Lặp lập luận này chứng minh tính tối ưu của Huffman trong phạm vi mã tiền tố từng ký hiệu.

## 4. b) Tính O, Ω, Θ

### 4.1. Định nghĩa và biến đầu vào

- n: tổng số byte của tệp WAV, gồm cả cấu trúc và dữ liệu PCM.
- k: số giá trị byte khác nhau, k≤256.
- B: số bit payload Huffman.
- L: tổng độ dài các từ mã khác nhau, L=Σ l(c).

O là giới hạn trên, Ω là giới hạn dưới, Θ là giới hạn chặt cùng bậc. Chúng không lần lượt đồng nghĩa với xấu nhất, tốt nhất và trung bình.

Phân tích theo mô hình RAM thông thường: phép toán cơ bản trên byte, chỉ số và tần suất được coi là hằng số. Không phân tích chi phí từng bit của số nguyên không giới hạn. log là log cơ số 2. Thời gian tính theo lượng công việc, không phải số giây đã đo.

### 4.2. Phân tích các bước

| Bước | Phân tích |
|---|---|
| Đọc tệp, kiểm tra WAV, đếm tần suất | Θ(n) với WAV hợp lệ |
| Sắp thứ tự k lá để xử lý hòa nhất quán | O(k log k) |
| Tạo min-heap | Θ(k) |
| Dựng cây với k−1 lần ghép | O(k log k); ít nhất Ω(k) công việc |
| Sinh bảng mã trong bản dùng nối chuỗi Python | Giới hạn trên an toàn O(k²) khi tổng quát hóa k |
| Mã hóa từng byte và đóng gói bit | Θ(n+B) |
| Ghi header và payload | Θ(k+ceil(B/8)+1) |

Dựng cây: mỗi lần ghép gồm hai lần EXTRACT_MIN và một lần INSERT, mỗi thao tác có giới hạn O(log k). Với k−1 lần ghép và heapify O(k):

T_cây = O(k) + (k−1)O(log k) = **O(k log k)**, với k≥2.

Đây là giới hạn trên cho phần dựng cây, chưa bao gồm đọc và mã hóa toàn bộ âm thanh. Không thay k bằng n chỉ vì cả hai đều là kích thước đầu vào theo những nghĩa khác nhau.

Sinh mã: cây có O(k) nút nhưng phép nối prefix+'0'/'1' sao chép chuỗi. Độ sâu tối đa k−1 và có O(k) cạnh nên dùng giới hạn an toàn O(k²). Không mặc nhiên coi toàn bộ bước sinh chuỗi từ mã là Θ(k).

Giới hạn trên tổng quát cho cách triển khai là:

**T_nén(n,k,B) = O(n + k log k + k² + B + 1).**

Một giới hạn dưới theo lượng công việc bắt buộc là Ω(n+B+k+L+1). Không kết luận Θ tổng quát chỉ từ các giới hạn trên và dưới chưa cùng dạng.

### 4.3. Kết quả chặt của bản nén WAV theo byte

Khi xét kích thước tệp n tăng, k luôn không vượt quá 256, nên chi phí chỉ phụ thuộc k bị chặn bởi hằng số theo n.

Hơn nữa, mã cố định 8 bit cho mỗi byte là một mã tiền tố hợp lệ. Huffman tối ưu payload nên **B≤8n**; trường hợp chỉ một byte phân biệt có B=n theo quy ước chương trình, cũng thỏa bất đẳng thức này. Vì phải đọc đủ n byte, thuật toán có cả giới hạn trên và dưới tuyến tính:

| Nội dung được xét | O | Ω | Θ |
|---|---|---|---|
| Nén toàn bộ WAV hợp lệ bằng bản theo byte này | O(n) | Ω(n) | Θ(n) |
| Giải nén HAU1 hợp lệ chứa WAV | O(n) | Ω(n) | Θ(n) |

Ở dòng giải nén, n là số byte WAV được khôi phục. Các chi phí kiểm tra WAV và đối chiếu tần suất cũng tuyến tính, không đổi kết luận. Các kết quả này áp dụng cho đầu vào hợp lệ; thời gian từ chối đầu vào sai định dạng có thể khác.

Không cần dùng n+1 để bao gồm tệp 0 byte ở giao diện âm thanh, vì tệp đó bị từ chối. Lõi Huffman tổng quát có thể viết Θ(n+1) để bao gồm dữ liệu rỗng.

## 5. c) Đánh giá độ phức tạp và hiệu quả

### 5.1. Bộ nhớ

Với k≥1, cây có k lá và k−1 nút trong, tổng 2k−1 nút. Cây, heap và bảng tần suất cần O(k) phần tử; chuỗi bảng mã có tổng độ dài L, với L≤k(k−1) khi k≥2.

Chương trình đọc toàn bộ WAV vào RAM, đọc vùng PCM để kiểm tra, giữ payload và tạo một số bản sao byte khi ghép kết quả. Giới hạn bộ nhớ an toàn là **O(n+ceil(B/8)+k²+1)**. Vì k≤256 và B≤8n, bộ nhớ toàn bộ bản triển khai là **Θ(n)** cho WAV hợp lệ. Giải nén cũng Θ(n) theo số byte WAV đầu ra.

Không chỉ ghi O(k) cho toàn bộ chương trình vì như vậy bỏ qua bộ nhớ giữ tệp. Bản này chưa xử lý dữ liệu theo khối để giảm bộ nhớ đỉnh.

### 5.2. Cách tính hiệu quả dung lượng

S_gốc = n byte; S_nén = 6+9k+ceil(B/8) byte.

**Tiết kiệm (%) = (1−S_nén/S_gốc)×100%.**

Giá trị dương nghĩa là giảm dung lượng; âm nghĩa là tệp nén lớn hơn. Mặc dù B≤8n, header HAU1 có thể khiến tổng tệp nén lớn hơn. Vì thế phải báo cáo cả header, không chỉ payload.

### 5.3. Ưu điểm và hạn chế

- Khôi phục nguyên byte; không mất dữ liệu âm thanh và thông tin kèm theo trong các WAV được hỗ trợ.
- Minh họa trực tiếp chiến lược tham lam và mã tiền tố, không gọi thư viện nén có sẵn thay cho Huffman.
- Có thể nén tốt dữ liệu lệch tần suất mạnh, chẳng hạn mẫu im lặng 16 bit của thực nghiệm.
- Bản theo byte không khai thác trực tiếp tương quan giữa các mẫu PCM hoặc các kênh. Với phân bố byte gần đều, payload ít giảm và header có thể làm tổng tệp tăng.
- Chưa sử dụng dự đoán mẫu hoặc mã hóa sai phân trước Huffman; đây chỉ là hướng mở rộng, không phải tính năng đã thực hiện hay đã đo kết quả.
- Xử lý từng bit bằng Python và giữ toàn bộ tệp trong RAM hạn chế tốc độ thực tế, quy mô tệp. Không suy ra tốc độ cụ thể chỉ từ Θ(n).
- Giao diện này không hỗ trợ MP3, AAC hoặc WAV chứa dữ liệu nén mà wave không đọc được. Không kết luận về hiệu quả nén các định dạng đó từ thực nghiệm WAV PCM.
- HAU1 chưa có checksum tích hợp. Kiểm tra cấu trúc và tần suất không phát hiện chắc chắn mọi thay đổi dữ liệu. SHA-256 trong thực nghiệm là kiểm chứng bên ngoài, không phải trường dữ liệu bên trong HAU1.

## 6. Thực nghiệm đã thực hiện

### 6.1. Nguồn dữ liệu và điều kiện

Bốn mẫu đều **tự tổng hợp**, thời lượng 1 giây, tần số lấy mẫu 16.000 Hz, PCM 16 bit. Ba mẫu mono, một mẫu stereo. Chương trình run_experiments.py tạo mẫu và chạy nén/giải nén.

- Im lặng: toàn bộ mẫu PCM 16 bit bằng 0.
- Sin 440 Hz mono: x[i]=round(12000×sin(2π×440×i/16000)), i từ 0 đến 15.999.
- Nhiễu mono: số nguyên giả ngẫu nhiên từ −32768 đến 32767, seed=20261031; sinh bằng random.Random của Python.
- Stereo: kênh trái sin 440 Hz, kênh phải sin 660 Hz, cùng biên độ số 12.000; hai kênh xen kẽ trong dữ liệu PCM.

Các giá trị sin được lượng tử hóa khi **tạo tệp thử**. Trong quá trình nén và giải nén không thực hiện lại lượng tử hóa hay biến đổi giá trị mẫu. Đây là các tín hiệu đơn giản phục vụ kiểm thử, không phải tập dữ liệu đại diện cho giọng nói hoặc âm nhạc thực tế. Kết quả không được suy rộng thành tỷ lệ nén chung cho âm thanh.

### 6.2. Kết quả đo kích thước thực tế

| Mẫu | Byte WAV gốc | k | Bit payload | Byte HAU1 | Tiết kiệm |
|---|---:|---:|---:|---:|---:|
| Im lặng mono | 32.044 | 21 | 32.159 | 4.215 | 86,85% |
| Sin 440 Hz mono | 32.044 | 187 | 231.552 | 30.633 | 4,40% |
| Nhiễu mono | 32.044 | 256 | 256.352 | 34.354 | −7,21% |
| Sin 440/660 Hz stereo | 64.044 | 219 | 470.209 | 60.754 | 5,14% |

Tỷ lệ tính cả header HAU1; số liệu là kết quả thực sự chạy chương trình, không phải tỷ lệ dự kiến.

Kiểm tra chéo ví dụ im lặng:

S_nén = 6+9×21+ceil(32159/8) = 195+4020 = **4.215 byte**.

Tiết kiệm = (1−4215/32044)×100% ≈ **86,85%**.

Vì nén toàn tệp WAV, mẫu im lặng có 21 byte phân biệt do phần cấu trúc WAV; không được ghi k=1 chỉ vì toàn bộ mẫu tín hiệu bằng 0.

Với nhiễu, B=256.352=8×32.044 nên payload không giảm. Header HAU1 có 6+9×256=2.310 byte, làm tổng tệp thành 34.354 byte. Đây là trường hợp nén không hiệu quả được giữ lại để đánh giá trung thực.

### 6.3. Kiểm chứng đầu ra

Cả bốn mẫu đều đạt:

1. Dữ liệu sau giải nén bằng dữ liệu WAV gốc khi so sánh từng byte.
2. SHA-256 trước/sau giống nhau; lưu đầy đủ trong results.json.
3. Các tham số số kênh, độ rộng mẫu, tần số lấy mẫu, số frame và thời lượng không đổi khi đọc lại WAV.

Đã chạy 9 nhóm unittest và tất cả đạt, gồm 100 WAV PCM giả ngẫu nhiên có thông số khác nhau; WAV có 0 frame; im lặng 8/16 bit; một số độ rộng mẫu khác mà wave đọc được; kiểm tra giữ nguyên chunk JUNK; từ chối đầu vào không phải WAV hoặc PCM bị cắt; trường hợp biên của lõi; tính tiền tố; lỗi HAU1; công thức kích thước, tính xác định và B≤8n trên mẫu kiểm tra.

Một nhóm kiểm tra đối chiếu payload 224.000 bit của ví dụ tần suất trong giáo trình để kiểm tra lõi Huffman. Đây là phép đối chiếu lý thuyết, không được tính là thực nghiệm âm thanh.

Đã chạy giao diện dòng lệnh nén và giải nén mẫu sin 440 Hz mono, rồi dùng cmp kiểm tra hai tệp WAV giống hệt nhau. Không sử dụng nghe bằng tai làm bằng chứng duy nhất và không tuyên bố đã đánh giá cảm nhận thính giác.

Kiểm thử xác nhận các trường hợp đã chạy, không bảo đảm chương trình không còn lỗi với mọi tệp có thể có. Lập luận tính đúng thuật toán nằm ở mục 3.5.

## 7. Mã nguồn và hướng dẫn chạy

Các tệp trong gói:

| Tệp | Nội dung |
|---|---|
| huffman_audio.py | Cây Huffman, bảng mã, nén/giải nén, kiểm tra WAV, giao diện dòng lệnh |
| test_huffman_audio.py | 9 nhóm kiểm thử tự động |
| run_experiments.py | Sinh bốn mẫu WAV, nén/giải nén và lưu kết quả |
| results.json | Thông số âm thanh, kích thước, tỷ lệ và SHA-256 đã chạy |
| samples/ | Bốn WAV tổng hợp và bốn tệp .huf tương ứng |
| README.md | Hướng dẫn ngắn |

Chạy từ thư mục chứa mã nguồn, dùng Python 3.12 trở lên:

```bash
# Nén tệp WAV mẫu
python3 huffman_audio.py compress samples/sine_440hz_16bit_mono.wav audio.huf

# Giải nén nguyên tệp WAV
python3 huffman_audio.py decompress audio.huf restored.wav

# Chạy kiểm thử
python3 -m unittest -v test_huffman_audio.py

# Tạo lại bốn mẫu thử và results.json
python3 run_experiments.py
```

Muốn xử lý tệp âm thanh khác, thay đường dẫn đầu vào bằng WAV PCM của người dùng. Chương trình không ghi đè tệp đích đã tồn tại và không cho nguồn/đích cùng đường dẫn. Khi chạy lại lệnh CLI, cần chọn tên đầu ra mới. Chương trình thực nghiệm chủ động tạo lại các mẫu tổng hợp cố định trong thư mục samples.

Chức năng các hàm:

- wav_info: đọc/kiểm tra WAV và trả các tham số.
- build_tree: ghép các nút nhỏ nhất bằng min-heap.
- build_codes: tạo mã tiền tố từ cây.
- compress_bytes/decompress_bytes: lõi Huffman cho dãy byte.
- compress_wav/decompress_wav: kiểm tra phạm vi WAV và gọi lõi.

## 8. GitHub

**Liên kết GitHub: https://github.com/haihathanhnienviet-arch/huffman-audio**

## 9. Kết luận

Bài làm áp dụng Huffman theo byte cho tệp WAV PCM để nén không mất mát. Lựa chọn tham lam là ghép hai nút tần suất nhỏ nhất. Phần dựng cây có giới hạn O(k log k); toàn bộ bản theo byte cố định có thời gian Θ(n), bộ nhớ Θ(n) với WAV hợp lệ. Kết quả bốn mẫu tổng hợp xác nhận khôi phục đúng từng byte và cho thấy hiệu quả dung lượng phụ thuộc dữ liệu: có mẫu giảm rõ rệt, có mẫu tăng sau khi tính header.

## Tài liệu tham khảo

1. Cormen, T. H., Leiserson, C. E., Rivest, R. L., Stein, C. *Introduction to Algorithms*, 4th ed., MIT Press, 2022. Mục 15.3 và chương 3. Bản người học cung cấp: Algorithms2022.pdf.
2. Đề BÀI KIỂM TRA GIỮA KỲ.pdf do người học cung cấp, trang 1.
3. Python Software Foundation. *wave — Read and write WAV files*, tài liệu Python 3.12. Nguồn: https://docs.python.org/3.12/library/wave.html . Đối chiếu phạm vi PCM và các hàm đọc tham số/frame ngày 31/10/2026.
4. Microsoft Learn. *WAVEFORMATEX structure (mmeapi.h)*. Nguồn: https://learn.microsoft.com/en-us/windows/win32/api/mmeapi/ns-mmeapi-waveformatex . Đối chiếu số kênh, tần số lấy mẫu và công thức block alignment ngày 31/10/2026.

