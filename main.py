import os
from dotenv import load_dotenv
from discord.ext import commands
from fileops import loadvarsfromfiles,addcharmoves,savechardata
from mischelpers import matchabbr,botgetcharinfo,botcharmove,botrollint,botrollstring
from fiascoclasses import *
import logging

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
    characterfile = 'characters.json'
    movefile = 'moves.json'
    bot.add_cog(LOTE(bot,characterfile,movefile))
    bot.add_cog(fiasco(bot)) # add command to toggle game?

#@bot.commands(name='setgame', help='Play LOTE or Fiasco.')

class LOTE(commands.Cog):
    def __init__(self,bot,characterfile,movefile):
        self.bot = bot
        self.characterfile = characterfile
        self.movefile = movefile
        self.chardata,self.movedata,self.charabbrs,self.allstats,self.statabbrs,self.moveabbrs = loadvarsfromfiles(characterfile,movefile)
        

    # roll based on character sheet or roll with a modifier depending on user input
    @commands.command(name='r', help='Roll 2d6 plus a stat or numeric modifier. By default, use the character your Discord user is associated with, or specify a specific character.')
    async def botroll(self, ctx, stat='0', character="user"):
        
        character = matchabbr(character,self.charabbrs)
        charinfo,response = botgetcharinfo(ctx,character,self.chardata)
        
        if response:
            await ctx.send(response)
        else:
            try:
                mod = int(stat)
                response = botrollint(ctx,mod,charinfo)
            except ValueError:
                stat = matchabbr(stat,self.statabbrs)
                if stat not in self.allstats:
                    response = f'{ctx.message.author.mention}: Invalid stat, try again.'
                else:
                    response = botrollstring(ctx,stat,charinfo)
            await ctx.send(response)

    @commands.command(name='m', help='Do a specific move. By default, use the character your Discord user is associated with, or specify a character to roll for.')
    async def rollformove(self,ctx,move=None,character="user"):
        character = matchabbr(character,self.charabbrs)
        charinfo,response = botgetcharinfo(ctx,character,self.chardata)    
        
        if response:
            await ctx.send(response)

        # find moves that are specific to a character
        cmovedata,cmoveabbrs = addcharmoves(charinfo,self.movedata,self.moveabbrs)
        move = matchabbr(move,cmoveabbrs)

        if move not in cmovedata:
            response = f'{ctx.message.author.mention}: Invalid move, try again.'
        else:
            moveinfo = cmovedata[move]
            response = botcharmove(ctx,moveinfo,charinfo)
                
        await ctx.send(response)

    # update the move list to include character moves
    @commands.command(name='list', help='List all moves, characters, or individual stats. Type m to see moves, and c to see characters.')
    async def liststuff(self,ctx,listtype='m'):
        
        responselist = [f'{ctx.message.author.mention}:']

        if listtype in ['m','move','moves']:
            responselist.extend(self.listmovedata())
        
        elif listtype in ['c','character','char','chars','characters']:
            for char in self.chardata:
                responselist.append(
                    f'**{self.chardata.get(char).get("character name")}**: ({self.chardata.get(char).get("playbook")}): {self.chardata.get(char).get("chakra1")}; {self.chardata.get(char).get("chakra2")}'
                )
        
        else:
            # if moves or characters aren't specified, list a specific character's full stats
            charname = matchabbr(listtype,self.charabbrs)
            if charname in self.chardata:
                responselist.extend(self.listchardata(listtype,charname))
            else:
                responselist[0] = responselist[0] + " Invalid input. Type m (or moves) to see moves, c (or characters) to see characters, or a character's name to see their stats."

        response = "\n".join(responselist)
        await ctx.send(response)

    def listmovedata(self):
        responselist = []

        responselist.append("*Basic Moves*")
        # basic moves
        for move in self.movedata:
            responselist.append(
                f'**{self.movedata.get(move).get("name")}**: {self.movedata.get(move).get("description")}'
            )

        # custom character moves
        responselist.append("\n*Character-Specific Moves*")
        for character in self.chardata:
            for cmove in self.chardata.get(character).get("custom moves").values():
                responselist.append(
                    f'**{cmove.get("name")}** ({self.chardata.get(character).get("character name")}): {cmove.get("description")}'
                )
        return responselist

    def listchardata(self, listtype,charname):
        responselist = []
        
        for key,value in self.chardata.get(charname).items():
            if key == "stats":
                statstr = '**Stats:** '
                for key, value in self.chardata.get(charname).get("stats").items():
                    statstr = statstr + f'{key.title()} {value}, '
                responselist.append(statstr[:-2])
            elif key == "custom moves":
                movestr = '**Custom Moves:** '
                for cmove in value.values():
                    movestr = movestr + f'\n - {cmove.get("name")}: {cmove.get("description")}'
                responselist.append(movestr)
            else:
                responselist.append(
                    f'**{key.title()}**: {value}'
                )
        return responselist

    @commands.command(name='set', help='Set a value inside a character\'s sheet. This can be overwritten unless saved using the save command.')
    async def outputlist(self,ctx,key=None,newval=None,character='user'):
        if not newval or not key:
            response = f'{ctx.message.author.mention}: Invalid input, try again. Example syntax: .set fluid 3 katara.'
        
        character = matchabbr(character,self.charabbrs)
        charinfo,response = botgetcharinfo(ctx,character,self.chardata)

        
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
                stat = matchabbr(key,self.statabbrs)
                if stat in self.allstats:
                    newstat = self.checkvalidstat(newval)
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

    def checkvalidstat(self,stat):
        try:
            if abs(int(stat)) > 3:
                return None
            else:
                return int(stat)
        except ValueError:
            return None
        except TypeError:
            return None

    @commands.command(name='save', help='Save all current character stats so they are not overrwritten on bot restart.')
    async def savetofile(self, ctx):

        response = f'{ctx.message.author.mention}: ' + savechardata(self.chardata,self.characterfile)

        await ctx.send(response)

