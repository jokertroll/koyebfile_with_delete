# plugins\addUpcoming.py
import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

# ---------------- Helper ----------------
def parse_trend_flags(text):
    """
    Parse /upcome or /delupcome command flags
    Example:
      /upcome -tmdb 550 -p 1
      /delupcome -tmdb 550
    """
    tokens = text.split()
    data = {"tmdbID": None, "upcomingOrder": None}

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
                data["upcomingOrder"] = int(tokens[i + 1])
            except:
                data["upcomingOrder"] = None
            i += 2
            continue

        i += 1

    return data


# ---------------- /trend ADD or UPDATE ----------------
@Client.on_message(filters.command("upcome") & filters.user(ADMINS))
async def handle_trend(client, message):
    try:
        cmd = parse_trend_flags(message.text)

        if not cmd["tmdbID"] or cmd["upcomingOrder"] is None:
            await message.reply("❌ Usage:\n/trend -tmdb 550 -p 1")
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "upcomingOrder": cmd["upcomingOrder"],
            "secret": ADMIN_SECRET
        }

        res = requests.post(
            f"{API_BASE}/movies/upcoming/add",
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
            f"📈 Added to Upcoming Releases : <b>{cmd['upcomingOrder']}</b>"
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
@Client.on_message(filters.command("delupcome") & filters.user(ADMINS))
async def handle_deltrend(client, message):
    try:
        cmd = parse_trend_flags(message.text)

        if not cmd["tmdbID"]:
            await message.reply("❌ Usage:\n/delupcome -tmdb 550")
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "secret": ADMIN_SECRET
        }

        res = requests.post(
            f"{API_BASE}/movies/upcoming/remove",
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
            f"❌ Removed from Upcoming releases"
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
