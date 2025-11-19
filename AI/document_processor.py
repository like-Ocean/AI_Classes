from typing import Optional, List
from PyPDF2 import PdfReader
import docx
import pdfplumber
from chonkie import SemanticChunker


class DocumentProcessor:

    def __init__(self):
        self.chunker = SemanticChunker(
            embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            threshold=0.7,
            chunk_size=2000
        )
        self.ocr_engine = None

    def _init_ocr(self):
        if self.ocr_engine is None:
            try:
                from paddleocr import PaddleOCR
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang='ru',
                )

            except Exception as e:
                print(f"Failed to initialize PaddleOCR: {str(e)}")
                import traceback
                traceback.print_exc()
                self.ocr_engine = False
        else:
            print(f"PaddleOCR already initialized")

    def _clean_text(self, text: str) -> str:
        """
        Очистка текста от недопустимых символов для PostgreSQL.

        Args:
            text: Исходный текст

        Returns:
            Очищенный текст
        """
        if not text:
            return ""

        text = text.replace('\x00', '')
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())

        return text.strip()

    async def extract_text_from_file(
            self, file_path: str, file_type: str
    ) -> Optional[str]:
        """Извлечение текста из файла"""
        print(f"   🔧 DocumentProcessor.extract_text_from_file")
        print(f"      Path: {file_path}")
        print(f"      Type: {file_type}")

        try:
            if file_type.lower() == '.pdf':
                print(f"Calling _extract_from_pdf")
                text = await self._extract_from_pdf(file_path)
            elif file_type.lower() in ['.docx', '.doc']:
                print(f"Calling _extract_from_docx")
                text = await self._extract_from_docx(file_path)
            elif file_type.lower() == '.txt':
                print(f"Calling _extract_from_txt")
                text = await self._extract_from_txt(file_path)
            elif file_type.lower() in ['.jpg', '.jpeg', '.png']:
                print(f"Calling _extract_from_image")
                text = await self._extract_from_image(file_path)
            else:
                print(f"❌ Unsupported file type: {file_type}")
                return None

            if text:
                text = self._clean_text(text)
                print(f"✅ Text cleaned: {len(text)} chars")

            return text

        except Exception as e:
            print(f"❌ Error extracting text: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def _extract_from_pdf(self, file_path: str) -> str:
        """Извлечение текста из PDF с правильной кодировкой"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"=== Страница {i} ===\n{page_text}\n\n"

            print(f"✅ Used pdfplumber for extraction")

        except ImportError:
            print(f"⚠️ pdfplumber not installed, using PyPDF2")
            try:
                reader = PdfReader(file_path)
                for i, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"=== Страница {i} ===\n{page_text}\n\n"
            except Exception as e:
                print(f"❌ PyPDF2 extraction error: {str(e)}")

        except Exception as e:
            print(f"❌ PDF extraction error: {str(e)}")

        return text.strip()

    async def _extract_from_docx(self, file_path: str) -> str:
        """Извлечение текста из DOCX"""
        text = ""
        try:
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"❌ DOCX extraction error: {str(e)}")

        return text.strip()

    async def _extract_from_txt(self, file_path: str) -> str:
        """Чтение текстового файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ TXT reading error: {str(e)}")
            return ""

    async def _extract_from_image(self, file_path: str) -> str:
        """
            OCR для изображений с PaddleOCR
            TODO: НЕ РАБОТАЕТ С РУ ТЕКСТОМ, КАКАЯ ТО ЖИЖА
        """
        self._init_ocr()
        if self.ocr_engine and self.ocr_engine is not False:
            try:
                print(f"   🚀 Running PaddleOCR...")
                result = self.ocr_engine.ocr(file_path)

                if result and result[0]:
                    texts = []
                    for line in result[0]:
                        text_content = line[1][0]
                        texts.append(text_content)

                    extracted = " ".join(texts)
                    return extracted
                else:
                    return ""

            except Exception as e:
                print(f"   ⚠️ PaddleOCR runtime error: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ⚠️ PaddleOCR engine not available (state: {self.ocr_engine})")
        return ""

    def chunk_text(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """Разбиение большого текста на семантические чанки"""
        if len(text) <= max_chunk_size:
            return [text]

        try:
            chunks = self.chunker.chunk(text)
            return [chunk.text for chunk in chunks]
        except Exception as e:
            print(f"      ❌ Chunking error: {str(e)}")
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
