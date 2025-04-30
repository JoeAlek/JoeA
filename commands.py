import logging
import discord
import requests
import random
import re
import math
import time
import aiosqlite
import asyncio
from datetime import datetime
from newsapi.newsapi_client import NewsApiClient
from discord.ext import commands
from database import Database
from ai_service import AIService
from config import DATABASE_PATH
import aiohttp

logger = logging.getLogger(__name__)


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(DATABASE_PATH)
        self.ai_service = AIService()

        # Initialize NewsAPI client
        from config import NEWS_API_KEY, WEATHER_API_KEY
        self.newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        self.weather_api_key = WEATHER_API_KEY

    async def cog_load(self):
        """Called when the cog is loaded."""
        await self.db.setup()

        # Check if AI service is available
        ai_available = await self.ai_service.is_available()
        if not ai_available:
            logger.warning("AI service is not available. Chat functionality will be limited.")

    @commands.command(
        name="register",
        description="Register yourself in the bot's database"
    )
    async def register(self, ctx, *, info: str = None):
        """Register a user in the database."""
        # Send initial response
        await ctx.send("Processing registration...")

        user_id = str(ctx.author.id)
        username = ctx.author.name
        display_name = ctx.author.display_name

        # Check if user is already registered
        if await self.db.is_user_registered(user_id):
            await ctx.send("You are already registered!")
            return

        # Register the user
        success = await self.db.register_user(user_id, username, display_name, info)

        if success:
            embed = discord.Embed(
                title="Registration Successful",
                description="You have been successfully registered in the database!",
                color=discord.Color.green()
            )
            embed.add_field(name="Username", value=username, inline=True)
            embed.add_field(name="Display Name", value=display_name, inline=True)
            if info:
                embed.add_field(name="Additional Info", value=info, inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send("There was an error during registration. Please try again later.")

    @commands.command(
        name="information",
        description="Display a list of all registered users"
    )
    async def information(self, ctx):
        """Display information about registered users."""
        await ctx.send("Retrieving user information...")

        users = await self.db.get_all_users()

        if not users:
            await ctx.send("No users are registered yet.")
            return

        embed = discord.Embed(
            title="Registered Users",
            description=f"Total registered users: {len(users)}",
            color=discord.Color.blue()
        )

        # Add first 25 users to the embed (Discord has a limit)
        for i, user in enumerate(users[:25]):
            reg_date = user['registration_date'].split('T')[0] if user['registration_date'] else "Unknown"
            value = f"ID: {user['user_id']}\nRegistered: {reg_date}"
            if user['additional_info']:
                value += f"\nInfo: {user['additional_info']}"

            embed.add_field(
                name=f"{i + 1}. {user['display_name'] or user['username']}",
                value=value,
                inline=False
            )

        if len(users) > 25:
            embed.set_footer(text=f"Showing 25 out of {len(users)} users")

        await ctx.send(embed=embed)

    @commands.command(
        name="chat",
        description="Start a conversation with the AI"
    )
    async def chat(self, ctx, *, message: str):
        """Chat with the AI."""
        await ctx.send("Thinking about your request...")

        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return

        # Generate AI response
        response = await self.ai_service.generate_response(message, ctx.author.id)

        # Store the interaction in the database
        await self.db.store_chat_interaction(ctx.author.id, message, response)

        # Create embed response
        embed = discord.Embed(
            title="AI Response",
            description=response,
            color=discord.Color.purple()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.add_field(name="Your message", value=message, inline=False)

        await ctx.send(embed=embed)

    # Command to ask AI about a specific message
    @commands.command(name="ask_ai")
    async def ask_ai_context(self, ctx, message_id: str):
        """Ask AI about a specific message by providing message ID."""
        await ctx.send("Processing your request...")

        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return

        try:
            # Try to fetch the message by ID
            message = await ctx.channel.fetch_message(int(message_id))
            content = message.content

            if not content:
                await ctx.send("The specified message has no text content to analyze.")
                return

            prompt = f"Respond to this message: {content}"

            # Generate AI response
            response = await self.ai_service.generate_response(prompt, ctx.author.id)

            # Store the interaction in the database
            await self.db.store_chat_interaction(ctx.author.id, prompt, response)

            # Create embed response
            embed = discord.Embed(
                title="AI Response",
                description=response,
                color=discord.Color.purple()
            )
            embed.set_author(name=ctx.author.display_name,
                             icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            embed.add_field(name="Original message", value=content, inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error processing message: {str(e)}")

    @commands.command(name="news")
    async def news(self, ctx):
        """Provides information about an important event in the world today."""
        await ctx.send("Fetching today's news...")

        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return

        try:
            # Get top headlines using NewsAPI
            today = datetime.now().strftime('%Y-%m-%d')
            news_data = self.newsapi.get_top_headlines(
                language='en',
                page_size=5
            )

            if news_data['status'] != 'ok' or news_data['totalResults'] == 0:
                # Fallback to AI if API fails or no results
                prompt = f"Provide a short summary of ONE significant news event happening today (Date: {datetime.now().strftime('%B %d, %Y')}). Include only factual information. Format: Title, followed by 2-3 sentences of description."

                # Generate AI response
                response = await self.ai_service.generate_response(prompt, ctx.author.id)

                # Create embed response
                embed = discord.Embed(
                    title="Today's News",
                    description=response,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"News as of {datetime.now().strftime('%B %d, %Y')}")
            else:
                # Create an embed with top headlines
                embed = discord.Embed(
                    title="Today's Top Headlines",
                    description="Here are today's top news stories:",
                    color=discord.Color.blue()
                )

                # Add top stories to the embed
                for i, article in enumerate(news_data['articles'][:5]):
                    title = article['title']
                    source = article['source']['name'] if article['source'] and article['source']['name'] else "Unknown"
                    description = article['description'] or "No description available."
                    url = article['url']

                    embed.add_field(
                        name=f"{i + 1}. {title}",
                        value=f"{description}\n[Read more at {source}]({url})",
                        inline=False
                    )

                # Add image from the first article if available
                if news_data['articles'][0]['urlToImage']:
                    embed.set_image(url=news_data['articles'][0]['urlToImage'])

                embed.set_footer(text=f"News powered by NewsAPI • {datetime.now().strftime('%B %d, %Y')}")

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in news command: {e}")
            await ctx.send("Sorry, I couldn't fetch the latest news at this time.")

    @commands.command(name="tdih")
    async def today_in_history(self, ctx):
        """Shows an interesting historical event that happened on this day."""
        await ctx.send("Looking up historical events for today...")

        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return

        try:
            today = datetime.now()

            # Use AI to generate historical events for today's date as requested
            prompt = "Tell me interesting events that happened today in history."

            # Generate AI response
            response = await self.ai_service.generate_response(prompt, ctx.author.id)

            # Create embed response
            embed = discord.Embed(
                title=f"This Day in History: {today.strftime('%B %d')}",
                description=response,
                color=discord.Color.gold()
            )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in today_in_history command: {e}")
            await ctx.send("Sorry, I couldn't find historical events for today.")

    @commands.command(name="calc")
    async def calculate(self, ctx, *, expression: str):
        """Calculates the given mathematical expression."""
        try:
            # Strip any code block formatting if present
            expression = expression.strip('`')

            # Simple sanitization to prevent code execution
            # Only allow: digits, operators +,-,*,/,^,%, parentheses, and decimal points
            if not re.match(r'^[\d\+\-\*\/\^\%\(\)\.\s]+$', expression):
                await ctx.send("Invalid expression. Only basic mathematical operations are allowed.")
                return

            # Replace ^ with ** for exponentiation
            expression = expression.replace('^', '**')

            # Safe evaluation of the expression
            result = eval(expression)

            embed = discord.Embed(
                title="Calculator",
                description=f"Expression: `{expression}`\nResult: `{result}`",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error calculating result: {str(e)}")


    @commands.command(name="weather")
    async def weather(self, ctx, *, city: str):
        """Shows the real-time weather for the given city using WeatherAPI."""
        await ctx.send(f"Fetching real-time weather for `{city}`...")

        WEATHER_API_KEY = "b4f35eb816224ee49dd82545252603"
        WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json"

        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return

        try:
            params = {
                "key": WEATHER_API_KEY,
                "q": city,
                "aqi": "no"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(WEATHER_API_URL, params=params) as resp:
                    if resp.status != 200:
                        await ctx.send("⚠️ Couldn't retrieve weather data. Please try again later.")
                        return

                    data = await resp.json()
                    location = data["location"]["name"]
                    country = data["location"]["country"]
                    temp_c = data["current"]["temp_c"]
                    condition = data["current"]["condition"]["text"]
                    icon_url = "https:" + data["current"]["condition"]["icon"]
                    humidity = data["current"]["humidity"]

                    embed = discord.Embed(
                        title=f"🌤️ Weather in {location}, {country}",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Temperature", value=f"{temp_c} °C", inline=True)
                    embed.add_field(name="Condition", value=condition, inline=True)
                    embed.add_field(name="Humidity", value=f"{humidity}%", inline=True)
                    embed.set_thumbnail(url=icon_url)
                    embed.set_footer(text="Powered by WeatherAPI.com")

                    await ctx.send(embed=embed)


        except Exception as e:

            await ctx.send(f"❌ Error: {str(e)}")  # Hata detayını kullanıcıya göster

            logger.error(f"Error in weather command: {e}")

    @commands.command(name="info")
    async def info(self, ctx):
        """Alias for the information command - displays a list of registered users."""
        await self.information(ctx)

    @commands.command(name="commands")
    async def help_command(self, ctx):
        """Shows all commands and their descriptions."""
        embed = discord.Embed(
            title="JoeA Bot Commands",
            description="Here are all available commands:",
            color=discord.Color.blue()
        )

        # General commands embed
        general_embed = discord.Embed(
            title="General Commands",
            description="Commands everyone can use:",
            color=discord.Color.green()
        )

        general_commands = [
            ("/register [info]", "Registers you in the bot's database with optional info"),
            ("/news", "Provides information about an important world event today"),
            ("/tdih", "Today in history: Shows a historical event that happened on this day"),
            ("/calc [expression]", "Calculates the given mathematical expression"),
            ("/weather [city]", "Shows the weather for the specified city"),
            ("/info", "Displays the list of registered users"),
            ("/chat [message]", "Chat with the AI"),
            ("/help", "Shows this help message"),
            ("/translate [language] [text]", "Translates the text to the specified language"),
            ("/profile", "Displays your profile information"),
            ("/fact", "Shows an interesting random fact"),
            ("/serverinfo", "Displays detailed information about the server")
        ]

        for cmd, desc in general_commands:
            general_embed.add_field(name=cmd, value=desc, inline=False)

        # Moderation commands embed
        mod_embed = discord.Embed(
            title="Moderation Commands",
            description="Admin-only commands:",
            color=discord.Color.red()
        )

        mod_commands = [
            ("/ban [user_id] [reason]", "Bans the user from the server (requires ban permission)"),
            ("/unban [user_id]", "Removes the ban on the user (requires ban permission)"),
            ("/kick [user] [reason]", "Kicks the user from the server (requires kick permission)"),
            ("/slowmode [seconds]", "Sets slowmode delay for the channel (requires manage channels)"),
            ("/rerole [user] [role]", "Removes a specific role from the user (requires manage roles)"),
            ("/role [user] [role]", "Adds or removes a role from the specified user (requires manage roles)"),
            ("/clear [number]", "Deletes the specified number of recent messages (requires manage messages)"),
            ("/warn [user] [reason] "," Issues a warning to the user."),
            ("/warnings [user] "," Displays all warnings received by the user."),
            ("/clearwarn [user] "," Clears all warnings for the user."),
            ("/slowmode [seconds] "," Sets a slow mode restriction in the channel."),
            ("/nick [user] [new name] "," Changes the user's nickname."),
            ("/antiraid on/off "," Prevents mass bot joining in the server."),
            ("/lock [channel] "," Locks the channel, preventing messages from being sent."),
            ("/unlock [channel] "," Unlocks the channel."),
            ("/mute [user] [duration] [reason] "," Mutes the user for a specified time."),
            ("/unmute [user] "," Unmutes the muted user."),
            ("/temprole [user] [role] [duration] "," Assigns a temporary role to a user."),
            ("/modlogs "," Displays recent moderation actions."),
            ("/massban [users] "," Bans multiple users at once."),
            ("/servermute [user] "," Mutes the user in all voice channels."),
            ("/unservermute [user] "," Unmutes the user in voice channels.")
        ]

        for cmd, desc in mod_commands:
            mod_embed.add_field(name=cmd, value=desc, inline=False)


        emod_embed = discord.Embed(
            title="Moderation Commands ",
            description="Moderation Commands that everyone can use:",
            color=discord.Color.blue()
        )


        emod_commands=[
             ("/report [user] [reason] ", " Reports a rule violation to moderators.")
        ]

        for cmd, desc in emod_commands:
            emod_embed.add_field(name=cmd, value=desc, inline=False)


        # Send both embeds
        await ctx.send(embed=general_embed)
        await ctx.send(embed=mod_embed)
        await ctx.send(embed=emod_embed)

    @commands.command(name="translate")
    async def translate(self, ctx, language: str, *, text: str):
        """Translates the given text to the specified language."""
        await ctx.send(f"Translating to {language}...")

        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return

        try:
            # Use AI to translate the text
            prompt = f"Translate the following text to {language}. Only respond with the translation, nothing else:\n\n{text}"

            # Generate AI response (translation)
            response = await self.ai_service.generate_response(prompt, ctx.author.id)

            # Create embed response
            embed = discord.Embed(
                title=f"Translation to {language}",
                color=discord.Color.green()
            )
            embed.add_field(name="Original Text", value=text, inline=False)
            embed.add_field(name="Translation", value=response, inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in translate command: {e}")
            await ctx.send("Sorry, I couldn't translate the text at this time.")

    @commands.command(name="profile")
    async def profile(self, ctx):
        """Displays the user's profile information."""
        user_id = str(ctx.author.id)

        # Check if user is registered
        if not await self.db.is_user_registered(user_id):
            await ctx.send("You need to register first using `!register`!")
            return

        try:
            # Get user data from database
            users = await self.db.get_all_users()
            user_data = None

            for user in users:
                if user['user_id'] == user_id:
                    user_data = user
                    break

            if not user_data:
                await ctx.send("Could not find your profile data.")
                return

            # Create embed for profile
            embed = discord.Embed(
                title=f"{ctx.author.display_name}'s Profile",
                color=discord.Color.purple()
            )

            reg_date = user_data['registration_date'].split('T')[0] if user_data['registration_date'] else "Unknown"

            embed.add_field(name="Username", value=user_data['username'], inline=True)
            embed.add_field(name="Display Name", value=user_data['display_name'], inline=True)
            embed.add_field(name="Registered On", value=reg_date, inline=True)

            if user_data['additional_info']:
                embed.add_field(name="Additional Info", value=user_data['additional_info'], inline=False)

            # Set user avatar as thumbnail if available
            if ctx.author.avatar:
                embed.set_thumbnail(url=ctx.author.avatar.url)

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in profile command: {e}")
            await ctx.send("Sorry, I couldn't retrieve your profile at this time.")

    @commands.command(name="role")
    @commands.has_permissions(administrator=True)
    async def role(self, ctx, member: discord.Member, *, role_name: str):
        """Adds or removes a role from the specified user (admin only)."""
        try:
            # Find the role by name
            role = discord.utils.get(ctx.guild.roles, name=role_name)

            if not role:
                await ctx.send(f"Role '{role_name}' not found.")
                return

            # Check if user already has the role
            if role in member.roles:
                # Remove role
                await member.remove_roles(role)
                await ctx.send(f"Removed role '{role_name}' from {member.display_name}.")
            else:
                # Add role
                await member.add_roles(role)
                await ctx.send(f"Added role '{role_name}' to {member.display_name}.")

        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except Exception as e:
            logger.error(f"Error in role command: {e}")
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="fact")
    async def fact(self, ctx):
        """Shows an interesting random fact."""
        await ctx.send("Generating an interesting fact...")

        # Check if user is registered
        if not await self.db.is_user_registered(ctx.author.id):
            await ctx.send("You need to register first using `!register`!")
            return

        try:
            # Use AI to generate a random fact
            prompt = "Share one interesting, different and unusual fact about anything (science, history, animals, etc.). Keep it brief (1-3 sentences) and make sure it's accurate. Don't include any introduction or conclusion text."

            # Generate AI response
            response = await self.ai_service.generate_response(prompt, ctx.author.id)

            # Create embed response
            embed = discord.Embed(
                title="Random Fact",
                description=response,
                color=discord.Color.gold()
            )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in fact command: {e}")
            await ctx.send("Sorry, I couldn't generate a fact at this time.")

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Deletes the specified number of recent messages (admin only)."""
        if amount <= 0:
            await ctx.send("Please provide a positive number of messages to delete.")
            return

        if amount > 100:
            await ctx.send("You can only delete up to 100 messages at once.")
            return

        try:
            # Delete messages
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message

            await ctx.send(f"Deleted {len(deleted) - 1} messages.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")
        except discord.HTTPException as e:
            await ctx.send(f"Error deleting messages: {str(e)}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user_id: int, *, reason=None):
        """Bans the user from the server."""
        try:
            # Fetch user by ID
            user = await self.bot.fetch_user(user_id)
            if user:
                await ctx.guild.ban(user, reason=reason)
                ban_message = f"User {user.name}#{user.discriminator} (ID: {user_id}) has been banned."
                if reason:
                    ban_message += f" Reason: {reason}"
                await ctx.send(ban_message)
            else:
                await ctx.send(f"Could not find user with ID {user_id}.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban members.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while banning the user: {str(e)}")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """Removes the ban on the user."""
        try:
            # Fetch user by ID
            user = await self.bot.fetch_user(user_id)
            if user:
                await ctx.guild.unban(user)
                await ctx.send(f"User {user.name}#{user.discriminator} (ID: {user_id}) has been unbanned.")
            else:
                await ctx.send(f"Could not find user with ID {user_id}.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to unban members.")
        except discord.NotFound:
            await ctx.send(f"User with ID {user_id} is not banned.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while unbanning the user: {str(e)}")

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        """Kicks the user from the server."""
        try:
            await user.kick(reason=reason)
            kick_message = f"User {user.name}#{user.discriminator} has been kicked."
            if reason:
                kick_message += f" Reason: {reason}"
            await ctx.send(kick_message)
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick members.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while kicking the user: {str(e)}")

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        """Sets how many seconds users must wait before sending another message."""
        if seconds < 0 or seconds > 21600:
            await ctx.send("Slowmode delay must be between 0 and 21600 seconds (6 hours).")
            return

        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                await ctx.send("Slowmode has been disabled for this channel.")
            else:
                await ctx.send(f"Slowmode set to {seconds} seconds for this channel.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to modify this channel.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while setting slowmode: {str(e)}")

    @commands.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, user: discord.Member, *, reason: str):
        """Issues a warning to the user."""
        try:
            async with aiosqlite.connect(self.db.db_path) as db:
                await db.execute(
                    "INSERT INTO warnings (user_id, reason, timestamp, moderator_id) VALUES (?, ?, ?, ?)",
                    (str(user.id), reason, datetime.now().isoformat(), str(ctx.author.id))
                )
                await db.commit()

            embed = discord.Embed(
                title="⚠️ Uyarı Verildi",
                color=discord.Color.orange()
            )
            embed.add_field(name="user", value=f"{user.mention}", inline=True)
            embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
            embed.add_field(name="Reson", value=reason, inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Uyarı verilirken bir hata oluştu: {str(e)}")

    @commands.command(name="warnings")
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, user: discord.Member):
        """Displays all warnings for a user."""
        async with aiosqlite.connect(self.db.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM warnings WHERE user_id = ?", (str(user.id),))
            warnings = await cursor.fetchall()

        if not warnings:
            await ctx.send(f"{user.mention} has no warnings.")
            return

        embed = discord.Embed(title=f"Warnings for {user.name}", color=discord.Color.yellow())
        for warn in warnings:
            embed.add_field(
                name=f"Warning {warn['id']}",
                value=f"Reason: {warn['reason']}\nDate: {warn['timestamp'].split('T')[0]}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="clearwarn")
    @commands.has_permissions(kick_members=True)
    async def clearwarn(self, ctx, user: discord.Member):
        """Clears all warnings for a user."""
        async with aiosqlite.connect(self.db.db_path) as db:
            await db.execute("DELETE FROM warnings WHERE user_id = ?", (str(user.id),))
            await db.commit()
        await ctx.send(f"✅ Cleared all warnings for {user.mention}")

    @commands.command(name="nick")
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, user: discord.Member, *, new_name: str):
        """Changes the user's nickname."""
        try:
            await user.edit(nick=new_name)
            await ctx.send(f"✅ Changed {user.name}'s nickname to {new_name}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to change that user's nickname.")

    @commands.command(name="antiraid")
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx, mode: str):
        """Enables/disables anti-raid mode."""
        mode = mode.lower()
        if mode not in ['on', 'off']:
            await ctx.send("Please specify either 'on' or 'off'")
            return

        verification_level = discord.VerificationLevel.high if mode == 'on' else discord.VerificationLevel.low
        await ctx.guild.edit(verification_level=verification_level)
        await ctx.send(f"Anti-raid mode has been turned {mode}.")

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Locks the specified channel."""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"🔒 {channel.mention} has been locked.")

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlocks the specified channel."""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"🔓 {channel.mention} has been unlocked.")

    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, user: discord.Member, duration: str, *, reason: str = None):
        """Mutes a user for the specified duration."""
        # Convert duration string to seconds
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        amount = int(duration[:-1])
        unit = duration[-1].lower()

        if unit not in time_units:
            await ctx.send("Invalid duration format. Use s/m/h/d for units (e.g., 30s, 5m, 1h, 1d)")
            return

        seconds = amount * time_units[unit]

        # Create muted role if it doesn't exist
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted", reason="Mute command setup")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)

        await user.add_roles(muted_role, reason=reason)
        await ctx.send(f"🔇 {user.mention} has been muted for {duration}. Reason: {reason}")

        # Unmute after duration
        await asyncio.sleep(seconds)
        if muted_role in user.roles:
            await user.remove_roles(muted_role)
            await ctx.send(f"🔊 {user.mention} has been automatically unmuted.")

    @commands.command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, user: discord.Member):
        """Unmutes a muted user."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            await ctx.send("No muted role found.")
            return

        if muted_role not in user.roles:
            await ctx.send(f"{user.mention} is not muted.")
            return

        await user.remove_roles(muted_role)
        await ctx.send(f"🔊 {user.mention} has been unmuted.")

    @commands.command(name="temprole")
    @commands.has_permissions(manage_roles=True)
    async def temprole(self, ctx, user: discord.Member, role: discord.Role, duration: str):
        """Assigns a temporary role to a user."""
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        amount = int(duration[:-1])
        unit = duration[-1].lower()

        if unit not in time_units:
            await ctx.send("Invalid duration format. Use s/m/h/d for units (e.g., 30s, 5m, 1h, 1d)")
            return

        seconds = amount * time_units[unit]

        await user.add_roles(role)
        await ctx.send(f"Added role {role.name} to {user.mention} for {duration}")

        await asyncio.sleep(seconds)
        if role in user.roles:
            await user.remove_roles(role)
            await ctx.send(f"Removed temporary role {role.name} from {user.mention}")

    @commands.command(name="report")
    async def report(self, ctx, user: discord.Member, *, reason: str):
        """Reports a user to moderators."""
        # Find mod log channel
        mod_channel = discord.utils.get(ctx.guild.channels, name="mod-logs")
        if not mod_channel:
            mod_channel = await ctx.guild.create_text_channel("mod-logs")

        embed = discord.Embed(title="User Report", color=discord.Color.red())
        embed.add_field(name="Reported User", value=f"{user.mention} ({user.id})", inline=False)
        embed.add_field(name="Reported By", value=f"{ctx.author.mention} ({ctx.author.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Channel", value=ctx.channel.mention, inline=False)
        embed.timestamp = datetime.utcnow()

        await mod_channel.send(embed=embed)
        await ctx.send("✅ Report has been sent to moderators.", delete_after=5)
        await ctx.message.delete()

    @commands.command(name="modlogs")
    @commands.has_permissions(view_audit_log=True)
    async def modlogs(self, ctx):
        """Displays recent moderation actions."""
        async with aiosqlite.connect(self.db.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM moderation_logs ORDER BY timestamp DESC LIMIT 10"
            )
            logs = await cursor.fetchall()

        if not logs:
            await ctx.send("No moderation logs found.")
            return

        embed = discord.Embed(title="Recent Moderation Actions", color=discord.Color.blue())
        for log in logs:
            embed.add_field(
                name=f"{log['action_type']} - {log['timestamp'].split('T')[0]}",
                value=f"User: <@{log['user_id']}>\nModerator: <@{log['moderator_id']}>\nReason: {log['reason']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="massban")
    @commands.has_permissions(ban_members=True)
    async def massban(self, ctx, users: commands.Greedy[discord.User]):
        """Bans multiple users at once."""
        if not users:
            await ctx.send("Please specify at least one user to ban.")
            return

        success = []
        failed = []
        for user in users:
            try:
                await ctx.guild.ban(user)
                success.append(user.name)
            except:
                failed.append(user.name)

        message = []
        if success:
            message.append(f"Successfully banned: {', '.join(success)}")
        if failed:
            message.append(f"Failed to ban: {', '.join(failed)}")
        await ctx.send("\n".join(message))

    @commands.command(name="servermute")
    @commands.has_permissions(mute_members=True)
    async def servermute(self, ctx, user: discord.Member):
        """Mutes the user in all voice channels."""
        await user.edit(mute=True)
        await ctx.send(f"🔇 {user.mention} has been server muted.")

    @commands.command(name="unservermute")
    @commands.has_permissions(mute_members=True)
    async def unservermute(self, ctx, user: discord.Member):
        """Unmutes the user in voice channels."""
        await user.edit(mute=False)
        await ctx.send(f"🔊 {user.mention} has been server unmuted.")

    @commands.command(name="rerole")
    @commands.has_permissions(manage_roles=True)
    async def rerole(self, ctx, user: discord.Member, *, role_name: str):
        """Removes a specific role from the user."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"Role '{role_name}' not found in this server.")
            return

        try:
            if role in user.roles:
                await user.remove_roles(role)
                await ctx.send(f"Removed role '{role_name}' from {user.name}#{user.discriminator}.")
            else:
                await ctx.send(f"{user.name}#{user.discriminator} doesn't have the role '{role_name}'.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while removing the role: {str(e)}")

    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx):
        """Displays server information including name, ID, owner, creation date, members, roles, and bot website."""
        guild = ctx.guild

        # Format creation time
        created_at = guild.created_at.strftime("%B %d, %Y")

        # Get owner
        owner = guild.owner

        # Create embed with server info
        embed = discord.Embed(
            title=f"{guild.name} Server Information",
            color=discord.Color.blue()
        )

        # Add server icon if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Add fields with server details
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=f"{owner.name}#{owner.discriminator}" if owner else "Unknown", inline=True)
        embed.add_field(name="Created On", value=created_at, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)

        # Add bot website link
        embed.add_field(name="Bot Website", value="[Visit JoeA Website](https://joea-bot.replit.app)", inline=False)

        # Set footer with timestamp
        embed.set_footer(text=f"Requested by {ctx.author.name}",
                         icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.timestamp = datetime.utcnow()

        await ctx.send(embed=embed)

    # Error handlers for missing permissions
    @role.error
    async def role_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need administrator permissions to use this command.")

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need manage messages permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the number of messages to delete.")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need ban members permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the user ID to ban.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid user ID (numbers only).")

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need ban members permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the user ID to unban.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid user ID (numbers only).")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need kick members permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the user to kick.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Could not find that user. Please mention a user or provide a valid user ID.")

    @slowmode.error
    async def slowmode_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need manage channels permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the slowmode delay in seconds.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid number of seconds.")

    @rerole.error
    async def rerole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need manage roles permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            if "user" in str(error):
                await ctx.send("Please specify the user to remove a role from.")
            else:
                await ctx.send("Please specify the role name to remove.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Could not find that user. Please mention a user or provide a valid user ID.")
