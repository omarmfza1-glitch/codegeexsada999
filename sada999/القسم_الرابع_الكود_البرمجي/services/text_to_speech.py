# === خدمة تحويل النص إلى كلام ===
# هذه الخدمة تحول النص إلى صوت باستخدام تقنيات TTS المتقدمة

import os
import logging
import io
import requests
from typing import Dict, Optional, List
import base64
import uuid
import datetime

logger = logging.getLogger(__name__)

class TextToSpeechService:
    """
    خدمة تحويل النص إلى كلام (TTS)
    تدعم اللغات المتعددة وتوفر أصواتاً طبيعية عالية الجودة
    """

    def __init__(self):
        """تهيئة خدمة تحويل النص إلى كلام"""
        # تهيئة الإعدادات
        self._initialize_settings()

        # تحميل الأصوات المتاحة
        self._load_available_voices()

        # تهيئة خدمة التشكيل
        self._setup_ssml_processor()

    def _initialize_settings(self):
        """تهيئة الإعدادات"""
        # تحميل الإعدادات من المتغيرات البيئية
        self.google_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

        # الإعدادات الافتراضية
        self.default_voice = "Polly.Ayah"  # الصوت الافتراضي للغة العربية
        self.default_language = "ar"
        self.default_voice_en = "Polly.Joanna"  # الصوت الافتراضي للغة الإنجليزية
        self.default_voice_fr = "Polly.Celine"  # الصوت الافتراضي للغة الفرنسية
        self.default_voice_es = "Polly.Conchita"  # الصوت الافتراضي للغة الإسبانية
        self.default_voice_de = "Polly.Vicki"  # الصوت الافتراضي للغة الألمانية

    def _load_available_voices(self):
        """تحميل الأصوات المتاحة"""
        try:
            # في التطبيق الفعلي، سيتم تحميل هذه الأصوات من ملف أو قاعدة بيانات
            # هذا مثال افتراضي
            self.available_voices = {
                "ar": [
                    {"id": "Polly.Ayah", "name": "آية", "gender": "female", "language": "ar-SA"},
                    {"id": "Polly.Farrah", "name": "فرح", "gender": "female", "language": "ar-AE"},
                    {"id": "Polly.Maryam", "name": "مريم", "gender": "female", "language": "ar-EG"}
                ],
                "en": [
                    {"id": "Polly.Joanna", "name": "Joanna", "gender": "female", "language": "en-US"},
                    {"id": "Polly.Kathy", "name": "Kathy", "gender": "female", "language": "en-US"},
                    {"id": "Polly.Salli", "name": "Salli", "gender": "female", "language": "en-US"},
                    {"id": "Polly.Justin", "name": "Justin", "gender": "male", "language": "en-US"}
                ],
                "fr": [
                    {"id": "Polly.Celine", "name": "Celine", "gender": "female", "language": "fr-FR"},
                    {"id": "Polly.Mathieu", "name": "Mathieu", "gender": "male", "language": "fr-FR"}
                ],
                "es": [
                    {"id": "Polly.Conchita", "name": "Conchita", "gender": "female", "language": "es-ES"},
                    {"id": "Polly.Miguel", "name": "Miguel", "gender": "male", "language": "es-ES"}
                ],
                "de": [
                    {"id": "Polly.Vicki", "name": "Vicki", "gender": "female", "language": "de-DE"},
                    {"id": "Polly.Hans", "name": "Hans", "gender": "male", "language": "de-DE"}
                ]
            }

            logger.info("تم تحميل الأصوات المتاحة بنجاح")
        except Exception as e:
            logger.error(f"فشل في تحميل الأصوات المتاحة: {str(e)}")
            self.available_voices = {}

    def _setup_ssml_processor(self):
        """إعداد معالج SSML"""
        try:
            # في التطبيق الفعلي، سيتم استخدام معالج SSML متخصص
            # هذا مثال افتراضي
            self.ssml_processor = {
                "status": "loaded",
                "service": "ssml_processor",
                "version": "1.0.0"
            }

            logger.info("تم إعداد معالج SSML بنجاح")
        except Exception as e:
            logger.error(f"فشل في إعداد معالج SSML: {str(e)}")
            self.ssml_processor = {"status": "not_loaded"}

    def text_to_speech(self, text: str, language: str = "ar", voice_id: Optional[str] = None, 
                      ssml: Optional[str] = None) -> Dict[str, str]:
        """
        تحويل النص إلى صوت

        Args:
            text: النص المراد تحويله إلى صوت
            language: لغة النص
            voice_id: معرف الصوت (اختياري)
            ssml: نص بصيغة SSML (اختياري)

        Returns:
            قاموس يحتوي على رابط الصوت أو ملف الصوت
        """
        try:
            # 1. اختيار الصوت المناسب
            selected_voice = self._select_voice(language, voice_id)

            # 2. إذا لم يكن هناك نص بصيغة SSML، قم بإنشائه
            if not ssml:
                ssml = self._create_ssml(text, language, selected_voice)

            # 3. تحويل النص إلى صوت باستخدام مزود الخدمة المفضل
            if self.elevenlabs_api_key:
                return self._convert_with_elevenlabs(ssml, selected_voice)
            elif self.aws_access_key and self.aws_secret_key:
                return self._convert_with_aws(ssml, selected_voice)
            elif self.google_credentials:
                return self._convert_with_google(ssml, language)
            else:
                logger.error("لا يوجد مزود خدمة TSM متاح")
                return {"error": "لا يوجد مزود خدمة TSM متاح"}

        except Exception as e:
            logger.error(f"فشل في تحويل النص إلى صوت: {str(e)}")
            return {"error": str(e)}

    def _select_voice(self, language: str, voice_id: Optional[str]) -> Dict:
        """
        اختيار الصوت المناسب

        Args:
            language: لغة النص
            voice_id: معرف الصوت المطلوب (اختياري)

        Returns:
            قاموس يحتوي على معلومات الصوت المحدد
        """
        # التحقق من وجود لغة في القائمة المتاحة
        if language not in self.available_voices:
            logger.warning(f"اللغة {language} غير مدعومة، سيتم استخدام اللغة العربية كافتراضي")
            language = "ar"

        # إذا تم تحديد صوت معين، تحقق من توفره
        if voice_id:
            for voice in self.available_voices[language]:
                if voice["id"] == voice_id:
                    return voice

            logger.warning(f"الصوت {voice_id} غير متاح للغة {language}، سيتم استخدام الصوت الافتراضي")

        # استخدام الصوت الافتراضي للغة
        default_voices = {
            "ar": self.default_voice,
            "en": self.default_voice_en,
            "fr": self.default_voice_fr,
            "es": self.default_voice_es,
            "de": self.default_voice_de
        }

        default_voice_id = default_voices.get(language, self.default_voice)

        for voice in self.available_voices[language]:
            if voice["id"] == default_voice_id:
                return voice

        # إذا لم يتم العثور على الصوت الافتراضي، استخدم أول صوت متاح
        return self.available_voices[language][0]

    def _create_ssml(self, text: str, language: str, voice: Dict) -> str:
        """
        إنشاء نص بصيغة SSML

        Args:
            text: النص المراد تحويله
            language: لغة النص
            voice: معلومات الصوت

        Returns:
            النص بصيغة SSML
        """
        try:
            # إذا كان معالج SSML متاحاً، استخدمه لإنشاء SSML متقدم
            if self.ssml_processor["status"] == "loaded":
                # في التطبيق الفعلي، سيتم استخدام معالج SSML متخصص
                # هذا مثال افتراضي
                ssml = f"""
                <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{voice['language']}">
                    <voice name="{voice['id']}">
                        <prosody rate="1.0" pitch="0">
                            {text}
                        </prosody>
                    </voice>
                </speak>
                """
            else:
                # إذا لم يكن معالج SSML متاحاً، استخدم SSML بسيط
                ssml = f"""
                <speak>
                    <voice name="{voice['id']}">
                        {text}
                    </voice>
                </speak>
                """

            return ssml
        except Exception as e:
            logger.error(f"فشل في إنشاء نص بصيغة SSML: {str(e)}")
            return text

    def _convert_with_elevenlabs(self, ssml: str, voice: Dict) -> Dict[str, str]:
        """
        تحويل النص إلى صوت باستخدام ElevenLabs

        Args:
            ssml: النص بصيغة SSML
            voice: معلومات الصوت

        Returns:
            قاموس يحتوي على رابط الصوت أو ملف الصوت
        """
        try:
            # في التطبيق الفعلي، سيتم استخدام مكتبة ElevenLabs
            # هذا مثال افتراضي
            response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice['id']}",
                headers={
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.elevenlabs_api_key
                },
                json={
                    "text": ssml,
                    "model_id": "eleven_multilingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.5
                    }
                }
            )

            if response.status_code == 200:
                # حفظ الملف الصوتي
                audio_file_name = f"audio_{uuid.uuid4()}.mp3"
                audio_file_path = os.path.join("temp", audio_file_name)

                # إنشاء المجلد إذا لم يكن موجوداً
                os.makedirs("temp", exist_ok=True)

                # حفظ الملف
                with open(audio_file_path, "wb") as audio_file:
                    audio_file.write(response.content)

                logger.info(f"تم تحويل النص إلى صوت باستخدام ElevenLabs: {audio_file_path}")

                return {
                    "audio_url": f"/temp/{audio_file_name}",
                    "audio_file": audio_file_path,
                    "service": "elevenlabs",
                    "voice": voice["id"]
                }
            else:
                logger.error(f"فشل في تحويل النص باستخدام ElevenLabs: {response.status_code}")
                return {"error": f"فشل في تحويل النص باستخدام ElevenLabs: {response.status_code}"}

        except Exception as e:
            logger.error(f"فشل في تحويل النص باستخدام ElevenLabs: {str(e)}")
            return {"error": str(e)}

    def _convert_with_aws(self, ssml: str, voice: Dict) -> Dict[str, str]:
        """
        تحويل النص إلى صوت باستخدام AWS Polly

        Args:
            ssml: النص بصيغة SSML
            voice: معلومات الصوت

        Returns:
            قاموس يحتوي على رابط الصوت أو ملف الصوت
        """
        try:
            # تحديد المنطقة واليوم الحالي للتوقيع
            region = "us-east-1"
            date = datetime.datetime.utcnow().strftime("%Y%m%d")
            datetime_str = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

            # في التطبيق الفعلي، سيتم استخدام مكتبة AWS Polly
            # هذا مثال افتراضي
            response = requests.post(
                f"https://polly.{region}.amazonaws.com/v1/speech",
                headers={
                    "Content-Type": "application/json",
                    "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
                    "X-Amz-Credential": f"{self.aws_access_key}/{date}/{region}/polly/aws4_request",
                    "X-Amz-Date": datetime_str,
                    "X-Amz-SignedHeaders": "host"
                },
                json={
                    "Text": ssml,
                    "OutputFormat": "mp3",
                    "VoiceId": voice["id"],
                    "Engine": "neural"
                }
            )

            if response.status_code == 200:
                # حفظ الملف الصوتي
                audio_file_name = f"audio_{uuid.uuid4()}.mp3"
                audio_file_path = os.path.join("temp", audio_file_name)

                # إنشاء المجلد إذا لم يكن موجوداً
                os.makedirs("temp", exist_ok=True)

                # حفظ الملف
                with open(audio_file_path, "wb") as audio_file:
                    audio_file.write(response.content)

                logger.info(f"تم تحويل النص إلى صوت باستخدام AWS Polly: {audio_file_path}")

                return {
                    "audio_url": f"/temp/{audio_file_name}",
                    "audio_file": audio_file_path,
                    "service": "aws",
                    "voice": voice["id"]
                }
            else:
                logger.error(f"فشل في تحويل النص باستخدام AWS Polly: {response.status_code}")
                return {"error": f"فشل في تحويل النص باستخدام AWS Polly: {response.status_code}"}

        except Exception as e:
            logger.error(f"فشل في تحويل النص باستخدام AWS Polly: {str(e)}")
            return {"error": str(e)}

    def _convert_with_google(self, ssml: str, language: str) -> Dict[str, str]:
        """
        تحويل النص إلى صوت باستخدام Google Text-to-Speech

        Args:
            ssml: النص بصيغة SSML
            language: لغة النص

        Returns:
            قاموس يحتوي على رابط الصوت أو ملف الصوت
        """
        try:
            # في التطبيق الفعلي، سيتم استخدام مكتبة Google Text-to-Speech
            # هذا مثال افتراضي
            response = requests.post(
                "https://texttospeech.googleapis.com/v1/text:synthesize",
                headers={
                    "Authorization": f"Bearer {os.getenv('GOOGLE_ACCESS_TOKEN')}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": {"ssml": ssml},
                    "voice": {
                        "languageCode": language,
                        "name": f"{language}-Standard-A",
                        "ssmlGender": "FEMALE"
                    },
                    "audioConfig": {
                        "audioEncoding": "MP3"
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                # فك تشفير الصوت
                audio_content = base64.b64decode(result["audioContent"])

                # حفظ الملف الصوتي
                audio_file_name = f"audio_{uuid.uuid4()}.mp3"
                audio_file_path = os.path.join("temp", audio_file_name)

                # إنشاء المجلد إذا لم يكن موجوداً
                os.makedirs("temp", exist_ok=True)

                # حفظ الملف
                with open(audio_file_path, "wb") as audio_file:
                    audio_file.write(audio_content)

                logger.info(f"تم تحويل النص إلى صوت باستخدام Google Text-to-Speech: {audio_file_path}")

                return {
                    "audio_url": f"/temp/{audio_file_name}",
                    "audio_file": audio_file_path,
                    "service": "google",
                    "language": language
                }
            else:
                logger.error(f"فشل في تحويل النص باستخدام Google Text-to-Speech: {response.status_code}")
                return {"error": f"فشل في تحويل النص باستخدام Google Text-to-Speech: {response.status_code}"}

        except Exception as e:
            logger.error(f"فشل في تحويل النص باستخدام Google Text-to-Speech: {str(e)}")
            return {"error": str(e)}

    def get_available_voices(self, language: Optional[str] = None) -> List[Dict]:
        """
        الحصول على قائمة الأصوات المتاحة

        Args:
            language: لغة الأصوات المطلوبة (اختياري)

        Returns:
            قائمة الأصوات المتاحة
        """
        if language:
            return self.available_voices.get(language, [])
        return self.available_voices

    def get_available_languages(self) -> List[str]:
        """
        الحصول على قائمة اللغات المدعومة

        Returns:
            قائمة اللغات المدعومة
        """
        return list(self.available_voices.keys())
