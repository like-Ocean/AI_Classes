from faster_whisper import WhisperModel
from typing import Optional
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor


class TranscriptionService:
    """Транскрибация аудио/видео через Faster-Whisper"""

    def __init__(self):
        self.model = None
        self.model_size = "base"  # tiny, base, small, medium, large-v3
        self.device = "cpu"
        self.compute_type = "int8"
        self.executor = ThreadPoolExecutor(max_workers=1)

    def load_model(self):
        """Ленивая загрузка Faster-Whisper"""
        if self.model is None:
            try:
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
                print("✅ Faster-Whisper loaded")
            except Exception as e:
                print(f"❌ Failed to load Faster-Whisper: {str(e)}")
                raise

    def _transcribe_sync(self, video_path: str, language: str = 'ru') -> Optional[str]:
        """
        Синхронная транскрибация (для выполнения в executor)
        """
        try:
            self.load_model()

            print(f"Transcribing video: {video_path}")
            segments, info = self.model.transcribe(
                video_path,
                language=language,
                vad_filter=True,
                beam_size=5
            )
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text)

            transcript = " ".join(transcript_parts).strip()
            print(f"Transcription completed: {len(transcript)} chars")
            print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
            return transcript
        except Exception as e:
            print(f"   ❌ Transcription error: {str(e)}")
            traceback.print_exc()
            return None

    async def transcribe_video(self, video_path: str, language: str = 'ru') -> Optional[str]:
        """
        Асинхронная обёртка для транскрибации видео.

        Args:
            video_path: Путь к видео/аудио файлу
            language: Язык аудио ('ru', 'en', None для автоопределения)

        Returns:
            Текст транскрипции
        """
        try:
            loop = asyncio.get_event_loop()
            transcript = await loop.run_in_executor(
                self.executor,
                self._transcribe_sync,
                video_path,
                language
            )
            return transcript

        except Exception as e:
            print(f"❌ Async transcription error: {str(e)}")
            traceback.print_exc()
            return None


transcription_service = TranscriptionService()
