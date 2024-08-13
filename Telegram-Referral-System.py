#!/usr/bin/env python
# pylint: disable=unused-argument

import os
import logging
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ChatMember, helpers
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants from environment variables
ADMINS = os.getenv("ADMINS", "").split(",")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GROUP_ID = os.getenv("GROUP_ID")
CHANNEL_URL = os.getenv("CHANNEL_URL")
GROUP_URL = os.getenv("GROUP_URL")
SOCIAL_LINK_1 = os.getenv("SOCIAL_LINK_1")
SOCIAL_LINK_2 = os.getenv("SOCIAL_LINK_2")
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_data.db")

# Logging configuration
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

# Define states for the bot
ADDING_WALLET, VERIFYING_MEMBERSHIP = map(chr, range(2))

# Database initialization
def create_database():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                wallet_address TEXT,
                points INTEGER DEFAULT 0,
                joined_channel INTEGER DEFAULT 0,
                joined_group INTEGER DEFAULT 0,
                referral_link TEXT
            )
        ''')

def add_user(user_id, username):
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))

def update_wallet(user_id, wallet_address):
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("UPDATE users SET wallet_address = ? WHERE user_id = ?", (wallet_address, user_id))

def update_user_membership_status(user_id, joined_channel, joined_group):
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("UPDATE users SET joined_channel = ?, joined_group = ? WHERE user_id = ?", (joined_channel, joined_group, user_id))

def update_points(user_id, points):
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))

def get_user_data(user_id):
    with sqlite3.connect(DATABASE_PATH) as conn:
        return conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

def get_top_users():
    with sqlite3.connect(DATABASE_PATH) as conn:
        return conn.execute("SELECT user_id, username, points, wallet_address FROM users ORDER BY points DESC LIMIT 10").fetchall()

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    add_user(user.id, user.username)

    user_data = get_user_data(user.id)
    args = context.args

    if args and args[0].startswith('referral-'):
        referrer_id = args[0].split('-')[1]
        if referrer_id.isdigit() and int(referrer_id) != user.id:
            context.user_data["referred_by"] = referrer_id
            await update.message.reply_text("Thanks for joining through a referral!")
        else:
            await update.message.reply_text("Invalid referral link.")

    keyboard = [
        [InlineKeyboardButton("Join Channel", callback_data='join_channel')],
        [InlineKeyboardButton("Join Group", callback_data='join_group')],
        [InlineKeyboardButton("Submit Wallet Address", callback_data='submit_wallet')],
        [InlineKeyboardButton("View Points", callback_data='view_points')]
    ]

    if user_data and user_data[3]:  # Assuming wallet_address is at index 3
        keyboard.append([InlineKeyboardButton("Show Referral Link", callback_data='show_referral_link')])
    else:
        keyboard.append([InlineKeyboardButton("Referral Link", callback_data='referral_link_not_available')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Please follow the steps below:", reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = None

    if query.data == 'join_channel':
        await query.message.reply_text(
            f"Please join our channel: [Channel]({CHANNEL_URL}) and follow us on [Social Platform 1]({SOCIAL_LINK_1})",
            parse_mode='Markdown'
        )
    elif query.data == 'join_group':
        await query.message.reply_text(
            f"Please join our group: [Group]({GROUP_URL}) and follow us on [Social Platform 2]({SOCIAL_LINK_2})",
            parse_mode='Markdown'
        )
    elif query.data == 'submit_wallet':
        context.user_data[ADDING_WALLET] = True
        await query.message.reply_text("Please enter your wallet address:")
    elif query.data in ['view_points', 'show_referral_link']:
        user_data = get_user_data(user_id)

    if query.data == 'view_points':
        points = user_data[3] if user_data else 'N/A'  # points are at index 3
        await query.message.reply_text(f"Your points: {points}")
    elif query.data == 'show_referral_link':
        if user_data and user_data[6]:  # referral_link is at index 6
            await query.message.reply_text(f"Your referral link: {user_data[6]}")
        else:
            await query.message.reply_text("Referral link not yet available. Please complete all steps.")

async def handle_wallet_address(update: Update, context: CallbackContext) -> None:
    if context.user_data.get(ADDING_WALLET):
        wallet_address = update.message.text
        update_wallet(update.effective_user.id, wallet_address)
        await update.message.reply_text("Wallet address updated.")
        
        membership_verified = await verify_membership(context.bot, update.effective_user.id)
        if membership_verified:
            update_user_membership_status(update.effective_user.id, 1, 1)
            referral_link = generate_referral_link(context.bot.username, update.effective_user.id)

            if "referred_by" in context.user_data:
                update_points(context.user_data["referred_by"], 1)
                del context.user_data["referred_by"]

            await update.message.reply_text(f"Your referral link: {referral_link}")
        else:
            await update.message.reply_text("You need to join the channel and group before proceeding.")
        context.user_data[ADDING_WALLET] = False

async def verify_membership(bot, user_id):
    try:
        channel_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        group_member = await bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)

        is_member_channel = channel_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        is_member_group = group_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]

        return is_member_channel and is_member_group
    except Exception as e:
        logger.error(f"Failed to get membership status for user {user_id}: {e}")
        return False

def generate_referral_link(bot_username, user_id):
    referral_link = helpers.create_deep_linked_url(bot_username, f"referral-{user_id}")
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("UPDATE users SET referral_link = ? WHERE user_id = ?", (referral_link, user_id))

    return referral_link

async def admin_start(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) in ADMINS:
        top_users = get_top_users()
        message = "Top 10 Users:\n"
        for user in top_users:
            message += f"User ID: {user[0]}, @{user[1]}, Points: {user[2]}, Wallet: <code>{user[3]}</code>\n"
        await update.message.reply_text(message, parse_mode='HTML')
    else:
        await update.message.reply_text("You are not authorized.")

def main():
    create_database()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.Regex('^Join Channel$'), join_channel))
    application.add_handler(MessageHandler(filters.Regex('^Join Group$'), join_group))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_address))
    application.add_handler(CommandHandler("admin", admin_start))

    application.run_polling()

if __name__ == "__main__":
    main()