class fiasco(commands.Cog):
    def __init__(self,bot):
        self.allplayers = []
        self.allrelationships = []
        self.tabledice = []
        self.diceemoji = [':sparkling_heart:',':gun:'] # first position is emoji to display for positive, second is for negative
        self.curphase = 'no game' # add a func to check the game phase


    @commands.command(name='addplayer',help='Add a player to Fiasco. Specify the player''s name.')
    async def botaddfiascoplayer(self, ctx, playername=None, username=None):
        if self.curphase != 'no game':
            response = 'Game in progress, invalid input. To add new players, you must reset the game and start over.'
        else: 
            if not username:
                username = ctx.message.author

            if not playername:
                response = 'No player name specified, please try again.'
            else:    
                self.curphase = 'picking players'
                self.allplayers,response = addplayer(self.allplayers,playername,username)

            response = f'{ctx.message.author.mention}: '+ response

            # prevent adding players if game has already been set up

            await ctx.send(response)

    @commands.command(name='setup',help='Set up a game of Fiasco with the current player list.')
    async def botsetupfiasco(self,ctx):
        self.allrelationships,self.tabledice = setupfiasco(self.allplayers)

        responselist = [f'{ctx.message.author.mention}: ']

        if not self.allrelationships:
            responselist.append('Not enough players. Add more players and try again.')
        else:
            playerlist = []
            for player in self.allplayers:
                playerlist.append(player.playername)
            self.curphase = 'setup'
            responselist.append('*Game started with players ' + ', '.join(playerlist)+'*')
            responselist.append('Begin the Setup!') # maybe add some rules explanation here
            responselist.append(displaydice(self.tabledice))
        
        response = "\n".join(responselist)
        await ctx.send(response)

    @commands.command(name='test',help='Set up a game of Fiasco with the current player list.')
    async def botaddtestchars(self,ctx,stage=None):
        username = ctx.message.author
        self.allplayers,response = addplayer(self.allplayers,'Sara',username)
        self.allplayers,response = addplayer(self.allplayers,'Karl','joe123')
        self.allplayers,response = addplayer(self.allplayers,'Joe','karl123')
        
        await ctx.send('Test setup characters complete')

        if stage == 'tilt':
            self.curphase = 'actone'
            self.allrelationships,self.tabledice = setupfiasco(self.allplayers) # setup

            for rel in self.allrelationships: # fill relationships
                rel.parentcategory = 'Friends'
                rel.parentelement = 'Grade school friends'
                rel.detailtype = 'Object'
                rel.detailcategory = 'Weapon'
                rel.detailelement = 'Old, taped-up oar'
            
            await ctx.send("Finished filling relationships")

            # start act one
            self.tabledice = rollactone(len(self.allplayers))

            # take enough dice
            for player in self.allplayers:                
                resp,player.dice,self.tabledice = movedie('positive',None,player.dice,self.tabledice)
                resp,player.dice,self.tabledice = movedie('negative',None,player.dice,self.tabledice)

            await ctx.send("Finished taking dice in act one")


    

    def matchuser(self,playername=None,username=None):
        
        curplayer = []
        for player in self.allplayers:
            if playername:
                if player.playername.lower() == playername.lower():
                    curplayer.append(player)
            else:
                if player.username == username:
                    curplayer.append(player)
        if len(curplayer) != 1:
            return None
        else:
            return curplayer[0]

    @commands.command(name='take',help='Take a die from the pool or from a player.')
    async def bottakeadie(self,ctx,diestring=None,takefrom='pool',taking=None):
        responselist = [f'{ctx.message.author.mention}: ']
        if self.curphase in ['actone','acttwo']:
            showemoji=self.diceemoji
        else:
            showemoji=None

        username = ctx.message.author
        takingplayer = self.matchuser(taking,username)

        if not takingplayer:
            responselist.append('Invalid player taking dice, try again.')
        else:
            if takefrom == 'pool':
                # fix this to make those other takedie funcs generic
                if self.curphase == 'setup':
                    r,self.tabledice,player = setuptakedie(self.tabledice,takingplayer,diestring)
                elif self.curphase == 'actone':
                    r,self.tabledice,player = acttakedie(self.tabledice,takingplayer,diestring)
                
                responselist.append(r)
                responselist.append(player.dispdice(showemoji))
                responselist.append(displaydice(self.tabledice,None,showemoji))
            else:
                if takefrom in ['me','mine']:
                    takefromplayer = self.matchuser(None,username)
                else:
                    takefromplayer = self.matchuser(takefrom,None)

                if not takefromplayer:
                    responselist.append('Invalid player to take from, try again.')
                else:
                    dietype,dienum = parsediestring(diestring,takefromplayer.dice)

                    resp,takingplayer.dice,takefromplayer.dice = movedie(dietype,dienum,takingplayer.dice,takefromplayer.dice)
                    
                    if resp:
                        responselist.append(f'{takingplayer.playername} {resp} {takefromplayer.playername}.')
                        responselist.append(takingplayer.dispdice(showemoji))
                        responselist.append(takefromplayer.dispdice(showemoji))
                    else:
                        responselist.append("Invalid die selection, try again.")

        response = "\n".join(responselist)
        await ctx.send(response)


    @commands.command(name='fset',help='Set a relationship aspect.')
    async def setrelaspect(self,ctx,p1=None,p2=None,reltype=None,relstring=None):
        responselist = [f'{ctx.message.author.mention}: ']

        if not p1 or not p2 or not reltype or not relstring:
            responselist.append('Invalid input. Example: .fset joe karl parentelement "fellow camp counselors"')

        else:
            p1 = p1.lower()
            p2 = p2.lower()
            responselist.append(setrelationshipinfo(self.allrelationships,p1,p2,reltype,relstring))
        
        response = "\n".join(responselist)
        await ctx.send(response)


    @commands.command(name='rel',help='Display a relationship')
    async def disprelationships(self,ctx,playername=None,username='all'): # player is a toggle to see only one player or user's relationships?
        if not self.allrelationships:
            response = f'{ctx.message.author.mention}: No relationships available. Set up game to create relationships.'
            await ctx.send(response)
        else:

            responselist = [f'{ctx.message.author.mention}: ']
            
            if playername in ['me','mine']:
                username = ctx.message.author
                playername = None

            player = self.matchuser(playername,username)

            if player:
                responselist.append(f'{player.playername}\'s Relationships:')
                for rel in self.allrelationships:    
                    if rel.withwho[0] == player or rel.withwho[1] == player:
                        responselist.append(rel.disprel())
            else:
                responselist.append('All Player Relationships:')
                for rel in self.allrelationships:    
                    responselist.append(rel.disprel())
            response = "\n".join(responselist)
            await ctx.send(response)
    
    @commands.command(name='dice',help='Display all the dice on the table or a specific user''s dice.')
    async def botdisplaydice(self,ctx,playername=None,username='all'):
        responselist = [f'{ctx.message.author.mention}: ']
        
        if playername in ['me','mine']:
            username = ctx.message.author
            playername = None

        player = self.matchuser(playername,username)

        if self.curphase in ['actone','acttwo']:
            showemoji = self.diceemoji
        else:
            showemoji = None

        if player:
            responselist.append(player.dispdice(showemoji))
        else:
            for player in self.allplayers:
                responselist.append(player.dispdice(showemoji))
            responselist.append(displaydice(self.tabledice,None,showemoji))

        response = "\n".join(responselist)
        await ctx.send(response)
    
    @commands.command(name='give',help='Give a die to another player or back to the pool')
    async def botgivedie(self,ctx,diestring,giveto='pool',getfrom=None):
        # arguments: .give [die] to [person to giveto] as [person to get from]
        responselist = [f'{ctx.message.author.mention}: ']
        showemoji=None

        if self.curphase in ['actone','acttwo']:
            showemoji=self.diceemoji
        
        username = ctx.message.author
        
        getfromplayer = self.matchuser(getfrom,username)

        if not getfromplayer:
            responselist.append('Invalid player to get dice from, try again.')
        else:

            dietype,dienum = parsediestring(diestring,getfromplayer.dice)

            if giveto == 'pool': # return dice to the table
                resp,self.tabledice,getfromplayer.dice = movedie(dietype,dienum,self.tabledice,getfromplayer.dice,"gave")
                if resp:
                    responselist.append(f'{getfromplayer.playername} {resp} the pool.')
                    responselist.append(getfromplayer.dispdice(showemoji))
                    responselist.append(displaydice(self.tabledice,None,showemoji))
                else:
                    responselist.append("Invalid die selection, try again.")
            else:
                if giveto in ['me','mine']:
                    givetoplayer = self.matchuser(None,username)
                else:
                    givetoplayer = self.matchuser(giveto,None)

                if givetoplayer:
                    resp,givetoplayer.dice,getfromplayer.dice = movedie(dietype,dienum,givetoplayer.dice,getfromplayer.dice,"gave")
                    if resp:
                        responselist.append(f'{getfromplayer.playername} {resp} {givetoplayer.playername}.')
                        responselist.append(getfromplayer.dispdice(showemoji))
                        responselist.append(givetoplayer.dispdice(showemoji))
                    else:
                        responselist.append("Invalid die selection, try again.")
                else:
                    responselist.append("Invalid player to give dice to, try again.")

        response = "\n".join(responselist)
        await ctx.send(response)

    @commands.command(name='resetfiasco',help='Completely reset your game of Fiasco.')
    async def botresetfiasco(self,ctx):
        self.allplayers = []
        self.allrelationships = []
        self.tabledice = []

        await ctx.send(f'{ctx.message.author.mention}: Fiasco game has been completely reset. Add players to start a new game.')

    # add stunt die handling to this someday
    @commands.command(name='actone',help='Begin Act One of Fiasco')
    async def botactone(self,ctx):
        responselist = [f'{ctx.message.author.mention}: ']
        
        # check to make sure that all relationships are full
        missing = []
        for rel in self.allrelationships:
            resp = checkfullrelationship(rel)
            if resp:
                missing.append(resp)
                missing.append(rel.disprel())
        
        if missing:
            responselist.append('Cannot start act one, the following relationships are incomplete: \n')
            responselist.append("\n".join(missing))
        else:
            self.curphase = 'actone'
            for player in self.allplayers:
                player.dice = []
            responselist.append('*Beginning Act One*')
            responselist.append('Idk here are some rules or something')
            
            self.tabledice = rollactone(len(self.allplayers))
            responselist.append(displaydice(self.tabledice,None,self.diceemoji))

        response = "\n".join(responselist)
        await ctx.send(response)

    @commands.command(name='fill',help='fill relationships for testing')
    async def botfill(self,ctx,all=None):
        for rel in self.allrelationships:
            rel.parentcategory = 'Friends'
            rel.parentelement = 'Grade school friends'
            rel.detailtype = 'Object'
            rel.detailcategory = 'Weapon'
            if all:
                rel.detailelement = 'Old, taped-up oar'
        
        await ctx.send("Finished filling relationships")

    # this whole thing is a hot mess... you should make it better
    @commands.command(name='tilt',help='Start the tilt!')
    async def bottilt(self,ctx):
        self.curphase='tilt'

        responselist = [f'{ctx.message.author.mention}: ']

        # check to make sure the right number of dice are in the pool
        numplayers = len(self.allplayers)
        if len(self.tabledice) != numplayers * 2:
            responselist.append(f'Incorrect number of dice in pool. To start the tilt, you should have {numplayers * 2} dice left.')
        else:
            allvals = dict()
            for player in self.allplayers:
                resp = player.calcscore("tilt")
                responselist.append(f'{player.playername}\'s Tilt Calculation:')
                responselist.append(resp)

                sign = player.scores["tilt"]["totalsign"]
                num = player.scores["tilt"]["totalval"]
                
                if sign in allvals:
                    
                    if allvals[sign].get(num):
                        allvals[sign][num].append(player)
                    else:
                        allvals[sign][num] = []
                        allvals[sign][num].append(player)

                else:
                    
                    if sign:
                        allvals[sign] = {num:[]}
                        allvals[sign][num].append(player)
                    else:
                        allvals["zero"] = {num:[]}
                        allvals["zero"][0].append(player)

            if 'positive' in allvals:
                maxpos = max(k for k in allvals['positive'].keys())
                if len(allvals['positive'][maxpos]) > 1:
                    responselist.append('Tie detected while getting Positive values.')
                    resp,winner = tilttie(allvals['positive'][maxpos])
                    responselist.append(resp)
                    tiltp1 = winner
                else:
                    tiltp1 = allvals['positive'][maxpos][0]
            else:
                responselist.append('No Positive values in Tilt calculation, getting player with lowest Negative value. \n')
                if allvals.get('zero'):
                    if len(allvals['zero'][0]) > 1:
                        responselist.append('Tie detected while getting Zero values.')
                        resp,winner = tilttie(allvals['zero'][0])
                        responselist.append(resp)
                        tiltp1 = winner
                    else: 
                        tiltp1 = allvals['zero'][0][0]
                else:
                    minneg = min(k for k in allvals['negative'].keys())
                    if len(allvals['negative'][minneg]) > 1:
                        responselist.append('Tie detected while calculating Negative values.')
                        resp,winner = tilttie(allvals['negative'][minneg])
                        responselist.append(resp)
                        tiltp1 = winner
                    else:
                        tiltp1 = allvals['negative'][minneg][0]

            if 'negative' in allvals:
                maxneg = max(k for k in allvals['negative'].keys())
                if len(allvals['negative'][maxneg]) > 1:
                    responselist.append('Tie detected while calculating Negative values.')
                    resp,winner = tilttie(allvals['negative'][maxneg])
                    responselist.append(resp)
                    tiltp2 = winner
                else:
                    tiltp2 = allvals['negative'][maxneg][0]
            else:
                responselist.append('No Negative values in Tilt calculation, getting player with lowest Positive value. \n')
                if allvals.get('zero'):
                    if len(allvals['zero'][0]) > 1:
                        responselist.append('Tie detected while calculating Zero values.')
                        resp,winner = tilttie(allvals['zero'][0])
                        responselist.append(resp)
                        tiltp2 = winner
                    else: 
                        tiltp2 = allvals['zero'][0][0]
                else:
                    minpos = min(k for k in allvals['positive'].keys())
                    if len(allvals['positive'][minpos]) > 1:
                        responselist.append('Tie detected while calculating Positive values.')
                        resp,winner = tilttie(allvals['positive'][minpos])
                        responselist.append(resp)
                        tiltp2 = winner
                    else:
                        tiltp2 = allvals['positive'][minpos][0]

            responselist.append(f"{tiltp1.playername} ({tiltp1.scores['tilt']['totalsign'].title()} {tiltp1.scores['tilt']['totalval']}) and {tiltp2.playername} ({tiltp2.scores['tilt']['totalsign'].title()} {tiltp2.scores['tilt']['totalval']}) get to decide what happens in the Tilt!")
            responselist.append(displaydice(self.tabledice))
        
        response = "\n".join(responselist)
        await ctx.send(response)

if __name__ == "__main__":
    bot.run(TOKEN)
    