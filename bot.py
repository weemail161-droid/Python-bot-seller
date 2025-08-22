# bot.py - تلقائي + دعم الرسائل
import os
import re
import logging
import imaplib
import email
import sqlite3

from index import keep_alive
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

keep_alive()
# --- تحميل الإعدادات ---
from dotenv import load_dotenv
load_dotenv("config.env")

# --- استيراد الملفات ---
from messages import *
from database import *
from trc20_checker import verify_tron_txid

# --- إعدادات البوت ---
logging.basicConfig(level=logging.INFO)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "").lower()
MIN_AMOUNT = float(os.getenv("USDT_PRICE", "10"))

if not TELEGRAM_TOKEN:
    print("❌ خطأ: لم يتم تحديد TELEGRAM_TOKEN")
    exit(1)

updater = Updater(TELEGRAM_TOKEN, use_context=True)
bot = updater.bot

# --- التحقق من المسؤول ---
def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

# --- جلب OTP ---
OTP_REGEX = re.compile(r"(?<!\d)(\d{4,8})(?!\d)")

def fetch_latest_otp(imap_server, login, pwd):
    try:
        m = imaplib.IMAP4_SSL(imap_server)
        m.login(login, pwd)
        m.select("INBOX")
        _, data = m.search(None, "ALL")
        ids = data[0].split()[-5:]
        for num in reversed(ids):
            _, msg_data = m.fetch(num, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode("utf-8", errors="ignore")
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="ignore")
            code = OTP_REGEX.search(body)
            if code:
                m.close()
                return code.group(1)
        m.close()
        return None
    except:
        return None

# === الأوامر ===
def cmd_start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = START_ADMIN if is_admin(user_id) else START_USER
    update.message.reply_text(text)

def cmd_myid(update: Update, context: CallbackContext):
    update.message.reply_text(f"ID: {update.message.from_user.id}")

def cmd_addaccount(update: Update, context: CallbackContext):
    if not is_admin(update.message.from_user.id):
        update.message.reply_text("❌ أمر خاص بالمسؤول.")
        return
    args = context.args
    if len(args) != 5:
        update.message.reply_text("الاستخدام:\n/addaccount email pass imap login apppass")
        return
    add_account_row(*args)
    update.message.reply_text("✅ تم إضافة الحساب.")

