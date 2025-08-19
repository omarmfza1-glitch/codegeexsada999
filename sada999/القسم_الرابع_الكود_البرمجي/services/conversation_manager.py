# === مدير المحادثات ===
# هذه الخدمة تدير جميع المحادثات النشطة وتوفر وصولاً إليها

import os
import logging
import json
import time
from typing import Dict, Optional, List, Any
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    مدير المحادثات - مسؤول عن تخزين وإدارة جميع تفاصيل المحادثة
    يوفر واجهة للوصول إلى تاريخ المحادثة وسياقها
    """

    def __init__(self):
        """تهيئة مدير المحادثات"""
        self.active_conversations: Dict[str, Dict] = {}
        self.conversation_history: Dict[str, List[Dict]] = {}
        self._initialize_storage()

    def _initialize_storage(self):
        """تهيئة نظام التخزين"""
        try:
            # في التطبيق الفعلي، سيتم استخدام قاعدة بيانات
            # هذا مثال افتراضي
            self.storage = {
                "type": "in_memory",
                "status": "initialized",
                "max_conversations": int(os.getenv("MAX_CONVERSATIONS", "1000")),
                "max_history": int(os.getenv("MAX_HISTORY", "50"))
            }

            logger.info("تم تهيئة نظام التخزين بنجاح")
        except Exception as e:
            logger.error(f"فشل في تهيئة نظام التخزين: {str(e)}")
            self.storage = {"type": "in_memory", "status": "error"}

    def start_conversation(self, phone_number: str, session_id: str) -> Dict:
        """
        بدء محادثة جديدة

        Args:
            phone_number: رقم هاتف المتصل
            session_id: معرف الجلسة

        Returns:
            معلومات المحادثة المنشأة
        """
        try:
            # إنشاء معرف فريد للمحادثة
            conversation_id = str(uuid.uuid4())

            # إنشاء سجل المحادثة
            conversation_info = {
                "conversation_id": conversation_id,
                "phone_number": phone_number,
                "session_id": session_id,
                "start_time": time.time(),
                "last_activity": time.time(),
                "language": "ar",  # اللغة الافتراضية
                "status": "active",
                "context": {},
                "transcripts": [],
                "responses": [],
                "metadata": {
                    "total_turns": 0,
                    "total_duration": 0,
                    "satisfaction_rating": None
                }
            }

            # حفظ المحادثة
            self.active_conversations[conversation_id] = conversation_info
            self.conversation_history[conversation_id] = []

            logger.info(f"تم بدء محادثة جديدة: {conversation_id} للمتصل: {phone_number}")
            return conversation_info

        except Exception as e:
            logger.error(f"فشل في بدء محادثة جديدة: {str(e)}")
            return {}

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        الحصول على معلومات المحادثة

        Args:
            conversation_id: معرف المحادثة

        Returns:
            معلومات المحادثة أو None إذا لم توجد
        """
        return self.active_conversations.get(conversation_id)

    def get_conversation_by_phone(self, phone_number: str) -> Optional[Dict]:
        """
        الحصول على المحادثة النشطة لرقم هاتف معين

        Args:
            phone_number: رقم الهاتف

        Returns:
            معلومات المحادثة أو None إذا لم توجد
        """
        for conversation in self.active_conversations.values():
            if conversation["phone_number"] == phone_number and conversation["status"] == "active":
                return conversation
        return None

    def update_conversation(self, conversation_id: str, **kwargs) -> bool:
        """
        تحديث معلومات المحادثة

        Args:
            conversation_id: معرف المحادثة
            **kwargs: سمات التحديث

        Returns:
            True إذا نجح التحديث، False إذا فشل
        """
        if conversation_id not in self.active_conversations:
            return False

        self.active_conversations[conversation_id].update(kwargs)
        self.active_conversations[conversation_id]["last_activity"] = time.time()
        return True

    def add_transcript(self, conversation_id: str, text: str, language: str = "ar", 
                      confidence: float = 0.0) -> bool:
        """
        إضافة نص محادثة إلى سجل المحادثة

        Args:
            conversation_id: معرف المحادثة
            text: نص المحادثة
            language: لغة النص
            confidence: درجة الثقة في النص

        Returns:
            True إذا نجت الإضافة، False إذا فشلت
        """
        try:
            if conversation_id not in self.active_conversations:
                logger.warning(f"المحادثة غير موجودة: {conversation_id}")
                return False

            # إنشاء سجل النص
            transcript = {
                "timestamp": time.time(),
                "text": text,
                "language": language,
                "confidence": confidence
            }

            # إضافة إلى سجل المحادثة
            self.active_conversations[conversation_id]["transcripts"].append(transcript)
            self.conversation_history[conversation_id].append({
                "type": "transcript",
                "data": transcript
            })

            # تحديث إحصائيات المحادثة
            self.active_conversations[conversation_id]["metadata"]["total_turns"] += 1

            # الاحتفاظ فقط بالعدد الأقصى من السجلات
            max_history = self.storage["max_history"]
            if len(self.active_conversations[conversation_id]["transcripts"]) > max_history:
                self.active_conversations[conversation_id]["transcripts"] =                     self.active_conversations[conversation_id]["transcripts"][-max_history:]

            logger.debug(f"تم إضافة نص إلى المحادثة: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"فشل في إضافة نص إلى المحادثة: {str(e)}")
            return False

    def add_response(self, conversation_id: str, text: str, audio_url: str = "", 
                    intent: str = "", entities: Dict = None) -> bool:
        """
        إضافة استجابة إلى سجل المحادثة

        Args:
            conversation_id: معرف المحادثة
            text: نص الاستجابة
            audio_url: رابط ملف الصوت
            intent: النية
            entities: الكيانات

        Returns:
            True إذا نجت الإضافة، False إذا فشلت
        """
        try:
            if conversation_id not in self.active_conversations:
                logger.warning(f"المحادثة غير موجودة: {conversation_id}")
                return False

            # إنشاء سجل الاستجابة
            response = {
                "timestamp": time.time(),
                "text": text,
                "audio_url": audio_url,
                "intent": intent,
                "entities": entities or {}
            }

            # إضافة إلى سجل المحادثة
            self.active_conversations[conversation_id]["responses"].append(response)
            self.conversation_history[conversation_id].append({
                "type": "response",
                "data": response
            })

            logger.debug(f"تم إضافة استجابة إلى المحادثة: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"فشل في إضافة استجابة إلى المحادثة: {str(e)}")
            return False

    def update_context(self, conversation_id: str, context: Dict) -> bool:
        """
        تحديث سياق المحادثة

        Args:
            conversation_id: معرف المحادثة
            context: السياق الجديد

        Returns:
            True إذا نجت التحديث، False إذا فشلت
        """
        try:
            if conversation_id not in self.active_conversations:
                logger.warning(f"المحادثة غير موجودة: {conversation_id}")
                return False

            # دمج السياق الجديد مع الق الحالي
            current_context = self.active_conversations[conversation_id]["context"]
            current_context.update(context)

            logger.debug(f"تم تحديث سياق المحادثة: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"فشل في تحديث سياق المحادثة: {str(e)}")
            return False

    def end_conversation(self, conversation_id: str, reason: str = "completed") -> bool:
        """
        إنهاء محادثة نشطة

        Args:
            conversation_id: معرف المحادثة
            reason: سبب إنهاء المحادثة

        Returns:
            True إذا نجت الإنهاء، False إذا فشلت
        """
        try:
            if conversation_id not in self.active_conversations:
                logger.warning(f"المحادثة غير موجودة: {conversation_id}")
                return False

            # تحديث حالة المحادثة
            self.active_conversations[conversation_id]["status"] = "ended"
            self.active_conversations[conversation_id]["end_time"] = time.time()
            self.active_conversations[conversation_id]["end_reason"] = reason

            # حساب إجمالي مدة المحادثة
            start_time = self.active_conversations[conversation_id]["start_time"]
            end_time = self.active_conversations[conversation_id]["end_time"]
            duration = end_time - start_time
            self.active_conversations[conversation_id]["metadata"]["total_duration"] = duration

            logger.info(f"تم إنهاء المحادثة: {conversation_id}، السبب: {reason}")
            return True

        except Exception as e:
            logger.error(f"فشل في إنهاء المحادثة: {str(e)}")
            return False

    def get_conversation_context(self, conversation_id: str) -> Dict:
        """
        الحصول على سياق المحادثة

        Args:
            conversation_id: معرف المحادثة

        Returns:
            سياق المحادثة
        """
        if conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]["context"]
        return {}

    def get_last_transcript(self, conversation_id: str) -> Optional[Dict]:
        """
        الحصول على آخر نص في المحادثة

        Args:
            conversation_id: معرف المحادثة

        Returns:
            آخر نص أو None إذا لم يوجد
        """
        if conversation_id not in self.active_conversations:
            return None

        transcripts = self.active_conversations[conversation_id]["transcripts"]
        if transcripts:
            return transcripts[-1]
        return None

    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """
        الحصول على تاريخ المحادثة

        Args:
            conversation_id: معرف المحادثة
            limit: الحد الأقصى للسجلات المرجعة

        Returns:
            قائمة بسجلات المحادثة
        """
        if conversation_id not in self.conversation_history:
            return []

        history = self.conversation_history[conversation_id]
        return history[-limit:] if limit else history

    def get_active_conversations_count(self) -> int:
        """
        الحصول على عدد المحادثات النشطة

        Returns:
            عدد المحادثات النشطة
        """
        return len([c for c in self.active_conversations.values() if c["status"] == "active"])

    def cleanup_inactive_conversations(self, timeout_seconds: int = 3600) -> int:
        """
        تنظيف المحادثات غير النشطة التي انتهت مهلتها

        Args:
            timeout_seconds: عدد الثواني التي يجب أن تكون المحادثة غير نشطة فيها

        Returns:
            عدد المحادثات التي تم تنظيفها
        """
        current_time = time.time()
        cleaned_count = 0

        for conversation_id, conversation in list(self.active_conversations.items()):
            if (conversation["status"] == "active" and 
                current_time - conversation["last_activity"] > timeout_seconds):
                self.end_conversation(conversation_id, "timeout")
                cleaned_count += 1

        return cleaned_count

    def export_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        تصدير محادثة كاملة

        Args:
            conversation_id: معرف المحادثة

        Returns:
            قاموس يحتوي على جميع تفاصيل المحادثة أو None إذا لم توجد
        """
        if conversation_id not in self.active_conversations:
            return None

        conversation = self.active_conversations[conversation_id]
        history = self.conversation_history.get(conversation_id, [])

        return {
            "conversation_info": conversation,
            "history": history
        }

    def get_conversation_statistics(self, conversation_id: str) -> Optional[Dict]:
        """
        الحصول على إحصائيات المحادثة

        Args:
            conversation_id: معرف المحادثة

        Returns:
            قاموس يحتوي على إحصائيات المحادثة أو None إذا لم توجد
        """
        if conversation_id not in self.active_conversations:
            return None

        conversation = self.active_conversations[conversation_id]
        metadata = conversation["metadata"]

        # حساب إحصائيات إضافية
        transcripts = conversation["transcripts"]
        responses = conversation["responses"]

        # حساب متوسط درجة الثقة
        avg_confidence = 0
        if transcripts:
            total_confidence = sum(t["confidence"] for t in transcripts)
            avg_confidence = total_confidence / len(transcripts)

        # حساب عدد النوايا المختلفة
        intents = set(r["intent"] for r in responses if r["intent"])

        return {
            "total_turns": metadata["total_turns"],
            "total_duration": metadata["total_duration"],
            "avg_confidence": avg_confidence,
            "unique_intents": len(intents),
            "status": conversation["status"],
            "start_time": conversation["start_time"],
            "last_activity": conversation["last_activity"]
        }

    def save_conversation_to_database(self, conversation_id: str) -> bool:
        """
        حفظ المحادثة في قاعدة البيانات

        Args:
            conversation_id: معرف المحادثة

        Returns:
            True إذا نجت عملية الحفظ، False إذا فشلت
        """
        try:
            if conversation_id not in self.active_conversations:
                logger.warning(f"المحادثة غير موجودة: {conversation_id}")
                return False

            conversation = self.active_conversations[conversation_id]
            history = self.conversation_history.get(conversation_id, [])

            # في التطبيق الفعلي، سيتم حفظ المحادثة في قاعدة بيانات
            # هذا مثال افتراضي
            data_to_save = {
                "conversation": conversation,
                "history": history,
                "export_timestamp": time.time()
            }

            # حفظ الملف
            filename = f"conversation_{conversation_id}.json"
            filepath = os.path.join("conversations", filename)

            # إنشاء المجلد إذا لم يكن موجوداً
            os.makedirs("conversations", exist_ok=True)

            # حفظ الملف
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            logger.info(f"تم حفظ المحادثة في قاعدة البيانات: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"فشل في حفظ المحادثة في قاعدة البيانات: {str(e)}")
            return False

    def search_conversations(self, phone_number: Optional[str] = None, 
                           intent: Optional[str] = None, 
                           date_from: Optional[datetime] = None,
                           date_to: Optional[datetime] = None) -> List[Dict]:
        """
        البحث في المحادثات

        Args:
            phone_number: رقم هاتف للبحث (اختياري)
            intent: نية للبحث (اختياري)
            date_from: تاريخ البداية (اختياري)
            date_to: تاريخ النهاية (اختياري)

        Returns:
            قائمة بالمحادثات التي تطابق معايير البحث
        """
        results = []

        for conversation_id, conversation in self.active_conversations.items():
            # التحقق من رقم الهاتف
            if phone_number and conversation["phone_number"] != phone_number:
                continue

            # التحقق من النية
            if intent:
                found_intent = False
                for response in conversation["responses"]:
                    if response["intent"] == intent:
                        found_intent = True
                        break
                if not found_intent:
                    continue

            # التحقق من تاريخ البداية
            if date_from:
                start_time = datetime.fromtimestamp(conversation["start_time"])
                if start_time < date_from:
                    continue

            # التحقق من تاريخ النهاية
            if date_to:
                end_time = conversation.get("end_time", time.time())
                end_datetime = datetime.fromtimestamp(end_time)
                if end_datetime > date_to:
                    continue

            # إذا تطابقت جميع المعايير، أضف المحادثة إلى النتائج
            results.append({
                "conversation_id": conversation_id,
                "phone_number": conversation["phone_number"],
                "start_time": conversation["start_time"],
                "status": conversation["status"]
            })

        return results

    def get_satisfaction_statistics(self) -> Dict:
        """
        الحصول على إحصائيات الرضا

        Returns:
            قاموس يحتوي على إحصائيات الرضا
        """
        # في التطبيق الفعلي، سيتم جمع هذه الإحصائيات من قاعدة البيانات
        # هذا مثال افتراضي
        return {
            "total_conversations": len(self.active_conversations),
            "satisfaction_ratings": {
                "excellent": 0,
                "good": 0,
                "average": 0,
                "poor": 0
            },
            "average_rating": 0.0
        }

    def analyze_conversation_patterns(self) -> Dict:
        """
        تحليل أنماط المحادثة

        Returns:
            قاموس يحتوي على تحليل الأنماط
        """
        # في التطبيق الفعلي، سيتم إجراء تحليل متقدم
        # هذا مثال افتراضي
        return {
            "most_common_intents": [],
            "average_conversation_duration": 0,
            "peak_hours": [],
            "common_issues": []
        }
def cleanup_inactive_conversations(self, timeout_seconds: int = 3600) -> int:
        """
        تنظيف المحادثات غير النشطة التي انتهت مهلتها

        Args:
            timeout_seconds: عدد الثواني التي يجب أن تكون المحادثة غير نشطة فيها

        Returns:
            عدد المحادثات التي تم تنظيفها
        """
        current_time = time.time()
        cleaned_count = 0

        for conversation_id, conversation in list(self.active_conversations.items()):
            if (conversation["status"] == "active" and 
                current_time - conversation["last_activity"] > timeout_seconds):
                self.end_conversation(conversation_id, "timeout")
                cleaned_count += 1

        return cleaned_count

    def export_conversation(self, conversation_id: str, format: str = "json") -> Optional[str]:
        """
        تصدير محادثة

        Args:
            conversation_id: معرف المحادثة
            format: تنسيق التصدير (json, csv)

        Returns:
            المحادثة المصدرة كسلسلة نصية أو None في حالة الفشل
        """
        try:
            if conversation_id not in self.active_conversations:
                logger.warning(f"المحادثة غير موجودة: {conversation_id}")
                return None

            conversation = self.active_conversations[conversation_id]

            if format.lower() == "json":
                return json.dumps(conversation, ensure_ascii=False, indent=2)
            elif format.lower() == "csv":
                # في التطبيق الفعلي، سيتم إنشاء ملف CSV
                # هذا مثال بسيط
                csv_lines = [
                    "timestamp,type,text,language,confidence,intent,entities",
                    ",".join([
                        str(conversation["start_time"]),
                        "conversation_info",
                        "",
                        "",
                        "",
                        "",
                        ""
                    ])
                ]

                for transcript in conversation["transcripts"]:
                    csv_lines.append(",".join([
                        str(transcript["timestamp"]),
                        "transcript",
                        transcript["text"],
                        transcript["language"],
                        str(transcript["confidence"]),
                        "",
                        ""
                    ]))

                for response in conversation["responses"]:
                    csv_lines.append(",".join([
                        str(response["timestamp"]),
                        "response",
                        response["text"],
                        "",
                        "",
                        response["intent"],
                        str(response["entities"])
                    ]))

                return "\n".join(csv_lines)
            else:
                logger.warning(f"تنسيق التصدير غير مدعوم: {format}")
                return None

        except Exception as e:
            logger.error(f"فشل في تصدير المحادثة: {str(e)}")
            return None
