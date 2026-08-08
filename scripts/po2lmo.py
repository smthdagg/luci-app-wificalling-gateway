#!/usr/bin/env python3
"""
po2lmo.py - Compile a GNU gettext .po file into a LuCI .lmo archive.

This is a pure-Python re-implementation of luci-base's `po2lmo.c`
(openwrt/luci, modules/luci-base/src/po2lmo.c). It produces byte-identical
output so the resulting .lmo is loadable by luci-base's lmo.c runtime.

LMO file layout:
    [ data section: msgstr bytes, each zero-padded to a 4-byte boundary ]
    [ index entries: 16 bytes each, sorted by key_id ascending ]
    [ data_size: uint32 big-endian (= start offset of the index) ]

Each index entry (struct lmo_entry, packed):
    key_id  uint32 BE  = sfh_hash(msgid-key, len, len)
    val_id  uint32 BE  = plural_num + 1  (0 for the Plural-Forms header)
    offset  uint32 BE  = offset of msgstr within the data section
    length  uint32 BE  = length of msgstr in bytes

The msgid-key is the raw msgid, optionally prefixed with "ctxt\\1" and/or
suffixed with "\\2<plural_index>". Entries whose translation hashes equal
their source hash (key_id == val_id, i.e. untranslated identical strings)
are skipped - LuCI then falls back to the source string at runtime.
"""
import struct
import sys


def sfh_hash(data: bytes, init: int) -> int:
    """SuperFastHash (Paul Hsieh), matching luci-base lmo.c sfh_hash().

    sfh_get16 reads two bytes little-endian: d[0] + (d[1] << 8).
    Called by po2lmo as sfh_hash(key, len, len) -> init == len.
    """
    length = len(data)
    if length <= 0:
        return 0
    MASK = 0xFFFFFFFF
    h = init & MASK
    rem = length & 3
    n = length >> 2
    i = 0
    for _ in range(n):
        h = (h + (data[i] | (data[i + 1] << 8))) & MASK
        tmp = (((data[i + 2] | (data[i + 3] << 8)) << 11) ^ h) & MASK
        h = ((h << 16) ^ tmp) & MASK
        i += 4
        h = (h + (h >> 11)) & MASK
    if rem == 3:
        h = (h + (data[i] | (data[i + 1] << 8))) & MASK
        h = (h ^ ((h << 16) & MASK)) & MASK
        sb = data[i + 2] if data[i + 2] < 128 else data[i + 2] - 256
        h = (h ^ ((sb << 18) & MASK)) & MASK
        h = (h + (h >> 11)) & MASK
    elif rem == 2:
        h = (h + (data[i] | (data[i + 1] << 8))) & MASK
        h = (h ^ ((h << 11) & MASK)) & MASK
        h = (h + (h >> 17)) & MASK
    elif rem == 1:
        sb = data[i] if data[i] < 128 else data[i] - 256
        h = (h + sb) & MASK
        h = (h ^ ((h << 10) & MASK)) & MASK
        h = (h + (h >> 1)) & MASK
    # avalanche
    h = (h ^ ((h << 3) & MASK)) & MASK
    h = (h + (h >> 5)) & MASK
    h = (h ^ ((h << 4) & MASK)) & MASK
    h = (h + (h >> 17)) & MASK
    h = (h ^ ((h << 25) & MASK)) & MASK
    h = (h + (h >> 6)) & MASK
    return h


def _pad4(n: int) -> int:
    return (4 - (n % 4)) % 4


class _Msg:
    __slots__ = ("ctxt", "id", "id_plural", "vals", "plural_num")

    def __init__(self):
        self.ctxt = None
        self.id = None
        self.id_plural = None
        self.vals = {}  # plural_index -> str
        self.plural_num = -1


def _extract_string(line: str):
    """Parse the quoted string content from one .po line.

    Mirrors po2lmo.c extract_string(): skip comment lines, find the first
    opening quote, then copy bytes honoring \\" and \\\\ escapes; a closing
    quote ends the string. Returns the decoded text or None.
    """
    if not line or line[0] == '#':
        return None
    off = -1
    out = []
    esc = False
    for pos, ch in enumerate(line):
        if off == -1:
            if ch == '"':
                off = pos + 1
            continue
        if esc:
            if ch == '"' or ch == '\\':
                pass
            out.append(ch)
            esc = False
        elif ch == '\\':
            out.append(ch)
            esc = True
        elif ch == '"':
            break
        else:
            out.append(ch)
    if off == -1:
        return None
    return ''.join(out)


