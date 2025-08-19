# === الملف الرئيسي لتشغيل نظام صدى999 ===
# هذا الملف يقوم بتنفيذ منطق المحادثة الكامل ويربط بين جميع الخدمات

import os
import uuid
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List

# استيراد الخدمات المختلفة
from services.session_manager import SessionManager
from services.twilio_handler import TwilioHandler
from services.speech_to_text import SpeechToTextService
from services.language_detector import LanguageDetector
from services.intent_handler import IntentHandler
from services.entity_extractor import EntityExtractor
from services.data_api import DataAPI
from services.response_generator import ResponseGenerator
from services.text_to_speech import TextToSpeechService
from services.conversation_manager import ConversationManager

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === التفويضات الفلسفية الأساسية ===
# 1. المقاطعة الديناميكية: تم تصميم النظام للتعامل مع مقاطعات المستخدم في أي لحظة. خدمة الاستماع (STT) تعمل في مسار موازٍ لخدمة إخراج الصوت (TTS).
# 2. التبديل السلس للغة: يقوم النظام تلقائيًا بكشف اللغة الأولية وتحميل نماذج STT/NLU والصوت الموافق لها ديناميكيًا، مما يضمن تجربة سلسة متعددة اللغات.
# 3. ذاكرة الحوار المستمرة: يتم تسجيل جميع التفاعلات لحظيًا ويمكن للنموذج اللغوي (NLG) الرجوع إليها لفهم السياق ضمن نفس المكالمة. رقم الهاتف هو المعرف الفريد للجلسة.
# 4. النبرة المعززة بـ SSML: الردود ليست مسطحة. يتم حقن علامات SSML للتوقفات والتأكيدات وتغيير حدة الصوت ديناميكيًا بواسطة خدمة NLG لمحاكاة التعبير البشري.
# =====================================

# تهيئ الخدمات الأساسية
session_manager = SessionManager()
conversation_manager = ConversationManager()
twilio_handler = TwilioHandler()
speech_to_text = SpeechToTextService()
language_detector = LanguageDetector()
intent_handler = IntentHandler()
entity_extractor = EntityExtractor()
data_api = DataAPI()
response_generator = ResponseGenerator()
text_to_speech = TextToSpeechService()

# إنشاء تطبيق FastAPI
app = FastAPI(title="نظام صدى999", version="1.0.0")

# إضافة CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# نماذج البيانات
class CallRequest(BaseModel):
    from_number: str
    to_number: str
    call_sid: str

class CallResponse(BaseModel):
    response: str
    status: str

class TwilioWebhook(BaseModel):
    CallSid: str
    From: str
    To: str
    Direction: str
    RecordingUrl: Optional[str] = None

@app.post("/start_call", response_model=CallResponse)
async def start_call(request: CallRequest):
    """
    بدء محادثة جديدة مع مستخدم
    """
    try:
        # إنشاء جلسة جديدة
        session_id = str(uuid.uuid4())
        session_manager.create_session(
            session_id=session_id,
            from_number=request.from_number,
            call_sid=request.call_sid
        )

        # تحديد لغة المتصل
        detected_language = language_detector.detect_language(request.from_number)

        # توليد رسالة الترحيب
        welcome_message = response_generator.generate_welcome_message(detected_language)

        # تحويل النص إلى صوت
        audio_url = text_to_speech.text_to_speech(welcome_message, detected_language)

        logger.info(f"بدأت مكالمة جديدة: {session_id}")

        return CallResponse(
            response=audio_url,
            status="success"
        )
    except Exception as e:
        logger.error(f"خطأ في بدء المكالمة: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/twilio_webhook", response_model=CallResponse)
async def handle_twilio_webhook(request: TwilioWebhook):
    """
    معالجة الويب هوكس من Twilio
    """
    try:
        # الحصول على معلومات الجلسة
        session_info = session_manager.get_session_by_call_sid(request.CallSid)

        if not session_info:
            # إنشاء جلسة جديدة إذا لم تكن موجودة
            session_id = str(uuid.uuid4())
            session_manager.create_session(
                session_id=session_id,
                from_number=request.From,
                call_sid=request.CallSid
            )
            session_info = {"session_id": session_id}

        # تحديد اتجاه المكالمة
        if request.Direction == "inbound":
            # معالجة المكالمة الواردة
            return await handle_inbound_call(session_info)
        else:
            # معالجة المكالمة الصادرة
            return await handle_outbound_call(session_info)

    except Exception as e:
        logger.error(f"خطأ في معالجة الويب هوكس: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_inbound_call(session_info: Dict):
    """
    معالجة المكالمة الواردة
    """
    session_id = session_info["session_id"]

    # الحصول على آخر نص تم تحويله
    last_transcript = conversation_manager.get_last_transcript(session_id)

    if not last_transcript:
        # إذا لم يكن هناك نص سابق، نرسل رسالة ترحيب
        welcome_message = response_generator.generate_welcome_message("ar")
        audio_url = text_to_speech.text_to_speech(welcome_message, "ar")

        return CallResponse(
            response=audio_url,
            status="success"
        )
    else:
        # تحليل النص لفهم النية والكيانات
        intent = intent_handler.extract_intent(last_transcript["text"], last_transcript["language"])
        entities = entity_extractor.extract_entities(last_transcript["text"], intent)

        # البحث في قاعدة البيانات
        data_response = data_api.query_data(intent, entities)

        # توليد الرد
        response_text = response_generator.generate_response(
            intent, 
            data_response, 
            last_transcript["language"],
            conversation_manager.get_conversation_context(session_id)
        )

        # تحويل الرد إلى صوت
        audio_url = text_to_speech.text_to_speech(response_text, last_transcript["language"])

        return CallResponse(
            response=audio_url,
            status="success"
        )

async def handle_outbound_call(session_info: Dict):
    """
    معالجة المكالمة الصادرة
    """
    # يمكن تطبيق منطق مختلف للمكالمات الصادرة
    return await handle_inbound_call(session_info)

@app.get("/health")
async def health_check():
    """
    فحص صحة النظام
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
