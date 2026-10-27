"""IR decode helpers for SIL fixtures and classified AUX captures.

NEC-like and Sony SIRC are tried only as timing families. The Sony decoder was
added after AUX On-Off signatures matched SIRC (≈2.4 ms header, 0.6/1.2 ms
marks). Do not treat outputs as manual-confirmed Bose codes beyond measured
captures.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IrFrame:
    protocol: str
    address: int
    command: int
    raw: tuple[int, ...]
    extended: int | None = None


# Typical NEC bit timings in microseconds (tolerance applied in decode).
NEC_HDR_MARK = 9000
NEC_HDR_SPACE = 4500
NEC_BIT_MARK = 560
NEC_ONE_SPACE = 1690
NEC_ZERO_SPACE = 560
NEC_TOL = 0.3

# Sony SIRC (SIRCS) pulse-width timings.
SONY_HDR_MARK = 2400
SONY_SPACE = 600
SONY_ZERO_MARK = 600
SONY_ONE_MARK = 1200
SONY_TOL = 0.35
SONY_GLITCH_US = 50

# Pulse-distance 24-bit seen on AUX+20000 On-Off: ~3.4 ms / ~3.4 ms header,
# ~0.8 ms marks, short space ~0.9 ms (0), long space ~2.6 ms (1).
PD24_HDR_MARK = 3400
PD24_HDR_SPACE = 3400
PD24_BIT_MARK = 800
PD24_ZERO_SPACE = 900
PD24_ONE_SPACE = 2600
PD24_TOL = 0.4


def _near(value: int, target: int, tol: float = NEC_TOL) -> bool:
    return abs(value - target) <= target * tol


def scrub_glitches(
    pulses: list[int] | tuple[int, ...],
    min_us: int = SONY_GLITCH_US,
) -> list[int]:
    """Drop sub-threshold spikes that break mark/space pairing."""
    return [int(pulse) for pulse in pulses if int(pulse) >= min_us]


def pulses_to_nec(pulses: list[int] | tuple[int, ...]) -> IrFrame | None:
    """Decode a flat mark/space list (µs) starting at header mark.

    Expects: hdr_mark, hdr_space, then 32 pairs of (bit_mark, bit_space).
    """
    if len(pulses) < 2 + 32 * 2:
        return None
    if not _near(pulses[0], NEC_HDR_MARK) or not _near(pulses[1], NEC_HDR_SPACE):
        return None
    bits: list[int] = []
    idx = 2
    for _ in range(32):
        mark = pulses[idx]
        space = pulses[idx + 1]
        idx += 2
        if not _near(mark, NEC_BIT_MARK):
            return None
        if _near(space, NEC_ONE_SPACE):
            bits.append(1)
        elif _near(space, NEC_ZERO_SPACE):
            bits.append(0)
        else:
            return None
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    address = (value >> 24) & 0xFF
    address_inv = (value >> 16) & 0xFF
    command = (value >> 8) & 0xFF
    command_inv = value & 0xFF
    if address ^ address_inv != 0xFF:
        return None
    if command ^ command_inv != 0xFF:
        return None
    return IrFrame(
        protocol="nec-like",
        address=address,
        command=command,
        raw=tuple(pulses[: 2 + 32 * 2]),
    )


def nec_to_pulses(address: int, command: int) -> list[int]:
    """Synthesize NEC-like mark/space timings for SIL."""
    address &= 0xFF
    command &= 0xFF
    payload = (
        (address << 24)
        | ((address ^ 0xFF) << 16)
        | (command << 8)
        | (command ^ 0xFF)
    )
    pulses = [NEC_HDR_MARK, NEC_HDR_SPACE]
    for i in range(31, -1, -1):
        bit = (payload >> i) & 1
        pulses.append(NEC_BIT_MARK)
        pulses.append(NEC_ONE_SPACE if bit else NEC_ZERO_SPACE)
    return pulses


def frame_key(frame: IrFrame) -> str:
    if frame.extended is None:
        return f"{frame.protocol}:{frame.address:02x}:{frame.command:02x}"
    return (
        f"{frame.protocol}:{frame.address:02x}:{frame.command:02x}:"
        f"{frame.extended:02x}"
    )


def _pack_lsb(bits: list[int]) -> int:
    value = 0
    for index, bit in enumerate(bits):
        value |= (bit & 1) << index
    return value


def pulses_to_sony(pulses: list[int] | tuple[int, ...]) -> IrFrame | None:
    """Decode Sony SIRC-12/15/20 from a scrubbed mark/space list."""
    values = scrub_glitches(pulses)
    if len(values) < 2 + 12:
        return None
    if not _near(values[0], SONY_HDR_MARK, SONY_TOL):
        return None
    if not _near(values[1], SONY_SPACE, SONY_TOL):
        return None
    bits: list[int] = []
    index = 2
    while index < len(values):
        mark = values[index]
        index += 1
        if _near(mark, SONY_ZERO_MARK, SONY_TOL):
            bits.append(0)
        elif _near(mark, SONY_ONE_MARK, SONY_TOL):
            bits.append(1)
        else:
            return None
        if index >= len(values):
            break
        space = values[index]
        index += 1
        if not _near(space, SONY_SPACE, SONY_TOL):
            return None
    bit_count = len(bits)
    if bit_count not in (12, 15, 20):
        return None
    command = _pack_lsb(bits[0:7])
    if bit_count == 12:
        address = _pack_lsb(bits[7:12])
        extended = None
        protocol = "sony-sirc12"
    elif bit_count == 15:
        address = _pack_lsb(bits[7:15])
        extended = None
        protocol = "sony-sirc15"
    else:
        address = _pack_lsb(bits[7:12])
        extended = _pack_lsb(bits[12:20])
        protocol = "sony-sirc20"
    return IrFrame(
        protocol=protocol,
        address=address,
        command=command,
        raw=tuple(values),
        extended=extended,
    )


def sony_to_pulses(
    address: int,
    command: int,
    *,
    bits: int = 12,
    extended: int = 0,
) -> list[int]:
    """Synthesize Sony SIRC mark/space timings for SIL."""
    if bits not in (12, 15, 20):
        raise ValueError(f"unsupported Sony bit count {bits}")
    command &= 0x7F
    bit_list = [(command >> index) & 1 for index in range(7)]
    if bits == 12:
        address &= 0x1F
        bit_list.extend((address >> index) & 1 for index in range(5))
    elif bits == 15:
        address &= 0xFF
        bit_list.extend((address >> index) & 1 for index in range(8))
    else:
        address &= 0x1F
        extended &= 0xFF
        bit_list.extend((address >> index) & 1 for index in range(5))
        bit_list.extend((extended >> index) & 1 for index in range(8))
    pulses = [SONY_HDR_MARK, SONY_SPACE]
    for bit in bit_list:
        pulses.append(SONY_ONE_MARK if bit else SONY_ZERO_MARK)
        pulses.append(SONY_SPACE)
    return pulses


def _pack_msb(bits: list[int]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | (bit & 1)
    return value


def pulses_to_pd24(pulses: list[int] | tuple[int, ...]) -> IrFrame | None:
    """Decode 24-bit pulse-distance (header ~3.4/3.4 ms) from AUX+20000 captures."""
    values = scrub_glitches(pulses)
    # Header + 24 marks + 23 spaces (optional trailing mark after last space).
    if len(values) < 2 + 24 + 23:
        return None
    if not _near(values[0], PD24_HDR_MARK, PD24_TOL):
        return None
    if not _near(values[1], PD24_HDR_SPACE, PD24_TOL):
        return None
    bits: list[int] = []
    index = 2
    while index < len(values) and len(bits) < 24:
        mark = values[index]
        index += 1
        if not _near(mark, PD24_BIT_MARK, PD24_TOL):
            return None
        if index >= len(values):
            break
        space = values[index]
        index += 1
        if _near(space, PD24_ONE_SPACE, PD24_TOL):
            bits.append(1)
        elif _near(space, PD24_ZERO_SPACE, PD24_TOL):
            bits.append(0)
        else:
            return None
    if len(bits) != 24:
        return None
    address = _pack_msb(bits[0:8])
    command = _pack_msb(bits[8:16])
    extended = _pack_msb(bits[16:24])
    return IrFrame(
        protocol="pd24",
        address=address,
        command=command,
        raw=tuple(values),
        extended=extended,
    )


def pd24_to_pulses(address: int, command: int, extended: int = 0) -> list[int]:
    """Synthesize pd24 mark/space timings for SIL."""
    bit_list: list[int] = []
    for value, width in ((address, 8), (command, 8), (extended, 8)):
        value &= (1 << width) - 1
        for shift in range(width - 1, -1, -1):
            bit_list.append((value >> shift) & 1)
    pulses = [PD24_HDR_MARK, PD24_HDR_SPACE]
    for bit in bit_list:
        pulses.append(PD24_BIT_MARK)
        pulses.append(PD24_ONE_SPACE if bit else PD24_ZERO_SPACE)
    return pulses


# Split demodulated captures on a long idle. Longer than an NEC header space
# (4.5 ms) and shorter than a typical inter-frame gap. Not a protocol id.
FRAME_GAP_US = 8000


def split_frames(
    pulses: list[int] | tuple[int, ...],
    gap_us: int = FRAME_GAP_US,
) -> list[list[int]]:
    """Split mark/space timings into frames at idle gaps.

    Spaces are the odd indexes. A space of at least ``gap_us`` ends the
    current frame and is not part of either frame.
    """
    values = [int(pulse) for pulse in pulses]
    if not values:
        return []
    frames: list[list[int]] = []
    start = 0
    index = 1
    while index < len(values):
        if values[index] >= gap_us:
            chunk = values[start:index]
            if chunk:
                frames.append(chunk)
            start = index + 1
        index += 2
    tail = values[start:]
    if tail:
        frames.append(tail)
    return frames


def _cluster(values: list[int], tol: float = 0.2) -> list[dict]:
    if not values:
        return []
    ordered = sorted(int(value) for value in values)
    groups: list[list[int]] = [[ordered[0]]]
    for value in ordered[1:]:
        center = sum(groups[-1]) / len(groups[-1])
        if abs(value - center) <= max(center * tol, 100):
            groups[-1].append(value)
        else:
            groups.append([value])
    return [
        {"us": int(round(sum(group) / len(group))), "n": len(group)}
        for group in groups
    ]


def pulse_signature(pulses: list[int] | tuple[int, ...]) -> dict:
    """Timing signature for a frame the NEC decoder rejected."""
    values = [int(pulse) for pulse in pulses]
    return {
        "count": len(values),
        "first_mark": values[0] if values else None,
        "first_space": values[1] if len(values) > 1 else None,
        "mark_clusters": _cluster(values[0::2]),
        "space_clusters": _cluster(values[1::2]),
    }


MAPPED_PROTOCOLS = frozenset(
    {
        "nec-like",
        "sony-sirc12",
        "sony-sirc15",
        "sony-sirc20",
        "pd24",
    }
)


def classify_pulses(pulses: list[int] | tuple[int, ...]) -> dict:
    """Classify the first decodable frame, or leave it unclassified.

    Tries NEC-like, Sony SIRC, then the 24-bit pulse-distance family measured
    on AUX+20000. Leading junk frames are skipped.
    """
    frames = split_frames(pulses)
    for index, command in enumerate(frames):
        decoded = pulses_to_nec(command) if command else None
        if decoded is None and command:
            decoded = pulses_to_sony(command)
        if decoded is None and command:
            decoded = pulses_to_pd24(command)
        if decoded is not None:
            payload = {
                "protocol": decoded.protocol,
                "frame_key": frame_key(decoded),
                "address": decoded.address,
                "command": decoded.command,
                "frame_count": len(frames),
                "frame_index": index,
            }
            if decoded.extended is not None:
                payload["extended"] = decoded.extended
            return payload
    command = frames[0] if frames else []
    return {
        "protocol": "unclassified",
        "frame_key": None,
        "frame_count": len(frames),
        "signature": pulse_signature(scrub_glitches(command)),
    }
