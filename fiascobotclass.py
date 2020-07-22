from fiascohelpers import *
from discord.ext import commands


def setup(bot):
    bot.add_cog(fiasco(bot))

class fiasco(commands.Cog):
    def __init__(self,bot):
        self.allplayers = []
        self.allrelationships = []
        self.tabledice = []
        self.dietypes = { # indices 0,1 are the two main die types, 2 is optional stunt die
            'types':['positive','negative','stunt'],
            'emoji':[':sparkling_heart:',':gun:',':lion:']}
        self.curphase = 'no game' 
        self.tiltelements = []
        self.tablefile = 'fiascotables.json'
        self.phaseorder = ('no game','setup','act one','tilt','act two','aftermath','reset')
        self.stuntdice = 0 # how many stunt dice are there, if any. stunt dice do not inherently have a type? need to toggle whether stunt dice have a type - mostly only matters for display
        self.stunttype = False # do stunt dice have a type?

    # func for toggling stunt dice
    @commands.command(name='stunt',help='Toggle whether to use stunt dice or not',description='make a description')
    async def botstunt(self,ctx,numstuntdice=0,stunttype=False):
        
        response = f'{ctx.message.author.mention}: ' # why is python mad at me


        if self.curphase != 'no game':
            response += 'This command cannot be used while a game is in progress.'
        else: # int(numstuntdice) > 0:
            self.stuntdice = int(numstuntdice)
            response += f'Number of stunt dice set to {self.stuntdice}.'
            if int(numstuntdice) > 0:
                if stunttype:
                    self.stunttype = stunttype
                dodonot = 'do' if self.stunttype else 'do not'
                response += f' Stunt dice **{dodonot}** have a specific type.'

        await ctx.send(response)

    def phasecheck(self,checkphase):
        
        curindex = self.phaseorder.index(self.curphase)
        nextindex = curindex + 1

        if checkphase != self.phaseorder[nextindex]:
            return f"Invalid phase selection. You're currently in {self.curphase.title()}, so your next phase should be {self.phaseorder[nextindex].title()}."
        else:
            return None

    @commands.command(name='next',help='Go to the next phase in Fiasco',description='Go to the next phase in Fiasco. Phase order: No Game > Setup > Act One > Tilt > Act Two > Aftermath')
    async def botnextphase(self, ctx):
        curindex = self.phaseorder.index(self.curphase)
        nextphase = self.phaseorder[curindex + 1].replace(" ","")
        
        cmd = ctx.bot.get_command(nextphase)
        
        if cmd:
            await ctx.invoke(cmd)
        
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
            self.tabledice = rollactone(len(self.allplayers),self.dietypes['types'],self.stuntdice,self.stunttype)

            # take enough dice
            for player in self.allplayers:                
                resp,player.dice,self.tabledice = movedie(self.dietypes.get('types')[0],None,player.dice,self.tabledice)
                resp,player.dice,self.tabledice = movedie(self.dietypes.get('types')[1],None,player.dice,self.tabledice)

            await ctx.send("Finished taking dice in act one")

        if stage in ['a']:
            self.curphase = 'act two'

            for player in self.allplayers:                
                resp,player.dice,self.tabledice = movedie(self.dietypes.get('types')[0],None,player.dice,self.tabledice)
                resp,player.dice,self.tabledice = movedie(self.dietypes.get('types')[1],None,player.dice,self.tabledice)
    
            await ctx.send("Finished taking dice in act two")

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


        

    @commands.command(name='take',help='Take a die',description='Take a die from a player or from the regular pool. Defaults to taking from the pool. \nExample usage:\n\t(.take [die] [*takefrom] [*taking]) *optional\n\t.take 6\n\t.take pos pool Sara\n\t .take pos Joe Sara')
    async def bottakeadie(self,ctx,diestring=None,takefrom='pool',taking=None):
        
        responselist = [f'{ctx.message.author.mention}: ']
        
        if self.curphase in ['tilt']:
            responselist.append('Cannot give or take dice during the Tilt.')
        elif not diestring:
            responselist.append('No valid die input, try again.')
        else:
            username = ctx.message.author
            takingplayer = self.matchuser(taking,username)

            if not takingplayer:
                responselist.append('Invalid player taking dice, try again.')
            else:
                if takefrom == 'pool':
                    dietype,dienum = self.parsediestring(diestring)

                    resp,takingplayer.dice,self.tabledice = movedie(dietype,dienum,takingplayer.dice,self.tabledice,"took")
                    if resp:
                        responselist.append(f'{takingplayer.playername} {resp} the pool.')
                        responselist.append(self.displaydice(takingplayer))
                        responselist.append(self.displaydice())
                    else:
                        responselist.append("Invalid die selection, try again.")
    
                else: # take from a player
                    takefromplayer = self.matchuser(None,username) if takefrom in ['me','mine'] else self.matchuser(takefrom,None)

                    if not takefromplayer:
                        responselist.append('Invalid player to take from, try again.')
                    else:
                        dietype,dienum = self.parsediestring(diestring)
                        resp,takingplayer.dice,takefromplayer.dice = movedie(dietype,dienum,takingplayer.dice,takefromplayer.dice)
                        
                        if resp:
                            responselist.append(f'{takingplayer.playername} {resp} {takefromplayer.playername}.')
                            responselist.append(self.displaydice(takingplayer))
                            responselist.append(self.displaydice(takefromplayer))
                        else:
                            responselist.append("Invalid die selection, try again.")

        response = "\n".join(responselist)
        await ctx.send(response)


    @commands.command(name='give',help='Give a die',description='Give a die. Defaults to giving to the pool. \nExample usage:\n\t(.give [die] [*giveto] [*giving]) *optional\n\t.give 6\n\t.give pos Joe Sara\n\t .give neg Sara')
    async def botgivedie(self,ctx,diestring=None,giveto='pool',getfrom=None):
        # arguments: .give [die] to [person to giveto] as [person to get from]
        # giving stunt dice is not supported, because after they leave the pool, they become normal dice

        responselist = [f'{ctx.message.author.mention}: ']
        
        if self.curphase in ['tilt']:
            responselist.append('Cannot give or take dice during the Tilt.')
        elif not diestring:
            responselist.append('No valid die input, try again.')
        else:
            username = ctx.message.author
            getfromplayer = self.matchuser(getfrom,username)

            if not getfromplayer:
                responselist.append('Invalid player to get dice from, try again.')
            else:
                dietype,dienum = self.parsediestring(diestring)

                if giveto == 'pool': # return dice to the table
                    resp,self.tabledice,getfromplayer.dice = movedie(dietype,dienum,self.tabledice,getfromplayer.dice,"gave")
                    if resp:
                        responselist.append(f'{getfromplayer.playername} {resp} the pool.')
                        responselist.append(self.displaydice(getfromplayer))
                        responselist.append(self.displaydice())
                    else:
                        responselist.append("Invalid die selection, try again.")
                else:
                    givetoplayer = self.matchuser(None,username) if giveto in ['me','mine'] else self.matchuser(giveto,None)

                    if givetoplayer:
                        resp,givetoplayer.dice,getfromplayer.dice = movedie(dietype,dienum,givetoplayer.dice,getfromplayer.dice,"gave")
                        if resp:
                            responselist.append(f'{getfromplayer.playername} {resp} {givetoplayer.playername}.')
                            responselist.append(self.displaydice(getfromplayer))
                            responselist.append(self.displaydice(givetoplayer))
                        else:
                            responselist.append("Invalid die selection, try again.")
                    else:
                        responselist.append("Invalid player to give dice to, try again.")

        response = "\n".join(responselist)
        await ctx.send(response)

    @commands.command(name='set',help='Set a relationship or Tilt element')
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
                responselist.append('Tilt element list full. If you would like to reset the current Tilt elements, use this command: ".set tilt reset" \n')
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


    @commands.command(name='show',help='Display relationships, Tilt elements, and/or dice', description='Usage ([argument] [*optional]): \n\nShow all: .show all \nShow relationships: .show rel [*player] \n Show Tilt elements: .show tilt \n Show dice: .show dice [*player or pool]')
    async def botshow(self,ctx,showwhat='all',playername='all'): # player is a toggle to see only one player or user's relationships
        username = None
        responselist = [f'{ctx.message.author.mention}: ']
        
        thingstocheck = ["relationships","dice","tiltelements","all"]
        showwhat = checkabbrs(showwhat,thingstocheck)

        if showwhat == 'dice' or showwhat == 'all':
            if playername in ['me','mine']:
                username,playername = ctx.message.author,None

            player = self.matchuser(playername,username)

            if player:
                responselist.append(self.displaydice(player))
            elif playername in ['table','pool']:
                responselist.append(self.displaydice())
            else:
                responselist.append("*All Dice:*")
                for player in self.allplayers: responselist.append(self.displaydice(player))
                responselist.append(self.displaydice())

        if showwhat == "relationships" or showwhat == 'all':
            if not self.allrelationships:
                responselist.append('No relationships available.')
            else:
                if playername in ['me','mine']:
                    username,playername = ctx.message.author,None

                player = self.matchuser(playername,username)

                respstr = ''
                if player:
                    responselist.append(f'*{player.playername}\'s Relationships:*')
                    for rel in self.allrelationships:    
                        if rel.withwho[0] == player or rel.withwho[1] == player:
                            respstr += rel.disprel()
                else:
                    responselist.append('*All Player Relationships:*')
                    for rel in self.allrelationships: respstr += rel.disprel()
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
    

    @commands.command(name='reset',help='Reset your game')
    async def botresetfiasco(self,ctx):
        self.curphase = 'no game'
        self.allplayers = []
        self.allrelationships = []
        self.tabledice = []

        await ctx.send(f'{ctx.message.author.mention}: Fiasco game has been completely reset. Add players to start a new game.')

    

    @commands.command(name='add',help='Add a player to Fiasco during setup',description='Add a new player to a new Fiasco game. \nExample usage: \n\t(.addplayer [player\'s name] [*Discord username] *optional)\n\t.addplayer Sara \n\t.addplayer Joe joesusername#1111')
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
                self.curphase,playerlist = 'setup',[]
                
                for player in self.allplayers:
                    playerlist.append(player.playername)
                responselist.append('*Game started with players ' + ', '.join(playerlist)+'*')
                responselist.append('Begin the Setup!') # maybe add some rules explanation here
                responselist.append(self.displaydice())
            
        response = "\n".join(responselist)
        await ctx.send(response)

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
                for player in self.allplayers: player.dice = []
                responselist.append('*Beginning Act One*')
                responselist.append('Take turns. When it is your turn, your character gets a scene. When only half the dice remain in the central pile, Act One ends.\n')
                
                self.tabledice = rollactone(len(self.allplayers),self.dietypes['types'],self.stuntdice,self.stunttype)
                responselist.append(self.displaydice())

        response = "\n".join(responselist)
        await ctx.send(response)


    def tiltcalc(self,allvals,pos,neg):
        valslist,responselist,winners = [pos,neg],[],[]
        
        for ix,val in enumerate(valslist):
            nextval,resp = valslist[(ix+1) % len(valslist)],''
            
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
                self.curphase,allvals = 'tilt',dict()
                
                for player in self.allplayers:
                    resp = player.calcscore("tilt",self.dietypes.get('types')[0],self.dietypes.get('types')[1])
                    responselist.append(f'*{player.playername}\'s Tilt Calculation:*')
                    responselist.append(resp)

                    sign,num = player.scores["tilt"]["totalsign"], player.scores["tilt"]["totalval"]
                    

                    if sign in allvals:
                        if not allvals[sign].get(num):
                            allvals[sign][num] = []
                    else:
                        allvals[sign] = {num:[]}

                    allvals[sign][num].append(player)

                tiltresp,tiltp1,tiltp2 = self.tiltcalc(allvals,self.dietypes.get('types')[0],self.dietypes.get('types')[1])

                responselist.extend(tiltresp)

                responselist.append(f"**{tiltp1.playername}** ({tiltp1.scores['tilt']['totalsign'].title()} {tiltp1.scores['tilt']['totalval']}) and **{tiltp2.playername}** ({tiltp2.scores['tilt']['totalsign'].title()} {tiltp2.scores['tilt']['totalval']}) get to decide what happens in the Tilt! Use the dice below and consult the Tilt table to add one Tilt element each.")
                responselist.append(self.displaydice())
        
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
                
                responselist.append(self.displaydice())
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
                    resp = player.calcscore('aftermath',self.dietypes.get('types')[0],self.dietypes.get('types')[1])
                    responselist.append(f'*{player.playername}\'s Aftermath Calculation:*')
                    responselist.append(resp)
                    
                    if soft == 'soft':
                        atype,maxval = "softaftermath",11
                    else:
                        atype,maxval = "aftermath",13
    
                    t = loadtables(self.tablefile,atype)
                    t2 = dict()

                    for ix,key in enumerate(t.keys()):
                        if key not in self.dietypes['types']:
                            t2[self.dietypes['types'][ix]] = t.get(key)
                        else:
                            t2[key] = t.get(key)
                            
                    paftermath = t2.get(player.scores["aftermath"]["totalsign"])
                    
                    if player.scores["aftermath"]["totalval"] > maxval:
                        player.scores["aftermath"]["totalval"] = maxval 

                    paftermath = paftermath.get(str(player.scores["aftermath"]["totalval"])) if paftermath else t2.get(self.dietypes['types'][0]).get('0')

                    responselist.append(f'> {paftermath} \n')
                    responselist.append(f'')

        response = "\n".join(responselist)
        await ctx.send(response)

    # need to display stunt dice someday   
    # stunt dice always show up in their own category in the table pool, show up as pos or neg in player pools
    def displaydice(self,player=None):
        dice = player.dice if player else self.tabledice
        emoji = True if self.curphase in ['act one','act two'] else False

        if self.curphase in ['setup','act two']:
            poolstr = f' ({len(self.tabledice)} until the end of {self.curphase.title()})'
        elif self.curphase == 'act one':
            poolstr = f' ({len(self.tabledice) - len(self.allplayers) * 2} until the end of {self.curphase.title()})'
        else:
            poolstr = ''

        response = f"```{player.playername}'s Dice Pool:" if player else f"```Table Dice Pool{poolstr}:"

        if emoji:
            response += '```'
            emojidict = {dietype:self.dietypes.get('emoji')[key] for key,dietype in enumerate(self.dietypes.get('types'))}
        else:
            response += '\n'

        typedict = {"no type":[],"stunt":[]}

        for die in dice:
            if die.stunt and die.dietype == 'stunt':
                typedict["stunt"].append(die)
            else:
                if die.dietype:
                    if die.dietype not in typedict:
                        typedict[die.dietype] = []
                    typedict[die.dietype].append(die)
                else:
                    typedict["no type"].append(die)

        for dietype in sorted(typedict.keys()):
            if typedict[dietype]:
                if len(typedict[dietype]) >= 1 and len(typedict) > 2: # don't show "no type" or "stunt" if they're the only things on the list
                    response += f'\t {dietype.title()}: '

                if emoji:
                    emojistr = ''
                    for die in typedict[dietype]: 
                        if die.stunt:
                            emojistr += f'{emojidict.get("stunt")} '
                        else:
                            emojistr += f'{emojidict.get(dietype)} ' # handle stunt dice when displaying emojis, needs handling for dice in player hands?
                    response = response + emojistr + '\n'
                else:
                    response += '[' # number display does not show stunt dice if they are typed, also do not need to show types if in tilt phase
                    for die in typedict[dietype]:
                        response += f'{die.dienum}, '
                    response = response[:-2] + ']\n'
        
        if not emoji:
            response += '```'
            
        return response

        
    def parsediestring(self,diestring):

        if len(diestring) == 1:
            try:
                dienum = int(diestring)
                dietype = None
            except ValueError or TypeError:
                dienum = None 
                dietype = diestring
        else:
            dietype = diestring[:-1]
            dienum = diestring[-1]
        
        if dietype:
            dietype = dietype.lower()
            dietype = checkabbrs(dietype,self.dietypes['types']) # check to see if this type of die exists in a given pool

        if dienum:
            try:
                dienum = int(dienum)
                if dienum > 0 and dienum <= 6:
                    return dietype,dienum 
                else:
                    return dietype,None
            except ValueError or TypeError:
                dienum = 's' if dienum == 's' else None # handle stunt dice
                return dietype,dienum

        return dietype,dienum