def cmd_buy(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    order_id = add_order(str(user_id))
    text = BUY_MESSAGE.format(PRICE=PRICE, WALLET_ADDRESS=WALLET_ADDRESS.upper(), order_id=order_id)
    update.message.reply_text(text)

def cmd_otp(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    accs = get_user_accounts(str(user_id))
    if not accs:
        update.message.reply_text(NO_ACCOUNTS)
        return
    if len(accs) == 1:
        code = fetch_latest_otp(accs[0][3], accs[0][4], accs[0][5])
        update.message.reply_text(OTP_CODE.format(code=code) if code else NO_OTP_FOUND)
    else:
        keyboard = [[InlineKeyboardButton(acc[1], callback_data=f"otp_{acc[0]}")] for acc in accs]
        update.message.reply_text("🔑 اختر الحساب:", reply_markup=InlineKeyboardMarkup(keyboard))

# === إرسال رسالة للمسؤول ===
def cmd_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = " ".join(context.args).strip()
    if not text:
        update.message.reply_text("✍️ استخدم: /message نص الرسالة")
        return
    save_message(user_id, text)
    try:
        bot.send_message(ADMIN_ID, f"📩 رسالة جديدة من {user_id}:\n{text}")
    except:
        pass
    update.message.reply_text("✅ تم إرسال رسالتك إلى الإدارة.")

# === عرض الرسائل للمشرف ===
def cmd_msglist(update: Update, context: CallbackContext):
    if not is_admin(update.message.from_user.id):
        update.message.reply_text("❌ أمر خاص بالمسؤول.")
        return
    messages = get_unreplied_messages()
    if not messages:
        update.message.reply_text("📭 لا توجد رسائل جديدة.")
        return
    for msg_id, user_id, content in messages:
        keyboard = [
            [InlineKeyboardButton("✉️ رد", callback_data=f"reply_{msg_id}_{user_id}")],
            [InlineKeyboardButton("🗑️ حذف", callback_data=f"delete_{msg_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"👤 من: {user_id}\n💬 الرسالة:\n{content}",
            reply_markup=reply_markup
        )

# === معالجة الأزرار ===
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data.split("_")
    action = data[0]

    if action == "reply":
        msg_id = int(data[1])
        user_id = int(data[2])
        context.user_data["reply_to"] = {"msg_id": msg_id, "user_id": user_id}
        try:
            query.edit_message_text(f"✏️ أرسل ردك الآن للمستخدم {user_id} (الرسالة #{msg_id})")
        except:
            pass

    elif action == "delete":
        msg_id = int(data[1])
        delete_message(msg_id)
        try:
            query.edit_message_text("🗑️ تم حذف الرسالة.")
        except:
            pass

    elif action == "otp":
        acc_id = int(data[1])
        conn = sqlite3.connect("accounts.db")
        c = conn.cursor()
        c.execute("SELECT * FROM accounts WHERE id=?", (acc_id,))
        acc = c.fetchone()
        conn.close()
        if acc:
            code = fetch_latest_otp(acc[3], acc[4], acc[5])
            bot.send_message(query.from_user.id, OTP_CODE.format(code=code) if code else NO_OTP_FOUND)

# === معالجة الرد من المسؤول ===
def handle_admin_reply(update: Update, context: CallbackContext):
    if not is_admin(update.message.from_user.id):
        return
    if "reply_to" not in context.user_data:
        return

    data = context.user_data["reply_to"]
    msg_id = data["msg_id"]
    user_id = data["user_id"]
    reply_text = update.message.text

    try:
        bot.send_message(user_id, f"📩 رد الإدارة: {reply_text}")
        update.message.reply_text(f"✅ تم إرسال الرد للمستخدم {user_id}.")
        mark_message_replied(msg_id)
    except Exception as e:
        update.message.reply_text(f"❌ فشل الإرسال: {str(e)}")

    del context.user_data["reply_to"]

# === استقبال TXID من العميل ===
def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text or ""

    if text.startswith("/"):
        return  # تجاهل الأوامر

    order = get_pending_order(str(user_id))
    if order:
        txid = text.strip()
        if len(txid) == 64 and all(c in "0123456789abcdefABCDEF" for c in txid):
            handle_payment_by_txid(update, context, user_id, txid, order[0])
        else:
            update.message.reply_text("❌ يرجى إرسال TXID صحيح (64 حرف).")
    else:
        update.message.reply_text("⚠️ ليس لديك طلب مفتوح. اكتب /buy أولًا.")

def handle_payment_by_txid(update, context, user_id, txid, order_id):
    update.message.reply_text("🔍 جاري التحقق من TXID...")

    if not verify_tron_txid(txid, WALLET_ADDRESS, MIN_AMOUNT):
        update.message.reply_text("❌ الدفع غير صحيح أو المبلغ غير كافٍ.")
        return

    if is_tx_processed(txid):
        update.message.reply_text("❌ هذا الرقم (TXID) تم استخدامه مسبقًا.")
        return

    acc = assign_account(user_id)
    if not acc:
        update.message.reply_text("❌ لا توجد حسابات متاحة حاليًا.")
        return

    update_order(order_id, "done")
    mark_tx_processed(txid)

    update.message.reply_text(PAYMENT_CONFIRMED.format(email=acc[1], password=acc[2]))

    bot.send_message(ADMIN_ID, f"✅ دفع ناجح\nالمستخدم: {user_id}\nTXID: {txid}")

# === التشغيل ===
def main():
    init_db()
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CommandHandler("myid", cmd_myid))
    dp.add_handler(CommandHandler("addaccount", cmd_addaccount))
    dp.add_handler(CommandHandler("buy", cmd_buy))
    dp.add_handler(CommandHandler("otp", cmd_otp))
    dp.add_handler(CommandHandler("message", cmd_message))
    dp.add_handler(CommandHandler("msglist", cmd_msglist))

    dp.add_handler(MessageHandler(
        Filters.text & Filters.user(user_id=int(ADMIN_ID)),
        handle_admin_reply
    ))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button_handler))

    print("✅ البوت يعمل الآن... تلقائي + دعم كامل")
    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == "__main__":
    main()