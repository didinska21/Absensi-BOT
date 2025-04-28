import os
import pytz
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    filters, ConversationHandler, CallbackContext
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WIB = pytz.timezone("Asia/Jakarta")
DB_FILE = "absensi.db"

CHOOSING, ADDING, DELETING, CEK_IN, BATAL_CEK_IN = range(5)

def get_today():
    return datetime.now(WIB).strftime('%Y-%m-%d')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS airdrops (name TEXT PRIMARY KEY)")
    c.execute("""
        CREATE TABLE IF NOT EXISTS login_status (
            name TEXT,
            date TEXT,
            PRIMARY KEY (name, date)
        )
    """)
    conn.commit()
    conn.close()

def get_airdrops():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM airdrops ORDER BY name")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def add_airdrop(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO airdrops (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def delete_airdrop(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM airdrops WHERE name=?", (name,))
    c.execute("DELETE FROM login_status WHERE name=?", (name,))
    conn.commit()
    conn.close()

def get_status(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT date FROM login_status WHERE name=?", (name,))
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def update_checkin(name, date):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO login_status (name, date) VALUES (?, ?)", (name, date))
    conn.commit()
    conn.close()

def delete_checkin(name, date):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM login_status WHERE name=? AND date=?", (name, date))
    conn.commit()
    conn.close()

main_menu = ReplyKeyboardMarkup(
    [
        ["➕ Tambah Garapan", "❌ Hapus Garapan"],
        ["📋 Daftar Garapan", "📈 Statistik Mingguan"],
        ["✅ Cek-in Harian", "⏰ Atur Reminder"]
    ], resize_keyboard=True
)

reminder_menu = ReplyKeyboardMarkup(
    [
        ["⏳ 6 Jam", "⏳ 8 Jam"],
        ["⏳ 12 Jam", "⏳ 24 Jam"],
        ["⛔️ Matikan Reminder", "⬅️ Kembali"]
    ], resize_keyboard=True
)

cek_in_menu = ReplyKeyboardMarkup(
    [["✅ Cek-in Hari Ini", "❌ Batalkan Cek-in"], ["⬅️ Kembali"]], resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Selamat datang di Bot Cek-in Airdrop!", reply_markup=main_menu
    )
    return CHOOSING

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "➕ Tambah Garapan":
        await update.message.reply_text("Kirim nama garapan yang ingin ditambahkan:", reply_markup=ReplyKeyboardRemove())
        return ADDING
    elif text == "❌ Hapus Garapan":
        await update.message.reply_text("Kirim nama garapan yang ingin dihapus:", reply_markup=ReplyKeyboardRemove())
        return DELETING
    elif text == "📋 Daftar Garapan":
        return await list_airdrop(update, context)
    elif text == "📈 Statistik Mingguan":
        return await statistik(update, context)
    elif text == "⏰ Atur Reminder":
        await update.message.reply_text("Pilih interval reminder:", reply_markup=reminder_menu)
        return CHOOSING
    elif text == "⏳ 6 Jam":
        return await mulai_reminder_interval(update, context, 6)
    elif text == "⏳ 8 Jam":
        return await mulai_reminder_interval(update, context, 8)
    elif text == "⏳ 12 Jam":
        return await mulai_reminder_interval(update, context, 12)
    elif text == "⏳ 24 Jam":
        return await mulai_reminder_interval(update, context, 24)
    elif text == "⛔️ Matikan Reminder":
        return await berhenti_reminder(update, context)
    elif text == "✅ Cek-in Harian":
        await update.message.reply_text("Pilih menu cek-in:", reply_markup=cek_in_menu)
        return CHOOSING
    elif text == "✅ Cek-in Hari Ini":
        return await pilih_airdrop_cek_in(update, context)
    elif text == "❌ Batalkan Cek-in":
        return await pilih_airdrop_batal_cek_in(update, context)
    elif text == "⬅️ Kembali":
        await update.message.reply_text("🔙 Kembali ke menu utama.", reply_markup=main_menu)
        return CHOOSING

async def handle_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip().upper()
    if name:
        add_airdrop(name)
        await update.message.reply_text(f"✅ Garapan <b>{name}</b> berhasil ditambahkan.", reply_markup=main_menu, parse_mode="HTML")
    return CHOOSING

async def handle_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip().upper()
    airdrops = get_airdrops()
    if name in airdrops:
        delete_airdrop(name)
        await update.message.reply_text(f"🗑️ Garapan <b>{name}</b> berhasil dihapus.", reply_markup=main_menu, parse_mode="HTML")
    else:
        await update.message.reply_text(f"⚠️ Garapan <b>{name}</b> tidak ditemukan.", reply_markup=main_menu, parse_mode="HTML")
    return CHOOSING

async def pilih_airdrop_cek_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton(name)] for name in get_airdrops()]
    await update.message.reply_text("✅ Pilih garapan untuk cek-in:", reply_markup=ReplyKeyboardMarkup(buttons + [["⬅️ Kembali"]], resize_keyboard=True))
    return CEK_IN

