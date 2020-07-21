import random

class fiascoplayer():
    def __init__(self,playername,username):
        self.playername = playername
        self.username = username
        self.dice = []
        self.scores = {
            "tilt": {
                "positive":[0],
                "negative":[0],
                "totalsign":None,
                "totalval":0
            },
            "aftermath": {
                "positive":[0],
                "negative":[0],
                "totalsign":None,
                "totalval":0
            }
        }
        

    def __repr__(self):
        return f'{self.playername} ({self.username})'

    def dispdice(self,emoji=None):
        return displaydice(self.dice,self.playername,emoji)

    def calcscore(self,scorekind): # only works with positive and negative dice
        self.scores[scorekind] = {
                "positive":[0],
                "negative":[0],
                "totalsign":None,
                "totalval":0
            }
        posstr = ''
        negstr = ''
        for die in self.dice:
            newnum = die.roll()
            if die.dietype == 'positive':
                self.scores[scorekind]['positive'].append(newnum)
                posstr = posstr + f'{newnum}+'
            elif die.dietype == 'negative':
                self.scores[scorekind]['negative'].append(newnum)
                negstr = negstr + f'{newnum}+'
        
        sumpos = sum(self.scores[scorekind]['positive'])
        sumneg = sum(self.scores[scorekind]['negative'])

        posstr = posstr[:-1] + f" = {sumpos}"
        negstr = negstr[:-1] + f" = {sumneg}"

        final = sumpos - sumneg

        if final > 0:
            sign = f'positive'
        elif final < 0:
            sign = f'negative'
        else:
            sign = ''
        
        resp = (
            f"```Rolling {len(self.scores[scorekind]['positive'])-1} Positive and {len(self.scores[scorekind]['negative'])-1} Negative: \n"
            f"Positive: {posstr} \n"
            f"Negative: {negstr} \n\n"
            f"Final Score: {sign.title()} {abs(final)}```"
        )

        self.scores[scorekind]["totalsign"] = sign
        self.scores[scorekind]["totalval"] = abs(final)

        return resp
    # func to roll the dice that you have

    

class fiascorelationship():
    
    def __init__(self, withwho1=None, withwho2=None):
        self.withwho = []
        self.withwho.append(withwho1)
        self.withwho.append(withwho2)

        self.parentcategory = None
        self.parentelement = None

        self.detailtype = None
        self.detailcategory = None
        self.detailelement = None

    abbrs = {
        'pc':'parentcategory',
        'pe':'parentelement',
        'dt':'detailtype',
        'dc':'detailcategory',
        'de':'detailelement'
    }

    def disprel(self):
        dispstr = (
            f"```Relationship between {self.withwho[0].playername} and {self.withwho[1].playername}: \n"
            f"\t {self.parentcategory.title() if self.parentcategory else '[ParentCategory]'} ({self.parentelement.title() if self.parentelement else '[ParentElement]'}) \n"
            f"\t {self.detailtype.upper() if self.detailtype else '[DetailType]'}: {self.detailcategory.title() if self.detailcategory else '[DetailCategory]'} ({self.detailelement.title() if self.detailelement else '[DetailElement]'}) ```"
            )
        return dispstr

    def __repr__(self):
        return f'{self.parentcategory},{self.withwho}'

    
def checkabbrs(inp,inputdict):
    abbrs = list(filter(lambda x: x.startswith(inp),inputdict.keys()))

    if not abbrs:
        # print('no match found')
        return inp
    elif len(abbrs) > 1:
        # Deal with more that one team.
        # print('input was not specific enough')
        return inp
    else:
        # Only one team found, so print that team.
        return abbrs[0]


    

class fiascodie():
    def __init__(self,dietype=None):
        self.dienum = random.randint(1,6)
        self.dietype = dietype
        self.stunt = None
    
    def roll(self):
        self.dienum = random.randint(1,6)
        return self.dienum
    # add optional init param to give die a dietype?
    # add optional init param to give die a number?

    

    def __repr__(self):
        # need this to take into account dietypes probably?
        if self.dietype:
            return f'{self.dietype.title()} {self.dienum}'
        else:
            return str(self.dienum)
    

