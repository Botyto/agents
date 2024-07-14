from dataclasses import dataclass
import gc
import time
import torch.cuda
from typing import List
import whisper


@dataclass(frozen=True)
class ModelInfo:
    name: str
    english_only_name: str|None
    parameters: str
    vram: str


TINY = ModelInfo("tiny", "tiny.en", "39M", "~1GB")
BASE = ModelInfo("base", "base.en", "74M", "~1GB")
SMALL = ModelInfo("small", "small.en", "224M", "~2GB")
MEDIUM = ModelInfo("medium", "medium.en", "769M", "~5GB")
LARGE = ModelInfo("large", None, "1550M", "~12GB")


class WhisperSegment:
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float

    def __init__(self, segment: dict):
        self.id = segment["id"]
        self.seek = segment["seek"]
        self.start = segment["start"]
        self.end = segment["end"]
        self.text = segment["text"]
        self.tokens = segment["tokens"]
        self.temperature = segment["temperature"]
        self.avg_logprob = segment["avg_logprob"]
        self.compression_ratio = segment["compression_ratio"]
        self.no_speech_prob = segment["no_speech_prob"]

    def __str__(self):
        return self.text


class WhisperResponse:
    text: str
    segments: List[WhisperSegment]
    language: str
    transcribe_time: float

    def __init__(self, response: dict, transcribe_time: float):
        self.text = response["text"]
        self.segments = [WhisperSegment(s) for s in response["segments"]]
        self.language = response["language"]
        self.transcribe_time = transcribe_time

    @property
    def duration(self):
        return self.segments[-1].end - self.segments[0].start
    
    @property
    def transcribe_speed_factor(self):
        return self.transcribe_time / self.duration
    
    def __str__(self):
        return self.text


class WhisperClient:
    _model: whisper.Whisper|None
    _auto_close: bool

    def __init__(self, model_info: ModelInfo, auto_close: bool = True):
        self.model_info = model_info
        self._model = None
        self._auto_close = auto_close

    def close(self):
        if not self._model:
            return
        self._model = None
        gc.collect()
        torch.cuda.empty_cache()

    def transcribe(self, file_path: str):
        if not self._model:
            self._model = whisper.load_model(self.model_info.name)
        start_time = time.time()
        response = self._model.transcribe(file_path)
        transcribe_time = time.time() - start_time
        if self._auto_close:
            self.close()
        return WhisperResponse(response, transcribe_time)
