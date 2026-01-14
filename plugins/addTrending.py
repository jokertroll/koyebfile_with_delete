# plugins/addTrending.py
import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

# ---------------- Helper ----------------
def parse_trend_flags(text):
    """
    Parse /trend or /deltrend command flags
    Example:
      /trend -tmdb 550 -p 1
      /deltrend -tmdb 550
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


# ---------------- /trend ADD or UPDATE ----------------
@Client.on_message(filters.command("trend") & filters.user(ADMINS))
async def handle_trend(client, message):
    try:
        cmd = parse_trend_flags(message.text)

        if not cmd["tmdbID"] or cmd["trendingOrder"] is None:
            await message.reply("❌ Usage:\n/trend -tmdb 550 -p 1")
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "trendingOrder": cmd["trendingOrder"],
            "secret": ADMIN_SECRET
        }

        res = requests.post(
            f"{API_BASE}/movies/trending/add",
            json=payload
        )

        if res.status_code != 200:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")
            return

        movie = res.json().get("movie", {})
        title = movie.get("title", "Unknown")
        overview = movie.get("overview", "No overview available.")
        poster = movie.get("poster_path")

        caption = (
            f"🔥 <b>{title}</b>\n\n"
            f"<code>{overview}</code>\n\n"
            f"📈 Trending Position: <b>{cmd['trendingOrder']}</b>"
        )

        if poster:
            await client.send_photo(
                message.chat.id,
                f"{TMDB_IMG}{poster}",
                caption=caption
            )
        else:
            await message.reply(caption)

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")


# ---------------- /deltrend REMOVE ----------------
@Client.on_message(filters.command("deltrend") & filters.user(ADMINS))
async def handle_deltrend(client, message):
    try:
        cmd = parse_trend_flags(message.text)

        if not cmd["tmdbID"]:
            await message.reply("❌ Usage:\n/deltrend -tmdb 550")
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "secret": ADMIN_SECRET
        }

        res = requests.post(
            f"{API_BASE}/movies/trending/remove",
            json=payload
        )

        if res.status_code != 200:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")
            return

        movie = res.json().get("movie", {})
        title = movie.get("title", "Unknown")
        overview = movie.get("overview", "No overview available.")
        poster = movie.get("poster_path")

        caption = (
            f"🗑️ <b>{title}</b>\n\n"
            f"<code>{overview}</code>\n\n"
            f"❌ Removed from Trending"
        )

        if poster:
            await client.send_photo(
                message.chat.id,
                f"{TMDB_IMG}{poster}",
                caption=caption
            )
        else:
            await message.reply(caption)

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")
