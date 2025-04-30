import os

# Bot configuration
BOT_PREFIX = "/"
BOT_NAME = "JoeA"
BOT_DESCRIPTION = "An automation and moderation tool for Discord servers"
BOT_OWNER = "Joseph Alekberov"

# Database configuration
DATABASE_PATH = "bot_database.db"

# AI API configuration (Using Google Gemini)
GEMINI_API_KEY = "AIzaSyAm9HeltaiakPIIL1Y8hXtJs-8Pu88p0ss"  # Google Gemini API key
GEMINI_MODEL = "gemini-2.0-flash-thinking-exp-01-21"  # Google Gemini 2.0 model
MAX_TOKENS = 750  # Increased token limit for more detailed responses
TEMPERATURE = 0.6  # Lower temperature for more focused responses
ENABLE_CACHING = True  # Enable response caching for frequently asked questions

# Response optimization
RESPONSE_TIMEOUT = 15  # Maximum seconds to wait for API response
CONCURRENT_REQUESTS = 3  # Maximum concurrent API requests

# Discord configuration
COMMAND_GUILDS = os.getenv("COMMAND_GUILDS", "").split(",") if os.getenv("COMMAND_GUILDS") else None

# News API configuration
NEWS_API_KEY = "842503d4b4114efb845986be43ad5296"

# Weather API configuration
WEATHER_API_KEY = "b4f35eb816224ee49dd82545252603"
