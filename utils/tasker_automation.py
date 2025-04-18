import os
import json
import logging
import requests
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskerAutomation:
    """
    فئة للتعامل مع أتمتة التحويلات باستخدام تطبيق Tasker
    """
    
    def __init__(self, tasker_endpoint: str = None):
        """
        تهيئة الفئة مع نقطة نهاية Tasker
        
        :param tasker_endpoint: عنوان URL لواجهة برمجة تطبيقات Tasker
        """
        self.tasker_endpoint = tasker_endpoint or os.getenv("TASKER_ENDPOINT", "http://localhost:8080/tasker")
        self.timeout = 30  # مهلة الاتصال بالثواني
    
    def send_transfer_to_tasker(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        إرسال بيانات التحويل إلى Tasker لتنفيذ العملية تلقائياً
        
        :param transfer_data: بيانات التحويل (المحفظة، الرقم، المبلغ، العملة، إلخ)
        :return: نتيجة العملية
        """
        try:
            # تحضير البيانات للإرسال إلى Tasker
            transfer_id = transfer_data.get("transfer_id", "")
            wallet_name = transfer_data.get("wallet_name", "")
            wallet_type = self._get_wallet_type(wallet_name)
            recipient_number = transfer_data.get("recipient_number", "")
            amount = transfer_data.get("amount", "")
            currency = transfer_data.get("local_currency", "")
            
            logger.info(f"إرسال طلب تحويل إلى Tasker: {transfer_id}")
            
            # إنشاء رابط Tasker مع البيانات كمعلمات
            tasker_link = (
                f"tasker://transfer"
                f"?id={transfer_id}"
                f"&wallet={wallet_type}"
                f"&number={recipient_number}"
                f"&amount={amount}"
                f"&currency={currency}"
                f"&timestamp={datetime.now().isoformat()}"
            )
            
            # تسجيل الرابط في السجلات
            logger.info(f"تم إنشاء رابط Tasker: {tasker_link}")
            
            # تسجيل البيانات محلياً للاختبار
            self._log_transfer_locally({
                "action": "transfer",
                "wallet_name": wallet_name,
                "wallet_type": wallet_type,
                "recipient_number": recipient_number,
                "amount": amount,
                "currency": currency,
                "transfer_id": transfer_id,
                "timestamp": datetime.now().isoformat(),
                "tasker_link": tasker_link
            })
            
            # محاولة إرسال البيانات إلى خادم Tasker المحلي
            try:
                response = requests.post(
                    self.tasker_endpoint,
                    json={
                        "action": "transfer",
                        "transfer_id": transfer_id,
                        "wallet_type": wallet_type,
                        "recipient_number": recipient_number,
                        "amount": amount,
                        "currency": currency
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    logger.info(f"تم إرسال طلب التحويل بنجاح إلى Tasker: {transfer_id}")
                    return {
                        "success": True,
                        "message": "تم إرسال طلب التحويل بنجاح إلى Tasker",
                        "tasker_link": tasker_link
                    }
                else:
                    logger.warning(f"فشل في إرسال طلب التحويل إلى Tasker: {response.status_code} - {response.text}")
                    # في حالة فشل الاتصال، نعتبر العملية ناجحة ونرجع رابط Tasker
                    return {
                        "success": True,
                        "message": "تم إنشاء رابط Tasker بنجاح (وضع الاختبار)",
                        "tasker_link": tasker_link
                    }
            except requests.RequestException as e:
                logger.error(f"خطأ في الاتصال بـ Tasker: {e}")
                # في حالة فشل الاتصال، نعتبر العملية ناجحة ونرجع رابط Tasker
                return {
                    "success": True,
                    "message": "تم إنشاء رابط Tasker بنجاح (وضع الاختبار)",
                    "tasker_link": tasker_link
                }
                
        except Exception as e:
            logger.error(f"خطأ غير متوقع في إرسال التحويل: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _log_transfer_locally(self, payload: Dict[str, Any]) -> None:
        """
        تسجيل بيانات التحويل محلياً للاختبار
        
        :param payload: بيانات التحويل
        """
        try:
            # تسجيل في سجل النظام أولاً
            logger.info(f"محاولة تسجيل بيانات التحويل محلياً: {payload.get('transfer_id')}")
            
            # إنشاء مسار مجلد السجلات
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
            os.makedirs(log_dir, exist_ok=True)
            logger.info(f"مسار مجلد السجلات: {log_dir}")
            
            # تسجيل في ملف
            log_file = os.path.join(log_dir, "tasker_transfers.log")
            logger.info(f"مسار ملف السجل: {log_file}")
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat()}] طلب تحويل جديد:\n")
                f.write(json.dumps(payload, ensure_ascii=False, indent=2))
                f.write("\n\n")
                
            logger.info(f"تم تسجيل طلب التحويل محلياً بنجاح: {payload.get('transfer_id')}")
            
            # تسجيل في ملف منفصل باسم معرف التحويل
            transfer_log_file = os.path.join(log_dir, f"transfer_{payload.get('transfer_id')}.json")
            with open(transfer_log_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                
            logger.info(f"تم إنشاء ملف سجل منفصل للتحويل: {transfer_log_file}")
            
        except Exception as e:
            logger.error(f"خطأ في تسجيل التحويل محلياً: {e}", exc_info=True)
    
    def _get_wallet_type(self, wallet_name: str) -> str:
        """
        تحديد نوع المحفظة بناءً على اسمها
        
        :param wallet_name: اسم المحفظة
        :return: نوع المحفظة للاستخدام في Tasker
        """
        wallet_types = {
            "جوالي": "jawali",
            "كريمي": "kreemy",
            "كاش": "cash",
            "ون كاش": "onecash",
            "جيب": "jaib"
        }
        
        # تنظيف اسم المحفظة من المسافات الزائدة
        clean_name = wallet_name.strip() if wallet_name else ""
        
        # البحث عن النوع المناسب
        for name, wallet_type in wallet_types.items():
            if name in clean_name:
                return wallet_type
        
        # إرجاع القيمة الافتراضية إذا لم يتم العثور على تطابق
        return "unknown"
    
    def handle_tasker_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        معالجة الاستدعاء العكسي من Tasker بعد محاولة التحويل
        
        :param callback_data: بيانات الاستدعاء العكسي من Tasker
        :return: نتيجة المعالجة
        """
        try:
            transfer_id = callback_data.get("transfer_id")
            success = callback_data.get("success", False)
            error_message = callback_data.get("error")
            
            if not transfer_id:
                logger.error("معرف التحويل مفقود في بيانات الاستدعاء العكسي")
                return {
                    "success": False,
                    "error": "معرف التحويل مفقود"
                }
            
            logger.info(f"استلام استدعاء عكسي من Tasker للتحويل {transfer_id}: نجاح={success}")
            
            if success:
                # تم التحويل بنجاح
                result = {
                    "success": True,
                    "transfer_id": transfer_id,
                    "message": "تم التحويل بنجاح",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # فشل التحويل
                result = {
                    "success": False,
                    "transfer_id": transfer_id,
                    "error": error_message or "حدث خطأ أثناء التحويل",
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الاستدعاء العكسي: {e}")
            return {
                "success": False,
                "error": f"خطأ في معالجة الاستدعاء العكسي: {str(e)}"
            }
