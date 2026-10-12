"""Decode Android binary XML (AndroidManifest.xml inside an APK) without aapt or Java.

Format: a RES_XML chunk holding a string pool, an optional resource-id map, then start/end namespace and
element chunks. Attribute values are typed (string, int, bool, reference). Enough of it is decoded here to
read a manifest; resources.arsc is not resolved, so references come back as "@0x7f......".
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

RES_STRING_POOL = 0x0001
RES_XML = 0x0003
RES_XML_START_NS = 0x0100
RES_XML_END_NS = 0x0101
RES_XML_START_ELEMENT = 0x0102
RES_XML_END_ELEMENT = 0x0103
RES_XML_CDATA = 0x0104
RES_XML_RESOURCE_MAP = 0x0180
UTF8_FLAG = 1 << 8
NO_INDEX = 0xFFFFFFFF

# android:* attribute ids, for manifests whose attribute-name strings were stripped by obfuscators
ANDROID_ATTRS = {
    0x01010001: "label", 0x01010002: "icon", 0x01010003: "name", 0x0101000C: "debuggable",
    0x0101000F: "permission", 0x01010010: "exported", 0x0101020C: "minSdkVersion",
    0x0101021B: "versionCode", 0x0101021C: "versionName", 0x01010270: "targetSdkVersion",
    0x01010280: "allowBackup", 0x010104EA: "extractNativeLibs", 0x01010024: "value",
    0x0101001E: "process", 0x01010011: "enabled",
}


class AxmlError(ValueError):
    pass


@dataclass
class Element:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Element] = field(default_factory=list)

    def iter(self, tag: str | None = None):
        if tag is None or self.tag == tag:
            yield self
        for c in self.children:
            yield from c.iter(tag)

    def get(self, name: str, default: str | None = None) -> str | None:
        """Attribute by local name, with or without the `android:` prefix."""
        if name in self.attrs:
            return self.attrs[name]
        return self.attrs.get("android:" + name, default)


def _string_pool(buf: bytes, off: int) -> list[str]:
    _t, hsize, _size, count, _styles, flags, strings_start, _styles_start = struct.unpack_from("<HHIIIIII", buf, off)
    utf8 = bool(flags & UTF8_FLAG)
    offsets = struct.unpack_from(f"<{count}I", buf, off + hsize)
    base = off + strings_start
    out = []
    for o in offsets:
        p = base + o
        if utf8:
            # utf-16 length then utf-8 length, each 1 or 2 bytes (high bit = 2 bytes)
            n = buf[p]
            p += 2 if n & 0x80 else 1
            n = buf[p]
            if n & 0x80:
                n = ((n & 0x7F) << 8) | buf[p + 1]
                p += 2
            else:
                p += 1
            out.append(buf[p:p + n].decode("utf-8", "replace"))
        else:
            n = struct.unpack_from("<H", buf, p)[0]
            p += 2
            if n & 0x8000:
                n = ((n & 0x7FFF) << 16) | struct.unpack_from("<H", buf, p)[0]
                p += 2
            out.append(buf[p:p + n * 2].decode("utf-16-le", "replace"))
    return out


def _value(strings: list[str], raw: int, vtype: int, data: int) -> str:
    if raw != NO_INDEX and raw < len(strings):
        return strings[raw]
    if vtype == 0x03:
        return strings[data] if data < len(strings) else ""
    if vtype == 0x12:
        return "true" if data else "false"
    if vtype == 0x10:
        return str(struct.unpack("<i", struct.pack("<I", data))[0])
    if vtype == 0x11:
        return hex(data)
    if vtype in (0x01, 0x02):
        return f"@0x{data:08x}" if vtype == 0x01 else f"?0x{data:08x}"
    if vtype == 0x04:
        return repr(struct.unpack("<f", struct.pack("<I", data))[0])
    return f"0x{data:x}"


def parse(buf: bytes) -> Element:
    if len(buf) < 8:
        raise AxmlError("too short for binary XML")
    rtype, _hs, total = struct.unpack_from("<HHI", buf, 0)
    if rtype != RES_XML:
        raise AxmlError(f"not binary XML (chunk type 0x{rtype:04x})")
    strings: list[str] = []
    res_ids: list[int] = []
    ns_prefix: dict[str, str] = {}
    root = Element("#document")
    stack = [root]
    off = 8
    end = min(total, len(buf))
    while off + 8 <= end:
        ctype, hsize, csize = struct.unpack_from("<HHI", buf, off)
        if csize < 8:
            raise AxmlError(f"bad chunk size at {off}")
        if ctype == RES_STRING_POOL:
            strings = _string_pool(buf, off)
        elif ctype == RES_XML_RESOURCE_MAP:
            n = (csize - hsize) // 4
            res_ids = list(struct.unpack_from(f"<{n}I", buf, off + hsize))
        elif ctype == RES_XML_START_NS:
            prefix, uri = struct.unpack_from("<II", buf, off + hsize)
            if prefix < len(strings) and uri < len(strings):
                ns_prefix[strings[uri]] = strings[prefix]
        elif ctype == RES_XML_START_ELEMENT:
            ns, name, astart, asize, acount = struct.unpack_from("<IIHHH", buf, off + hsize)
            el = Element(strings[name] if name < len(strings) else "?")
            p = off + hsize + astart
            for _ in range(acount):
                a_ns, a_name, a_raw = struct.unpack_from("<III", buf, p)
                _sz, _r0, vtype, data = struct.unpack_from("<HBBI", buf, p + 12)
                aname = strings[a_name] if a_name < len(strings) else ""
                if not aname and a_name < len(res_ids):
                    aname = ANDROID_ATTRS.get(res_ids[a_name], f"0x{res_ids[a_name]:08x}")
                if a_ns != NO_INDEX and a_ns < len(strings):
                    prefix = ns_prefix.get(strings[a_ns], "android")
                    aname = f"{prefix}:{aname}"
                el.attrs[aname] = _value(strings, a_raw, vtype, data)
                p += asize or 20
            stack[-1].children.append(el)
            stack.append(el)
        elif ctype == RES_XML_END_ELEMENT:
            if len(stack) > 1:
                stack.pop()
        off += csize
    if not root.children:
        raise AxmlError("no elements")
    return root.children[0]


def to_xml(el: Element, indent: int = 0) -> str:
    from xml.sax.saxutils import quoteattr

    pad = "  " * indent
    attrs = "".join(f" {k}={quoteattr(v)}" for k, v in el.attrs.items())
    if not el.children:
        return f"{pad}<{el.tag}{attrs}/>\n"
    inner = "".join(to_xml(c, indent + 1) for c in el.children)
    return f"{pad}<{el.tag}{attrs}>\n{inner}{pad}</{el.tag}>\n"


def parse_any(buf: bytes) -> Element:
    """Binary XML, or plain-text XML (apktool output, hand-made test manifests)."""
    if buf[:2] == b"\x03\x00":
        return parse(buf)
    import xml.etree.ElementTree as ET

    def conv(e) -> Element:
        attrs = {}
        for k, v in e.attrib.items():
            if k.startswith("{http://schemas.android.com/apk/res/android}"):
                k = "android:" + k.split("}", 1)[1]
            attrs[k] = v
        return Element(e.tag, attrs, [conv(c) for c in e])

    return conv(ET.fromstring(buf))
