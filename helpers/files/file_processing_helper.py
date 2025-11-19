from typing import List, Optional, Tuple
import os


async def process_single_file(
        file_path: str, file_extension: str,
        document_processor, transcription_service
) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns:
        Tuple[text_content, transcript] - текст из документа/транскрипция из видео
    """
    VIDEO_AUDIO_EXTENSIONS = ['.mp4', '.webm', '.avi', '.mov', '.mp3', '.wav']
    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None, None

    if file_extension in VIDEO_AUDIO_EXTENSIONS:
        print(f"🎬 Transcribing: {os.path.basename(file_path)}")
        try:
            transcript = await transcription_service.transcribe_video(file_path, language='ru')
            return None, transcript if transcript else None
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            return None, None

    elif file_extension in IMAGE_EXTENSIONS or file_extension in ['.pdf', '.docx', '.doc', '.txt']:
        file_type = "image" if file_extension in IMAGE_EXTENSIONS else "document"
        print(f"📄 Processing {file_type}: {os.path.basename(file_path)}")
        try:
            text = await document_processor.extract_text_from_file(file_path, file_extension)
            return text if text else None, None
        except Exception as e:
            print(f"❌ Extraction error: {str(e)}")
            return None, None

    return None, None


def combine_contents(
        existing_text: Optional[str],
        new_texts: List[str],
        existing_transcript: Optional[str],
        new_transcripts: List[str]
) -> Tuple[Optional[str], Optional[str]]:
    combined_text = None
    combined_transcript = None
    if new_texts:
        new_text = "\n\n--- Следующий файл ---\n\n".join(new_texts)
        if existing_text and existing_text != "string":
            combined_text = f"{existing_text}\n\n--- Следующий файл ---\n\n{new_text}"
        else:
            combined_text = new_text

    if new_transcripts:
        new_transcript = "\n\n--- Следующее видео ---\n\n".join(new_transcripts)
        if existing_transcript:
            combined_transcript = f"{existing_transcript}\n\n--- Следующее видео ---\n\n{new_transcript}"
        else:
            combined_transcript = new_transcript

    return combined_text, combined_transcript

