from flask import Flask
from threading import Thread
import os
from replit import web

app = Flask('')

@app.route('/')
def home():
    return 'البوت شغال! ✅'

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- هنا نبدأ التفاعل مع Replit ---
if __name__ == "__main__":
    # إذا كان المشروع على Replit، نستخدم web.run() لربط المنفذ
    if os.getenv("REPLIT_DB_URL"):
        from replit import db
    else:
        keep_alive()
        # ثم نبدأ الخادم مباشرة
        web.run(port=8080)  # ← هذا هو المفتاح!