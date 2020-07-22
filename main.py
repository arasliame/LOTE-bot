import os
from dotenv import load_dotenv
from discord.ext import commands
import logging
from lotehelpers import matchabbr

'''
directory = os.path.dirname(__file__)
fullpath = os.path.abspath(os.path.join(directory, "info.log"))
logging.basicConfig(level=logging.WARNING,
                    format=f'(%(asctime)s) %(levelname)s:%(name)s:%(message)s',
                    datefmt=f'%Y-%m-%d %H:%M:%S',
                    filename=fullpath)
'''

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='.')

'''
@bot.event
async def on_command_error(self, ctx,error):
    logging.error(f"Unhandled message: {error}. Command: {ctx.command}. Args: {ctx.args}")
'''
@bot.event
async def on_ready():
    readystr = f'{bot.user.name} has connected to Discord!'
    print(readystr)
    logging.info(readystr)
    bot.load_extension('lotebotclass')
    bot.load_extension('fiascobotclass')
     # add command to toggle game?
'''
@bot.commands(name='setgame', help='Play Legend of the Elements or Fiasco.')
async def setgame(ctx,game='both'):
    game = matchabbr(game,['both','lote','legendofthelements'])
    if game == 'lote'
'''
if __name__ == "__main__":
    bot.run(TOKEN)
    