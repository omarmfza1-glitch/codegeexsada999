# === معالج Twilio ===
# هذا المكون يتعامل مع جميع عمليات التواصل مع منصة Twilio

import os
import logging
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from typing import Dict, Optional, List
import requests

logger = logging.getLogger(__name__)

class TwilioHandler:
    """
    معالج Twilio - يدير جميع عمليات التواصل مع منصة Twilio
    """

    def __init__(self):
        """تهيئة معالج Twilio"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.client = Client(self.account_sid, self.auth_token)
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

    def make_outbound_call(self, to_number: str, url: str) -> Optional[str]:
        """
        إجراء مكالمة صادرة

        Args:
            to_number: رقم الهاتف الذي ستم إجراء المكالمة إليه
            url: عنوان URL الذي سيتم استدعاؤه عند بدء المكالمة

        Returns:
            معرف المكالمة (call_sid) أو None في حالة الفشل
        """
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.twilio_number,
                url=url,
                method='GET'
            )
            logger.info(f"تم إجراء مكالمة صادرة: {call.sid} إلى {to_number}")
            return call.sid
        except Exception as e:
            logger.error(f"فشل في إجراء المكالمة الصادرة: {str(e)}")
            return None

    def generate_twiml_response(self, text: str, language: str = "ar", gather_next: bool = True) -> str:
        """
        توليد استجابة TwiML

        Args:
            text: النص الذي سيتم نقله إلى المتصل
            language: لغة النص
            gather_next: ما إذا كان يجب جمع مدخلات المستخدم التالية

        Returns:
            سلسلة نصية تحتوي على استجابة TwiML
        """
        response = VoiceResponse()

        if gather_next:
            gather = Gather(
                input='speech',
                speech_timeout='auto',
                language=language,
                action='/process_speech'
            )
            gather.say(text, language=language, voice='Polly.Ayah')
            response.append(gather)
        else:
            response.say(text, language=language, voice='Polly.Ayah')

        return str(response)

    def get_call_recording(self, call_sid: str) -> Optional[str]:
        """
        الحصول على تسجيل المكالمة

        Args:
            call_sid: معرف المكالمة

        Returns:
            رابط تسجيل المكالمة أو None إذا لم يكن موجودًا
        """
        try:
            call = self.client.calls(call_sid).fetch()
            if call.recording_url:
                return call.recording_url
            return None
        except Exception as e:
            logger.error(f"فشل في الحصول على تسجيل المكالمة: {str(e)}")
            return None

    def send_sms(self, to_number: str, message: str) -> Optional[str]:
        """
        إرسال رسالة SMS

        Args:
            to_number: رقم الهاتف الذي ستُرسل إليه الرسالة
            message: محتوى الرسالة

        Returns:
            معرف الرسالة أو None في حالة الفشل
        """
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.twilio_number,
                to=to_number
            )
            logger.info(f"تم إرسال رسالة SMS: {message.sid} إلى {to_number}")
            return message.sid
        except Exception as e:
            logger.error(f"فشل في إرسال الرسالة: {str(e)}")
            return None

    def transcribe_audio(self, audio_url: str) -> Optional[str]:
        """
        تحويل الصوت إلى نص باستخدام خدمة تحويل الكلام إلى نص

        Args:
            audio_url: رابط ملف الصوت

        Returns:
            النص المحول أو None في حالة الفشل
        """
        try:
            # هنا يمكن استخدام خدمة مثل Google Speech-to-Text أو أي خدمة أخرى
            # هذا مثال افتراضي
            response = requests.post(
                "https://speech-to-text-service/api/transcribe",
                json={"audio_url": audio_url},
                headers={"Authorization": f"Bearer {os.getenv('STT_API_TOKEN')}"}
            )
            if response.status_code == 200:
                return response.json().get("transcript")
            return None
        except Exception as e:
            logger.error(f"فشل في تحويل الصوت إلى نص: {str(e)}")
            return None
