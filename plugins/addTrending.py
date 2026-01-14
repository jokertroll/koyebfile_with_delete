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
            await message.reply(
                "❌ Usage:\n/trend -tmdb 550 -p 1"
            )
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "trending": {"isTrending": True, "trendingOrder": cmd["trendingOrder"]},
            "secret": ADMIN_SECRET
        }

        # Try ADD or UPDATE trending
        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            caption = f"🔥 <b>{title}</b> is now trending at position {cmd['trendingOrder']} ✅"
            await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to add trending:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred:\n<code>{str(e)}</code>")


# ---------------- /trendu UPDATE trending order ----------------
@Client.on_message(filters.command("trendu") & filters.user(ADMINS))
async def handle_trendu(client, message):
    try:
        cmd = parse_trend_flags(message.text)

        if not cmd["tmdbID"] or cmd["trendingOrder"] is None:
            await message.reply(
                "❌ Usage:\n/trendu -tmdb 550 -p 4"
            )
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "trending": {"isTrending": True, "trendingOrder": cmd["trendingOrder"]},
            "secret": ADMIN_SECRET
        }

        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            caption = f"✏️ Updated trending for <b>{title}</b> to position {cmd['trendingOrder']} ✅"
            await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to update trending:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred:\n<code>{str(e)}</code>")


# ---------------- /deltrend DELETE trending ----------------
@Client.on_message(filters.command("deltrend") & filters.user(ADMINS))
async def handle_deltrend(client, message):
    try:
        tokens = message.text.split()
        if "-tmdb" not in tokens:
            await message.reply("❌ Usage:\n/deltrend -tmdb 550")
            return

        tmdb_id = int(tokens[tokens.index("-tmdb") + 1])

        # Set trending to false
        payload = {"tmdbID": tmdb_id, "trending": {"isTrending": False}, "secret": ADMIN_SECRET}

        res = requests.put(f"{API_BASE}/updateMovie", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie", {})
            title = movie.get("title", "Unknown")
            await message.reply(f"🗑️ <b>{title}</b> removed from trending successfully ✅")
        else:
            await message.reply(f"❌ Failed to delete trending:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred:\n<code>{str(e)}</code>")
