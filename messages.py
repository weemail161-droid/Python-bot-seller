# messages.py
import os

PRICE = f"{os.getenv('USDT_PRICE', '10')} USDT"
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS', 'TRON_WALLET_ADDRESS')

START_USER = """أهلًا 👋
/buy - شراء حساب
/otp - جلب رمز التحقق
/myid - إظهار معرفك
/message - إرسال رسالة إلى المسؤول
"""

START_ADMIN = START_USER + """
— أوامر الإدارة —
/addaccount email password imap_server email_login email_app_password
/orders - عرض الطلبات المعلقة
/msglist - عرض رسائل المستخدمين
"""

BUY_MESSAGE = f"""💲 سعر الحساب: {{PRICE}}
📩 أرسل المبلغ إلى:
{{WALLET_ADDRESS}}

ثم أرسل لي txid أو صورة التحويل.
🔑 رقم طلبك: {{order_id}}
"""

NO_ACCOUNTS = "❌ لا يوجد حساب مرتبط بك."
OTP_CODE = "📩 رمز التحقق: {code}"
NO_OTP_FOUND = "⚠️ لم أعثر على رمز جديد."
OTP_CHOOSE = "🔑 اختر الحساب لعرض رمز OTP:"

ORDER_SENT_PHOTO = "⏳ تم إرسال الإثبات (صورة) إلى المسؤول."
ORDER_SENT_TEXT = "⏳ تم إرسال الإثبات إلى المسؤول."

PAYMENT_CONFIRMED = """🎉 تم تأكيد الدفع!
هذا حسابك:
Email: {email}
Password: {password}
"""

PAYMENT_REJECTED = "❌ تم رفض الدفع. تأكد من العملية."
NO_ACCOUNTS_AVAILABLE = "❌ لا توجد حسابات متاحة حاليًا."