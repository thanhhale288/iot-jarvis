"""A5: STT tiếng Việt qua faster-whisper (language=vi) — tối ưu tốc độ."""

from __future__ import annotations

import os
from typing import Any

import numpy as np
from dotenv import load_dotenv

load_dotenv()

# small+beam5 đúng VI hơn base+beam1 (đổi base/1 nếu cần tốc độ)
STT_MODEL = os.getenv("STT_MODEL", "small")
STT_LANGUAGE = os.getenv("STT_LANGUAGE", "vi")
STT_DEVICE = os.getenv("STT_DEVICE", "cpu")
STT_COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE", "int8")
STT_BEAM = int(os.getenv("STT_BEAM", "5"))
STT_INITIAL_PROMPT = os.getenv(
    "STT_INITIAL_PROMPT",
    "Tiếng Việt. Nhiệt độ và độ ẩm. Bật đèn. Tắt quạt. Tưới nước hai giây.",
)


class FasterWhisperSTT:
    """Whisper local; mặc định khóa tiếng Việt."""

    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
        language: str | None = None,
    ) -> None:
        from faster_whisper import WhisperModel

        self.model_size = model_size or STT_MODEL
        self.device = device or STT_DEVICE
        self.compute_type = compute_type or STT_COMPUTE_TYPE
        self.language = language if language is not None else STT_LANGUAGE
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )

    def transcribe(
        self,
        audio: str | np.ndarray,
        *,
        language: str | None = None,
        sample_rate: int = 16_000,
        beam_size: int | None = None,
        vad_filter: bool = True,
    ) -> str:
        """Transcribe path wav/mp3 hoặc mảng float32 mono."""
        del sample_rate
        lang = self.language if language is None else language
        lang_arg: str | None = (lang or "").strip() or None
        beam = STT_BEAM if beam_size is None else beam_size

        kwargs: dict[str, Any] = {
            "beam_size": beam,
            "vad_filter": vad_filter,
            "condition_on_previous_text": False,
        }
        if lang_arg:
            kwargs["language"] = lang_arg
        if STT_INITIAL_PROMPT.strip():
            kwargs["initial_prompt"] = STT_INITIAL_PROMPT.strip()

        if isinstance(audio, np.ndarray):
            samples = np.asarray(audio, dtype=np.float32).reshape(-1)
            peak = float(np.max(np.abs(samples))) if samples.size else 0.0
            if peak > 1.0:
                samples = samples / 32768.0
            segments, _info = self._model.transcribe(samples, **kwargs)
        else:
            segments, _info = self._model.transcribe(str(audio), **kwargs)

        parts = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
        return " ".join(parts).strip()


_default: FasterWhisperSTT | None = None


def _get_default() -> FasterWhisperSTT:
    global _default
    if _default is None:
        _default = FasterWhisperSTT()
    return _default


def transcribe_file(path: str, *, language: str | None = None) -> str:
    return _get_default().transcribe(path, language=language)


def transcribe_array(
    samples: np.ndarray,
    *,
    sample_rate: int = 16_000,
    language: str | None = None,
) -> str:
    return _get_default().transcribe(
        samples, language=language, sample_rate=sample_rate
    )
