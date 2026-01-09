# addSeries.py
import requests
from pyrogram import Client, filters
from config import ADMINS
import html

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env

# ---------------- Add / Put Series ----------------
@Client.on_message(filters.command("puts") & filters.user(ADMINS))
async def handle_put_series(client, message):
    try:
        # Example command:
        # /puts -tmdb 257340 -lang en -season 1 -720p https://filelink.mp4
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())
        lang = parts[2].replace("lang", "").strip() if "lang" in parts[2] else "en"
        season_number = int(parts[3].replace("season", "").strip())
        quality_file = parts[4].strip()

        if " " in quality_file:
            quality, file_link = quality_file.split(maxsplit=1)
        else:
            await message.reply("❌ Missing file link for the given quality.")
            return

        payload = {
            "tmdbID": tmdb_id,
            "seasons": [
                {
                    "seasonNumber": season_number,
                    "language": lang,
                    "versions": [
                        {"quality": quality, "fileLink": file_link}
                    ]
                }
            ],
            "secret": ADMIN_SECRET
        }

        res = requests.post(f"{API_BASE}/series/add", json=payload)

        if res.status_code == 200:
            data = res.json()
            series = data.get("series", {})
            title = series.get("title", "Unknown")
            overview = series.get("overview", "No overview available.")
            poster_path = series.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            caption = f"✅ <b>{title}</b>\n\n<code>{overview}</code>\n\n🎬 Series uploaded successfully!"
            if poster_url:
                await client.send_photo(chat_id=message.chat.id, photo=poster_url, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to upload series:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{html.escape(str(e))}</code>")

# ---------------- Update Series ----------------
@Client.on_message(filters.command("updateseries") & filters.user(ADMINS))
async def handle_update_series(client, message):
    try:
        # /updateseries -tmdb 257340 -lang en -season 1 -720p https://newfilelink.mp4
        parts = message.text.split("-")
        tmdb_id = int(parts[1].replace("tmdb", "").strip())
        lang = parts[2].replace("lang", "").strip() if "lang" in parts[2] else "en"
        season_number = int(parts[3].replace("season", "").strip())
        quality_file = parts[4].strip()

        if " " in quality_file:
            quality, file_link = quality_file.split(maxsplit=1)
        else:
            await message.reply("❌ Missing file link for the given quality.")
            return

        payload = {
            "tmdbID": tmdb_id,
            "seasonNumber": season_number,
            "language": lang,
            "quality": quality,
            "fileLink": file_link,
            "secret": ADMIN_SECRET
        }

        res = requests.put(f"{API_BASE}/series/update", json=payload)

        if res.status_code == 200:
            data = res.json()
            series = data.get("series", {})
            title = series.get("title", "Unknown")
            overview = series.get("overview", "No overview available.")
            poster_path = series.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            caption = f"✏️ <b>{title}</b>\n\n<code>{overview}</code>\n\n🎬 Series updated successfully!"
            if poster_url:
                await client.send_photo(chat_id=message.chat.id, photo=poster_url, caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed to update series:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception occurred: <code>{html.escape(str(e))}</code>")
