📌 Project Name: JoeA


💡 Project Goal:

This project is to create a bot that answers users' questions on the Discord platform, using artificial intelligence. The bot works in any channel and returns answers according to the message written by the user.


💡Deploying the bot to the server:

If you want to place the bot on any Discord server, open the html, css, js codes along with the python codes in the VS code program. (Jinja was used when writing the site codes. Therefore, after placing the codes in the VS code program, download Better Jinja from the Extensions section). Then, after writing cd in the terminal, write the path where the file is located. For example, "cd c:\Users\localadmin\Desktop\Discord_bot_projesi\DiscordAssistant". After writing this, write "python app.py". You should get a link like "http://192.168.100.11:5000" or something similar. After you paste this link into your browser, you should see the website I created. Click "Add to Discord". And now you can place the bot on the server you want to host.I am confident that I will enhance my skills and improve the quality of my project in the future.

OR

You can create a new bot by logging into the Discord developer portal. Follow the steps below:
1)Go to the Discord Developer Portal:
Link: https://discord.com/developers/applications
Log in with your Discord account.
2)Create a new application:
Click the “New Application” button at the top right.
Give your application a name (e.g., “JoeA”) and click Create.
3)Create the bot:
In the left-hand menu, go to the “Bot” tab.
Click “Add Bot”, then confirm with “Yes, do it!”.
You can change the bot's name and profile picture if you want
4)Get the token:
On the same page, find the “Token” section.
Click “Reset Token” (if needed), then “Copy” to get your token.
You have created the Token. Now you need to copy this Token and paste it into the .env file.


💡Activating the bot:

To activate the bot, open all python files in VS code. In the terminal, type cd (write the path to the code location). For example: c:\Users\localadmin\Desktop\Discord_bot_project\DiscordAssistant). Then, just type "python main.py".

🔧 Technologies and Libraries Used:

The following Python libraries were used in the project:

aiohttp>=3.9.1 # To send asynchronous HTTP requests

aiosqlite>=0.21.0 # To work asynchronously with SQLite databases

discord.py>=2.3.2 # To create a Discord bot

python-dotenv>=1.0.1 # To read hidden parameters (token, db URL, etc.) from the .env file

flask>=3.0.2 # To create a simple web server (for example, to control the bot via the web)

google-generativeai>=0.3.2 # To use Google AI services (AI-based responses, etc.)

newsapi-python>=0.2.7 # To pull news data from NewsAPI

requests>=2.32.3 # To send simple requests to HTTP APIs

All of this is listed in the requirements.txt file. To install, simply type the following command in the terminal:

pip install -r requirements.txt


🛠️ Installation Guide:

Download the project files from GitHub or in ZIP format.

In the terminal, go to the project folder.

Install the required libraries:

pip install -r requirements.txt

Open the .env file:

DISCORD_BOT_TOKEN=here_discord_token


🤖 Main Features of the bot:

Message Responder: Analyzes questions written by the user and responds using the Gemini API.

Keyword Search: Returns answers matching specific keywords.

Differentiation of different users: Each user is identified by their Discord ID and responses can be personalized accordingly.

Commands:

Commands everyone can use:

1)/register [info]
Registers you in the bot's database with optional info

2)/news
Provides information about an important world event today

3)/tdih
Today in history: Shows a historical event that happened on this day

4)/calc [expression]
Calculates the given mathematical expression

5)/weather [city]
Shows the weather for the specified city

6)/info
Displays the list of registered users

7)/chat [message]
Chat with the AI

8)/help
  Shows this help message

9)/translate [language] [text]
  Translates the text to the specified language

10)/profile
  Displays your profile information

11)/fact
  Shows an interesting random fact

12)/serverinfo
  Displays detailed information about the server

Moderation Commands:

Admin-only commands:

13)/ban [user_id] [reason]
  Bans the user from the server (requires ban permission)

14)/unban [user_id]
  Removes the ban on the user (requires ban permission)

