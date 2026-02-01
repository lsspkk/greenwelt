"""
audio_variance.py

Reads a soundmap YAML, and for any sound entry that has `pitchvariance > 0`,
generates N pre-pitched variant .ogg files per source sound file, writes them
to an output folder, and writes an updated soundmap YAML that references the
generated variants (optionally keeping the original too).

This tool does offline preprocessing so your runtime pygame code can just pick
random files without doing pitch work at runtime.

Requirements:
- Python 3.10+
- ffmpeg available on PATH (used to decode/encode .ogg reliably)
- PyYAML
- NumPy

Install deps (example with uv):
  uv pip install numpy pyyaml

Run:
  python generate_pitch_variants.py
"""

from __future__ import annotations

import io
import math
import os
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import yaml


YAML_IN_PATH = Path("data/soundmap.yaml")
YAML_OUT_PATH = Path("data/soundmap.yaml")

ASSETS_AUDIO_DIR = Path("assets/audio")
OUTPUT_AUDIO_DIR = Path("assets/audio/_pitched")

VARIANT_COUNT_PER_SOURCE = 3
INCLUDE_ORIGINAL_IN_SOUNDS_LIST = True
OVERWRITE_EXISTING_FILES = False

VARIANT_FILENAME_PATTERN = "{stem}__pv{pv_pct:03d}__v{idx}.ogg"

PITCH_FACTOR_DISTRIBUTION = "symmetric"  # "symmetric" or "random"
RANDOM_SEED = 12345

FFMPEG_BIN = "ffmpeg"


@dataclass(frozen=True)
class WavData:
    sr: int
    channels: int
    sampwidth: int
    pcm: np.ndarray  # shape (n, ch), int16 recommended


def _run(cmd: List[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {p.returncode}): {' '.join(cmd)}\n\n"
            f"STDOUT:\n{p.stdout.decode('utf-8', 'replace')}\n\n"
            f"STDERR:\n{p.stderr.decode('utf-8', 'replace')}"
        )


def _ffmpeg_decode_to_wav_bytes(input_ogg: Path) -> bytes:
    cmd = [
        FFMPEG_BIN,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_ogg),
        "-f",
        "wav",
        "-acodec",
        "pcm_s16le",
        "-",
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(
            f"ffmpeg decode failed for {input_ogg}\n{p.stderr.decode('utf-8', 'replace')}"
        )
    return p.stdout


def _read_wav_bytes(wav_bytes: bytes) -> WavData:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        channels = wf.getnchannels()
        sr = wf.getframerate()
        sampwidth = wf.getsampwidth()
        nframes = wf.getnframes()
        frames = wf.readframes(nframes)

    if sampwidth != 2:
        raise ValueError(f"Expected 16-bit PCM WAV (sampwidth=2), got {sampwidth}")

    pcm = np.frombuffer(frames, dtype=np.int16)
    if channels > 1:
        pcm = pcm.reshape(-1, channels)
    else:
        pcm = pcm.reshape(-1, 1)

    return WavData(sr=sr, channels=channels, sampwidth=sampwidth, pcm=pcm)


def _write_wav_file(path: Path, wav: WavData) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = wav.pcm
    if pcm.dtype != np.int16:
        pcm = np.clip(pcm, -32768, 32767).astype(np.int16)

    interleaved = pcm.reshape(-1)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(wav.channels)
        wf.setsampwidth(wav.sampwidth)
        wf.setframerate(wav.sr)
        wf.writeframes(interleaved.tobytes())


def _ffmpeg_encode_wav_to_ogg(wav_path: Path, ogg_path: Path) -> None:
    ogg_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG_BIN,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if OVERWRITE_EXISTING_FILES else "-n",
        "-i",
        str(wav_path),
        "-c:a",
        "libvorbis",
        "-q:a",
        "5",
        str(ogg_path),
    ]
    _run(cmd)


def _resample_pcm_linear(pcm: np.ndarray, factor: float) -> np.ndarray:
    if factor <= 0:
        raise ValueError("factor must be > 0")

    n, ch = pcm.shape
    new_n = max(1, int(round(n / factor)))
    x_old = np.arange(n, dtype=np.float64)
    x_new = np.linspace(0.0, n - 1, new_n, dtype=np.float64)

    out = np.empty((new_n, ch), dtype=np.float64)
    for c in range(ch):
        out[:, c] = np.interp(x_new, x_old, pcm[:, c].astype(np.float64))

    return np.clip(np.round(out), -32768, 32767).astype(np.int16)


