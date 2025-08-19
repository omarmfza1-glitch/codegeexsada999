# === معالج النوايا ===
# هذه الخدمة تحدد نية المستخدم من خلال تحليل النص المدخل

import os
import logging
import json
from typing import Dict, Optional, List
import requests

logger = logging.getLogger(__name__)

class IntentHandler:
    """
    معالج النوايا - يقوم بتحليل النص لتحديد نية المستخدم
    يدعم اللغات المتعددة ويوفر دقة عالية في تحديد النوايا
    """

    def __init__(self):
        """تهيئة معالج النوايا"""
        self.supported_intents = {
            "greeting": {
                "name": "تحية",
                "description": "عندما يرحب المستخدم بالنظام",
                "keywords": {
                    "ar": ["مرحبا", "أهلا", "زين", "صباح الخير", "مساء الخير", "أهلا وسهلا"],
                    "en": ["hello", "hi", "hey", "good morning", "good evening"],
                    "fr": ["bonjour", "salut", "bonsoir"],
                    "es": ["hola", "buenos días", "buenas tardes"],
                    "de": ["hallo", "guten Morgen", "guten Abend"]
                },
                "responses": {
                    "ar": ["مرحباً بك! كيف يمكنني مساعدتك اليوم؟"],
                    "en": ["Hello! How can I help you today?"],
                    "fr": ["Bonjour! Comment puis-je vous aider aujourd'hui?"],
                    "es": ["¡Hola! ¿Cómo puedo ayudarte hoy?"],
                    "de": ["Hallo! Wie kann ich Ihnen heute helfen?"]
                }
            },
            "goodbye": {
                "name": "وداعا",
                "description": "عندما يودع المستخدم النظام",
                "keywords": {
                    "ar": ["وداعا", "مع السلامة", "راحت بالك", "حتى اللقاء"],
                    "en": ["goodbye", "bye", "see you", "farewell"],
                    "fr": ["au revoir", "salut", "à plus tard"],
                    "es": ["adiós", "hasta luego", "nos vemos"],
                    "de": ["auf Wiedersehen", "tschüss", "bis später"]
                },
                "responses": {
                    "ar": ["مع السلامة! أتمنى لك يوماً سعيداً."],
                    "en": ["Goodbye! Have a great day."],
                    "fr": ["Au revoir! Passez une excellente journée."],
                    "es": ["¡Adiós! Que tengas un gran día."],
                    "de": ["Auf Wiedersehen! Einen schönen Tag noch."]
                }
            },
            "appointment_booking": {
                "name": "حجز موعد",
                "description": "عندما يحاول المستخدم حجز موعد",
                "keywords": {
                    "ar": ["أريد حجز موعد", "احجز لي موعد", "مواعيد", "متى يمكنني الحجز"],
                    "en": ["book appointment", "schedule meeting", "when can I book"],
                    "fr": ["prendre rendez-vous", "planifier une réunion"],
                    "es": ["cita", "reservar cita", "agendar cita"],
                    "de": ["Termin vereinbaren", "Termin buchen"]
                },
                "responses": {
                    "ar": ["بالتأكيد! سأساعدك في حجز موعد. ما هو نوع الموعد الذي تود حجزه؟"],
                    "en": ["Sure! I'll help you book an appointment. What type of appointment would you like to book?"],
                    "fr": ["Bien sûr! Je vais vous aider à prendre rendez-vous. Quel type de rendez-vous souhaitez-vous prendre?"],
                    "es": ["¡Claro! Te ayudaré a agendar una cita. ¿Qué tipo de cita te gustaría agendar?"],
                    "de": ["Selbstverständlich! Ich helfe Ihnen bei der Terminvereinbarung. Welchen Termin möchten Sie vereinbaren?"]
                }
            },
            "shipment_inquiry": {
                "name": "استعلام شحنة",
                "description": "عندما يسأل المستخدم عن حالة شحنته",
                "keywords": {
                    "ar": ["حالة شحنتي", "تتبع شحنتي", "أين شحنتي", "متابعة شحنة"],
                    "en": ["track shipment", "where is my package", "shipping status"],
                    "fr": ["suivre la livraison", "où est mon colis", "statut d'expédition"],
                    "es": ["seguir envío", "dónde está mi paquete", "estado del envío"],
                    "de": ["Sendung verfolgen", "Wo ist mein Paket", "Versandstatus"]
                },
                "responses": {
                    "ar": ["بالتأكيد! يرجى إدخال رقم تتبع الشحنة لمعرفة حالتها."],
                    "en": ["Of course! Please enter your tracking number to check its status."],
                    "fr": ["Bien sûr! Veuillez entrer votre numéro de suivi pour vérifier son état."],
                    "es": ["¡Claro! Por favor, ingrese su número de seguimiento para verificar su estado."],
                    "de": ["Selbstverständlich! Bitte geben Sie Ihre Sendungsnummer ein, um ihren Status zu überprüfen."]
                }
            },
            "account_balance": {
                "name": "رصيد الحساب",
                "description": "عندما يسأل المستخدم عن رصيد حسابه",
                "keywords": {
                    "ar": ["ما رصيد حسابي", "رصيدي", "حسابي", "رصيدي الحالي"],
                    "en": ["account balance", "my balance", "check balance"],
                    "fr": ["solde du compte", "mon solde", "vérifier le solde"],
                    "es": ["saldo de la cuenta", "mi saldo", "verificar saldo"],
                    "de": ["Kontostand", "Mein Kontostand", "Kontostand prüfen"]
                },
                "responses": {
                    "ar": ["بالتأكيد! سأتحقق من رصيد حسابك حالاً."],
                    "en": ["Of course! I'll check your account balance right away."],
                    "fr": ["Bien sûr! Je vais vérifier votre solde de compte tout de suite."],
                    "es": ["¡Claro! Verificaré tu saldo de cuenta de inmediato."],
                    "de": ["Selbstverständlich! Ich überprüfe Ihren Kontostand sofort."]
                }
            },
            "general_inquiry": {
                "name": "استعلام عام",
                "description": "عندما يسأل المستخدم عن معلومات عامة",
                "keywords": {
                    "ar": ["ما هو", "ماذا", "كيف", "متى", "أين", "لماذا"],
                    "en": ["what is", "what", "how", "when", "where", "why"],
                    "fr": ["quoi", "comment", "quand", "où", "pourquoi"],
                    "es": ["qué", "cómo", "cuándo", "dónde", "por qué"],
                    "de": ["was ist", "was", "wie", "wann", "wo", "warum"]
                },
                "responses": {
                    "ar": ["سأقوم بالبحث عن الإجابة لسؤالك."],
                    "en": ["I'll search for an answer to your question."],
                    "fr": ["Je vais rechercher une réponse à votre question."],
                    "es": ["Buscaré una respuesta a su pregunta."],
                    "de": ["Ich werde nach einer Antwort auf Ihre Frage suchen."]
                }
            }
        }

        # تحميل النماذج المسبقة التدريب إذا كانت متاحة
        self._load_pretrained_models()

    def _load_pretrained_models(self):
        """تحميل النماذج المسبقة التدريب لتحسين دقة تحديد النوايا"""
        try:
            # في التطبيق الفعلي، سيتم تحميل نماذج مثل Dialogflow أو Rasa
            # هذا مثال افتراضي
            self.pretrained_models = {
                "dialogflow": {
                    "status": "loaded",
                    "model_id": "dialogflow_v3",
                    "version": "3.0.0"
                },
                "rasa": {
                    "status": "not_loaded",
                    "model_id": "rasa_custom",
                    "version": "2.8.0"
                }
            }
            logger.info("تم تحميل النماذج المسبقة التدريب بنجاح")
        except Exception as e:
            logger.error(f"فشل في تحميل النماذج المسبقة التدريب: {str(e)}")
            self.pretrained_models = {}

    def extract_intent(self, text: str, language: str = "ar", context: Optional[Dict] = None) -> Dict:
        """
        استخراج نية المستخدم من النص

        Args:
            text: النص المراد تحليله
            language: لغة النص
            context: سياق المحادثة (اختياري)

        Returns:
            قاموس يحتوي على معلومات النية المكتشفة
        """
        try:
            # 1. تنظيف النص
            cleaned_text = self._clean_text(text)

            # 2. محاولة تحديد النية باستخدام النماذج المسبقة التدريب
            intent_result = self._extract_with_pretrained_models(cleaned_text, language)

            # 3. إذا فشل النموذج المسبق، استخدم الكلمات المفتاحية
            if not intent_result:
                intent_result = self._extract_with_keywords(cleaned_text, language)

            # 4. إذا تم العثور على نية، تحديثها بالسياق إذا كان متوفراً
            if intent_result and context:
                intent_result = self._enhance_with_context(intent_result, context)

            logger.info(f"تم تحديد النية: {intent_result.get('intent', 'unknown')} بنسبة ثقة {intent_result.get('confidence', 0.0):.2f}")

            return intent_result

        except Exception as e:
            logger.error(f"فشل في تحديد النية: {str(e)}")
            return {
                "intent": "general_inquiry",
                "confidence": 0.0,
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

    def _extract_with_pretrained_models(self, text: str, language: str) -> Optional[Dict]:
        """
        محاولة تحديد النية باستخدام النماذج المسبقة التدريب

        Args:
            text: النص المراد تحليله
            language: لغة النص

        Returns:
            قاموس يحتوي على معلومات النية المكتشفة أو None إذا لم يتم العثور عليها
        """
        try:
            # في التطبيق الفعلي، سيتم استخدام نماذج مثل Dialogflow أو Rasa
            # هذا مثال افتراضي
            if "dialogflow" in self.pretrained_models and self.pretrained_models["dialogflow"]["status"] == "loaded":
                response = requests.post(
                    "https://dialogflow.googleapis.com/v2/projects/your-project-id/agent/sessions/123456789/detectIntent",
                    headers={
                        "Authorization": f"Bearer {os.getenv('DIALOGFLOW_ACCESS_TOKEN')}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "queryInput": {
                            "text": {
                                "text": text,
                                "languageCode": language
                            }
                        }
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    intent_name = result["queryResult"].get("intent").get("displayName")
                    confidence = result["queryResult"].get("intentDetectionConfidence", 0.0)

                    return {
                        "intent": intent_name,
                        "confidence": confidence,
                        "source": "dialogflow"
                    }

            # إذا كان Rasa مثبتاً، جربه
            if "rasa" in self.pretrained_models and self.pretrained_models["rasa"]["status"] == "loaded":
                response = requests.post(
                    "http://rasa-server/model/parse",
                    json={
                        "text": text,
                        "sender_id": "user123"
                    },
                    headers={"Authorization": f"Bearer {os.getenv('RASA_ACCESS_TOKEN')}"}
                )

                if response.status_code == 200:
                    result = response.json()
                    intent = result["intent"]

                    return {
                        "intent": intent["name"],
                        "confidence": intent["confidence"],
                        "source": "rasa"
                    }

            return None

        except Exception as e:
            logger.error(f"فشل في تحديد النية باستخدام النماذج المسبقة التدريب: {str(e)}")
            return None

    def _extract_with_keywords(self, text: str, language: str) -> Dict:
        """
        تحديد النية باستخدام الكلمات المفتاحية

        Args:
            text: النص المراد تحليله
            language: لغة النص

        Returns:
            قاموس يحتوي على معلومات النية المكتشفة
        """
        # حساب درجة التطابق لكل نية
        intent_scores = {}

        for intent_name, intent_info in self.supported_intents.items():
            if language in intent_info["keywords"]:
                keywords = intent_info["keywords"][language]

                # حساب عدد الكلمات المفتاحية الموجودة في النص
                matches = sum(1 for keyword in keywords if keyword in text)

                # حساب نسبة التطابق
                match_ratio = matches / len(keywords) if keywords else 0

                # حساب درجة الثقة بناءً على طول النص
                if len(text) < 10:
                    match_ratio *= 0.7  # تقليل الثقة للنصوص القصيرة
                elif len(text) > 100:
                    match_ratio *= 1.2  # زيادة الثقة للنصوص الطويلة

                intent_scores[intent_name] = match_ratio

        # اختيار النية ذات أعلى درجة
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]

            return {
                "intent": best_intent,
                "confidence": confidence,
                "source": "keywords"
            }
        else:
            # إذا لم يتم العثور على أي كلمات مفتاحية، استخدم النية العامة
            return {
                "intent": "general_inquiry",
                "confidence": 0.5,
                "source": "keywords"
            }

    def _enhance_with_context(self, intent: Dict, context: Dict) -> Dict:
        """
        تحسين تحديد النية بالاعتماد على سياق المحادثة

        Args:
            intent: النية المحددة مسبقاً
            context: سياق المحادثة

        Returns:
            قاموس يحتوي على معلومات النية المحسنة
        """
        try:
            # إذا كان هناك سياق سابق، تحقق مما إذا كان يتطابق مع النية الحالية
            if "previous_intent" in context:
                previous_intent = context["previous_intent"]

                # إذا كان المستخدم يكرر نفس الطلب، زد الثقة
                if intent["intent"] == previous_intent["intent"]:
                    intent["confidence"] = min(intent["confidence"] * 1.2, 1.0)

            # إذا كان هناك سياق للغة، تأكد من تطابق اللغة
            if "language" in context and context["language"] != intent.get("language"):
                intent["language"] = context["language"]

            return intent

        except Exception as e:
            logger.error(f"فشل في تحسين تحديد النية بالسياق: {str(e)}")
            return intent

    def get_intent_info(self, intent_name: str) -> Optional[Dict]:
        """
        الحصول على معلومات عن نية محددة

        Args:
            intent_name: اسم النية

        Returns:
            قاموس يحتوي على معلومات النية أو None إذا لم توجد
        """
        return self.supported_intents.get(intent_name)

    def get_supported_intents(self) -> List[str]:
        """
        الحصول على قائمة النوايا المدعومة

        Returns:
            قائمة بأسماء النوايا المدعومة
        """
        return list(self.supported_intents.keys())
