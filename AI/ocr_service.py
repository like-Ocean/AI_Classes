import torch
from transformers import AutoModelForCausalLM, AutoProcessor
from typing import Optional
import json


class OCRService:

    def __init__(self):
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self):
        """Ленивая загрузка модели (только при первом использовании)"""
        if self.model is None:
            print("Loading dots.ocr model...")
            model_path = "rednote-hilab/dots.ocr"

            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True
            )

            self.processor = AutoProcessor.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            print("✅ Model loaded")

    async def extract_with_formulas(self, image_path: str) -> Optional[str]:
        """
        Извлечение текста и формул из изображения/PDF.

        Returns:
            Текст с формулами в LaTeX формате
        """
        try:
            self.load_model()

            prompt = """Extract all text and formulas from this document.
Format formulas in LaTeX.
Return plain text with formulas marked as $formula$."""

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image_path},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]

            text = self.processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            inputs = self.processor(
                text=[text],
                images=[image_path],
                padding=True,
                return_tensors="pt"
            ).to(self.device)

            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=4000
            )

            output = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0]

            return output

        except Exception as e:
            print(f"OCR with formulas error: {str(e)}")
            return None


ocr_service = OCRService()
