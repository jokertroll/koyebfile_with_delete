import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend

# ---------------- Helper ----------------
def parse_flags(text):
    """Parse command flags like -tmdb, -r, -u"""
    tokens = text.split()
    data = {"tmdbID": None, "rank": None, "unpin": False}

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token == "-tmdb" and i + 1 < len(tokens):
            data["tmdbID"] = int(tokens[i + 1])
            i += 2
            continue

        if token == "-r" and i + 1 < len(tokens):
            data["rank"] = int(tokens[i + 1])
            i += 2
            continue

        if token == "-u":  # unpin / remove pinned
            data["unpin"] = True
            i += 1
            continue

        i += 1
    return data

# ---------------- ADD TO TOP 10 ----------------
@Client.on_message(filters.command("topa") & filters.user(ADMINS))
async def add_top10(client, message):
    try:
        cmd = parse_flags(message.text)
        if not cmd["tmdbID"] or not cmd["rank"]:
            await message.reply("❌ Usage:\n/topa -tmdb 550 -r 1")
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "rank": cmd["rank"],
            "secret": ADMIN_SECRET
        }

        res = requests.post(f"{API_BASE}/top10/add", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie")
            title = movie.get("title")
            poster = movie.get("poster_path")
            caption = f"🎬 <b>{title}</b>\nAdded to Top 10 at rank {cmd['rank']}"
            if poster:
                await client.send_photo(message.chat.id, f"https://image.tmdb.org/t/p/w500{poster}", caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed: <code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

# ---------------- UPDATE TOP 10 ----------------
@Client.on_message(filters.command("topu") & filters.user(ADMINS))
async def update_top10(client, message):
    try:
        cmd = parse_flags(message.text)
        if not cmd["tmdbID"] or not cmd["rank"]:
            await message.reply("❌ Usage:\n/topu -tmdb 550 -r 1 [-u]")
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "rank": cmd["rank"],
            "unpin": cmd["unpin"],
            "secret": ADMIN_SECRET
        }

        res = requests.put(f"{API_BASE}/top10/update", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie")
            title = movie.get("title")
            poster = movie.get("poster_path")
            caption = f"✏️ <b>{title}</b>\nUpdated Top 10 rank to {cmd['rank']}"
            if cmd["unpin"]:
                caption += "\n📌 Unpinned"
            if poster:
                await client.send_photo(message.chat.id, f"https://image.tmdb.org/t/p/w500{poster}", caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed: <code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

# ---------------- DELETE FROM TOP 10 ----------------
@Client.on_message(filters.command("deltop") & filters.user(ADMINS))
async def delete_top10(client, message):
    try:
        cmd = parse_flags(message.text)
        if not cmd["tmdbID"]:
            await message.reply("❌ Usage:\n/deltop -tmdb 550")
            return

        payload = {"tmdbID": cmd["tmdbID"], "secret": ADMIN_SECRET}
        res = requests.delete(f"{API_BASE}/top10/delete", json=payload)

        if res.status_code == 200:
            movie = res.json().get("movie")
            title = movie.get("title")
            poster = movie.get("poster_path")
            caption = f"🗑️ <b>{title}</b>\nRemoved from Top 10"
            if poster:
                await client.send_photo(message.chat.id, f"https://image.tmdb.org/t/p/w500{poster}", caption=caption)
            else:
                await message.reply(caption)
        else:
            await message.reply(f"❌ Failed: <code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")
