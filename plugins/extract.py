import re
import httpx
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS

TMDB_API_KEY = "c58c996e06beee1e8a355354c229a784"

# In-memory cache for movie data to avoid duplicate requests
cache = {}

async def make_request(query, params):
    """
    Makes a request to TMDB and implements rate-limiting and exponential backoff.
    """
    attempt = 0
    while attempt < 5:  # Retry up to 5 times in case of hitting rate limit
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.themoviedb.org/3/search/movie", params=params)
            
            # Check if rate limit is exceeded (429 error)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))  # Default to 60 seconds if no header
                await asyncio.sleep(retry_after)
                attempt += 1
                continue  # Retry after waiting
                
            # If not rate-limited, handle the response normally
            response.raise_for_status()
            return response.json()

    # If maximum retries are exceeded
    raise Exception("Exceeded maximum retry attempts due to rate limit.")

@Client.on_message(filters.command("extract") & filters.user(ADMINS))
async def handle_extract(client, message):
    if len(message.command) < 2:
        return await message.reply("<b>❌ Usage:</b> <code>/extract Movie Name [Year]</code>")

    raw_query = message.text.split(None, 1)[1]
    
    # Extract 4-digit year if present (e.g., "Movie 2023")
    year_match = re.search(r'\b(19|20)\d{2}\b', raw_query)
    year = year_match.group(0) if year_match else None
    query = raw_query.replace(year, "").strip() if year else raw_query

    # Check if the movie data is already cached
    if query in cache:
        data = cache[query]
    else:
        params = {
            "api_key": TMDB_API_KEY,
            "query": query,
            "include_adult": "false",
            "language": "en-US"
        }
        if year:
            params["primary_release_year"] = year

        try:
            # Make the API request with rate-limiting and exponential backoff
            data = await make_request(query, params)
            cache[query] = data  # Cache the result for future use
        except Exception as e:
            return await message.reply(f"<b>❌ System Error:</b> <code>{str(e)}</code>")

    results = data.get("results", [])

    if not results:
        return await message.reply(f"<b>❌ No results found for:</b> <code>{raw_query}</code>")

    # Get top result
    movie = results[0]
    m_id = movie["id"]
    title = movie["title"]
    r_date = movie.get("release_date", "N/A")
    r_year = r_date[:4] if r_date else "N/A"
    poster = movie.get("poster_path")
    overview = movie.get("overview", "No description available.")

    caption = (
        f"🎯 <b>Match Found</b>\n\n"
        f"🎬 <b>Title:</b> {title} ({r_year})\n"
        f"🆔 <b>TMDB ID:</b> <code>{m_id}</code>\n\n"
        f"📝 <b>Plot:</b> {overview[:150]}..."
    )

    # Button to quickly trigger your /put command syntax
    # This makes it one-tap to start the next step
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 View on TMDB", url=f"https://www.themoviedb.org/movie/{m_id}")]
    ])

    if poster:
        await client.send_photo(
            message.chat.id,
            f"https://image.tmdb.org/t/p/w500{poster}",
            caption=caption,
            reply_markup=keyboard
        )
    else:
        await message.reply(caption, reply_markup=keyboard)
