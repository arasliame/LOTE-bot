import random
import os
import json

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
            sign = 'positive'
        elif final < 0:
            sign = 'negative'
        else:
            sign = 'zero'
        
        resp = (
            f"```Rolling {len(self.scores[scorekind]['positive'])-1} Positive and {len(self.scores[scorekind]['negative'])-1} Negative: \n"
            f"Positive: {posstr} \n"
            f"Negative: {negstr} \n\n"
            f"Final Score: {sign.title()} {abs(final)}```"
        )

        self.scores[scorekind]["totalsign"] = sign
        self.scores[scorekind]["totalval"] = abs(final)

        return resp
    

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
            f"```{self.withwho[0].playername} and {self.withwho[1].playername}: \n"
            f"\t{self.parentcategory.title() if self.parentcategory else '[ParentCategory]'} ({self.parentelement.title() if self.parentelement else '[ParentElement]'}) \n"
            f"\t{self.detailtype.upper() if self.detailtype else '[DetailType]'}: {self.detailcategory.title() if self.detailcategory else '[DetailCategory]'} ({self.detailelement.title() if self.detailelement else '[DetailElement]'}) ```"
            )
        return dispstr

    def __repr__(self):
        return f'{self.parentcategory},{self.withwho}'

class fiascotilt():
    def __init__(self,category,element):
        self.category = category
        self.element = element
    
    def disp(self):
        return f"```Tilt: {self.category.upper()} - {self.element}```"

    def __repr__(self):
        return f'{self.category.upper()} - {self.element}'

def gettilttable(soft=None):
    t = loadtables("fiascotables.json","tilt") if not soft else loadtables("fiascotables.json","softtilt")

def checkabbrs(inp,inputlist):
    abbrs = list(filter(lambda x: x.startswith(inp),inputlist))

    if not abbrs:
        # no match found
        return inp
    elif len(abbrs) > 1:
        # input not specific enough
        return inp
    else:
        return abbrs[0]




class fiascodie():
    def __init__(self,dietype=None):
        self.dienum = random.randint(1,6)
        self.dietype = dietype
        self.stunt = None
    
    def roll(self):
        self.dienum = random.randint(1,6)
        return self.dienum

    def __repr__(self):
        # need this to take into account dietypes probably?
        return f'{self.dietype.title()} {self.dienum}' if self.dietype else str(self.dienum)
    
def setupdice(numplayers):
    numdice = numplayers * 4
    alldice = []
    for x in range(numdice): alldice.append(fiascodie())

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

def setupfiasco(allplayers):
    numplayers = len(allplayers)
    allrelationships = []

    if numplayers < 3:
        return None,None
    else: 
        # set up relationships between players
        for x in range(numplayers):
            mod1 = (x-1) % numplayers
            allrelationships.append(fiascorelationship(allplayers[x],allplayers[mod1]))
        
        return allrelationships,setupdice(numplayers)
    
def displaydice(tabledice,whose=None,emoji=None):
    return displaydiceemoji(tabledice,whose,emoji) if emoji else displaydicenums(tabledice,whose) 
    # also need to display stunt dice somehow someday
            
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
    
    response = f"```{whose}'s Dice Pool:```" if whose else f"```Table Dice Pool ({len(tabledice)}):```"
    
    for dietype in typedict:
        if typedict[dietype]:
            emojistr = f'\t{dietype}: '
            for oneemoji in typedict[dietype]: emojistr = f'{emojistr}{oneemoji} '
            response = response + emojistr + '\n'

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
        
    responselist = [f"```{whose}'s Dice Pool:"] if whose else ["```Table Dice Pool:"]
    
    keys = list(typedict.keys())

    if keys == ['No type']:
        responselist.append(f'{typedict["No type"]}')
    else:
        for dietype in typedict:
            if typedict[dietype]:
                responselist.append(f'\t{dietype.title()}: {typedict[dietype]}')
        
    responselist.append("```")
    return "\n".join(responselist)
            
def movedie(dietype,dienum,giveto,getfrom,giveortake='took'):
    tofrom = 'from' if giveortake == 'took' else 'to'

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

            reltype = rel.abbrs[reltype] if reltype in rel.abbrs else checkabbrs(reltype,rel.__dict__.keys())
            
            if reltype in rel.__dict__:
                rel.__dict__[reltype] = relstring
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
    
    return None if not missing else resp

def tilttie(players):
    tiewinner = None
    while not tiewinner:
        resp = '*Rolling Tilt tiebreak:* ```'
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

def tilttie2(players,tietocheck):
    responselist = []
    if len(players) > 1:
        responselist.append(f'Tie detected while calculating {tietocheck.title()} values.')
        resp,winner = tilttie(players)
        responselist.append(resp)
    else:
        winner = players[0]
    
    return responselist,winner

def displaytilt(elems):
    resp = '*All Tilt Elements:*'
    for elem in elems: resp += f'{elem.disp()}'
    return resp


def parsediestring(diestring,pooldice):
    poollist = {}
    poollist = {die.dietype for die in pooldice if die.dietype}

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
        dietype = checkabbrs(dietype,poollist) # check to see if this type of die exists in a given pool

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

def loadtables(tablefile,whichtable):
    directory = os.path.dirname(__file__)
    fullpath = os.path.abspath(os.path.join(directory, tablefile))
   
    with open(fullpath, 'r', encoding='utf-8') as fin:
        filedata = json.load(fin)
    
    t = filedata.get(whichtable)
    return t

if __name__ == "__main__":
    t = loadtables("fiascotables.json","aftermath")
    print(t.get('positive'))