# funcs for each stage of the game
def setupdice(numplayers):
    numdice = numplayers * 4

    alldice = []
    for x in range(numdice):
        alldice.append(fiascodie())
    
    return alldice

def addplayer(allplayers,playername,username):
    if len(allplayers) >= 5:
        response = "Players list is full. No new players added."
        return allplayers,response
    
    if playername.lower() in ['me','mine']:
        response = "Cannot set player name to ''me'' or ''mine'' due to protected system command. No new players added."
        return allplayers,response

    for player in allplayers:
        if player.playername == playername:
            response = f'{playername} already exists, cannot add new player with same name.'
            return allplayers,response

    allplayers.append(fiascoplayer(playername,username))
    response = f'Added {playername} ({username}) as Player {len(allplayers)}.'
    return allplayers,response

# rename this to something better
def setupfiasco(allplayers):
    numplayers = len(allplayers)
    allrelationships = []

    if numplayers < 3:
        #print("Not enough players.")
        return None,None
    else: 
        # set up relationships between players
        for x in range(numplayers):
            mod1 = (x-1) % numplayers
            allrelationships.append(fiascorelationship(allplayers[x],allplayers[mod1]))
        
        return allrelationships,setupdice(numplayers)
    
def displaydice(tabledice,whose=None,emoji=None):
    

    if emoji: # don't display die numbers - only supports "positive" and "negative" die types because i'm lazy
        return displaydiceemoji(tabledice,whose,emoji)
    else: # display die numbers
        return displaydicenums(tabledice,whose)
        
    # also need to display stunt dice somehow
            
def displaydiceemoji(tabledice,whose=None,emoji=None):
    typedict = {
        "Positive":[],
        "Negative":[],
        "No type":[],
    }
    for die in tabledice:
        if die.dietype == 'positive':
            typedict["Positive"].append(f'{emoji[0]}')
        elif die.dietype == 'negative':
            typedict["Negative"].append(f'{emoji[1]}')
        else:
            typedict["No type"].append(die.dienum)
    
    if whose:
        response = f"```{whose}'s Dice Pool:```"
    else:
        response = "```Table Dice Pool:```"
    
    for dietype in typedict:
        if typedict[dietype]:
            emojistr = f'{dietype}: '
            for oneemoji in typedict[dietype]:
                emojistr = f'{emojistr}{oneemoji} '
            response = response + emojistr + '\n'
        
    # response = response + "``` ```"
    return response

def displaydicenums(tabledice,whose=None):
    typedict = {"No type":[]}
    for die in tabledice:
        if die.dietype:
            if die.dietype not in typedict:
                typedict[die.dietype] = []
                typedict[die.dietype].append(die.dienum)
            else:
                typedict[die.dietype].append(die.dienum)
        else:
            typedict["No type"].append(die.dienum)
        
    if whose:
        responselist = [f"```{whose}'s Dice Pool:"]
    else:
        responselist = ["```Table Dice Pool:"]
    
    keys = list(typedict.keys())

    if keys == ['No type']:
        responselist.append(f'{typedict["No type"]}')
    else:
        for dietype in typedict:
            if typedict[dietype]:
                responselist.append(f'{dietype.title()}: {typedict[dietype]}')
        
    responselist.append("```")
    return "\n".join(responselist)
            

def setuptakedie(setupdice,player,diestring):
    
    dietype,dienum = parsediestring(diestring,setupdice)

    if not dienum:
        return 'Invalid dice input. Try again.',setupdice,player
    elif not setupdice:
        return 'No setup dice available.',setupdice,player
    else:
        resp,player.dice,tabledice = movedie(dietype,dienum,player.dice,setupdice)
        if resp:
            return f'{player.playername} {resp} the pool.',setupdice,player
        else:
            return f'Invalid selection, try again.',setupdice,player
    
 
def acttakedie(tabledice,player,diestring):
# consolidate this with the other take func
    # only accepts 'positive' or 'negative' as input
    dietype,dienum = parsediestring(diestring,tabledice)

    if not dietype or dietype not in ['positive','negative']:
        return 'Invalid dice input. Try again.',tabledice,player
    elif not tabledice:
        return 'No table dice available.',tabledice,player
    else:
        resp,player.dice,tabledice = movedie(dietype,dienum,player.dice,tabledice)
        if resp:
            return f'{player.playername} {resp} the pool.',tabledice,player
        else:
            return f'Invalid selection, try again.',tabledice,player


