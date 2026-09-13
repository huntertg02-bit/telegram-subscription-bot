
import os
import sqlite3
import logging
from datetime import datetime, timedelta, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Put your Telegram channel/group IDs or @usernames here.
GROUPS = {
    "vip": {"name": "📌 VIP stock", "chat_id": os.getenv("VIP_CHAT_ID", "")},
    "tango": {"name": "📌 Tango exclusive 💕", "chat_id": os.getenv("TANGO_CHAT_ID", "")},
    "snap": {"name": "📌 Snap Video", "chat_id": os.getenv("SNAP_CHAT_ID", "")},
    "vilayati": {"name": "📌 Vilayati Mal 😉", "chat_id": os.getenv("VILAYATI_CHAT_ID", "")},
}

PLANS = {
    "vip": [
        ("VIP Stock — ₹10.0 / 1 din", 10, 1),
        ("VIP Stock — ₹30.0 / 7 din", 30, 7),
        ("VIP Stock — ₹100.0 / 30 din", 100, 30),
        ("VIP Stock — ₹300.0 / 999 din", 300, 999),
    ]
}

DB = "bot.db"
logging.basicConfig(level=logging.INFO)

def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        group_key TEXT NOT NULL,
        plan_name TEXT NOT NULL,
        amount REAL NOT NULL,
        days INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL
    )""")
    con.commit()
    return con

def add_order(user_id, group_key, plan_name, amount, days):
    con = db()
    cur = con.execute(
        "INSERT INTO orders(user_id,group_key,plan_name,amount,days,status,created_at) VALUES(?,?,?,?,?,?,?)",
        (user_id, group_key, plan_name, amount, days, "pending", datetime.now(timezone.utc).isoformat())
    )
    con.commit()
    oid = cur.lastrowid
    con.close()
    return oid

def get_order(oid):
    con = db()
    row = con.execute("SELECT id,user_id,group_key,plan_name,amount,days,status FROM orders WHERE id=?", (oid,)).fetchone()
    con.close()
    return row

def set_status(oid, status):
    con = db()
    con.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
    con.commit()
    con.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Namaste! 👋\n\n"
        "Subscription lene ke liye neeche 🧾 Buy Subscription button dabayein "
        "(ya /buy bhi likh sakte hain).\n\n"
        "Kisi bhi group me join karne ke liye pehle subscription lena zaroori hai.\n\n"
        "📌 Available Commands:\n"
        "/start - Bot start karein\n"
        "/buy - Subscription lein\n"
        "/help - Madad lein"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🧾 Buy Subscription", callback_data="buy")]])
    await update.message.reply_text(text, reply_markup=kb)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🧾 Group chuniye:\n\nJis group me join karna hai, usko select karein."
    kb = [
        [InlineKeyboardButton(GROUPS["vip"]["name"], callback_data="group:vip")],
        [InlineKeyboardButton(GROUPS["tango"]["name"], callback_data="group:tango")],
        [InlineKeyboardButton(GROUPS["snap"]["name"], callback_data="group:snap")],
        [InlineKeyboardButton(GROUPS["vilayati"]["name"], callback_data="group:vilayati")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def show_vip_plans(query):
    kb = []
    for i, (name, amount, days) in enumerate(PLANS["vip"]):
        kb.append([InlineKeyboardButton(f"📅 {name}", callback_data=f"plan:vip:{i}")])
    kb.append([InlineKeyboardButton("⬅️ Wapas", callback_data="buy")])
    await query.edit_message_text(
        "📌 VIP stock\n\nApna plan chuniye:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def payment_screen(query, context, group_key, plan_index):
    plan_name, amount, days = PLANS[group_key][plan_index]
    oid = add_order(query.from_user.id, group_key, plan_name, amount, days)
    context.user_data["last_order"] = oid

    qr_path = os.path.join(os.path.dirname(__file__), "qr.png")
    caption = (
        "✅ QR code neeche bhej diya gaya.\n\n"
        f"💳 ₹{amount:.1f} — {plan_name}\n\n"
        f"📌 Group: {GROUPS[group_key]['name'].replace('📌 ', '')}\n\n"
        "QR code scan karein aur payment karein.\n"
        "Payment ke baad neeche ✅ Paid — Check Payment button dabayein.\n\n"
        "⏳ Payment verify hone ke baad aapko join link mil jayega."
    )
    kb = [[InlineKeyboardButton("✅ Paid — Check Payment", callback_data=f"check:{oid}")]]
    if os.path.exists(qr_path):
        await query.message.reply_photo(
            photo=open(qr_path, "rb"),
            caption=caption,
            reply_markup=InlineKeyboardMarkup(kb)
        )
        await query.delete_message()
    else:
        await query.edit_message_text(
            caption + "\n\n⚠️ Admin ne abhi qr.png add nahi kiya hai.",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "buy":
        text = "🧾 Group chuniye:\n\nJis group me join karna hai, usko select karein."
        kb = [
            [InlineKeyboardButton(GROUPS["vip"]["name"], callback_data="group:vip")],
            [InlineKeyboardButton(GROUPS["tango"]["name"], callback_data="group:tango")],
            [InlineKeyboardButton(GROUPS["snap"]["name"], callback_data="group:snap")],
            [InlineKeyboardButton(GROUPS["vilayati"]["name"], callback_data="group:vilayati")],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("group:"):
        group_key = data.split(":")[1]
        if group_key == "vip":
            await show_vip_plans(query)
        else:
            await query.edit_message_text(
                f"{GROUPS[group_key]['name']}\n\n"
                "Plans is group ke liye baad me config kiye ja sakte hain.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Wapas", callback_data="buy")]]
                )
            )
        return

    if data.startswith("plan:"):
        _, group_key, idx = data.split(":")
        await payment_screen(query, context, group_key, int(idx))
        return

    if data.startswith("check:"):
        oid = int(data.split(":")[1])
        row = get_order(oid)
        if not row or row[1] != query.from_user.id:
            await query.message.reply_text("❌ Order nahi mila.")
            return
        if row[6] == "approved":
            await send_join_link(query.message, row)
        elif row[6] == "pending":
            await query.message.reply_text(
                "❌ Payment nahi mili.\n\n"
                "Kuch der baad dobara try karein.\n"
                "Agar payment kar diya hai toh thoda wait karein aur dobara button dabayein."
            )
            if ADMIN_ID:
                await context.bot.send_message(
                    ADMIN_ID,
                    f"🔔 Payment check requested\nOrder: #{oid}\nUser: {row[1]}\n"
                    f"Plan: {row[3]}\nAmount: ₹{row[4]}"
                )
        else:
            await query.message.reply_text("❌ Is order ka status available nahi hai.")
        return

async def send_join_link(message, row):
    _, user_id, group_key, plan_name, amount, days, status = row
    chat_id = GROUPS[group_key]["chat_id"]
    if not chat_id:
        await message.reply_text("✅ Payment verified.\n⚠️ Admin ne group/channel ID set nahi ki.")
        return

    try:
        link = await message.get_bot().create_chat_invite_link(
            chat_id=chat_id,
            name=f"Order-{row[0]}",
            member_limit=1
        )
        await message.reply_text(
            f"🎉 Payment verified!\n\n"
            f"💳 {plan_name}\n\n"
            f"🔗 Join link:\n{link.invite_link}"
        )
    except Exception as e:
        logging.exception(e)
        await message.reply_text(
            "✅ Payment verified!\n"
            "Lekin join link generate nahi ho saka. Admin se contact karein."
        )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Use: /approve ORDER_ID")
        return
    oid = int(context.args[0])
    row = get_order(oid)
    if not row:
        await update.message.reply_text("Order nahi mila.")
        return
    set_status(oid, "approved")
    await update.message.reply_text(f"✅ Order #{oid} approved.")
    try:
        user = await context.bot.get_chat(row[1])
        await context.bot.send_message(
            row[1],
            "🎉 Payment verified!\n\nAapka join link generate ho raha hai..."
        )
        # create link using a temporary message-like object is awkward;
        # directly call Telegram API through bot:
        chat_id = GROUPS[row[2]]["chat_id"]
        link = await context.bot.create_chat_invite_link(
            chat_id=chat_id, name=f"Order-{oid}", member_limit=1
        )
        await context.bot.send_message(
            row[1],
            f"🔗 Join link:\n{link.invite_link}"
        )
    except Exception as e:
        logging.exception(e)
        await update.message.reply_text("User ko link bhejne me error hua. Check group ID/admin rights.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n/start\n/buy\n/help\n\n"
        "Payment ke baad bot me 'Paid — Check Payment' dabayein."
    )

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable missing")
    db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
