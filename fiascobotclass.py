from fiascoclasses import *
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

    def phasecheck(self,checkphase):
        phaseorder = ['no game','setup','actone','tilt','acttwo','aftermath','reset']
        
        curindex = phaseorder.index(self.curphase)
        nextindex = (curindex + 1) % len(phaseorder)

        return self.curphase if checkphase != phaseorder[nextindex] else checkphase

    @commands.command(name='addplayer',help='Add a player to Fiasco. Specify the player''s name.')
    async def botaddfiascoplayer(self, ctx, playername=None, username=None):
        self.curphase = self.phasecheck('no game')
        if self.curphase != 'no game':
            response = 'Game in progress, invalid input. To add new players, you must reset the game and start over.'

        else: 
            username = ctx.message.author if not username else username
                
            if not playername:
                response = 'No player name specified, please try again.'
            else:    
                self.allplayers,response = addplayer(self.allplayers,playername,username)

            response = f'{ctx.message.author.mention}: '+ response

        await ctx.send(response)

    @commands.command(name='setup',help='Set up a game of Fiasco with the current player list.')
    async def botsetupfiasco(self,ctx):
        responselist = [f'{ctx.message.author.mention}: ']
        self.curphase = self.phasecheck('setup')
        if self.curphase != 'setup':
            responselist.append('Game in progress, invalid input. To restart setup, you must reset the game and start over.')
        
        else:
            self.allrelationships,self.tabledice = setupfiasco(self.allplayers)            

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
    async def bottest(self,ctx,stage=None):
        username = ctx.message.author
        self.allplayers,response = addplayer(self.allplayers,'Sara',username)
        self.allplayers,response = addplayer(self.allplayers,'Karl','joe123')
        self.allplayers,response = addplayer(self.allplayers,'Joe','karl123')
        
        await ctx.send('Test setup characters complete')

        if stage in ['t','a']:
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

        if stage in ['a']:
            self.curphase = 'acttwo'

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
        

    @commands.command(name='take',help='Take a die from the pool or from a player.')
    async def bottakedie(self,ctx,diestring=None,takefrom='pool',taking=None):
        
        responselist = [f'{ctx.message.author.mention}: ']
        showemoji = self.diceemoji if self.curphase in ['actone','acttwo'] else None
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


    @commands.command(name='set',help='Set a relationship or tilt element.')
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
                t = loadtables("fiascotables.json","softtilt") if reltype == 'soft' else loadtables("fiascotables.json","tilt")
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


    @commands.command(name='show',help='Display things, like relationships and tilt elements and dice.')
    async def botshow(self,ctx,showwhat='all',playername=None,username='all'): # player is a toggle to see only one player or user's relationships
        responselist = [f'{ctx.message.author.mention}: ']
        
        thingstocheck = ["relationships","dice","tiltelements","all"]
        showwhat = checkabbrs(showwhat,thingstocheck)

        if showwhat == 'dice' or showwhat == 'all':
            if playername in ['me','mine']:
                username = ctx.message.author
                playername = None

            showemoji = self.diceemoji if self.curphase in ['actone','acttwo'] else None
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
                responselist.append('*No Tilt elements to display.*')

        response = "\n".join(responselist)
        await ctx.send(response)
    
    @commands.command(name='give',help='Give a die to another player or back to the pool')
    async def botgivedie(self,ctx,diestring,giveto='pool',getfrom=None):
        # arguments: .give [die] to [person to giveto] as [person to get from]
        responselist = [f'{ctx.message.author.mention}: ']
        showemoji = self.diceemoji if self.curphase in ['actone','acttwo'] else None
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

    @commands.command(name='resetfiasco',help='Completely reset your game of Fiasco.')
    async def botresetfiasco(self,ctx):
        self.curphase = 'no game'
        self.allplayers = []
        self.allrelationships = []
        self.tabledice = []

        await ctx.send(f'{ctx.message.author.mention}: Fiasco game has been completely reset. Add players to start a new game.')

    # add stunt die handling to this someday
    @commands.command(name='actone',help='Act One of Fiasco')
    async def botactone(self,ctx):      
        responselist = [f'{ctx.message.author.mention}: ']
        self.curphase = self.phasecheck('actone')
        if self.curphase != 'actone':
            responselist.append('Invalid phase, Act One can only be started after Setup. To restart Act One, you must reset the game and start over.')
        else:

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
                responselist.append('Take turns. When it is your turn, your character gets a scene. When only half the dice remain in the central pile, Act One ends.')
                
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

    @commands.command(name='tilt',help='Tilt phase of Fiasco')
    async def bottilt(self,ctx):
        responselist = [f'{ctx.message.author.mention}: ']
        
        self.curphase = self.phasecheck('tilt')
        if self.curphase != 'tilt':
            responselist.append('Invalid phase, Tilt can only be started after Act One. To restart Tilt, you must reset the game and start over.')
        else:

            # check to make sure the right number of dice are in the pool
            numplayers = len(self.allplayers)
            if len(self.tabledice) != numplayers * 2:
                responselist.append(f'Incorrect number of dice in pool. To start the tilt, you should have {numplayers * 2} dice left.')
            else:
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

    @commands.command(name='acttwo',help='Act Two of Fiasco')
    async def botacttwo(self,ctx):
        responselist = [f'{ctx.message.author.mention}: ']
        
        self.curphase = self.phasecheck('acttwo')
        if self.curphase != 'acttwo':
            responselist.append('Invalid phase, Act Two can only be started after Tilt. To restart Act Two, you must reset the game and start over.')
        elif len(self.tiltelements) != 2:
            responselist.append('Before starting Act Two, you must have 2 Tilt elements. Use the ".set" command to add Tilt elements.')
        else:
            # add thing here - don't start unless tilt elements are full
            responselist.append('*Beginning Act Two*')
            responselist.append('Same as Act One! Take turns, when it\'s your turn, your character gets a scene. This time, the final die is wild! \n')
            
            responselist.append(displaydice(self.tabledice,None,self.diceemoji))
            responselist.append(f'{displaytilt(self.tiltelements)}')

        response = "\n".join(responselist)
        await ctx.send(response)
    
    @commands.command(name='aftermath',help='Aftermath phase of Fiasco')
    async def botaftermath(self,ctx,soft=None):
        responselist = [f'{ctx.message.author.mention}: ']

        # check to make sure there are no dice left in the pool
        if self.tabledice != []:
            responselist.append('You cannot start the Aftermath while there are still dice left in the table pool. Allocate all dice before trying again.')
        else:
            self.curphase = self.phasecheck('aftermath')
            if self.curphase != 'aftermath':
                responselist.append('Invalid phase, Aftermath can only be started after Act Two.')
            else:
                for player in self.allplayers:
                    resp = player.calcscore("aftermath")
                    responselist.append(f'*{player.playername}\'s Aftermath Calculation:*')
                    responselist.append(resp)

                    atype = "softaftermath" if soft == 'soft' else "aftermath"
                    t = loadtables("fiascotables.json",atype)

                    paftermath = t.get(player.scores["aftermath"]["totalsign"])
                    if player.scores["aftermath"]["totalval"] > 13 and not soft:
                        player.scores["aftermath"]["totalval"] = 13 
                    if player.scores["aftermath"]["totalval"] > 11 and soft == 'soft':
                        player.scores["aftermath"]["totalval"] = 11 

                    paftermath = paftermath.get(str(player.scores["aftermath"]["totalval"])) if paftermath else t.get('positive').get('0')

                    responselist.append(f'> {paftermath} \n')
                    responselist.append(f'')

        response = "\n".join(responselist)
        await ctx.send(response)

