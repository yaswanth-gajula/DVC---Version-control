"""
Content-defined chunking (CDC) — the O3 differentiator.

Why not fixed-size chunks? If you split a file into fixed 256-byte blocks
and someone inserts a single byte at the start, EVERY block after that
point shifts by one byte and hashes completely differently -- you'd get
zero dedup benefit from a one-byte edit. That defeats the whole purpose.

Content-defined chunking finds boundaries based on the DATA ITSELF (via a
rolling hash), not fixed offsets. Insert a byte anywhere and only the
chunk(s) touching that byte change -- everything before and after the
edit still hashes identically to before, so it's still deduplicated.

This is a simplified Gear-hash CDC (the same family of technique behind
restic/borg's chunkers, and conceptually what FastCDC refines further).
It is NOT FastCDC -- no normalized chunking, no dual masks -- but it
demonstrates the real mechanism CP2 is measuring: storage proportional
to CHANGED content, not file size or version count.

Tuned for demo-scale text/code files (default sizes in bytes are small
so the effect is visible even on short source files); for large binary
artefacts these constants would be scaled up (e.g. KB instead of bytes).
"""
import random
from typing import List

MIN_CHUNK_SIZE = 64
AVG_CHUNK_SIZE = 256   # must be a power of two -- used to build the mask
MAX_CHUNK_SIZE = 1024

_MASK = AVG_CHUNK_SIZE - 1
_MOD = (1 << 64) - 1

# Deterministic seed -> same chunk boundaries on every run, every machine.
# This matters: if the table changed between saves, chunks from an old
# version would never match chunks from a new one, silently breaking dedup.
_rng = random.Random(1337)
_GEAR = [_rng.getrandbits(64) for _ in range(256)]


def chunk_content(data: bytes) -> List[bytes]:
    """
    Split `data` into content-defined chunks. A boundary is declared once
    a chunk reaches MIN_CHUNK_SIZE and the rolling hash matches the mask
    pattern, or once it reaches MAX_CHUNK_SIZE regardless (a hard cap so
    pathological input can't produce one giant chunk).

    The rolling hash rotates instead of pure-shifting (`h = rotl(h,1) ^
    GEAR[byte]` rather than `h = (h<<1) + GEAR[byte]`). A plain left-shift
    loses each byte's influence after 64 more shifts, so on repetitive
    input (e.g. consistently indented code) the hash falls into a short
    cycle that can systematically miss the mask -- every chunk would hit
    the MAX_CHUNK_SIZE cutoff instead of a real content boundary, and a
    single inserted byte would then shift every later chunk in lockstep,
    silently defeating dedup. Rotating keeps every byte's influence alive
    indefinitely, which avoids that failure mode.
    """
    n = len(data)
    if n == 0:
        return [b""]

    chunks = []
    start = 0
    h = 0
    for i in range(n):
        h = (((h << 1) | (h >> 63)) & _MOD) ^ _GEAR[data[i]]
        length = i - start + 1
        if length >= MIN_CHUNK_SIZE and (h & _MASK) == 0:
            chunks.append(data[start:i + 1])
            start = i + 1
            h = 0
        elif length >= MAX_CHUNK_SIZE:
            chunks.append(data[start:i + 1])
            start = i + 1
            h = 0

    if start < n:
        chunks.append(data[start:n])
    return chunks
