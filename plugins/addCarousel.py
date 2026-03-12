#plugins/addCarousel.py
from pyrogram import Client, filters
import requests
from config import ADMINS

API_BASE = "https://christian-erminia-abhisworkspace-82b29324.koyeb.app/api/carousel"
ADMIN_SECRET = "admin"

# ---------------- Helper ----------------
def parse_carousel_flags(text):
    tokens = text.split()
    data = {
        "tmdbID": None,
        "imagePath": None,
        "orderPos": "f",   # default insert first
        "position": None
    }

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token == "-tmdb" and i + 1 < len(tokens):
            data["tmdbID"] = int(tokens[i + 1])
            i += 2
            continue

        if token == "-i" and i + 1 < len(tokens):
            data["imagePath"] = tokens[i + 1]
            i += 2
            continue

        if token == "-o" and i + 1 < len(tokens):
            if tokens[i + 1] in ["f", "l"]:
                data["orderPos"] = tokens[i + 1]
            i += 2
            continue

        if token == "-p" and i + 1 < len(tokens):
            data["position"] = int(tokens[i + 1])
            i += 2
            continue

        i += 1

    return data
# ---------------- ADD CAROUSEL ----------------
@Client.on_message(filters.command("addc") & filters.user(ADMINS))
async def handle_add_carousel(client, message):
    try:
        cmd = parse_carousel_flags(message.text)
        if not cmd["tmdbID"] or not cmd["imagePath"]:
            await message.reply("❌ Usage:\n/addc -tmdb 550 -i https://image.com/img.jpg")
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "imagePath": cmd["imagePath"],
            "imageType": "tmdb" if cmd["tmdbID"] else "external",
            "orderPos": cmd["orderPos"],
            "secret": ADMIN_SECRET
        }

        res = requests.post(f"{API_BASE}/add", json=payload)
        if res.status_code == 200:
            slide = res.json().get("slide", {})
            await message.reply(f"✅ Carousel slide added: <b>{slide.get('title','No title')}</b>")
        else:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")
    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

# ---------------- DELETE CAROUSEL ----------------
@Client.on_message(filters.command("delc") & filters.user(ADMINS))
async def handle_del_carousel(client, message):
    try:
        cmd = parse_carousel_flags(message.text)
        if not cmd["tmdbID"]:
            await message.reply("❌ Usage:\n/delc -tmdb 550")
            return

        payload = {"tmdbID": cmd["tmdbID"], "secret": ADMIN_SECRET}
        res = requests.delete(f"{API_BASE}/delete", json=payload)

        if res.status_code == 200:
            await message.reply(f"🗑️ Carousel slide deleted: TMDB ID {cmd['tmdbID']}")
        else:
            await message.reply(f"❌ Failed to delete:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

@Client.on_message(filters.command("movec") & filters.user(ADMINS))
async def move_carousel(client, message):
    try:
        cmd = parse_carousel_flags(message.text)

        if not cmd["tmdbID"] or cmd["position"] is None:
            await message.reply(
                "❌ Usage:\n"
                "/movec -tmdb 550 -p 1\n\n"
                "Move carousel slide to position"
            )
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "position": cmd["position"],
            "secret": ADMIN_SECRET
        }

        res = requests.post(f"{API_BASE}/move", json=payload)

        if res.status_code == 200:
            await message.reply(f"✅ Slide moved to position {cmd['position']}")
        else:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")

@Client.on_message(filters.command("pinc") & filters.user(ADMINS))
async def pin_carousel(client, message):
    try:
        cmd = parse_carousel_flags(message.text)

        if not cmd["tmdbID"]:
            await message.reply(
                "❌ Usage:\n"
                "/pinc -tmdb 550\n\n"
                "Pin slide to top of carousel"
            )
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "secret": ADMIN_SECRET
        }

        res = requests.post(f"{API_BASE}/pin", json=payload)

        if res.status_code == 200:
            await message.reply(f"📌 Slide pinned: TMDB {cmd['tmdbID']}")
        else:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")


@Client.on_message(filters.command("unpinc") & filters.user(ADMINS))
async def unpin_carousel(client, message):
    try:
        cmd = parse_carousel_flags(message.text)

        if not cmd["tmdbID"]:
            await message.reply(
                "❌ Usage:\n"
                "/unpinc -tmdb 550\n\n"
                "Remove slide pin"
            )
            return

        payload = {
            "tmdbID": cmd["tmdbID"],
            "secret": ADMIN_SECRET
        }

        res = requests.post(f"{API_BASE}/unpin", json=payload)

        if res.status_code == 200:
            await message.reply(f"📍 Slide unpinned: TMDB {cmd['tmdbID']}")
        else:
            await message.reply(f"❌ Failed:\n<code>{res.text}</code>")

    except Exception as e:
        await message.reply(f"❌ Exception:\n<code>{str(e)}</code>")