def parse_po(text: str):
    """Yield _Msg objects from .po text, matching po2lmo.c's line state machine."""
    msg = _Msg()
    cur = None  # (target_attr, plural_index or None)

    def flush():
        nonlocal msg, cur
        m = msg
        msg = _Msg()
        cur = None
        return m

    for raw in text.split('\n'):
        line = raw.rstrip('\r')
        if line.startswith('msgctxt "'):
            if msg.id is not None or msg.vals:
                yield flush()
            else:
                msg.ctxt = None
            cur = ("ctxt", None)
        elif line.startswith('msgid_plural "'):
            msg.id_plural = None
            cur = ("id_plural", None)
        elif not line.startswith('msgstr') and (line.startswith('msgid "') or line is None):
            if msg.id is not None or msg.vals:
                yield flush()
            else:
                msg.id = None
            cur = ("id", None)
        elif line.startswith('msgstr[') :
            idx = int(line[7:line.index(']')])
            msg.plural_num = idx
            if idx >= 10:
                raise ValueError("Too many plural forms")
            msg.vals.pop(idx, None)
            cur = ("val", idx)
        elif line.startswith('msgstr "'):
            msg.plural_num = 0
            msg.vals.pop(0, None)
            cur = ("val", 0)

        if cur is None:
            continue
        s = _extract_string(line)
        if s:
            attr, pidx = cur
            if attr == "ctxt":
                msg.ctxt = (msg.ctxt or '') + s
            elif attr == "id":
                msg.id = (msg.id or '') + s
            elif attr == "id_plural":
                msg.id_plural = (msg.id_plural or '') + s
            elif attr == "val":
                msg.vals[pidx] = (msg.vals.get(pidx) or '') + s

    if msg.id is not None or msg.vals:
        yield flush()


def compile_po(po_text: str) -> bytes:
    """Compile .po text to .lmo bytes, matching po2lmo.c exactly."""
    data = bytearray()
    entries = []  # list of (key_id, val_id, offset, length)
    offset = 0

    for msg in parse_po(po_text):
        if msg.id is not None and 0 in msg.vals:
            # real message (possibly plural)
            plural_num = msg.plural_num if msg.plural_num >= 0 else 0
            for i in range(plural_num + 1):
                val = msg.vals.get(i)
                if val is None:
                    continue
                if msg.ctxt and msg.id_plural:
                    key = "%s\1%s\2%d" % (msg.ctxt, msg.id, i)
                elif msg.ctxt:
                    key = "%s\1%s" % (msg.ctxt, msg.id)
                elif msg.id_plural:
                    key = "%s\2%d" % (msg.id, i)
                else:
                    key = msg.id
                kb = key.encode('utf-8')
                vb = val.encode('utf-8')
                key_id = sfh_hash(kb, len(kb))
                val_id = sfh_hash(vb, len(vb))
                if key_id == val_id:
                    continue  # untranslated identical string: skip
                entries.append((key_id, plural_num + 1, offset, len(vb)))
                data += vb
                data += b'\x00' * _pad4(len(vb))
                offset += len(vb) + _pad4(len(vb))
        elif 0 in msg.vals:
            # header (empty msgid): extract Plural-Forms line, key_id=0
            field = msg.vals[0]
            cur_field = None
            i = 0
            while i < len(field):
                ch = field[i]
                if ch == '\\':
                    i += 1
                    if i < len(field) and field[i] == 'n':
                        # newline boundary
                        if cur_field is not None and cur_field[:14] == "Plural-Forms: ":
                            pf = cur_field[14:]
                            vb = pf.encode('utf-8')
                            entries.append((0, 0, offset, len(vb)))
                            data += vb
                            data += b'\x00' * _pad4(len(vb))
                            offset += len(vb) + _pad4(len(vb))
                            break
                        cur_field = ''
                    elif cur_field is not None:
                        cur_field += ch
                else:
                    if cur_field is None:
                        cur_field = ch
                    else:
                        cur_field += ch
                i += 1

    # sort index by key_id ascending (stable enough; po2lmo uses qsort on key_id)
    entries.sort(key=lambda e: e[0])

    out = bytearray()
    out += data
    for key_id, val_id, off, length in entries:
        out += struct.pack('>IIII', key_id, val_id, off, length)
    out += struct.pack('>I', offset)
    return bytes(out)


def main(argv):
    if len(argv) != 3:
        sys.stderr.write("Usage: %s input.po output.lmo\n" % argv[0])
        return 1
    with open(argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    blob = compile_po(text)
    if not blob:
        return 0
    with open(argv[2], 'wb') as f:
        f.write(blob)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
