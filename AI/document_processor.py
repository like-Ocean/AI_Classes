import io
from typing import Optional, List
from PyPDF2 import PdfReader
import docx
from PIL import Image
from chonkie import SemanticChunker


class DocumentProcessor:

    def __init__(self):
        self.chunker = SemanticChunker(
            embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            threshold=0.7,
            chunk_size=2000
        )

    async def extract_text_from_file(
            self,
            file_path: str,
            file_type: str
    ) -> Optional[str]:
        """Извлечение текста из файла."""
        print(f"   🔧 DocumentProcessor.extract_text_from_file")
        print(f"      Path: {file_path}")
        print(f"      Type: {file_type}")

        try:
            if file_type.lower() == '.pdf':
                print(f"      → Calling _extract_from_pdf")
                return await self._extract_from_pdf(file_path)
            elif file_type.lower() in ['.docx', '.doc']:
                print(f"      → Calling _extract_from_docx")
                return await self._extract_from_docx(file_path)
            elif file_type.lower() == '.txt':
                print(f"      → Calling _extract_from_txt")
                return await self._extract_from_txt(file_path)
            elif file_type.lower() in ['.jpg', '.jpeg', '.png']:
                print(f"      → Calling _extract_from_image")
                return await self._extract_from_image(file_path)
            else:
                print(f"      ❌ Unsupported file type: {file_type}")
                return None
        except Exception as e:
            print(f"      ❌ Error extracting text: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def _extract_from_pdf(self, file_path: str) -> str:
        """Извлечение текста из PDF"""
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        except Exception as e:
            print(f"PDF extraction error: {str(e)}")

        return text.strip()

    async def _extract_from_docx(self, file_path: str) -> str:
        """Извлечение текста из DOCX"""
        text = ""
        try:
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"DOCX extraction error: {str(e)}")

        return text.strip()

    async def _extract_from_txt(self, file_path: str) -> str:
        """Чтение текстового файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"TXT reading error: {str(e)}")
            return ""

    async def _extract_from_image(self, file_path: str) -> str:
        """OCR для изображений с fallback"""
        try:
            from .ocr_service import ocr_service
            text = await ocr_service.extract_with_formulas(file_path)
            if text:
                return text
        except Exception as e:
            print(f"dots.ocr not available: {str(e)}")

        try:
            import pytesseract
            from PIL import Image
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='rus+eng')
            return text.strip()
        except Exception as e:
            print(f"pytesseract error: {str(e)}")
            return ""

    def chunk_text(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """
        Разбиение большого текста на семантические чанки.

        Args:
            text: Исходный текст
            max_chunk_size: Максимальный размер чанка

        Returns:
            Список чанков
        """
        if len(text) <= max_chunk_size:
            return [text]

        try:
            chunks = self.chunker.chunk(text)
            return [chunk.text for chunk in chunks]
        except Exception as e:
            print(f"Chunking error: {str(e)}")
            # Fallback: простое разбиение
            return self._simple_chunk(text, max_chunk_size)

    def _simple_chunk(self, text: str, chunk_size: int) -> List[str]:
        """Простое разбиение по размеру (fallback)"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0

        for word in words:
            if current_size + len(word) > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks


document_processor = DocumentProcessor()