15)/kick [user] [reason]
  Kicks the user from the server (requires kick permission)

16)/slowmode [seconds]
  Sets slowmode delay for the channel (requires manage channels)

17)/rerole [user] [role]
  Removes a specific role from the user (requires manage roles)

18)/role [user] [role]
  Adds or removes a role from the specified user (requires manage roles)

19)/clear [number]
  Deletes the specified number of recent messages (requires manage messages)

20)/warn [user] [reason]
  Issues a warning to the user.

21)/warnings [user]
  Displays all warnings received by the user.

22)/clearwarn [user]
  Clears all warnings for the user.

23)/nick [user] [new name]
  Changes the user's nickname.

24)/antiraid on/off
  Prevents mass bot joining in the server.

25)/lock [channel]
  Locks the channel, preventing messages from being sent.

26)/unlock [channel]
  Unlocks the channel.

27)/mute [user] [duration] [reason]
  Mutes the user for a specified time.

28)/unmute [user]
  Unmutes the muted user.

29)/temprole [user] [role] [duration]
  Assigns a temporary role to a user.

30)/report [user] [reason]
  Reports a rule violation to moderators.

31)/modlogs
  Displays recent moderation actions.

32)/massban [users]
  Bans multiple users at once.

33)/checkperms [user]
  Shows the user's permissions.

34)/servermute [user]
  Mutes the user in all voice channels.

35)/unservermute [user]
  Unmutes the user in voice channels.

📁 File Structure Explanation:

1)bot.py: Contains the main class of the Discord bot. The bot uses the discord.py library to communicate with the Discord Token. It processes commands, automatically modifies status messages, and sends greeting messages when connecting to servers.

2)commands.py: A large file containing all the commands of the bot. Commands include user registration, AI chat, weather information, calculator, news, translation, moderation commands (kick, ban, slowmode), and other functionalities.

3)ai_service.py: Communicates with the Google Gemini API and provides the AI ​​functionality of the bot. It has a caching system for queries and handles API requests.

4)database.py: Manages the connection to the SQLite database. It stores user data and chat history.

Web Interface Components:

5)app.py: Creates a web interface for the bot using Flask. It provides various pages (homepage, features, about, status, list of commands) and API status.

6)convert_to_static.py: Converts Flask templates to static HTML files so they can be hosted on a platform like GitHub Pages.

Configuration and Executable Files:

7)config.py: Stores configuration settings for the bot - API keys, bot name, command prefix, database path and other settings.

8)main.py: The entry point of the project. It starts the bot and configures the log settings.

9)layout.html - This is the main layout file for all pages. All pages use this main template. Here:
The general structure of the website: header, main content and footer
Navbar with links to Home, Features, About us
Button to add to Discord
Adding external styles such as Bootstrap and Font Awesome

10)index.html - The main (home) page of the site. It includes:

Introduction section showing the main features of the bot
Card section showing the advantages of the bot (AI chat, moderation, user analytics)
List of popular commands
Call button to add to Discord

11)features.html - A demo of the server control panel, showing the bot's functionality. Here:

Shows features such as general settings, moderation, user onboarding, and automatic role assignment
Demonstrates how users can configure their servers
Different settings for each feature and functional elements for changing settings

12)commands.html - A page showing all available commands of the bot:

List of general commands
List of moderation commands
Information about the use of commands
Section showing command categories (for user management, AI interaction, utilities, and moderation)

13)about.html - Information about the bot and its creator:

JoeA's story
Bot's mission and purpose
Information about the creator (Joseph Alakbarov)
Technologies used by the bot (Gemini AI and Discord API)

14)bot_database.db – Bot Database
This file is a database in SQLite format used to store the bot's data. It serves the following purposes:

User data – stores user IDs, names, and interactions with the bot
Command logs – used to track user activities bot_database.db – Bot Database
This file is a database in SQLite format used to store the bot's data. It serves the following purposes:
User data – stores user IDs, names, and interactions with the bot
Command logs – used to track user activities
