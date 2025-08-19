# === خدمة كشف اللغة ===
# هذه الخدمة تقوم بالكشف عن لغة المستخدم تلقائياً وتحميل النماذج المناسبة

import os
import logging
import re
from typing import Dict, Optional, List
import requests

logger = logging.getLogger(__name__)

class LanguageDetector:
    """
    خدمة كشف اللغة - تقوم بالكشف عن لغة المستخدم تلقائياً
    وتوفر معلومات حول النماذج والصوت المناسبين للغة
    """

    def __init__(self):
        """تهيئة خدمة كشف اللغة"""
        self.supported_languages = {
            "ar": {
                "name": "العربية",
                "model": "arabic_nlp_model",
                "voice": "Polly.Ayah",
                "confidence_threshold": 0.85,
                "pattern": r"[؀-ۿ]"
            },
            "en": {
                "name": "English",
                "model": "english_nlp_model",
                "voice": "Polly.Joanna",
                "confidence_threshold": 0.8,
                "pattern": r"[a-zA-Z]"
            },
            "fr": {
                "name": "Français",
                "model": "french_nlp_model",
                "voice": "Polly.Celine",
                "confidence_threshold": 0.8,
                "pattern": r"[a-zA-Zàâäéèêëïîôöùûüÿç]"
            },
            "es": {
                "name": "Español",
                "model": "spanish_nlp_model",
                "voice": "Polly.Conchita",
                "confidence_threshold": 0.8,
                "pattern": r"[a-zA-Záéíóúüñ¿¡]"
            },
            "de": {
                "name": "Deutsch",
                "model": "german_nlp_model",
                "voice": "Polly.Vicki",
                "confidence_threshold": 0.8,
                "pattern": r"[a-zA-Zäöüß]"
            }
        }

    def detect_language(self, text: str, audio_stream: Optional[bytes] = None) -> str:
        """
        كشف لغة النص أو الصوت

        Args:
            text: النص المراد كشف لغته
            audio_stream: تدفق بايت للصوت (اختياري)

        Returns:
            رمز اللغة المكتشف
        """
        try:
            # 1. محاولة الكشف بناءً على النص
            text_language = self._detect_from_text(text)

            # 2. إذا كان هناك تدفق صوتي، حاول الكشف منه
            if audio_stream:
                audio_language = self._detect_from_audio(audio_stream)

                # إذا كان الناتجان متطابقين، أرجع النتيجة
                if text_language == audio_language:
                    return text_language

                # إذا كانا مختلفين، اختر الأكثر ثقة
                text_confidence = self._get_language_confidence(text, text_language)
                audio_confidence = self._get_language_confidence("", audio_language, audio_stream)

                if text_confidence > audio_confidence:
                    return text_language
                else:
                    return audio_language

            # إذا لم يكن هناك تدفق صوتي، أرجع نتيجة النص
            return text_language

        except Exception as e:
            logger.error(f"فشل في كشف اللغة: {str(e)}")
            # العودة إلى اللغة العربية كافتراضي في حالة الفشل
            return "ar"

    def _detect_from_text(self, text: str) -> str:
        """
        كشف لغة النص بناءً على الأنماط اللغوية

        Args:
            text: النص المراد كشف لغته

        Returns:
            رمز اللغة المكتشف
        """
        # تحويل النص إلى أحرف صغيرة للكشف
        text = text.lower()

        # حساب النسب المئوية لكل حرف مدعوم
        language_scores = {}

        for lang_code, lang_info in self.supported_languages.items():
            pattern = lang_info["pattern"]
            matches = re.findall(pattern, text)

            # حساب نسبة الأحرف المتطابقة
            language_ratio = len(matches) / len(text) if text else 0

            # تطبيق معامل تعديل بناءً على طول النص
            if len(text) < 10:
                language_ratio *= 0.7  # تقليل الثقة للنصوص القصيرة
            elif len(text) > 100:
                language_ratio *= 1.2  # زيادة الثقة للنصوص الطويلة

            language_scores[lang_code] = language_ratio

        # اختيار اللغة ذات أعلى نسبة
        detected_language = max(language_scores, key=language_scores.get)

        logger.info(f"تم كشف اللغة من النص: {detected_language} بنسبة ثقة {language_scores[detected_language]:.2f}")

        return detected_language

    def _detect_from_audio(self, audio_stream: bytes) -> str:
        """
        كشف لغة الصوت

        Args:
            audio_stream: تدفق بايت للصوت

        Returns:
            رمز اللغة المكتشف
        """
        try:
            # في التطبيق الفعلي، سيتم استخدام خدمة مثل Google Speech-to-Text
            # هذا مثال افتراضي
            response = requests.post(
                "https://language-detection-service/api/detect_from_audio",
                files={"audio": audio_stream},
                headers={"Authorization": f"Bearer {os.getenv('LANGUAGE_DETECTION_TOKEN')}"}
            )

            if response.status_code == 200:
                result = response.json()
                detected_language = result.get("language")
                confidence = result.get("confidence", 0.0)

                logger.info(f"تم كشف اللغة من الصوت: {detected_language} بنسبة ثقة {confidence:.2f}")

                # التحقق من أن اللغة مدعومة
                if detected_language in self.supported_languages:
                    return detected_language

                logger.warning(f"اللغة {detected_language} غير مدعومة، سيتم استخدام اللغة العربية كافتراضي")
                return "ar"
            else:
                logger.warning("فشل في كشف اللغة من الصوت، سيتم استخدام اللغة العربية كافتراضي")
                return "ar"

        except Exception as e:
            logger.error(f"فشل في كشف اللغة من الصوت: {str(e)}")
            return "ar"

    def _get_language_confidence(self, text: str, language: str, audio_stream: Optional[bytes] = None) -> float:
        """
        الحصول على درجة ثقة كشف اللغة

        Args:
            text: النص المراد كشف لغته
            language: اللغة المكتشفة
            audio_stream: تدفق بايت للصوت (اختياري)

        Returns:
            درجة الثقة بين 0 و 1
        """
        try:
            if language in self.supported_languages:
                # إذا كان هناك تدفق صوتي، استخدم خدمة كشف اللغة
                if audio_stream:
                    response = requests.post(
                        "https://language-detection-service/api/get_confidence",
                        files={"audio": audio_stream} if audio_stream else None,
                        json={"text": text} if text else None,
                        headers={"Authorization": f"Bearer {os.getenv('LANGUAGE_DETECTION_TOKEN')}"}
                    )

                    if response.status_code == 200:
                        return response.json().get("confidence", 0.0)

                # إذا لم يكن هناك تدفق صوتي، احسب الثقة بناءً على النص
                if text:
                    text_confidence = self._calculate_text_confidence(text, language)
                    return text_confidence

            return 0.0

        except Exception as e:
            logger.error(f"فشل في حساب ثقة اللغة: {str(e)}")
            return 0.0

    def _calculate_text_confidence(self, text: str, language: str) -> float:
        """
        حساب درجة ثقة كشف اللغة بناءً على النص

        Args:
            text: النص المراد كشف لغته
            language: اللغة المحددة

        Returns:
            درجة الثقة بين 0 و 1
        """
        if language not in self.supported_languages:
            return 0.0

        lang_info = self.supported_languages[language]
        pattern = lang_info["pattern"]
        matches = re.findall(pattern, text)

        # حساب نسبة الأحرف المتطابقة
        language_ratio = len(matches) / len(text) if text else 0

        # تطبيق معامل تعديل بناءً على طول النص
        if len(text) < 10:
            language_ratio *= 0.7  # تقليل الثقة للنصوص القصيرة
        elif len(text) > 100:
            language_ratio *= 1.2  # زيادة الثقة للنصوص الطويلة

        return language_ratio

    def get_language_info(self, language_code: str) -> Optional[Dict]:
        """
        الحصول على معلومات اللغة

        Args:
            language_code: رمز اللغة

        Returns:
            قاموس يحتوي على معلومات اللغة أو None إذا لم توجد
        """
        return self.supported_languages.get(language_code)

    def is_supported_language(self, language_code: str) -> bool:
        """
        التحقق مما إذا كانت اللغة مدعومة

        Args:
            language_code: رمز اللغة

        Returns:
            True إذا كانت اللغة مدعومة، False إذا لم تكن كذلك
        """
        return language_code in self.supported_languages

    def get_supported_languages(self) -> List[str]:
        """
        الحصول على قائمة اللغات المدعومة

        Returns:
            قائمة برموز اللغات المدعومة
        """
        return list(self.supported_languages.keys())
