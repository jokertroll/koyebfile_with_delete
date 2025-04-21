# premium.py - Handles all premium user-related functionality
import os
import yt_dlp
import requests
from datetime import datetime, timedelta
from config import ADMINS, DB_URI, DB_NAME
from pymongo import MongoClient
from pyrogram import Client, filters
import pytz
import random
import string
import base64
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Connect to MongoDB
client = MongoClient(DB_URI)
db = client[DB_NAME]
premium_users = db.premium_users

def grant_temporary_premium(user_id, hours=3):
    """Grants a temporary premium membership for a given number of hours."""
    expiry_time = datetime.utcnow() + timedelta(hours=hours)

    premium_users.update_one(
        {"user_id": user_id},
        {"$set": {"expiry_date": expiry_time}},
        upsert=True
    )

    print(f"✅ Granted {hours} hours of temporary premium to user {user_id}")

# ✅ Add Premium User
async def add_premium(client, message):
    args = message.text.split()
    if len(args) != 3:
        return await message.reply("Usage: /addpremium <user_id> <days>")

    try:
        user_id = int(args[1])
        days = int(args[2])
    except ValueError:
        return await message.reply("Invalid input. User ID and days must be numbers.")

    expiry_date = datetime.utcnow() + timedelta(days=days)

    premium_users.update_one(
        {"user_id": user_id},
        {"$set": {"expiry_date": expiry_date}},
        upsert=True
    )

    await message.reply(f"✅ Premium activated for {user_id} until {expiry_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    try:
        await client.send_message(user_id, "🎉<b> You are now a premium user!</b>\n Enjoy your benefits. 💎")
    except Exception as e:
        print(f"Error sending message to user {user_id}: {e}")

# ✅ Check if a user is premium
def is_premium(user_id):
    user = premium_users.find_one({"user_id": user_id})
    if user and "expiry_date" in user:
        expiry_date = user["expiry_date"]

        # Convert expiry_date to datetime if needed
        if isinstance(expiry_date, str):
            expiry_date = datetime.fromisoformat(expiry_date)

        return expiry_date > datetime.utcnow()
    return False

# ✅ Extend Premium Duration
async def extend_premium(client, message):
    args = message.text.split()
    if len(args) != 3:
        return await message.reply("Usage: /extendpremium <user_id> <days>")

    try:
        user_id = int(args[1])
        days = int(args[2])
    except ValueError:
        return await message.reply("Invalid input. User ID and days must be numbers.")

    user = premium_users.find_one({"user_id": user_id})

    if user and "expiry_date" in user:
        new_expiry = user["expiry_date"] + timedelta(days=days)
    else:
        new_expiry = datetime.utcnow() + timedelta(days=days)

    premium_users.update_one(
        {"user_id": user_id},
        {"$set": {"expiry_date": new_expiry}},
        upsert=True
    )

    await message.reply(f"✅ Premium extended for {user_id} until <b>{new_expiry.strftime('%Y-%m-%d %H:%M:%S UTC')} </b>")

# # ✅ Check User's Premium Status
async def my_premium(client, message):
    user_id = message.from_user.id
    user = premium_users.find_one({"user_id": user_id})

    if user and "expiry_date" in user:
        expiry_date = user["expiry_date"]
        if isinstance(expiry_date, str):
            expiry_date = datetime.fromisoformat(expiry_date)

        # Check if premium has expired
        if expiry_date < datetime.utcnow():
            # Remove premium status
            premium_users.update_one({"user_id": user_id}, {"$unset": {"is_premium": 1, "expiry_date": 1}})
            return await message.reply("<b>❌ Your premium has expired. Upgrade to regain access!</b>")

        # Convert to IST
        ist = pytz.timezone("Asia/Kolkata")
        expiry_date_ist = expiry_date.replace(tzinfo=pytz.utc).astimezone(ist)

        # Format: April 23, 2025 11:34PM IST
        formatted_date = expiry_date_ist.strftime("%B %d, %Y %I:%M%p")

        await message.reply(f"🛡️ <b>Your premium status:</b>\n Active until {formatted_date} IST")
    else:
        await message.reply("❌ You are not a premium user.") 

# async def my_premium(client, message):
#     user_id = message.from_user.id
#     user = premium_users.find_one({"user_id": user_id})

#     if user and "expiry_date" in user:
#         expiry_date = user["expiry_date"]
#         if isinstance(expiry_date, str):
#             expiry_date = datetime.fromisoformat(expiry_date)

#         # Convert to IST
#         ist = pytz.timezone("Asia/Kolkata")
#         expiry_date_ist = expiry_date.replace(tzinfo=pytz.utc).astimezone(ist)

#         # Format: 13 May 2025 11:30PM IST
#         formatted_date = expiry_date_ist.strftime("%d %b %Y %I:%M%p IST")

#         await message.reply(f"🛡️ <b>Your premium status:</b> Active until {formatted_date}")
#     else:
#         await message.reply("❌ You are not a premium user.")


# ✅ Remove Expired Premium Users
async def clean_expired_premium():
    now = datetime.utcnow()
    expired_users = premium_users.find({"expiry_date": {"$lt": now}})
    for user in expired_users:
        premium_users.delete_one({"user_id": user["user_id"]})

# ✅ List Premium Users
async def list_premium_users(client, message):
    users = premium_users.find()
    if premium_users.count_documents({}) == 0:
        return await message.reply("No active premium users.")
    
    msg = "📜 **List of Premium Users:**\n"
    for user in users:
        expiry_date = user["expiry_date"]
        if isinstance(expiry_date, str):
            expiry_date = datetime.fromisoformat(expiry_date)
        msg += f"👤 User ID: `{user['user_id']}` - Expiry: `{expiry_date.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n"

    await message.reply(msg)

# ✅ Revoke Premium Access (Admin Only)
async def revoke_premium(client, message):
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /revoke_premium <user_id>")

    try:
        user_id = int(args[1])
    except ValueError:
        return await message.reply("Invalid input. User ID must be a number.")

    if not premium_users.find_one({"user_id": user_id}):
        return await message.reply("⚠️ User is not a premium member.")

    premium_users.delete_one({"user_id": user_id})
    await message.reply(f"🚫 <b>User {user_id} has been removed from Premium.</b>")

async def notify_expiring_premium(client):
    now = datetime.utcnow()
    for days_left in [3, 2, 1]:
        expiry_threshold = now + timedelta(days=days_left)
        expiring_users = premium_users.find({
            "expiry_date": {"$gte": expiry_threshold, "$lt": expiry_threshold + timedelta(days=1)}
        })
        
        for user in expiring_users:
            user_id = user["user_id"]
            message_text = f"⚠️ Reminder: Your Premium subscription expires in {days_left} day(s)! Renew now to continue enjoying benefits. 💎"
            try:
                await client.send_message(user_id, message_text)
            except Exception as e:
                print(f"Failed to notify user {user_id}: {e}")

# Shortener API details
SHORTENER_API_KEY = "bfc37716230e4c6d60d4554f978dda390ba33670"
SHORTENER_API_URL = "https://shortxlinks.com/api"

@Client.on_message(filters.command("music") & filters.private)
async def download_music(client, message):
    user_id = message.from_user.id
    
    if not is_premium(user_id):
        return await message.reply("❌ This feature is only available for Premium users. Upgrade now! Or try premium with /tryPremium")
    
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /music <YouTube URL>")
    
    url = args[1]
    await message.reply("🎵 Downloading audio, please wait...")
    
    os.makedirs("downloads", exist_ok=True)  # Ensure downloads directory exists
    
    ydl_opts = {
        'format': 'bestaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(id)s',  # Use video ID to keep filenames simple
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = os.path.join("downloads", f"{info['id']}.mp3")  # Get correct filename
        
        await message.reply_audio(file_path, caption=f"🎶 {info['title']}")
        os.remove(file_path)  # Clean up downloaded file
    except Exception as e:
        await message.reply(f"❌ Error downloading audio: {e}")

def generate_token(length=8):
    """Generate a unique 8-character trial token."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# @Client.on_message(filters.command("tryPremium") & filters.private)
# async def try_premium(client, message):
#     user_id = message.from_user.id

#     # Check if the user has already used a trial
#     existing_trial = premium_users.find_one({"user_id": user_id, "trial_used": True})
#     if existing_trial:
#         return await message.reply("❌ You have already used the free trial!")

#     # Generate a unique trial token
#     trial_token = generate_token()
    
#     # Store the token in the database with expiry
#     expiry_time = datetime.utcnow() + timedelta(hours=3)
#     premium_users.update_one(
#         {"user_id": user_id},
#         {"$set": {"trial_token": trial_token, "expiry_date": expiry_time, "trial_used": False}},
#         upsert=True
#     )

#     # Generate the Telegram deep link
#     bot_username = (await client.get_me()).username
#     long_url = f"https://telegram.me/{bot_username}?start=trial-{trial_token}"

#         # Shorten the URL
#     response = requests.get(f"{SHORTENER_URL}?api={SHORTENER_API_KEY}&url={long_url}")
#     if response.status_code == 200:
#         short_url = response.json().get("shortenedUrl", long_url)
#     else:
#         short_url = long_url  # Fallback if shortener fails

#     # Send message with a button containing the short link
#     keyboard = InlineKeyboardMarkup(
#         [[InlineKeyboardButton("🔗 Activate Trial", url=short_url)]]
#     )

#     await message.reply(
#         "🎉 Click the button below to activate your 3-hour Premium trial!\n\n"
#         "Once activated, you will receive confirmation automatically.",
#         reply_markup=keyboard
#     )

#     # await message.reply(
#     #     f"🎉 Click this link to activate your 3-hour Premium trial:\n🔗 {start_link}\n\n"
#     #     "Once activated, you will receive confirmation automatically!"
#     # )

# @Client.on_message(filters.command("tryPremium") & filters.private)
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

#     # Generate the Telegram deep link
#     bot_username = (await client.get_me()).username
#     long_url = f"https://t.me/{bot_username}?start=trial-{trial_token}"

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
#         "Click the button below to activate your <b>3-hour Premium trial!\n\n"
#         "Once activated, you will receive confirmation automatically.",
#         reply_markup=keyboard
#     )


@Client.on_message(filters.regex(r"^/start trial-(\w+)$") & filters.private)
async def activate_trial(client, message):
    user_id = message.from_user.id
    token = message.matches[0].group(1)

    # Find trial in database
    trial_entry = premium_users.find_one({"user_id": user_id, "trial_token": token, "trial_used": False})

    if not trial_entry:
        return await message.reply("❌ Invalid or expired trial token.")

    # Grant premium and mark trial as used
    expiry_time = datetime.utcnow() + timedelta(hours=3)
    premium_users.update_one(
        {"user_id": user_id},
        {"$set": {"is_premium": True, "expiry_date": expiry_time, "trial_used": True}}
    )

    await message.reply("✅ Your 3-hour Premium trial has been activated! Enjoy your benefits. 🚀")

# ✅ Command Handlers
@Client.on_message(filters.command("addpremium") & filters.user(ADMINS))
async def handle_add_premium(client, message):
    await add_premium(client, message)

@Client.on_message(filters.command("extendpremium") & filters.user(ADMINS))
async def handle_extend_premium(client, message):
    await extend_premium(client, message)

@Client.on_message(filters.command("mypremium"))
async def handle_my_premium(client, message):
    await my_premium(client, message)

@Client.on_message(filters.command("listpremium") & filters.user(ADMINS))
async def handle_list_premium_users(client, message):
    await list_premium_users(client, message)

@Client.on_message(filters.command("revokepremium") & filters.user(ADMINS))
async def handle_revoke_premium(client, message):
    await revoke_premium(client, message)
