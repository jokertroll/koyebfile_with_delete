import requests
from pyrogram import Client, filters
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api"
ADMIN_SECRET = "admin"  # must match backend .env

# ---------------- Helper ----------------
def parse_4k_flags(text):
    tokens = text.split()
    data = {
        "tmdbID": None,
        "fileLink": None,
        "is4K": False,
        "size": None,  # optional
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

# ---------------- PUT 4K / UPDATE ----------------
@Client.on_message(filters.command("put4k") & filters.user(ADMINS))
async def handle_put4k(client, message):
    try:
        cmd = parse_4k_flags(message.text)

        if not cmd["tmdbID"]:
            await message.reply("❌ Usage:\n/put4k -tmdb 550 [-f fileLink] [-i t|f] [-s 12GB] [-d]")
            return

        # If delete flag is set, redirect to del logic
        if cmd["delete"]:
            await handle_del4k_direct(cmd["tmdbID"], message)
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

        res = requests.post(f"{API_BASE}/admin/put4k", json=payload)

        if res.status_code == 200:
            await message.reply(f"✅ Ultra link added/updated for TMDbID {cmd['tmdbID']}")
        else:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

# ---------------- DELETE 4K ----------------
@Client.on_message(filters.command("del4k") & filters.user(ADMINS))
async def handle_del4k(client, message):
    try:
        tokens = message.text.split()
        if len(tokens) < 3 or tokens[1].lower() != "-tmdb":
            await message.reply("❌ Usage:\n/del4k -tmdb [TMDbID]")
            return

        tmdbID = int(tokens[2])
        await handle_del4k_direct(tmdbID, message)

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

# ---------------- DELETE LOGIC HELPER ----------------
async def handle_del4k_direct(tmdbID, message):
    payload = {
        "tmdbID": tmdbID,
        "ultraLink": None,  # tell backend to remove it
        "secret": ADMIN_SECRET
    }

    res = requests.post(f"{API_BASE}/admin/put4k", json=payload)

    if res.status_code == 200:
        await message.reply(f"✅ Ultra link deleted successfully for TMDbID {tmdbID}")
    else:
        await message.reply(f"❌ Failed to delete:\n<code>{res.text}</code>")
