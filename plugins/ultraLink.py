import asyncio
import requests
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"


# ---------------- safe requests wrapper ----------------
def post_sync(url, payload):
    return requests.post(url, json=payload, timeout=20)


# ---------------- Helper: parse flags ----------------
def parse_4k_flags(text: str):

    tokens = text.split()[1:]  # remove command itself

    data = {
        "tmdbID": None,
        "fileLink": None,
        "is4K": False,
        "size": None,
        "delete": False
    }

    i = 0
    while i < len(tokens):

        token = tokens[i]

        if token == "-tmdb" and i + 1 < len(tokens):
            data["tmdbID"] = int(tokens[i + 1])
            i += 2
            continue

        if token == "-f" and i + 1 < len(tokens):
            data["fileLink"] = tokens[i + 1]
            i += 2
            continue

        if token == "-i" and i + 1 < len(tokens):
            data["is4K"] = tokens[i + 1].lower() == "t"
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


# ---------------- send movie info ----------------
async def send_movie_info(client, chat_id, movie, action="Updated"):

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
        f"{action}\n"
        f"{flag_text}"
    )

    if poster:
        await client.send_photo(
            chat_id,
            f"https://image.tmdb.org/t/p/w500{poster}",
            caption=caption,
            parse_mode=ParseMode.HTML
        )
    else:
        await client.send_message(
            chat_id,
            caption,
            parse_mode=ParseMode.HTML
        )


# ---------------- PUT 4K ----------------
@Client.on_message(filters.command("put4k") & filters.user(ADMINS))
async def put4k_handler(client, message):

    try:

        # check if arguments exist
        if len(message.command) == 1:
            await message.reply(
                "❌ Usage:\n"
                "/put4k -tmdb 550 [-f link] [-i t|f] [-s 12GB] [-d]"
            )
            return

        cmd = parse_4k_flags(message.text)

        if not cmd["tmdbID"]:
            await message.reply("❌ TMDb ID missing.")
            return

        # delete mode
        if cmd["delete"]:
            await del4k_direct(client, cmd["tmdbID"], message)
            return

        if not cmd["fileLink"]:
            await message.reply("❌ File link required.")
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

        res = await asyncio.to_thread(
            post_sync,
            f"{API_BASE}/admin/put4k",
            payload
        )

        if res.status_code == 200:

            movie = res.json().get("movie")

            if movie:
                await send_movie_info(
                    client,
                    message.chat.id,
                    movie,
                    "Ultra link added/updated"
                )
            else:
                await message.reply("✅ Ultra link added/updated.")

        else:
            await message.reply(
                f"❌ Failed:\n<code>{res.text}</code>",
                parse_mode=ParseMode.HTML
            )

    except Exception as e:

        await message.reply(
            f"❌ Error: <code>{e}</code>",
            parse_mode=ParseMode.HTML
        )


# ---------------- DEL 4K ----------------
@Client.on_message(filters.command("del4k") & filters.user(ADMINS))
async def del4k_handler(client, message):

    try:

        if len(message.command) < 3 or message.command[1] != "-tmdb":

            await message.reply(
                "❌ Usage:\n/del4k -tmdb 550"
            )
            return

        tmdbID = int(message.command[2])

        await del4k_direct(client, tmdbID, message)

    except Exception as e:

        await message.reply(
            f"❌ Error: <code>{e}</code>",
            parse_mode=ParseMode.HTML
        )


# ---------------- DELETE LOGIC ----------------
async def del4k_direct(client, tmdbID, message):

    payload = {
        "tmdbID": tmdbID,
        "ultraLink": None,
        "secret": ADMIN_SECRET
    }

    res = await asyncio.to_thread(
        post_sync,
        f"{API_BASE}/admin/put4k",
        payload
    )

    if res.status_code == 200:

        movie = res.json().get("movie")

        if movie:
            await send_movie_info(
                client,
                message.chat.id,
                movie,
                "Ultra link deleted"
            )
        else:
            await message.reply(
                f"✅ Ultra link deleted for TMDbID {tmdbID}"
            )

    else:

        await message.reply(
            f"❌ Failed to delete:\n<code>{res.text}</code>",
            parse_mode=ParseMode.HTML
        )
