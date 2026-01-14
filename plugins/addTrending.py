# plugins\addTrending.py
import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env

# ---------------- Helper ----------------
def parse_trend_flags(text):
    """
    Parse /trend or /trendu command flags
    Example: /trend -tmdb 550 -p 1
             /trendu -tmdb 550 -p 4
    """
    tokens = text.split()
    data = {"tmdbID": None, "trendingOrder": None}

    i = 0
    while i < len(tokens):
        token = tokens[i].lower()

        if token == "-tmdb" and i + 1 < len(tokens):
            try:
                data["tmdbID"] = int(tokens[i + 1])
            except:
                data["tmdbID"] = None
            i += 2
            continue

        if token == "-p" and i + 1 < len(tokens):
            try:
                data["trendingOrder"] = int(tokens[i + 1])
            except:
                data["trendingOrder"] = None
            i += 2
            continue

        i += 1

    return data

# ---------------- /trend ADD OR UPDATE ----------------
@Client.on_message(filters.command("trend") & filters.user(ADMINS))
async def handle_trend(client, message):
    try:
        cmd = parse_trend_flags(message.text)

        if not cmd["tmdbID"] or cmd["trendingOrder"] is None:
            await message.reply("❌ Usage:\n/trend -tmdb 550 -p 1")
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "trendingOrder": cmd["trendingOrder"]
        }

        # Use new trending API endpoint
        res = requests.post(f"{API_BASE}/movies/trending/add", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            caption = f"🔥 <b>{title}</b> is now trending at position {cmd['trendingOrder']} ✅"
            await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to add trending:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred:\n<code>{str(e)}</code>")

# ---------------- /deltrend DELETE trending ----------------
@Client.on_message(filters.command("deltrend") & filters.user(ADMINS))
async def handle_deltrend(client, message):
    try:
        cmd = parse_trend_flags(message.text)
        if not cmd["tmdbID"]:
            await message.reply("❌ Usage:\n/deltrend -tmdb 550")
            return

        payload = {"tmdbID": cmd["tmdbID"]}

        # Use new trending remove API
        res = requests.post(f"{API_BASE}/movies/trending/remove", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            caption = f"🗑️ <b>{title}</b>\n\nRemoved from trending successfully!"
            await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to remove trending:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred:\n<code>{str(e)}</code>")
