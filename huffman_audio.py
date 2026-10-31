"""Nen khong mat mat cho tep WAV PCM: Huffman tren toan bo byte cua tep.

Dinh dang minh hoa HAU1, khong phai codec WAV/MP3 tieu chuan.
Khong can thu vien ngoai Python 3.
"""
import argparse
from collections import Counter
from dataclasses import dataclass
import heapq
import io
from itertools import count
from pathlib import Path
import struct
import wave

MAGIC = b'HAU1'


@dataclass
class Node:
    symbol: object = None
    left: object = None
    right: object = None


def build_tree(freq):
    """Giai quyet trung tan suat nhat quan bang thu tu tao nut."""
    serial = count()
    heap = [(f, next(serial), Node(symbol=b))
            for b, f in sorted(freq.items())]
    heapq.heapify(heap)
    while len(heap) > 1:
        fa, _, a = heapq.heappop(heap)
        fb, _, b = heapq.heappop(heap)
        heapq.heappush(heap, (fa + fb, next(serial), Node(left=a, right=b)))
    return heap[0][2] if heap else None


def build_codes(root):
    codes = {}
    if root is None:
        return codes
    stack = [(root, '')]
    while stack:
        node, prefix = stack.pop()
        if node.symbol is not None:
            codes[node.symbol] = prefix or '0'
        else:
            stack.append((node.right, prefix + '1'))
            stack.append((node.left, prefix + '0'))
    return codes


def compress_bytes(data):
    """Loi Huffman dung chung; khong thay doi byte nguon."""
    freq = Counter(data)
    codes = build_codes(build_tree(freq))
    header = bytearray(MAGIC + struct.pack('>H', len(freq)))
    for symbol, f in sorted(freq.items()):
        header.extend(struct.pack('>BQ', symbol, f))
    payload = bytearray()
    value = used = 0
    for symbol in data:
        for bit in codes[symbol]:
            value = (value << 1) | (bit == '1')
            used += 1
            if used == 8:
                payload.append(value)
                value = used = 0
    if used:
        payload.append(value << (8 - used))
    return bytes(header + payload)


def decompress_bytes(blob):
    if len(blob) < 6 or blob[:4] != MAGIC:
        raise ValueError('Sai dinh dang HAU1')
    k = struct.unpack_from('>H', blob, 4)[0]
    if k > 256 or len(blob) < 6 + 9 * k:
        raise ValueError('Header HAU1 khong hop le')
    freq = {}
    offset = 6
    for _ in range(k):
        symbol, f = struct.unpack_from('>BQ', blob, offset)
        offset += 9
        if symbol in freq or f == 0:
            raise ValueError('Bang tan suat khong hop le')
        freq[symbol] = f
    root = build_tree(freq)
    codes = build_codes(root)
    bit_count = sum(freq[s] * len(codes[s]) for s in freq)
    if len(blob) != offset + (bit_count + 7) // 8:
        raise ValueError('Do dai payload khong hop le')
    padding = (-bit_count) % 8
    if padding and blob[-1] & ((1 << padding) - 1):
        raise ValueError('Bit dem khong hop le')
    if root is None:
        return b''
    out = bytearray()
    node = root
    for i in range(bit_count):
        bit = (blob[offset + i // 8] >> (7 - i % 8)) & 1
        if root.symbol is not None:
            if bit:
                raise ValueError('Ma don ky hieu khong hop le')
            out.append(root.symbol)
        else:
            node = node.right if bit else node.left
            if node.symbol is not None:
                out.append(node.symbol)
                node = root
    if node is not root or Counter(out) != freq:
        raise ValueError('Du lieu khong khop bang tan suat')
    return bytes(out)


def wav_data_size(data):
    """Doc kich thuoc chunk data trong RIFF/WAVE, khong dung thuoc tinh rieng.

    Chap nhan chunk cuoi le khong co byte dem, nhu tep do wave tao ra.
    Chi ho tro mot chunk data, tuong ung cach wave doc am thanh.
    """
    if len(data) < 12 or data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        raise ValueError('Tep khong phai RIFF/WAVE duoc ho tro')
    riff_end = 8 + struct.unpack_from('<I', data, 4)[0]
    if riff_end < 12 or riff_end > len(data):
        raise ValueError('Kich thuoc RIFF khong hop le hoac tep bi cat')
    offset = 12
    data_size = None
    while offset < riff_end:
        if offset + 8 > riff_end:
            raise ValueError('Header chunk WAV bi thieu')
        chunk_id = data[offset:offset + 4]
        size = struct.unpack_from('<I', data, offset + 4)[0]
        end = offset + 8 + size
        if end > riff_end:
            raise ValueError('Du lieu chunk WAV bi thieu')
        if chunk_id == b'data':
            if data_size is not None:
                raise ValueError('Khong ho tro WAV co nhieu chunk data')
            data_size = size
        offset = end if end == riff_end else end + (size & 1)
    if data_size is None:
        raise ValueError('WAV thieu chunk data')
    return data_size


def wav_info(data):
    """Doc WAV PCM duoc wave ho tro, kiem tra du so byte frame khai bao.

    Chi doc de xac nhan; khong ghi lai WAV nen giu nguyen metadata.
    """
    data_size = wav_data_size(data)
    try:
        with wave.open(io.BytesIO(data), 'rb') as audio:
            channels = audio.getnchannels()
            width = audio.getsampwidth()
            rate = audio.getframerate()
            frames = audio.getnframes()
            if rate <= 0 or channels <= 0 or width <= 0:
                raise ValueError('Thong so WAV khong hop le')
            if audio.getcomptype() != 'NONE':
                raise ValueError('Chi ho tro WAV PCM khong nen')
            frame_size = channels * width
            if data_size % frame_size:
                raise ValueError('Chunk data PCM khong chua tron ven cac frame')
            if data_size != frames * frame_size:
                raise ValueError('Kich thuoc PCM khong khop so frame')
            pcm = audio.readframes(frames)
            if len(pcm) != data_size:
                raise ValueError('Du lieu PCM bi thieu so voi so frame khai bao')
            return {'channels': channels, 'sample_width_bytes': width,
                    'sample_rate_hz': rate, 'frames': frames,
                    'duration_seconds': frames / rate}
    except (wave.Error, EOFError, struct.error, RuntimeError) as exc:
        raise ValueError('Tep WAV PCM khong hop le hoac khong duoc ho tro') from exc


def compress_wav(data):
    wav_info(data)
    return compress_bytes(data)


def decompress_wav(blob):
    data = decompress_bytes(blob)
    wav_info(data)
    return data


def main():
    parser = argparse.ArgumentParser(description='Nen/giai nen WAV PCM bang Huffman')
    parser.add_argument('action', choices=['compress', 'decompress'])
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError('Tep nguon va tep dich phai khac nhau')
        if args.output.exists():
            raise ValueError('Tep dich da ton tai; hay chon ten khac')
        source = args.input.read_bytes()
        if args.action == 'compress':
            info = wav_info(source)
            result = compress_bytes(source)
        else:
            result = decompress_wav(source)
            info = wav_info(result)
        with args.output.open('xb') as stream:
            stream.write(result)
    except ValueError as exc:
        parser.error(str(exc))
    except OSError as exc:
        parser.error(f'Khong the doc/ghi tep: {exc}')
    print(f'Input: {len(source)} bytes; output: {len(result)} bytes')
    print(f'WAV: {info}')
    if args.action == 'compress':
        print(f'Tiet kiem (tinh ca header HAU1): {(1-len(result)/len(source))*100:.2f}%')


if __name__ == '__main__':
    main()
