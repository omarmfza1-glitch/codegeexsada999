# === مستخرج الكيانات ===
# هذه الخدمة تستخرج الكيانات المهمة من النبناء على النية المحددة

import os
import logging
import re
from typing import Dict, Optional, List, Any
import json

logger = logging.getLogger(__name__)

class EntityExtractor:
    """
    مستخرج الكيانات - يقوم باستخراج الكيانات المهمة من النص بناءً على النية
    يدعم أنواع مختلفة من الكيانات مثل الأرقام، الأسماء، التواريخ، والمواقع
    """

    def __init__(self):
        """تهيئة مستخرج الكيانات"""
        self.entity_patterns = {
            "number": {
                "pattern": r"\b\d+(\.\d+)?\b",
                "description": "رقم أو قيمة رقمية"
            },
            "phone_number": {
                "pattern": r"\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
                "description": "رقم هاتف"
            },
            "date": {
                "pattern": r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{1,2}\s+(يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+\d{4}\b",
                "description": "تاريخ"
            },
            "time": {
                "pattern": r"\b\d{1,2}:\d{2}\s*(ص|م|AM|PM)?\b",
                "description": "وقت"
            },
            "name": {
                "pattern": r"\b[A-Za-z\u0600-\u06FF]{3,}\b",
                "description": "اسم"
            },
            "location": {
                "pattern": r"\b([A-Za-z\u0600-\u06FF]+(\s+[A-Za-z\u0600-\u06FF]+)*)\b",
                "description": "موقع أو مكان"
            },
            "email": {
                "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "description": "بريد إلكتروني"
            },
            "id": {
                "pattern": r"\b([A-Z]{2,}\d{4,}|[A-Z]{2,}\s+\d{4,})\b",
                "description": "معرف أو رمز"
            }
        }

        # تعريف الكيانات المطلوبة لكل نية
        self.intent_required_entities = {
            "appointment_booking": ["date", "time", "service_type"],
            "shipment_inquiry": ["id"],
            "account_balance": ["account_id"],
            "general_inquiry": []
        }

        # تحميل النماذج المتخصصة إذا كانت متاحة
        self._load_specialized_models()

    def _load_specialized_models(self):
        """تحميل النماذج المتخصصة لاستخراج الكيانات"""
        try:
            # في التطبيق الفعلي، سيتم تحميل نماذج متخصصة
            # هذا مثال افتراضي
            self.specialized_models = {
                "medical_entities": {
                    "status": "loaded",
                    "model_id": "medical_ner_v2",
                    "version": "2.1.0"
                },
                "financial_entities": {
                    "status": "loaded",
                    "model_id": "financial_ner_v1",
                    "version": "1.5.0"
                }
            }
            logger.info("تم تحميل النماذج المتخصصة بنجاح")
        except Exception as e:
            logger.error(f"فشل في تحميل النماذج المتخصصة: {str(e)}")
            self.specialized_models = {}

    def extract_entities(self, text: str, intent: str, language: str = "ar") -> Dict[str, Any]:
        """
        استخراج الكيانات من النص بناءً على النية

        Args:
            text: النص المراد استخراج الكيانات منه
            intent: النية المحددة مسبقاً
            language: لغة النص

        Returns:
            قاموس يحتوي على الكيانات المستخرجة
        """
        try:
            # 1. تنظيف النص
            cleaned_text = self._clean_text(text)

            # 2. استخراج الكيانات العامة باستخدام الأنماط
            general_entities = self._extract_with_patterns(cleaned_text)

            # 3. استخراج الكيانات المتخصصة إذا كانت النية تتطلبها
            specialized_entities = {}
            if intent in self.intent_required_entities:
                specialized_entities = self._extract_with_specialized_models(cleaned_text, intent, language)

            # 4. دمج الكيانات من المصادر المختلفة
            all_entities = {**general_entities, **specialized_entities}

            # 5. التحقق من الكيانات المطلوبة للنية
            missing_entities = self._check_required_entities(intent, all_entities)

            logger.info(f"تم استخراج الكيانات بنجاح للنية: {intent}")

            return {
                "entities": all_entities,
                "missing_entities": missing_entities,
                "intent": intent,
                "language": language
            }

        except Exception as e:
            logger.error(f"فشل في استخراج الكيانات: {str(e)}")
            return {
                "entities": {},
                "missing_entities": [],
                "intent": intent,
                "language": language,
                "error": str(e)
            }

    def _clean_text(self, text: str) -> str:
        """
        تنظيف النص من العلامات الترقيمية والإضافيات غير الضرورية

        Args:
            text: النص المراد تنظيفه

        Returns:
            النص المنظف
        """
        # إزالة علامات الترقيم الزائدة
        text = re.sub(r'[^\w\s؀-ۿ]', ' ', text)

        # إزالة المسافات الزائدة
        text = re.sub(r'\s+', ' ', text)

        # تحويل النص إلى أحرف صغيرة
        text = text.lower()

        return text.strip()

    def _extract_with_patterns(self, text: str) -> Dict[str, List[str]]:
        """
        استخراج الكيانات باستخدام الأنماط المحددة مسبقاً

        Args:
            text: النص المراد استخراج الكيانات منه

        Returns:
            قاموس يحتوي على أنواع الكيانات والقيم المستخرجة
        """
        entities = {}

        for entity_type, entity_info in self.entity_patterns.items():
            pattern = entity_info["pattern"]
            matches = re.findall(pattern, text)

            if matches:
                entities[entity_type] = matches

        return entities

    def _extract_with_specialized_models(self, text: str, intent: str, language: str) -> Dict[str, List[str]]:
        """
        استخراج الكيانات باستخدام النماذج المتخصصة

        Args:
            text: النص المراد استخراج الكيانات منه
            intent: النية المحددة
            language: لغة النص

        Returns:
            قاموس يحتوي على الكيانات المستخرجة
        """
        entities = {}

        try:
            # في التطبيق الفعلي، سيتم استخدام نماذج متخصصة مثل Spacy أو Stanza
            # هذا مثال افتراضي
            if intent == "appointment_booking":
                # استخراج الكيانات المتعلقة بحجز الموعد
                response = requests.post(
                    "https://ner-service/api/extract_appointment_entities",
                    json={"text": text, "language": language},
                    headers={"Authorization": f"Bearer {os.getenv('NER_API_TOKEN')}"}
                )

                if response.status_code == 200:
                    result = response.json()
                    entities.update(result.get("entities", {}))

            elif intent == "shipment_inquiry":
                # استخراج الكيانات المتعلقة بالشحن
                response = requests.post(
                    "https://ner-service/api/extract_shipment_entities",
                    json={"text": text, "language": language},
                    headers={"Authorization": f"Bearer {os.getenv('NER_API_TOKEN')}"}
                )

                if response.status_code == 200:
                    result = response.json()
                    entities.update(result.get("entities", {}))

            elif intent == "account_balance":
                # استخراج الكيانات المتعلقة بالحسابات
                response = requests.post(
                    "https://ner-service/api/extract_financial_entities",
                    json={"text": text, "language": language},
                    headers={"Authorization": f"Bearer {os.getenv('NER_API_TOKEN')}"}
                )

                if response.status_code == 200:
                    result = response.json()
                    entities.update(result.get("entities", {}))

        except Exception as e:
            logger.error(f"فشل في استخراج الكيانات المتخصصة: {str(e)}")

        return entities

    def _check_required_entities(self, intent: str, entities: Dict[str, List[str]]) -> List[str]:
        """
        التحقق من الكيانات المطلوبة للنية

        Args:
            intent: النية المحددة
            entities: الكيانات المستخرجة

        Returns:
            قائمة بالكيانات المفقودة
        """
        missing_entities = []

        if intent in self.intent_required_entities:
            required_entities = self.intent_required_entities[intent]

            for entity in required_entities:
                if entity not in entities or not entities[entity]:
                    missing_entities.append(entity)

        return missing_entities

    def get_entity_description(self, entity_type: str) -> Optional[str]:
        """
        الحصول على وصف الكيان

        Args:
            entity_type: نوع الكيان

        Returns:
            الوصف أو None إذا لم يوجد
        """
        if entity_type in self.entity_patterns:
            return self.entity_patterns[entity_type]["description"]
        return None

    def get_required_entities(self, intent: str) -> List[str]:
        """
        الحصول على الكيانات المطلوبة للنية

        Args:
            intent: النية المحددة

        Returns:
            قائمة بالكيانات المطلوبة
        """
        return self.intent_required_entities.get(intent, [])

    def is_entity_required(self, intent: str, entity_type: str) -> bool:
        """
        التحقق مما إذا كان الكيان مطلوباً للنية

        Args:
            intent: النية المحددة
            entity_type: نوع الكيان

        Returns:
            True إذا كان الكيان مطلوباً، False إذا لم يكن كذلك
        """
        if intent not in self.intent_required_entities:
            return False

        return entity_type in self.intent_required_entities[intent]
