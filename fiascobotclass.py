from fiascohelpers import *
from discord.ext import commands

def setup(bot):
    bot.add_cog(fiasco(bot))

class fiasco(commands.Cog):
    def __init__(self,bot):
        self.allplayers = []
        self.allrelationships = []
        self.tabledice = []
        self.diceemoji = [':sparkling_heart:',':gun:'] # first position is emoji to display for positive, second is for negative
        self.curphase = 'no game' 
        self.tiltelements = []
        self.tablefile = 'fiascotables.json'
        self.phaseorder = phaseorder = ['no game','setup','act one','tilt','act two','aftermath','reset fiasco']

    def phasecheck(self,checkphase):
        
        curindex = self.phaseorder.index(self.curphase)
        nextindex = curindex + 1

        if checkphase != self.phaseorder[nextindex]:
            return f"Invalid phase selection. You're currently in {self.curphase.title()}, so your next phase should be {self.phaseorder[nextindex].title()}."
        else:
            return None

    @commands.command(name='nextphase',help='Go to the next phase in Fiasco',description='Go to the next phase in Fiasco. Phase order: No Game > Setup > Act One > Tilt > Act Two > Aftermath')
    async def botnextphase(self, ctx):
        curindex = self.phaseorder.index(self.curphase)
        nextphase = self.phaseorder[curindex + 1].replace(" ","")
        
        cmd = ctx.bot.get_command(nextphase)
        
        if cmd:
            await ctx.invoke(cmd)
        

            

    @commands.command(name='addplayer',help='Add a player to Fiasco',description='Add a new player to a Fiasco game. \nExample usage: \n\t(.addplayer [player\'s name] [*Discord username] *optional)\n\t.addplayer Sara \n\t.addplayer Joe joesusername#1111')
    async def botaddfiascoplayer(self, ctx, playername=None, username=None):
        if self.curphase != 'no game':
            response = 'Game in progress, invalid input. To add new players, you must reset the game and start over.'
        else: 
            self.curphase = 'no game'
            username = ctx.message.author if not username else username
                
            if not playername:
                response = 'No player name specified, please try again.'
            else:    
                self.allplayers,response = addplayer(self.allplayers,playername,username)

            response = f'{ctx.message.author.mention}: '+ response

        await ctx.send(response)

    @commands.command(name='setup',help='Setup phase of Fiasco',hidden=True)
    async def botsetupfiasco(self,ctx):
        responselist = [f'{ctx.message.author.mention}: ']

        self.allrelationships,self.tabledice = setupfiasco(self.allplayers)            

        if not self.allrelationships:
            responselist.append('Not enough players. Add more players and try again.')
        else:
            resp = self.phasecheck('setup')
            
            if resp:
                responselist.append(resp)
            else:
                self.curphase = 'setup'
                playerlist = []
                for player in self.allplayers:
                    playerlist.append(player.playername)
                responselist.append('*Game started with players ' + ', '.join(playerlist)+'*')
                responselist.append('Begin the Setup!') # maybe add some rules explanation here
                responselist.append(displaydice(self.tabledice))
            
        response = "\n".join(responselist)
        await ctx.send(response)

    @commands.command(name='test',help='Command used in testing',hidden=True)
    async def botaddtestchars(self,ctx,stage=None):
        username = ctx.message.author
        self.allplayers,response = addplayer(self.allplayers,'Sara',username)
        self.allplayers,response = addplayer(self.allplayers,'Karl','joe123')
        self.allplayers,response = addplayer(self.allplayers,'Joe','karl123')
        
        await ctx.send('Test setup characters complete')

        if stage in ['t','a']:
            self.curphase = 'act one'
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

        if stage in ['a']:
            self.curphase = 'act two'

            for player in self.allplayers:                
                resp,player.dice,self.tabledice = movedie('positive',None,player.dice,self.tabledice)
                resp,player.dice,self.tabledice = movedie('negative',None,player.dice,self.tabledice)
    
            await ctx.send("Finished taking dice in act two")

    def matchuser(self,playername=None,username=None):
        curplayer = []
        
        for player in self.allplayers:
            if playername:
                # there is probably a better way of doing this that doesn't involve being in the for loop twice?
                allnames = [player.playername.lower() for player in self.allplayers]
                playername = checkabbrs(playername.lower(),allnames)

                if player.playername.lower() == playername.lower():
                    curplayer.append(player)
            else:
                if player.username == username:
                    curplayer.append(player)

        return None if len(curplayer) != 1 else curplayer[0]
        

    @commands.command(name='take',help='Take a die',description='Take a die from a player or from the regular pool. Defaults to taking from the pool. \nExample usage:\n\t(.take [die] [*takefrom] [*taking]) *optional\n\t.take 6\n\t.take pos pool Sara\n\t .take pos Joe Sara')
    async def bottakeadie(self,ctx,diestring=None,takefrom='pool',taking=None):
        
        responselist = [f'{ctx.message.author.mention}: ']
        showemoji = self.diceemoji if self.curphase in ['act one','act two'] else None
        if self.curphase in ['tilt']:
            responselist.append('Cannot give or take dice during the Tilt.')
        else:
            username = ctx.message.author
            takingplayer = self.matchuser(taking,username)

            if not takingplayer:
                responselist.append('Invalid player taking dice, try again.')
            else:
                if takefrom == 'pool':
                    dietype,dienum = parsediestring(diestring,self.tabledice)
                    resp,takingplayer.dice,self.tabledice = movedie(dietype,dienum,takingplayer.dice,self.tabledice,"took")
                    if resp:
                        responselist.append(f'{takingplayer.playername} {resp} the pool.')
                        responselist.append(takingplayer.dispdice(showemoji))
                        responselist.append(displaydice(self.tabledice,None,showemoji))
                    else:
                        responselist.append("Invalid die selection, try again.")
    
                else: # take from a player
                    takefromplayer = self.matchuser(None,username) if takefrom in ['me','mine'] else self.matchuser(takefrom,None)

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


    @commands.command(name='give',help='Give a die',description='Give a die. Defaults to giving to the pool. \nExample usage:\n\t(.give [die] [*giveto] [*giving]) *optional\n\t.give 6\n\t.give pos Joe Sara\n\t .give neg Sara')
    async def botgivedie(self,ctx,diestring,giveto='pool',getfrom=None):
        # arguments: .give [die] to [person to giveto] as [person to get from]
        responselist = [f'{ctx.message.author.mention}: ']
        showemoji = self.diceemoji if self.curphase in ['act one','act two'] else None
        if self.curphase in ['tilt']:
            responselist.append('Cannot give or take dice during the Tilt.')
        else:
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
                    givetoplayer = self.matchuser(None,username) if giveto in ['me','mine'] else self.matchuser(giveto,None)

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

    @commands.command(name='set',help='Set a relationship or tilt element')
    async def botsetelement(self,ctx,p1=None,p2=None,reltype=None,relstring=None):
        responselist = [f'{ctx.message.author.mention}: ']

        if self.curphase == 'setup':
            if not p1 or not p2 or not reltype or not relstring:
                responselist.append('Invalid input. Example: .set joe karl parentelement "fellow camp counselors"')
            else:
                responselist.append(setrelationshipinfo(self.allrelationships,p1.lower(),p2.lower(),reltype,relstring))
        elif self.curphase == 'tilt':
            # p1 = tilt category, p2 = tilt element
            if p1 == 'tilt' and p2 == 'reset':
                self.tiltelements = []
                responselist.append('Tilt element list reset.')
            elif len(self.tiltelements) > 1:
                responselist.append('Tilt element list full. If you would like to reset the current tilt elements, use this command: ".set tilt reset" \n')
                responselist.append(displaytilt(self.tiltelements))
            else:         
                # allow selection of soft tilt table
                t = loadtables(self.tablefile,"softtilt") if reltype == 'soft' else loadtables(self.tablefile,"tilt")
                elems = t.get(p1)

                if elems:
                    category = elems["category"]
                    element = elems.get(p2)
                else:
                    category = p1
                    element = p2

                if category and element:
                    self.tiltelements.append(fiascotilt(category,element))
                    responselist.append(f'Added Tilt element: {category.upper()} - "{element}"\n')
                    responselist.append(displaytilt(self.tiltelements))
                else:
                    responselist.append('Invalid input. Example: ".set 1 6", ".set Mayhem "A frantic chase"')
        else:
            responselist.append('This command can only be used during the Setup and the Tilt.')

        response = "\n".join(responselist)
        await ctx.send(response)


    @commands.command(name='show',help='Display relationships, tilt elements, and/or dice.', description='Usage ([argument] [*optional]): \n\tShow all: .show all \n\tShow relationships: .show rel [*player] \n\t Show Tilt elements: .show tilt \n\t Show dice: .show dice [*player or pool]')
    async def botshow(self,ctx,showwhat='all',playername=None,username='all'): # player is a toggle to see only one player or user's relationships
        responselist = [f'{ctx.message.author.mention}: ']
        
        thingstocheck = ["relationships","dice","tiltelements","all"]
        showwhat = checkabbrs(showwhat,thingstocheck)

        if showwhat == 'dice' or showwhat == 'all':
            if playername in ['me','mine']:
                username = ctx.message.author
                playername = None

            showemoji = self.diceemoji if self.curphase in ['act one','act two'] else None
            player = self.matchuser(playername,username)

            if player:
                responselist.append(player.dispdice(showemoji))
            elif playername in ['table','pool']:
                responselist.append(displaydice(self.tabledice,None,showemoji))
            else:
                responselist.append("*All Dice:*")
                for player in self.allplayers:
                    responselist.append(player.dispdice(showemoji))
                responselist.append(displaydice(self.tabledice,None,showemoji))

        if showwhat == "relationships" or showwhat == 'all':
            if not self.allrelationships:
                responselist.append('No relationships available.')
            else:
                if playername in ['me','mine']:
                    username = ctx.message.author
                    playername = None

                player = self.matchuser(playername,username)

                respstr = ''
                if player:
                    responselist.append(f'*{player.playername}\'s Relationships:*')
                    for rel in self.allrelationships:    
                        if rel.withwho[0] == player or rel.withwho[1] == player:
                            respstr += rel.disprel()
                else:
                    responselist.append('*All Player Relationships:*')
                    for rel in self.allrelationships:    
                        respstr += rel.disprel()
                responselist.append(respstr)

        if showwhat =='tiltelements' or showwhat =='all':
            if self.tiltelements:
                responselist.append(displaytilt(self.tiltelements))
            else:
                responselist.append('*No Tilt elements to display.* Use .show tilttable to see the Tilt table.')

        if showwhat =='tilttable':
            # show the soft tilt table instead
            
            t = loadtables(self.tablefile,'softtilt') if playername == 'soft' else loadtables(self.tablefile,'tilt')
            resp = '*Tilt Table:* ```'
            for num in t:
                resp += f'{num}: {t.get(num).get("category").upper()}'
                for x in range(1,7):
                    resp += f'\n\t{x}: {t.get(num).get(str(x))}'
                resp += '\n'
            resp += '```'
            responselist.append(resp)

        response = "\n".join(responselist)
        await ctx.send(response)
    

    @commands.command(name='resetfiasco',help='Reset your game')
    async def botresetfiasco(self,ctx):
        self.curphase = 'no game'
        self.allplayers = []
        self.allrelationships = []
        self.tabledice = []

        await ctx.send(f'{ctx.message.author.mention}: Fiasco game has been completely reset. Add players to start a new game.')

    # add stunt die handling to this someday
    @commands.command(name='actone',help='Act One of Fiasco',hidden=True)
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
            responselist.append('Cannot start Act One, the following relationships are incomplete: \n')
            responselist.append("\n".join(missing))
        else:
            resp = self.phasecheck('act one')
            
            if resp:
                responselist.append(resp)
            else:
                self.curphase = 'act one'
                for player in self.allplayers:
                    player.dice = []
                responselist.append('*Beginning Act One*')
                responselist.append('Take turns. When it is your turn, your character gets a scene. When only half the dice remain in the central pile, Act One ends.\n')
                
                self.tabledice = rollactone(len(self.allplayers))
                responselist.append(displaydice(self.tabledice,None,self.diceemoji))

        response = "\n".join(responselist)
        await ctx.send(response)

    @commands.command(name='fill',help='fill relationships for testing',hidden=True)
    async def botfill(self,ctx,all=None):
        for rel in self.allrelationships:
            rel.parentcategory = 'Friends'
            rel.parentelement = 'Grade school friends'
            rel.detailtype = 'Object'
            rel.detailcategory = 'Weapon'
            if all:
                rel.detailelement = 'Old, taped-up oar'
        
        await ctx.send("Finished filling relationships")

    def tiltcalc(self,allvals,pos,neg):
        valslist = [pos,neg]
        # find one winner for pos and for neg. pos = 'positive', neg = 'negative'
        responselist = []
        winners = []
        for ix,val in enumerate(valslist):
            nextval = valslist[(ix+1) % len(valslist)]
            resp = ''
            if val in allvals:
                maxval = max(k for k in allvals[val].keys())
                resp,winner = tilttie2(allvals[val][maxval],val)
                responselist.extend(resp)
                winners.append(winner)

            else:
                responselist.append(f'No {val.title()} values in Tilt calculation, getting player with lowest {nextval.title()} value. \n')
                if allvals.get('zero'):
                    resp,winner = tilttie2(allvals['zero'][0],'zero')
                    responselist.extend(resp)
                    winners.append(winner)
                else:
                    minval = min(k for k in allvals[nextval].keys())
                    resp,winner = tilttie2(allvals[nextval][minval],nextval)
                    responselist.extend(resp)
                    winners.append(winner)

        return responselist,winners[0],winners[1]

    @commands.command(name='tilt',help='Tilt phase of Fiasco',hidden=True)
    async def bottilt(self,ctx):
        responselist = [f'{ctx.message.author.mention}: ']
        
        # check to make sure the right number of dice are in the pool
        numplayers = len(self.allplayers)
        if len(self.tabledice) != numplayers * 2:
            responselist.append(f'Incorrect number of dice in pool. To start the tilt, you should have {numplayers * 2} dice left, so you need to take {len(self.tabledice) - (numplayers * 2)} dice from the pool.')
        else:
            resp = self.phasecheck('tilt')
            
            if resp:
                responselist.append(resp)
            else:
                self.curphase = 'tilt'
                allvals = dict()
                for player in self.allplayers:
                    resp = player.calcscore("tilt")
                    responselist.append(f'*{player.playername}\'s Tilt Calculation:*')
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
                        allvals[sign] = {num:[]}
                        allvals[sign][num].append(player)

                tiltresp,tiltp1,tiltp2 = self.tiltcalc(allvals,'positive','negative')

                responselist.extend(tiltresp)

                responselist.append(f"**{tiltp1.playername}** ({tiltp1.scores['tilt']['totalsign'].title()} {tiltp1.scores['tilt']['totalval']}) and **{tiltp2.playername}** ({tiltp2.scores['tilt']['totalsign'].title()} {tiltp2.scores['tilt']['totalval']}) get to decide what happens in the Tilt! Use the dice below and consult the tilt table to add one tilt element each.")
                responselist.append(displaydice(self.tabledice))
        
        response = "\n".join(responselist)
        await ctx.send(response)

    @commands.command(name='acttwo',help='Act Two of Fiasco',hidden=True)
    async def botacttwo(self,ctx):
        responselist = [f'{ctx.message.author.mention}: ']
        
        if len(self.tiltelements) != 2:
            responselist.append('Before starting Act Two, you must have 2 Tilt elements. Use the ".set" command to add Tilt elements.')
        else:
            resp = self.phasecheck('act two')
            
            if resp:
                responselist.append(resp)
            else:
                self.curphase = 'act two'
                responselist.append('*Beginning Act Two*')
                responselist.append('Same as Act One! Take turns, when it\'s your turn, your character gets a scene. This time, the final die is wild! \n')
                
                responselist.append(displaydice(self.tabledice,None,self.diceemoji))
                responselist.append(f'{displaytilt(self.tiltelements)}')

        response = "\n".join(responselist)
        await ctx.send(response)
    
    @commands.command(name='aftermath',help='Aftermath phase of Fiasco',hidden=True)
    async def botaftermath(self,ctx,soft=None):
        responselist = [f'{ctx.message.author.mention}: ']

        # check to make sure there are no dice left in the pool
        if self.tabledice != []:
            responselist.append('You cannot start the Aftermath while there are still dice left in the table pool. Allocate all dice before trying again.')
        else:
            resp = self.phasecheck('aftermath')
            
            if resp:
                responselist.append(resp)
            else:
                self.curphase = 'aftermath'
                for player in self.allplayers:
                    resp = player.calcscore("aftermath")
                    responselist.append(f'*{player.playername}\'s Aftermath Calculation:*')
                    responselist.append(resp)
                    
                    if soft == 'soft':
                        atype = "softaftermath" 
                        maxval = 11
                    else:
                        atype = "aftermath"
                        maxval = 13
                    
                    t = loadtables(self.tablefile,atype)

                    paftermath = t.get(player.scores["aftermath"]["totalsign"])
                    if player.scores["aftermath"]["totalval"] > maxval:
                        player.scores["aftermath"]["totalval"] = maxval 

                    paftermath = paftermath.get(str(player.scores["aftermath"]["totalval"])) if paftermath else t.get('positive').get('0')

                    responselist.append(f'> {paftermath} \n')
                    responselist.append(f'')

        response = "\n".join(responselist)
        await ctx.send(response)

