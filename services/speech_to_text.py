# === خدمة تحويل الكلام إلى نص ===
# هذه الخدمة تحول الكلام إلى نص باستخدام تقنيات STT المتقدمة

import os
import logging
import io
import requests
from typing import Dict, Optional, List
import soundfile as sf

logger = logging.getLogger(__name__)

class SpeechToTextService:
    """
    خدمة تحويل الكلام إلى نص (STT)
    تدعم اللغات المتعددة وتوفر دقة عالية في التحويل
    """

    def __init__(self):
        """تهيئة خدمة تحويل الكلام إلى نص"""
        self.google_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.supported_languages = {
            "ar": "Arabic",
            "en": "English",
            "fr": "French",
            "es": "Spanish",
            "de": "German"
        }

    def transcribe_audio_stream(self, audio_stream: io.BytesIO, language: str = "auto") -> Dict:
        """
        تحديث تدفيع الصوت إلى نص

        Args:
            audio_stream: تدفق بايت للصوت
            language: لغة الصوت (auto للكشف التلقائي)

        Returns:
            قاموس يحتوي على النص المحول ومعلومات أخرى
        """
        try:
            # إذا كانت اللغة تلقائية، قم بالكشف أولاً
            if language == "auto":
                detected_language = self._detect_language(audio_stream)
                if detected_language:
                    language = detected_language

            # التأكد من أن اللغة مدعومة
            if language not in self.supported_languages:
                logger.warning(f"اللغة {language} غير مدعومة، سيتم استخدام اللغة العربية كافتراضي")
                language = "ar"

            # استخدام Google Speech-to-Text للتحويل
            google_result = self._transcribe_with_google(audio_stream, language)

            # استخدام Whisper للتحويل كبديل
            whisper_result = self._transcribe_with_whisper(audio_stream, language)

            # دمج النتائج للحصول على أفضل دقة
            final_result = self._combine_transcription_results(google_result, whisper_result)

            logger.info(f"تم تحويل الصوت إلى بنجاح باللغة: {language}")
            return final_result

        except Exception as e:
            logger.error(f"فشل في تحويل الصوت إلى نص: {str(e)}")
            return {"text": "", "language": language, "confidence": 0.0, "error": str(e)}

    def _detect_language(self, audio_stream: io.BytesIO) -> Optional[str]:
        """
        كشف لغة الصوت تلقائيًا

        Args:
            audio_stream: تدفق بايت للصوت

        Returns:
            رمز اللغة المكتشف أو None في حالة الفشل
        """
        try:
            # هنا يمكن استخدام خدمة مثل Google Speech-to-Text للكشف التلقائي
            # هذا مثال افتراضي
            response = requests.post(
                "https://language-detection-service/api/detect",
                files={"audio": audio_stream},
                headers={"Authorization": f"Bearer {os.getenv('LANGUAGE_DETECTION_TOKEN')}"}
            )
            if response.status_code == 200:
                return response.json().get("language")
            return None
        except Exception as e:
            logger.error(f"فشل في كشف لغة الصوت: {str(e)}")
            return None

    def _transcribe_with_google(self, audio_stream: io.BytesIO, language: str) -> Dict:
        """
        تحويل الصوت إلى نص باستخدام Google Speech-to-Text

        Args:
            audio_stream: تدفق بايت للصوت
            language: لغة الصوت

        Returns:
            قاموس يحتوي على النص المحول ومعلومات أخرى
        """
        try:
            # في التطبيق الفعلي، سيتم استخدام مكتبة Google Speech-to-Text
            # هذا مثال افتراضي
            response = requests.post(
                "https://speech-to-text.googleapis.com/v1/speech:recognize",
                headers={
                    "Authorization": f"Bearer {os.getenv('GOOGLE_ACCESS_TOKEN')}",
                    "Content-Type": "application/json"
                },
                json={
                    "config": {
                        "encoding": "LINEAR16",
                        "sampleRateHertz": 16000,
                        "languageCode": language,
                        "enableWordTimeOffsets": True,
                        "enableWordConfidence": True
                    },
                    "audio": {
                        "content": audio_stream.read().hex()
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                text = " ".join([alternative["transcript"] for alternative in result["results"]])
                confidence = result["results"][0]["alternatives"][0]["confidence"]

                return {
                    "text": text,
                    "language": language,
                    "confidence": confidence,
                    "service": "google"
                }
            else:
                return {
                    "text": "",
                    "language": language,
                    "confidence": 0.0,
                    "service": "google",
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"فشل في تحويل الصوت باستخدام Google: {str(e)}")
            return {
                "text": "",
                "language": language,
                "confidence": 0.0,
                "service": "google",
                "error": str(e)
            }

    def _transcribe_with_whisper(self, audio_stream: io.BytesIO, language: str) -> Dict:
        """
        تحويل الصوت إلى نص باستخدام Whisper

        Args:
            audio_stream: تدفق بايت للصوت
            language: لغة الصوت

        Returns:
            قاموس يحتوي على النص المحول ومعلومات أخرى
        """
        try:
            # في التطبيق الفعلي، سيتم استخدام مكتبة Whisper
            # هذا مثال افتراضي
            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                },
                files={
                    "file": audio_stream,
                    "model": "whisper-1",
                    "language": language,
                    "response_format": "verbose_json"
                }
            )

            if response.status_code == 200:
                result = response.json()
                text = result["text"]
                confidence = result.get("confidence", 0.0)

                return {
                    "text": text,
                    "language": language,
                    "confidence": confidence,
                    "service": "whisper"
                }
            else:
                return {
                    "text": "",
                    "language": language,
                    "confidence": 0.0,
                    "service": "whisper",
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"فشل في تحويل الصوت باستخدام Whisper: {str(e)}")
            return {
                "text": "",
                "language": language,
                "confidence": 0.0,
                "service": "whisper",
                "error": str(e)
            }

    def _combine_transcription_results(self, google_result: Dict, whisper_result: Dict) -> Dict:
        """
        دمج نتائج التحويل من مصادر مختلفة للحصول على أفضل دقة

        Args:
            google_result: نتيجة التحويل من Google
            whisper_result: نتيجة التحويل من Whisper

        Returns:
            قاموس يحتوي على النص المحول المدمج ومعلومات أخرى
        """
        # اختيار النتيجة ذات الثقة الأعلى
        if google_result["confidence"] > whisper_result["confidence"]:
            final_result = google_result
        else:
            final_result = whisper_result

        # إذا كانت النتائج مختلفة، يمكن دمجهما للحصول على دقة أفضل
        if google_result["text"] and whisper_result["text"] and google_result["text"] != whisper_result["text"]:
            # هنا يمكن تطبيق منطق أكثر تعقيدًا لدمج النصوص
            final_result["combined_text"] = f"{google_result['text']} | {whisper_result['text']}"

        return final_result