def movedie(dietype,dienum,giveto,getfrom,giveortake='took'):
# add a bit to the str to say where they got the die from
    if giveortake == 'took':
        tofrom = 'from'
    else:
        tofrom = 'to'

    if dietype and dienum:
        for die in getfrom:
            if die.dietype == dietype and die.dienum == dienum:
                giveto.append(die)
                getfrom.remove(die)
                response = f'{giveortake} a {dietype.title()} {dienum} {tofrom}'
                return response,giveto,getfrom
    elif dietype:
        for die in getfrom:
            if die.dietype == dietype:
                giveto.append(die)
                getfrom.remove(die)
                response = f'{giveortake} a {dietype.title()} die {tofrom}'
                return response,giveto,getfrom
    elif dienum:
        for die in getfrom:
            if die.dienum == dienum:
                giveto.append(die)
                getfrom.remove(die)
                response = f'{giveortake} a {dienum} {tofrom}'
                return response,giveto,getfrom
    return None,giveto,getfrom


def setrelationshipinfo(relationships,p1name,p2name,reltype,relstring):

    for rel in relationships:
        player1 = rel.withwho[0]
        player2 = rel.withwho[1]

        if (p1name == player1.playername.lower() and p2name == player2.playername.lower()) or (p1name == player2.playername.lower() and p2name == player1.playername.lower()):
            # now update the relationship

            if reltype in rel.abbrs:
                reltype = rel.abbrs[reltype]
            else:
                reltype = checkabbrs(reltype,rel.__dict__)
            
            if reltype in rel.__dict__:
                # set the value in the class
                rel.__dict__[reltype] = relstring

                # add a line to distinguish which relationship is being set
                resp = f'For {player1.playername} and {player2.playername}\'s relationship, {reltype} has been set to "{relstring}" \n'
                return resp + rel.disprel()

            else:
                return f'No match for {reltype} found. Try again.'
        
    return "No matching relationship found. Try again."

def checkfullrelationship(rel):
    resp = f'*Missing aspect(s) in {rel.withwho[0].playername} and {rel.withwho[1].playername}\'s relationship:* '
    missing = False
    for var in rel.__dict__:
        if not rel.__dict__[var]:
            resp = resp + f'[{var}] '
            missing = True
    
    if not missing:
        return None
    else:
        return resp

def tilttie(players):
    tiewinner = None
    while not tiewinner:
        resp = 'Rolling tilt tiebreak: ```'
        alltotals = dict()
        for player in players:
            total = 0
            resp += f'{player.playername} rolls '
            for die in player.dice:
                dieroll = die.roll()
                resp += f'{dieroll}+'
                total += dieroll
            resp = resp[:-1] + f' = {total} \n'
            alltotals[total] = player
        resp += '```'
        if len(alltotals) < len(players):
            resp += 'Tiebreak tied! \n'
            tiewinner = None
        else:
            maxtotal = max(k for k in alltotals.keys())
            tiewinner = alltotals[maxtotal]
            resp += f'{tiewinner.playername} wins the tiebreak!\n'
    return resp,tiewinner

def parsediestring(diestring,pooldice):
    pooldict = {}

    for die in pooldice:
        if die.dietype and die.dietype not in pooldict:
            pooldict[die.dietype] = None
    
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
        dietype = checkabbrs(dietype,pooldict) # check to see if this type of die exists in a given pool
    
    if dienum:
        try:
            dienum = int(dienum)
            if dienum > 0 and dienum <= 6:
                return dietype,dienum
            else:
                return dietype,None
        except ValueError or TypeError:
            return dietype,None

    return dietype,dienum
    
def rollactone(numplayers):
    numdice = numplayers * 2

    alldice = []
    for x in range(numdice):
        alldice.append(fiascodie('positive'))
        alldice.append(fiascodie('negative'))
    
    return alldice

if __name__ == "__main__":
    allplayers = []
    addplayer(allplayers,'karl','karl123')
    addplayer(allplayers,'sara','sara123')
    addplayer(allplayers,'sara2','sara1233')
    addplayer(allplayers,'sara3','sara1223')

    
