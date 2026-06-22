print("4787858")
from flask import Flask
from threading import Thread
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

import os

TOKEN = os.getenv("BOT_TOKEN")

print("TOKEN:", repr(TOKEN))
print("LENGTH:", len(TOKEN) if TOKEN else 0)

ADMINS = [109524351, 1475934163]

db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    nickname TEXT DEFAULT '',
    blocked INTEGER DEFAULT 0
)
""")

db.commit()

def get_nickname(user_id):
    cursor.execute(
        "SELECT nickname FROM users WHERE user_id=?",
        (user_id,)
    )
    result = cursor.fetchone()

    if result and result[0]:
        return result[0]

    return "ثبت نشده"


def set_nickname(user_id, nickname):

    cursor.execute("""
    INSERT OR REPLACE INTO users(user_id,nickname,blocked)
    VALUES(
        ?,
        ?,
        COALESCE(
            (SELECT blocked FROM users WHERE user_id=?),
            0
        )
    )
    """, (user_id, nickname, user_id))

    db.commit()


def is_blocked(user_id):

    cursor.execute(
        "SELECT blocked FROM users WHERE user_id=?",
        (user_id,)
    )

    result = cursor.fetchone()

    if result:
        return result[0] == 1

    return False


def block_user_db(user_id):

    cursor.execute("""
    INSERT OR REPLACE INTO users(user_id,nickname,blocked)
    VALUES(
        ?,
        COALESCE(
            (SELECT nickname FROM users WHERE user_id=?),
            ''
        ),
        1
    )
    """, (user_id, user_id))

    db.commit()


def unblock_user_db(user_id):

    cursor.execute("""
    INSERT OR REPLACE INTO users(user_id,nickname,blocked)
    VALUES(
        ?,
        COALESCE(
            (SELECT nickname FROM users WHERE user_id=?),
            ''
        ),
        0
    )
    """, (user_id, user_id))

    db.commit()

user_map = {}        # user_id -> chat_id
nicknames = {}       # user_id -> name
blocked_users = set()

pending_action = {}  # admin_id -> {"type": ..., "user_id": ...}


# ───────── START ─────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دلام به ربات یونزونیسم خوش اومدین💗 هر حرف و پیشنهادی دارین میتونید اینجا بهمون بگید.")


# ───────── USER MESSAGE ─────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id in ADMINS:
        return

    if is_blocked(user_id):
        await update.message.reply_text("🚫 شما بلاک هستید")
        return

    user_map[user_id] = update.effective_chat.id

    first_name = update.effective_user.first_name
    nickname = get_nickname(user_id)

    username = update.effective_user.username

    caption_info = (
        f"👤 کاربر:\n"
        f"نام: {first_name}\n"
        f"اسم نمایشی: {nickname}\n"
        f"یوزرنیم: @{username if username else 'ندارد'}\n"
        f"ID: {user_id}"
    )
    user_caption = update.message.caption or ""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 پاسخ", callback_data=f"reply:{user_id}"),
            InlineKeyboardButton("🚫 بلاک", callback_data=f"block:{user_id}")
        ],
        [
            InlineKeyboardButton("✅ آنبلاک", callback_data=f"unblock:{user_id}")
        ],
        [
            InlineKeyboardButton("✏️ تغییر اسم", callback_data=f"rename:{user_id}")
        ]
    ])

    # متن
    if update.message.text:

        for admin in ADMINS:

            await context.bot.send_message(
                chat_id=admin,
                text=f"{update.message.text}",
                reply_markup=keyboard
            )

            await context.bot.send_message(
                chat_id=admin,
                text=caption_info
            )

    # عکس
    elif update.message.photo:

        photo = update.message.photo[-1].file_id

        for admin in ADMINS:

            await context.bot.send_photo(
                chat_id=admin,
                photo=photo,
                caption=f"{user_caption}",
                reply_markup=keyboard
            )

            await context.bot.send_message(
                chat_id=admin,
                text=caption_info
            )

    # ویدیو
    elif update.message.video:

        video = update.message.video.file_id

        for admin in ADMINS:

            await context.bot.send_video(
                chat_id=admin,
                video=video,
                caption=f"{user_caption}",
                reply_markup=keyboard
            )

            await context.bot.send_message(
                chat_id=admin,
                text=caption_info
            )

    # ویس
    elif update.message.voice:

        voice = update.message.voice.file_id

        for admin in ADMINS:

            await context.bot.send_voice(
                chat_id=admin,
                voice=voice,
                caption=f"{user_caption}",
                reply_markup=keyboard
            )

            await context.bot.send_message(
                chat_id=admin,
                text=caption_info
            )

    # موزیک
    elif update.message.audio:

        audio = update.message.audio.file_id

        for admin in ADMINS:

            await context.bot.send_audio(
                chat_id=admin,
                audio=audio,
                caption=f"{user_caption}",
                reply_markup=keyboard
            )

            await context.bot.send_message(
                chat_id=admin,
                text=caption_info
            )
        #استیکر
    elif update.message.sticker:

        sticker = update.message.sticker.file_id

        for admin in ADMINS:

            await context.bot.send_sticker(
                chat_id=admin,
                sticker=sticker
            )

            await context.bot.send_message(
                chat_id=admin,
                text=caption_info,
                reply_markup=keyboard
            )
    #گیف
    elif update.message.animation:

        animation = update.message.animation.file_id

        for admin in ADMINS:

            await context.bot.send_animation(
                chat_id=admin,
                animation=animation,
                caption=f"{user_caption}",
                reply_markup=keyboard
            )

            await context.bot.send_message(
                chat_id=admin,
                text=caption_info
            )
    #فایل
    elif update.message.document:

        document = update.message.document.file_id

        for admin in ADMINS:

            await context.bot.send_document(
                chat_id=admin,
                document=document,
                caption=f"{user_caption}",
                reply_markup=keyboard
            )

            await context.bot.send_message(
                chat_id=admin,
                text=caption_info
            )

    await update.message.reply_text("ارسال شد.")


# ───────── BUTTON HANDLER ─────────
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    admin_id = update.effective_user.id
    action, user_id = query.data.split(":")
    user_id = int(user_id)

    if action in ["reply", "rename"]:

        pending_action[admin_id] = {
            "type": action,
            "user_id": user_id
        }

        if action == "reply":
            await query.message.reply_text("✍️ پیام پاسخ را بنویس")

        elif action == "rename":
            await query.message.reply_text("✏️ اسم جدید را بنویس")

    elif action == "block":

        block_user_db(user_id)
        await query.message.reply_text("🚫 کاربر بلاک شد")

    elif action == "unblock":

        unblock_user_db(user_id)
        await query.message.reply_text("✅ کاربر آنبلاک شد")


# ───────── ADMIN TEXT INPUT (AFTER BUTTON) ─────────
async def admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):

    admin_id = update.effective_user.id

    if admin_id not in ADMINS:
        return

    if admin_id not in pending_action:
        return

    action_data = pending_action[admin_id]
    user_id = action_data["user_id"]
    action_type = action_data["type"]

    chat_id = user_map.get(user_id)

    if chat_id is None:
        await update.message.reply_text("❌ کاربر پیدا نشد")
        return

    text = update.message.text

    if action_type == "reply":

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✉️ پاسخ ادمین:\n\n{text}"
        )

        await update.message.reply_text("✅ ارسال شد")


    elif action_type == "rename":

        set_nickname(user_id, text)
        await update.message.reply_text("✅ اسم تغییر کرد")


    del pending_action[admin_id]


# ───────── UNBLOCK ─────────
async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS:
        return

    try:
        user_id = int(context.args[0])
        unblock_user_db(user_id)
        await update.message.reply_text("✅ آنبلاک شد")
    except:
        await update.message.reply_text("/unblock USER_ID")


async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # ───── ادمین‌ها ─────
    if user_id in ADMINS:

        # اگر منتظر input بعد از دکمه هست
        if user_id in pending_action:
            await admin_input(update, context)
        return

    # ───── کاربران ─────
    await handle_message(update, context)



# ───────── APP ─────────
print("TOKEN =", repr(TOKEN))
print("LEN =", len(TOKEN))
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("unblock", unblock_user))

app.add_handler(CallbackQueryHandler(button_click))

app.add_handler(MessageHandler(filters.ALL, handle_all))

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is alive"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

Thread(target=run_web, daemon=True).start()

app.run_polling()
