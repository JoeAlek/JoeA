from flask import Flask, render_template, jsonify, redirect, url_for
import os
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/features')
def features():
    return render_template('features.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/commands')
def command_list():
    general_commands = [
        {"name": "/register [info]","description": "Register yourself with the bot with optional additional information"},
        {"name": "/chat [message]", "description": "Start a conversation with the AI"},
        {"name": "/news", "description": "Get information about an important world event today"},
        {"name": "/tdih", "description": "Shows a historical event that happened on this day"},
        {"name": "/calc [expression]", "description": "Calculate mathematical expressions"},
        {"name": "/weather [city]", "description": "Get current weather for any city"},
        {"name": "/translate [language] [text]", "description": "Translate text to another language"},
        {"name": "/fact", "description": "Get an interesting random fact"},
        {"name": "/profile", "description": "View your profile information"},
        {"name": "/info", "description": "List all registered users"},
        {"name": "/commands", "description": "Show all available commands"},
        {"name": "/serverinfo", "description": "Display detailed information about the server"}
    ]

    moderation_commands = [
        {"name": "/ban [user_id] [reason]", "description": "Ban a user from the server (requires ban permission)"},
        {"name": "/unban [user_id]", "description": "Remove a ban from a user (requires ban permission)"},
        {"name": "/kick [user] [reason]", "description": "Kick a user from the server (requires kick permission)"},
        {"name": "/slowmode [seconds]", "description": "Set slowmode delay for the channel (requires manage channels)"},
        {"name": "/rerole [user] [role]", "description": "Remove a specific role from a user (requires manage roles)"},
        {"name": "/role [user] [role]", "description": "Add or remove roles from a user (requires manage roles)"},
        {"name": "/clear [amount]", "description": "Delete recent messages (requires manage messages)"},
        {"name": "/warn [user] [reason]","description":"Issues a warning to the user."},
        {"name": "/warnings [user]","description":"Displays all warnings received by the user."},
        {"name": "/clearwarn [user]", "description": "Clears all warnings for the user."},
        {"name": "/nick [user] [new name]", "description": "Changes the user's nickname."},
        {"name": "/antiraid on/off", "description": "Prevents mass bot joining in the server."},
        {"name": "/lock [channel]", "description": "Locks the channel, preventing messages from being sent."},
        {"name": "/unlock [channel]", "description": "Unlocks the channel."},
        {"name": "/mute [user] [duration] [reason]", "description": "Mutes the user for a specified time."},
        {"name": "/unmute [user]", "description": "Unmutes the muted user."},
        {"name": "/temprole [user] [role] [duration]", "description": "Assigns a temporary role to a user."},
        {"name": "/report [user] [reason]", "description": "Reports a rule violation to moderators."},
        {"name": "/modlogs", "description": "Displays recent moderation actions."},
        {"name": "/massban [users]", "description": "Bans multiple users at once."},
        {"name": "/servermute [user]", "description": "Mutes the user in all voice channels."},
        {"name": "/unservermute [user]", "description": "Unmutes the user in voice channels."}
    ]

    return render_template('commands.html', general_commands=general_commands, moderation_commands=moderation_commands)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)