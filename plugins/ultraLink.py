import os
import asyncio
import httpx
from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMINS  # ensure this is a list of INT user IDs

API_BASE = os.getenv("API_BASE", "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "admin")  # set in Koyeb as a secret

# Create your app instance somewhere in your entrypoint:
# app = Client("mybot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))

# ---------------- Helper: parse 4K flags ----------------
def parse_4k_flags(text: str):
    tokens = text.split()
    data = {
        "tmdbID": None,
        "fileLink": None,
        "is4K": False,
        "size": None,   # optional
        "delete": False
    }

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token == "-tmdb" and i + 1 < len(tokens):
            try:
                data["tmdbID"] = int(tokens[i + 1])
            except ValueError:
                raise ValueError("TMDb ID must be an integer.")
            i += 2
            continue

        if token == "-f" and i + 1 < len(tokens):
            data["fileLink"] = tokens[i + 1]
            i += 2
            continue

        if token == "-i" and i + 1 < len(tokens):
            v = tokens[i + 1].lower()
            if v not in ("t", "f", "true", "false", "1", "0"):
                raise ValueError("Invalid value for -i. Use t/f.")
            data["is4K"] = v in ("t", "true", "1")
            i += 2
            continue

        if token == "-s" and i + 1 < len(tokens):
            data["size"] = tokens[i + 1]
            i += 2
            continue

        if token == "-d":
            data["delete"] = True
            i += 1
            continue

        i += 1

    return data

# ---------------- Helper: send movie info ----------------
async def send_movie_info(client: Client, chat_id: int, movie: dict, action: str = "Updated"):
    title = movie.get("title", "Unknown")
    overview = movie.get("overview", "No overview available.")
    poster = movie.get("poster_path")

    flags = []
    if movie.get("order") == 0:
        flags.append("⬆ First")
    if movie.get("pinned") is True:
        flags.append("⭐ Pinned")
    elif movie.get("pinned") is False:
        flags.append("📌 Unpinned")

    flag_text = " | ".join(flags) if flags else ""

    caption = (
        f"🎬 <b>{title}</b>\n\n"
        f"<code>{overview}</code>\n\n"
        f"{action} successfully\n"
        f"{flag_text}"
    )

    if poster:
        await client.send_photo(
            chat_id,
            f"https://image.tmdb.org/t/p/w500{poster}",
            caption=caption,
            parse_mode="html"
        )
    else:
        await client.send_message(chat_id, caption, parse_mode="html")

# ---------------- HTTP helper ----------------
def get_http_client() -> httpx.AsyncClient:
    # You may share one client per module if you prefer; here we create a short-lived client per handler
    return httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=20, write=20, pool=5))

# ---------------- PUT 4K / UPDATE ----------------
def register_handlers(app: Client):
    @app.on_message(filters.command("put4k") & filters.user(ADMINS))
    async def handle_put4k(client: Client, message: Message):
        try:
            if not message.text:
                await message.reply("❌ Usage:\n/put4k -tmdb 550 [-f fileLink] [-i t|f] [-s 12GB] [-d]")
                return

            cmd = parse_4k_flags(message.text)

            if not cmd["tmdbID"]:
                await message.reply("❌ Usage:\n/put4k -tmdb 550 [-f fileLink] [-i t|f] [-s 12GB] [-d]")
                return

            # If delete flag is set, redirect to delete logic
            if cmd["delete"]:
                await handle_del4k_direct(client, cmd["tmdbID"], message)
                return

            if not cmd["fileLink"]:
                await message.reply("❌ File link required when adding/updating 4K link.")
                return

            ultraLinkObj = {
                "is4K": cmd["is4K"],
                "downloadLink": cmd["fileLink"]
            }
            if cmd["size"]:
                ultraLinkObj["size"] = cmd["size"]

            payload = {
                "tmdbID": cmd["tmdbID"],
                "ultraLink": ultraLinkObj,
                "secret": ADMIN_SECRET
            }

            async with get_http_client() as http:
                res = await http.post(f"{API_BASE}/admin/put4k", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    movie = data.get("movie")
                    if movie:
                        await send_movie_info(client, message.chat.id, movie, action="Ultra link added/updated")
                    else:
                        await message.reply(f"✅ Ultra link added/updated for TMDbID {cmd['tmdbID']}")
                else:
                    # relay backend error body safely
                    text = res.text
                    await message.reply(f"❌ Failed:\n<code>{httpx.utils.escape_html(text)}</code>", parse_mode="html")

        except ValueError as ve:
            await message.reply(f"❌ {str(ve)}")
        except httpx.RequestError as ne:
            await message.reply(f"❌ Network error contacting backend: <code>{httpx.utils.escape_html(str(ne))}</code>", parse_mode="html")
        except Exception as e:
            await message.reply(f"❌ Exception:\n<code>{httpx.utils.escape_html(str(e))}</code>", parse_mode="html")

    # ---------------- DELETE 4K ----------------
    @app.on_message(filters.command("del4k") & filters.user(ADMINS))
    async def handle_del4k(client: Client, message: Message):
        try:
            if not message.text:
                await message.reply("❌ Usage:\n/del4k -tmdb [TMDbID]")
                return

            tokens = message.text.split()
            if len(tokens) < 3 or tokens[1].lower() != "-tmdb":
                await message.reply("❌ Usage:\n/del4k -tmdb [TMDbID]")
                return

            try:
                tmdbID = int(tokens[2])
            except ValueError:
                await message.reply("❌ TMDb ID must be an integer.")
                return

            await handle_del4k_direct(client, tmdbID, message)

        except Exception as e:
            await message.reply(f"❌ Exception:\n<code>{httpx.utils.escape_html(str(e))}</code>", parse_mode="html")

# ---------------- DELETE LOGIC HELPER ----------------
async def handle_del4k_direct(client: Client, tmdbID: int, message: Message):
    payload = {
        "tmdbID": tmdbID,
        "ultraLink": None,  # tell backend to remove it
        "secret": ADMIN_SECRET
    }

    try:
        async with get_http_client() as http:
            res = await http.post(f"{API_BASE}/admin/put4k", json=payload)
            if res.status_code == 200:
                data = res.json()
                movie = data.get("movie")
                if movie:
                    await send_movie_info(client, message.chat.id, movie, action="Ultra link deleted")
                else:
                    await message.reply(f"✅ Ultra link deleted successfully for TMDbID {tmdbID}")
            else:
                await message.reply(f"❌ Failed to delete:\n<code>{httpx.utils.escape_html(res.text)}</code>", parse_mode="html")
    except httpx.RequestError as ne:
        await message.reply(f"❌ Network error contacting backend: <code>{httpx.utils.escape_html(str(ne))}</code>", parse_mode="html")
