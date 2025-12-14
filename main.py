import os
import discord
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from datetime import datetime, date
import pytz
import random
from typing import Optional

load_dotenv()
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")
users = {}
last_selected: dict[str, Optional[date | int]] = {
    'user_id': None,
    'date': None
}


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
        hourly_check.start()
        print("Hourly check command started")
    except Exception as e:
        print(f"Failed to sync")
    print(f"{bot.user} has restarted!")


@bot.tree.command(name="add", description="Add a user to be in the Niche Wordle rotation")
@app_commands.describe(
    user="The user to add into the Niche Wordle rotation",
    timezone="Select their timezone"
)
@app_commands.choices(timezone=[
    app_commands.Choice(name="Pacific (PST/PDT)", value="America/Los_Angeles"),
    app_commands.Choice(name="Mountain (MST/MDT", value="America/Denver"),
    app_commands.Choice(name="Central (CST/CDT)", value="America/Chicago"),
    app_commands.Choice(name="Eastern (EST/EDT)", value="America/New_York")
])
async def add(interaction: discord.Interaction, user: discord.User, timezone: str):
    users[user.id] = {'name': user.name, 'timezone': timezone}
    await interaction.response.send_message(
        f"{user.mention} was added to Niche Wordle rotation with timezone: {timezone}"
    )


@bot.tree.command(name="remove", description="Remove a user from the Niche Wordle rotation")
@app_commands.describe(
    user="The user to remove from the Niche Wordle rotation"
)
async def remove(interaction: discord.Interaction, user: discord.User):
    removedUser = users.pop(user.id, None)
    if removedUser is None:
        await interaction.response.send_message(
            f"{user.mention} is not participating in the Niche Wordle rotation"
        )
    else:
        await interaction.response.send_message(
            f"{user.mention} was removed from Niche Wordle rotation"
        )


@bot.tree.command(name="list", description="List all users in the Niche Wordle rotation")
async def list_users(interaction: discord.Interaction):
    await interaction.response.defer()
    if not users:
        await interaction.followup.send(
            "There are no users in the Niche Wordle rotation."
        )
    else:
        user_list = "\n".join(
            f"{user['name']} - {user['timezone']}"
            for user in users.values()
        )
        await interaction.followup.send(user_list)


@bot.tree.command(name="test")
@app_commands.describe(
    user="The user"
)
async def test(interaction: discord.Interaction, user: discord.User):
    await hourly_check()
    await interaction.response.send_message("Message sent")


@tasks.loop(minutes=1)
async def hourly_check():
    if not users:
        print("There are no users in the Niche Wordle rotation.")
        return

    now = datetime.now()
    today = now.date()
    if last_selected['date'] == today:
        return

    print(now.hour, now.minute, now.second)
    if now.minute == 59:
        userId = random.choice(list(users.keys()))
        relativeTime = datetime.now(pytz.timezone(users[userId]['timezone']))
        if relativeTime == 23:
            try:
                user = await bot.fetch_user(userId)
                last_selected['user_id'] = userId
                last_selected['date'] = today
                await user.send("Your Niche")
                print(f"Selected {users[userId]}")
            except Exception as e:
                print(f"Error: {e}")


@bot.tree.command(name="random", description="Get a random valid Wordle word")
async def random_generate_word(interaction: discord.Interaction):
    with open('possible_answers.txt', 'r') as f:
        words = [line.strip() for line in f]

    randomWord = random.choice(words)
    msg = f"Your random Wordle word is {randomWord}"
    await interaction.response.send_message(msg)


bot.run(TOKEN)