def _normalize_sound_path(s: str) -> Path:
    p = Path(s)
    if p.is_absolute():
        return p
    if "assets" in p.parts:
        return p
    return ASSETS_AUDIO_DIR / p


def _relativize_for_yaml(p: Path) -> str:
    return p.as_posix()


def _variant_factors(pitchvariance: float, count: int, seed: int) -> List[float]:
    if count <= 0:
        return []
    if pitchvariance <= 0:
        return [1.0]

    rng = np.random.default_rng(seed)

    if PITCH_FACTOR_DISTRIBUTION == "random":
        factors = 1.0 + rng.uniform(-pitchvariance, pitchvariance, size=count)
        return [float(f) for f in factors]

    if count == 1:
        return [1.0 + float(rng.uniform(-pitchvariance, pitchvariance))]

    offsets = np.linspace(-pitchvariance, pitchvariance, count, dtype=np.float64)
    offsets = offsets[offsets != 0.0]
    if offsets.size < count:
        more = count - offsets.size
        extra = 1.0 + rng.uniform(-pitchvariance, pitchvariance, size=more)
        return [float(f) for f in (1.0 + offsets).tolist()] + [float(f) for f in extra]
    return [float(1.0 + o) for o in offsets[:count]]


def main() -> None:
    if shutil.which(FFMPEG_BIN) is None:
        raise RuntimeError(f"ffmpeg not found on PATH. Set FFMPEG_BIN or install ffmpeg.")

    if not YAML_IN_PATH.exists():
        raise FileNotFoundError(f"YAML not found: {YAML_IN_PATH}")

    with open(YAML_IN_PATH, "r", encoding="utf-8") as f:
        soundmap: Dict[str, Any] = yaml.safe_load(f) or {}

    OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    rng_base = RANDOM_SEED
    updated: Dict[str, Any] = {}

    for key, info_any in soundmap.items():
        info = dict(info_any or {})
        sounds = list(info.get("sounds", []) or [])
        pv = float(info.get("pitchvariance", 0) or 0)
        if pv <= 0:
            updated[key] = info
            continue

        new_sounds: List[str] = []
        if INCLUDE_ORIGINAL_IN_SOUNDS_LIST:
            new_sounds.extend(sounds)

        for i, s in enumerate(sounds):
            src_path = _normalize_sound_path(s)
            if not src_path.exists():
                raise FileNotFoundError(f"Missing source sound for '{key}': {src_path}")

            wav_bytes = _ffmpeg_decode_to_wav_bytes(src_path)
            wav = _read_wav_bytes(wav_bytes)

            factors = _variant_factors(pv, VARIANT_COUNT_PER_SOURCE, seed=rng_base + hash((key, i)) % 10_000_000)

            stem = src_path.stem
            pv_pct = int(round(pv * 100))

            for idx, fct in enumerate(factors, start=1):
                pitched_pcm = _resample_pcm_linear(wav.pcm, factor=fct)
                pitched = WavData(sr=wav.sr, channels=wav.channels, sampwidth=wav.sampwidth, pcm=pitched_pcm)

                out_name = VARIANT_FILENAME_PATTERN.format(stem=stem, pv_pct=pv_pct, idx=idx)
                out_ogg = OUTPUT_AUDIO_DIR / out_name

                if out_ogg.exists() and not OVERWRITE_EXISTING_FILES:
                    new_sounds.append(_relativize_for_yaml(out_ogg))
                    continue

                with tempfile.TemporaryDirectory() as td:
                    tmp_wav = Path(td) / "tmp.wav"
                    _write_wav_file(tmp_wav, pitched)
                    _ffmpeg_encode_wav_to_ogg(tmp_wav, out_ogg)

                new_sounds.append(_relativize_for_yaml(out_ogg))

        info["sounds"] = new_sounds
        updated[key] = info

    YAML_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(YAML_OUT_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(updated, f, sort_keys=False, allow_unicode=True)

    print(f"Wrote updated YAML: {YAML_OUT_PATH}")
    print(f"Generated audio under: {OUTPUT_AUDIO_DIR}")


if __name__ == "__main__":
    main()
