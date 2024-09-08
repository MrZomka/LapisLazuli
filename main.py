import json
import disnake
from disnake.ext import commands

bot = commands.InteractionBot()

@bot.event
async def on_ready():
    print("The bot is ready!")

bot.load_extension("cogs.music")

with open('config.json') as f:
    config = json.load(f)

bot.run(config.get('token'))