async def pilih_airdrop_batal_cek_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton(name)] for name in get_airdrops()]
    await update.message.reply_text("❌ Pilih garapan untuk membatalkan cek-in:", reply_markup=ReplyKeyboardMarkup(buttons + [["⬅️ Kembali"]], resize_keyboard=True))
    return BATAL_CEK_IN

async def handle_cek_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip().upper()
    if name in get_airdrops():
        update_checkin(name, get_today())
        await update.message.reply_text(f"✅ Garapan <b>{name}</b> berhasil dicatat cek-in hari ini.", reply_markup=main_menu, parse_mode="HTML")
    return CHOOSING

async def handle_batal_cek_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip().upper()
    if name in get_airdrops():
        delete_checkin(name, get_today())
        await update.message.reply_text(f"❌ Cek-in untuk <b>{name}</b> berhasil dibatalkan.", reply_markup=main_menu, parse_mode="HTML")
    return CHOOSING

async def list_airdrop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    airdrops = get_airdrops()
    date = get_today()
    if not airdrops:
        await update.message.reply_text("⚠️ Belum ada garapan.", reply_markup=main_menu)
        return CHOOSING
    text = "📋 <b>Daftar Garapan Hari Ini</b>\n\n"
    for i, name in enumerate(airdrops, start=1):
        history = get_status(name)
        if date in history:
            text += f"{i}. <b>{name}</b> - ✅ ({len(history)} hari)\n"
        else:
            text += f"{i}. <b>{name}</b> - ❌ ({len(history)} hari)\n"
    await update.message.reply_text(text.strip(), reply_markup=main_menu, parse_mode="HTML")
    return CHOOSING

async def statistik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    airdrops = get_airdrops()
    if not airdrops:
        await update.message.reply_text("⚠️ Belum ada garapan untuk statistik.", reply_markup=main_menu)
        return CHOOSING
    now = datetime.now(WIB)
    days = [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    text = f"📈 <b>Statistik Mingguan</b>\n🗓️ Periode: {days[0]} - {days[-1]}\n\n"
    for name in airdrops:
        history = get_status(name)
        icons = ['✅' if d in history else '❌' for d in days]
        total = icons.count("✅")
        text += f"<b>{name}</b>: {''.join(icons)} ({total}/7 hari)\n"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_menu)
    return CHOOSING

async def kirim_reminder(context: CallbackContext):
    chat_id = context.job.data["chat_id"]
    airdrops = get_airdrops()
    date = get_today()
    if not airdrops:
        await context.bot.send_message(chat_id, "⚠️ Belum ada garapan.")
        return
    text = "⏰ <b>Reminder Cek-in Hari Ini</b>\n\n"
    for i, name in enumerate(airdrops, start=1):
        history = get_status(name)
        status = "✅" if date in history else "❌"
        text += f"{i}. <b>{name}</b> - {status} ({len(history)} hari)\n"
    await context.bot.send_message(chat_id, text, parse_mode="HTML")

async def mulai_reminder_interval(update: Update, context: ContextTypes.DEFAULT_TYPE, interval_jam: int = 0):
    chat_id = update.effective_chat.id
    job = context.chat_data.get("reminder_job")
    if job:
        job.schedule_removal()
    interval = interval_jam * 60 * 60
    new_job = context.job_queue.run_repeating(
        kirim_reminder,
        interval=interval,
        first=5,
        data={"chat_id": chat_id},
        name=str(chat_id)
    )
    context.chat_data["reminder_job"] = new_job
    await update.message.reply_text(f"⏰ Reminder dimulai setiap {interval_jam} jam.", reply_markup=reminder_menu)
    return CHOOSING

async def berhenti_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job = context.chat_data.pop("reminder_job", None)
    if job:
        job.schedule_removal()
        await update.message.reply_text("✅ Reminder dihentikan.", reply_markup=reminder_menu)
    else:
        await update.message.reply_text("⚠️ Tidak ada reminder aktif.", reply_markup=reminder_menu)
    return CHOOSING

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            ADDING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add)],
            DELETING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete)],
            CEK_IN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cek_in)],
            BATAL_CEK_IN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batal_cek_in)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    print("Bot aktif...")
    app.run_polling()
