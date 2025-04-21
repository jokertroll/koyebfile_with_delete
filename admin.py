import os
import asyncio
import humanize
import random
import string
import requests
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pymongo import MongoClient
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
# from database.database import  premium_users
from bot import Bot
from config import *
from helper_func import subscribed, encode, decode, get_messages

client = MongoClient(DB_URI)
db = client[DB_NAME]
premium_users = db.premium_users

def generate_token(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

SHORTENER_API_KEY = "975c875296c32a908bf5a41a2f10bee9db27fd80"
SHORTENER_API_URL = "https://softurl.in/api"

@Bot.on_message(filters.command("tryPremium") & filters.private)
async def try_premium(client, message):
    user_id = message.from_user.id
    existing_trial = premium_users.find_one({"user_id": user_id, "trial_used": True})
    if existing_trial:
        return await message.reply("❌ You have already used the free trial!")

    trial_token = generate_token()
    expiry_time = datetime.utcnow() + timedelta(hours=3)
    premium_users.update_one(
        {"user_id": user_id},
        {"$set": {"trial_token": trial_token, "expiry_date": expiry_time, "trial_used": False}},
        upsert=True
    )

    bot_username = (await client.get_me()).username
    long_url = f"https://t.me/{bot_username}?start=trial-{trial_token}"

    # **Shorten the URL**
    try:
        response = requests.get(f"{SHORTENER_API_URL}?api={SHORTENER_API_KEY}&url={long_url}")
        if response.status_code == 200:
            short_url = response.json().get("shortenedUrl", long_url)
        else:
            short_url = long_url  # Fallback if the shortener fails
    except:
        short_url = long_url  # Fallback in case of an error

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔗 Activate Trial", url=short_url)]]
    )

    await message.reply(
        "🎉 Click the button below to activate your 3-hour Premium trial!",
        reply_markup=keyboard
    )

    # **Notify Admins AFTER user receives the message**
    for admin in ADMINS:
        try:
            await client.send_message(admin, f"📢 User {message.from_user.mention} ({user_id}) has started a premium trial!\n🔗 Trial Link: {short_url}")
        except:
            pass

# @Bot.on_message(filters.command("tryPremium") & filters.private)
# async def try_premium(client, message):
#     user_id = message.from_user.id

#     # Check if the user has already used 3 trials
#     user_data = premium_users.find_one({"user_id": user_id})
#     trial_count = user_data.get("trial_count", 0) if user_data else 0

#     if trial_count >= 3:
#         return await message.reply("❌ You have already used all 3 free trials!")

#     # Generate a unique trial token
#     trial_token = generate_token()
    
#     # Store the token in the database with expiry
#     expiry_time = datetime.utcnow() + timedelta(hours=3)
#     premium_users.update_one(
#         {"user_id": user_id},
#         {"$set": {"trial_token": trial_token, "expiry_date": expiry_time},
#          "$inc": {"trial_count": 1}},  # Increment the trial count by 1
#         upsert=True
#     )
    
#     bot_username = (await client.get_me()).username
#     long_url = f"https://telegram.me/{bot_username}?start=trial-{trial_token}"

#     # Shorten the URL
#     response = requests.get(f"{SHORTENER_API_URL}?api={SHORTENER_API_KEY}&url={long_url}")
#     if response.status_code == 200:
#         short_url = response.json().get("shortenedUrl", long_url)
#     else:
#         short_url = long_url  # Fallback if shortener fails

#     # Send message with a button containing the short link
#     keyboard = InlineKeyboardMarkup(
#         [[InlineKeyboardButton("🔗 Activate Trial", url=short_url)]]
#     )

#     await message.reply(
#         f"🎉 You have used {trial_count}/3 trials.\n"
#         "Click the button below to activate your <b>3-hour Premium trial</b>!\n\n"
#         "Once activated, you will receive confirmation automatically.",
#         reply_markup=keyboard
#     )
#     # await message.reply(
#     #     f"🎉 Click this link to activate your 3-hour Premium trial:\n🔗 {start_link}\n\nOnce activated, you will receive confirmation automatically!"
#     # )
    
#     for admin in ADMINS:
#         try:
#             await client.send_message(admin, f"📢 User {message.from_user.mention} ({user_id}) has started a premium trial!")
#         except:
#             pass

@Bot.on_message(filters.command("resetTrial") & filters.user(ADMINS))
async def reset_trial(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /resetTrial <user_id>")
    
    user_id = int(message.command[1])
    premium_users.update_one({"user_id": user_id}, {"$set": {"trial_used": False}})
    await message.reply(f"✅ Trial count reset for user {user_id}")

@Bot.on_message(filters.command("trackPromo") & filters.user(ADMINS))
async def track_promo(client, message):
    promo_codes = premium_users.find({}, {"promo_code": 1, "redeemed_by": 1})
    
    report = "📊 Promo Code Usage:\n"
    found = False
    
    for promo in promo_codes:  # Regular loop (not async for)
        promo_code = promo.get("promo_code", "Unknown")
        redeemed_by = promo.get("redeemed_by", [])
        
        report += f"🔹 {promo_code} - Redeemed {len(redeemed_by)} times\n"
        found = True

    if not found:
        report += "No promo codes found."

    await message.reply(report)


