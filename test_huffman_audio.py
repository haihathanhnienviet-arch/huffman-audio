import io
import random
import struct
import unittest
import wave
from collections import Counter
from huffman_audio import (compress_bytes, decompress_bytes, compress_wav,
                           decompress_wav, wav_info, build_codes, build_tree)


def make_wav(pcm, channels=1, width=2, rate=16000):
    stream = io.BytesIO()
    with wave.open(stream, 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(pcm)
    return stream.getvalue()


class AudioHuffmanTests(unittest.TestCase):
    def test_wav_roundtrips(self):
        cases = [make_wav(b''), make_wav(b'\0\0'*16000),
                 make_wav(b'\x80'*8000, width=1, rate=8000),
                 make_wav(bytes(range(256))*100, channels=2),
                 make_wav(b'\0\0\0'*100, width=3),
                 make_wav(b'\0\0\0\0'*100, width=4)]
        for data in cases:
            with self.subTest(size=len(data)):
                restored = decompress_wav(compress_wav(data))
                self.assertEqual(restored, data)
                self.assertEqual(wav_info(restored), wav_info(data))

    def test_100_random_pcm_wavs(self):
        rng = random.Random(20261031)
        for _ in range(100):
            ch, width = rng.choice([1, 2]), rng.choice([1, 2, 3, 4])
            frames = rng.randrange(300)
            pcm = bytes(rng.randrange(256) for _ in range(frames*ch*width))
            data = make_wav(pcm, ch, width, rng.choice([8000, 16000, 44100]))
            self.assertEqual(decompress_wav(compress_wav(data)), data)

    def test_metadata_preserved(self):
        # Chen mot chunk JUNK hop le truoc chunk data cua WAV tu tao.
        base = make_wav(b'\0\0'*100)
        data = bytearray(base[:36]+b'JUNK'+struct.pack('<I',4)+b'test'+base[36:])
        struct.pack_into('<I', data, 4, len(data)-8)
        data = bytes(data)
        self.assertEqual(decompress_wav(compress_wav(data)), data)

    def test_reject_non_wav_and_truncated_pcm(self):
        for data in [b'', b'not an audio file', make_wav(b'\0\0'*100)[:-1]]:
            with self.assertRaises(ValueError):
                compress_wav(data)
        with self.assertRaises(ValueError):
            decompress_wav(compress_bytes(b'plain text'))

    def test_core_empty_and_single_symbol(self):
        for data in [b'', b'A', b'A'*10000, bytes(range(256))]:
            self.assertEqual(decompress_bytes(compress_bytes(data)), data)

    def test_prefix_free(self):
        codes = list(build_codes(build_tree(Counter(bytes(range(256))))).values())
        for i, a in enumerate(codes):
            for j, b in enumerate(codes):
                if i != j:
                    self.assertFalse(b.startswith(a))

    def test_textbook_payload(self):
        freq = dict(zip(b'abcdef', [45000,13000,12000,16000,9000,5000]))
        codes = build_codes(build_tree(freq))
        self.assertEqual(sum(freq[s]*len(codes[s]) for s in freq),224000)

    def test_hau1_errors(self):
        packed = compress_wav(make_wav(b'\0\0'*100))
        for data in [b'', b'xxxxxx', packed[:-1], packed+b'\0',
                     b'HAU1'+struct.pack('>H',257)]:
            with self.assertRaises(ValueError):
                decompress_bytes(data)

    def test_size_determinism_payload_bound(self):
        data = make_wav(bytes(range(256))*10)
        freq = Counter(data)
        codes = build_codes(build_tree(freq))
        bits = sum(freq[s]*len(codes[s]) for s in freq)
        packed = compress_wav(data)
        self.assertLessEqual(bits,8*len(data))
        self.assertEqual(len(packed),6+9*len(freq)+(bits+7)//8)
        self.assertEqual(packed,compress_wav(data))


if __name__ == '__main__':
    unittest.main(verbosity=2)
