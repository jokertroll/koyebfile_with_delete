import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from bot import Bot
from config import ADMINS, CHANNEL_ID, DISABLE_CHANNEL_BUTTON
from helper_func import encode

# 🔹 Handles private messages from admin (to create post + generate shareable link)
admin_commands = ['start', 'users', 'broadcast', 'batch', 'genlink', 'stats', 'join', 'try_premium',
                  'music', 'premium', 'addpremium', 'listpremium', 'mypremium', 'extendpremium',
                  'revokepremium', 'trackPromo', 'generatePromo', 'resetTrial','adminHelp','put','delete','update',
                  'deleteseries', 'updateseries', 'puts','pin','unpin','addc','delc']]

@Bot.on_message(filters.private & filters.user(ADMINS) & ~filters.command(admin_commands))
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("Please Wait...!", quote=True)

    try:
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except Exception as e:
        print(f"❌ Copy failed: {e}")
        await reply_text.edit_text("Something went Wrong..!")
        return

    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]
    ])

    await reply_text.edit(
        f"<b>Here is your link</b>\n\n{link}",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

    # ✅ Safely try to edit the markup of the channel post (only if valid)
    if not DISABLE_CHANNEL_BUTTON and post_message and post_message.chat.id == client.db_channel.id:
        try:
            await post_message.edit_reply_markup(reply_markup)
        except Exception as e:
            print(f"❌ Failed to edit reply markup: {e}")


# 🔹 Auto-add button when a new post is made directly in the channel
@Bot.on_message(filters.channel & filters.incoming & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):
    if DISABLE_CHANNEL_BUTTON:
        return

    converted_id = message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]
    ])

    try:
        await message.edit_reply_markup(reply_markup)
    except Exception as e:
        print(f"❌ Failed to add button to new channel post: {e}")
