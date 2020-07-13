import os
from dotenv import load_dotenv
from discord.ext import commands
from fileops import loadvarsfromfiles,savechardata
from mischelpers import matchabbr,botgetcharinfo,botcharmove,botrollint,botrollstring
import logging

directory = os.path.dirname(__file__)
fullpath = os.path.abspath(os.path.join(directory, "info.log"))
logging.basicConfig(level=logging.WARNING,
                    format=f'(%(asctime)s) %(levelname)s:%(name)s:%(message)s',
                    datefmt=f'%Y-%m-%d %H:%M:%S',
                    filename=fullpath)


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='.')

@bot.event
async def on_command_error(ctx,error):
    logging.error(f"Unhandled message: {error}. Command: {ctx.command}. Args: {ctx.args}")

@bot.event
async def on_ready():
    readystr = f'{bot.user.name} has connected to Discord!'
    print(readystr)
    logging.info(readystr)

# roll based on character sheet or roll with a modifier depending on user input
@bot.command(name='r', help='Roll 2d6 plus a stat or numeric modifier. By default, use the character your Discord user is associated with, or specify a specific character.')
async def botroll(ctx, stat=None, character="user"):
    
    character = matchabbr(character,charabbrs)
    charinfo,response = botgetcharinfo(ctx,character,chardata)
    
    if response:
        await ctx.send(response)
    else:
        try:
            mod = int(stat)
            response = botrollint(ctx,mod,charinfo)
        except ValueError:
            stat = matchabbr(stat,statabbrs)
            if stat not in allstats:
                response = f'{ctx.message.author.mention}: Invalid stat, try again.'
            else:
                response = botrollstring(ctx,stat,charinfo)
        except TypeError:
            response = "Stat/modifier cannot be empty, try again."
        await ctx.send(response)

@bot.command(name='m', help='Do a specific move. By default, use the character your Discord user is associated with, or specify a character to roll for.')
async def rollformove(ctx,move=None,character="user"):
    move = matchabbr(move,moveabbrs)
    character = matchabbr(character,charabbrs)

    if move not in allmoves:
        response = f'{ctx.message.author.mention}: Invalid move, try again.'
        await ctx.send(response)
    else:
        moveinfo = movedata[move]
        charinfo,response = botgetcharinfo(ctx,character,chardata)    
                
        if response:
            await ctx.send(response)
        else:
            response = botcharmove(ctx,moveinfo,charinfo)
            
            await ctx.send(response)

@bot.command(name='list', help='List all moves, characters, or individual stats. Type m to see moves, and c to see characters.')
async def outputlist(ctx,listtype='m'):
    
    responselist = [f'{ctx.message.author.mention}:']

    if listtype in ['m','move','moves']:
        for move in allmoves:
            responselist.append(
                f'**{movedata.get(move).get("name")}**: {movedata.get(move).get("description")}'
            )
    
    elif listtype in ['c','character','char','characters']:
        for char in allchars:
            responselist.append(
                f'**{chardata.get(char).get("character name")}**: ({chardata.get(char).get("playbook")}): {chardata.get(char).get("chakra1")}; {chardata.get(char).get("chakra2")}'
            )
    
    else:
        # if moves or characters aren't specified, list a specific character's full stats
        charname = matchabbr(listtype,charabbrs)
        if charname in allchars:
            for key,value in chardata.get(charname).items():
                if key == "stats":
                    statstr = '**Stats:** '
                    for key, value in chardata.get(charname).get("stats").items():
                        statstr = statstr + f'{key.title()} {value}, '
                    responselist.append(statstr[:-2])
                else:
                    responselist.append(
                        f'**{key.title()}**: {value}'
                    )
            
        else:
            responselist[0] = responselist[0] + " Invalid input. Type m (or moves) to see moves, c (or characters) to see characters, or a character's name to see their stats."

    response = "\n".join(responselist)
    await ctx.send(response)

@bot.command(name='set', help='Set a value inside a character\'s sheet. This can be overwritten unless saved using the save command.')
async def outputlist(ctx,key,newval,character='user'):
    character = matchabbr(character,charabbrs)
    charinfo,response = botgetcharinfo(ctx,character,chardata)

    if not newval or not key:
        response = f'{ctx.message.author.mention}: Invalid input, try again. Example syntax: .set fluid 3 katara.'

    if response:
        await ctx.send(response)
    else:
        if key in charinfo:
            if charinfo[key] != newval:
                response = f"{ctx.message.author.mention}: {charinfo.get('character name')}\\'s {key.title()} has been changed from {charinfo[key]} to {newval}."
                charinfo[key] = newval
            else:
                response = f"{ctx.message.author.mention}: {charinfo.get('character name')}\\'s {key.title()} is already equal to {charinfo[key]}. No changes made."
        else:
            stat = matchabbr(key,statabbrs)
            if stat in allstats:
                newstat = checkvalidstat(newval)
                if not newstat:
                    response = f'{ctx.message.author.mention}: Invalid input, try again. Stats can only be set to a maximum of +3.'
                elif charinfo['stats'][stat] != newstat:
                    response = f"{ctx.message.author.mention}: {charinfo.get('character name')}\\'s {stat.title()} stat has been changed from {charinfo['stats'][stat]} to {newstat}."
                    charinfo['stats'][stat] = newstat
                else:
                    response = f"{ctx.message.author.mention}: {charinfo.get('character name')}\\'s {stat.title()} stat is already equal to {newstat}. No changes made."
            else:
                response = f'{ctx.message.author.mention}: Invalid input, try again. Example syntax: .set fluid 3 katara'

    await ctx.send(response)

def checkvalidstat(stat):
    try:
        if abs(int(stat)) > 3:
            return None
        else:
            return int(stat)
    except ValueError:
        return None
    except TypeError:
        return None

@bot.command(name='save', help='Save all current character stats so they are not overrwritten on bot restart.')
async def savetofile(ctx):

    response = f'{ctx.message.author.mention}: ' + savechardata(chardata,characterfile)

    await ctx.send(response)

if __name__ == "__main__":
    characterfile = 'characters.json'
    movefile = 'moves.json'

    chardata,movedata,allchars,charabbrs,allstats,statabbrs,allmoves,moveabbrs = loadvarsfromfiles(characterfile,movefile)
    
    bot.run(TOKEN)
    