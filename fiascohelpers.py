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
                "type1":[0],
                "type2":[0],
                "totalsign":None,
                "totalval":0
            },
            "aftermath": {
                "type1":[0],
                "type2":[0],
                "totalsign":None,
                "totalval":0
            }
        }
        

    def __repr__(self):
        return f'{self.playername} ({self.username})'

    def calcscore(self,scorekind,type1,type2):
        self.scores[scorekind] = {
                type1:[0],
                type2:[0],
                "totalsign":None,
                "totalval":0
            }
        str1 = ''
        str2 = ''
        for die in self.dice:
            newnum = die.roll()
            if die.dietype == type1:
                self.scores[scorekind][type1].append(newnum)
                str1 = str1 + f'{newnum}+'
            elif die.dietype == type2:
                self.scores[scorekind][type2].append(newnum)
                str2 = str2 + f'{newnum}+'
        
        sum1,sum2 = sum(self.scores[scorekind][type1]), sum(self.scores[scorekind][type2])

        str1,str2 = str1[:-1] + f" = {sum1}",str2[:-1] + f" = {sum2}"

        final = sum1 - sum2

        if final > 0:
            sign = type1
        elif final < 0:
            sign = type2
        else:
            sign = 'zero'
        
        resp = (
            f"```Rolling {len(self.scores[scorekind][type1])-1} {type1.title()} and {len(self.scores[scorekind][type2])-1} {type2.title()}: \n"
            f"{type1.title()}: {str1} \n"
            f"{type2.title()}: {str2} \n\n"
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
            f"\t{self.parentcategory.title() if self.parentcategory else '[ParentCategory]'} - {self.parentelement.title() if self.parentelement else '[ParentElement]'} \n"
            f"\t({self.detailtype.upper() if self.detailtype else '[DetailType]'}) {self.detailcategory.title() if self.detailcategory else '[DetailCategory]'} - {self.detailelement.title() if self.detailelement else '[DetailElement]'} ```"
            )
        return dispstr

    def __repr__(self):
        return f'{self.parentcategory},{self.withwho}'

class fiascotilt():
    def __init__(self,category,element):
        self.category = category
        self.element = element

    def __repr__(self):
        return f"```Tilt: {self.category.upper()} - {self.element}```"


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
        rep = f'{self.dienum}'
        if self.dietype:
            rep = f'{self.dietype.title()} {rep}'
        if self.stunt:
            rep += 'S'
        return rep
    
def setupdice(numplayers):
    numdice,alldice = numplayers * 4,[]
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
    numplayers,allrelationships = len(allplayers),[]

    if numplayers < 3:
        return None,None
    else: 
        # set up relationships between players
        for x in range(numplayers):
            mod1 = (x-1) % numplayers
            allrelationships.append(fiascorelationship(allplayers[x],allplayers[mod1]))
        
        return allrelationships,setupdice(numplayers)
    

            
def movedie(dietype,dienum,giveto,getfrom,giveortake='took'):
    tofrom = 'from' if giveortake == 'took' else 'to'
    response = None
    
# if dienum is s, then you're moving a stunt die
    inpdietype = dietype
    if dienum == 's':    
        dietype = 'stunt'

    for die in getfrom:

        if dietype == 'stunt':
            if die.stunt and die.dietype == 'stunt': # stunt dice do not have a type
                if inpdietype != 'stunt':
                    response = f'{giveortake} a {inpdietype.title()} stunt die {tofrom}'
                    die.dietype = inpdietype
                    die.stunt = False
                    
            elif die.stunt and die.dietype != 'stunt': # stunt dice do have a type
                if die.dietype == inpdietype:
                    die.stunt = False
                    response = f'{giveortake} a {die.dietype.title()} stunt die {tofrom}'

        else:
            if not die.stunt: # can't move a stunt die unless you specify that it is a stunt die
                if die.dietype == dietype and die.dienum == dienum and dietype and dienum:
                    response = f'{giveortake} a {dietype.title()} {dienum} {tofrom}'
                elif die.dietype == dietype and not dienum:
                    response = f'{giveortake} a {dietype.title()} die {tofrom}'
                elif die.dienum == dienum and not dietype:
                    response = f'{giveortake} a {dienum} {tofrom}'
            
        if response:
            giveto.append(die)
            getfrom.remove(die)
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
    for elem in elems: resp += f'{elem}'
    return resp


def rollactone(numplayers,types,stunt=None,stunttype=False):
    numdice = numplayers * 2

    alldice = []
    for x in range(numdice):
        alldice.append(fiascodie(types[0]))
        alldice.append(fiascodie(types[1]))
    
    if stunt:
        for x in range(stunt):
            alldice[x].stunt = True
            if not stunttype:
                alldice[x].dietype = "stunt"

    return alldice

def loadtables(tablefile,whichtable):
    directory = os.path.dirname(__file__)
    fullpath = os.path.abspath(os.path.join(directory, tablefile))
   
    with open(fullpath, 'r', encoding='utf-8') as fin:
        filedata = json.load(fin)
    
    t = filedata.get(whichtable)
    return t

if __name__ == "__main__":
    pass
