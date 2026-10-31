"""Tao 4 WAV tong hop, nen/giai nen, do dung luong va doi chieu tung byte."""
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path
import random
import struct
import wave
from huffman_audio import (compress_wav, decompress_wav, wav_info,
                           build_tree, build_codes)


def pcm_wav(samples, channels=1, rate=16000):
    pcm = b''.join(struct.pack('<h',s) for s in samples)
    buf = io.BytesIO()
    with wave.open(buf,'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def main():
    root = Path(__file__).resolve().parent
    sample_dir = root/'samples'
    sample_dir.mkdir(exist_ok=True)
    rate, frames = 16000, 16000
    rng = random.Random(20261031)
    stereo = []
    for i in range(frames):
        stereo.extend([round(12000*math.sin(2*math.pi*440*i/rate)),
                       round(12000*math.sin(2*math.pi*660*i/rate))])
    samples = {
        'silence_16bit_mono.wav': pcm_wav([0]*frames),
        'sine_440hz_16bit_mono.wav': pcm_wav([
            round(12000*math.sin(2*math.pi*440*i/rate)) for i in range(frames)]),
        'noise_16bit_mono.wav': pcm_wav([
            rng.randrange(-32768,32768) for _ in range(frames)]),
        'sine_440_660hz_16bit_stereo.wav': pcm_wav(stereo,channels=2),
    }
    rows = []
    for name,data in samples.items():
        blob = compress_wav(data)
        restored = decompress_wav(blob)
        assert restored == data, name
        assert wav_info(restored) == wav_info(data), name
        freq = Counter(data)
        codes = build_codes(build_tree(freq))
        bits = sum(freq[s]*len(codes[s]) for s in freq)
        rows.append({'file':name,**wav_info(data),'original_bytes':len(data),
                     'distinct_bytes':len(freq),'payload_bits':bits,
                     'hau1_header_bytes':6+9*len(freq),'compressed_bytes':len(blob),
                     'saved_percent':round((1-len(blob)/len(data))*100,6),
                     'byte_equal':restored==data,
                     'sha256_original':hashlib.sha256(data).hexdigest(),
                     'sha256_restored':hashlib.sha256(restored).hexdigest()})
        (sample_dir/name).write_bytes(data)
        (sample_dir/(name+'.huf')).write_bytes(blob)
    result = json.dumps(rows,ensure_ascii=False,indent=2)
    (root/'results.json').write_text(result+'\n',encoding='utf-8')
    print(result)


if __name__ == '__main__':
    main()
