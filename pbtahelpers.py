import random
import os
import json
from shutil import copyfile
from datetime import datetime
import logging


# roll plus a modifier, with advantage or disadvantage
def rollmod(mod=None,addtlmod=None,adv=None):
    mod = 0 if not mod else mod
    addtlmod = 0 if not addtlmod else addtlmod

    dice = []
    dice.append(random.randint(1,6))
    dice.append(random.randint(1,6))

    if adv:
        dice.append(random.randint(1,6))

    if adv == 'advantage':
        dice.sort(reverse=True)
    elif adv == 'disadvantage':
        dice.sort()

    total = dice[0] + dice[1] + mod
    modsign = '+' if mod >= 0 else ''

    dicestr = f'({dice[0]}+{dice[1]}'
    
    if adv:
        dicestr += f'~~_+{dice[2]}_~~'
    
    dicestr += f'){modsign}{mod}'
    
    if addtlmod != 0:
        total += addtlmod
        amodsign = '+' if addtlmod >=0 else ''
        dicestr += f'{amodsign}{addtlmod}'
    
    dicestr += f' = **{total}**'

    return total,dicestr

# check for roll result based on PbTA tiers
def checksuccess(roll):
    if roll < 7:
        return "Failure","6-"
    elif roll >= 7 and roll < 10:
        return "Mild success","7-9"
    elif roll >= 10 and roll < 12:
        return "Great success!","10-11"
    elif roll >= 12:
        return "***Spectacular*** success!!","12+"

def matchabbr(inp,inputlist,frombeginning=False):
    firstletters = {}
    nospaces = {}

# check for abbreviations
    for item in inputlist:
        words = item.split()
        letters = [word[0] for word in words]
        firstletters["".join(letters)] = item
        nospaces[item.replace(" ","")] = item
    
    if inp in firstletters:
        inp = firstletters[inp]    

    if frombeginning: #match only from the beginning, not anything in the string
        abbrs = list(filter(lambda x: x.find(inp) == 0,inputlist))
        abbrs2 = list(filter(lambda x: x.find(inp) == 0,nospaces.keys()))
    else:
        abbrs = list(filter(lambda x: inp in x,inputlist))
        abbrs2 = list(filter(lambda x: inp in x,nospaces.keys()))

    if not abbrs and not abbrs2:
        return inp
    elif len(abbrs) > 1 or len(abbrs2) > 1:
        return inp
    else:
        if abbrs:
            return abbrs[0]
        elif abbrs2:
            return nospaces.get(abbrs2[0])

def checkvalidstat(stat):
    try:
        return None if abs(int(stat)) > 3 else int(stat)
    except ValueError or TypeError:
        return None


# make a temporary dict for custom character moves
def addcharmoves(charinfo,movedata):
    cmovedata = {}

    if charinfo.get("custom moves"):
        cmovedata = charinfo["custom moves"].copy()
    
    cmovedata.update(movedata)
    
    return cmovedata

# check if bot has been passed a valid character
def botgetcharinfo(username,character,chardata):
    response = None

    if character == "user":
        character = matchuser(username,chardata)
        if not character:
            response = 'No character linked to user, specify a character to roll.'
            return None,response

    info = chardata.get(character.lower())

    if not info:
        response = 'Invalid character, try again.'  
    return info,response

# match discord user with a character
def matchuser(username,chardata): 
    for character,info in chardata.items():
        if info.get("username") == username:
            return character

# parse a modifier string
def parsemod(modifier,stats):
    modlist = str(modifier).split('+')

    if len(modlist) > 3:
        return None
    
    stat,adv,mod = None,None,None

    for i in modlist:
        if stat not in stats:
            stat = matchabbr(i,stats,True)
        if adv not in ['advantage','disadvantage']:
            adv = matchabbr(i,['advantage','disadvantage'],True)
        try:
            mod = int(i) if not mod else mod
        except:
            None
    
    adv = None if adv not in ['advantage','disadvantage'] else adv
    stat = None if stat not in stats else stat
    #add handling to prevent ridiculous modifiers?
    mod = None if mod and abs(mod) > 3 else mod

    return stat,mod,adv

# roll a specific move based on a character sheet
def charmove(moveinfo,charinfo,modifier=0):
    if not moveinfo or not charinfo:
        return

    rstat,mod,adv = parsemod(modifier,charinfo.get("stats"))
    mstat = moveinfo.get("stat")
    
    if mstat == '*choose':
        roll = rollmod(charinfo.get("stats").get(rstat),mod,adv) if rstat else None 
        # can't roll if you haven't picked a stat
    elif mstat:
        roll = rollmod(charinfo.get("stats").get(mstat),mod,adv)
    else:
        roll = rollmod(0,mod,adv)

    return roll

# get the result of a move given the move and the roll
def moveresult(moveinfo,roll):
    movetier = checksuccess(roll[0])[1]
    
    moveresult = moveinfo.get("results").get(movetier)

    if moveresult == '*miss':
        moveresult = "A complication occurs, the Keeper may respond."

    return moveresult

# make the bot roll a character move
def botcharmove(moveinfo,charinfo,modifier=0):
    roll = charmove(moveinfo, charinfo,modifier)
    
    rstat,mod,adv = parsemod(modifier,charinfo.get("stats"))
    mstat = moveinfo.get("stat")

    if mstat == '*choose':
        if not rstat:
            response = f'"{moveinfo.get("name").title()}" requires you to choose a stat. Choose a valid stat.'
            return response
        else:
            mstat = rstat

    modstr = f'{moveinfo.get("name").title()} (+{mstat.title()}'
    if mod and mod != 0:
        modsign = '+' if mod > 0 else ''
        modstr += f' and {modsign}{mod}'
    
    modstr += ')'

    if adv:
        modstr += f' with {adv.title()}'

    response = responsestr(charinfo,modstr,roll,moveinfo)

    return response

def botrollgeneric(modifier,info):
    rstat,mod,adv = parsemod(modifier,info.get("stats"))

    modstr = '('

    if rstat:
        mod1 = info.get("stats").get(rstat)
        mod2 = mod
        mod2sign = '+' if mod2 and mod2 > 0 else ''
        modstr += f'+{rstat.title()}'
    else:
        mod1 = mod
        mod1sign = '+' if mod1 and mod1 > 0 else ''
        mod2 = 0
        modstr += f'{mod1sign}{mod1}'

    if mod2 and mod2 != 0:
        modstr += f'{mod2sign}{mod2}'
    
    modstr += ')'

    if adv:
        modstr += f' with {adv.title()}'

    roll = rollmod(mod1,mod2,adv)

    response = responsestr(info,modstr,roll)

    return response
    

# build the response string for a roll
def responsestr(charinfo,modstr,roll,moveinfo=None):
    
    response = (
            f'{charinfo.get("character name")} rolled {modstr} \n'
            f'{roll[1]}, {checksuccess(roll[0])[0]} \n'
        )

    if moveinfo:
        response = response + (
            f'```{moveresult(moveinfo,roll)}```'
        )
    
    return response




def loaddata(filename):
    directory = os.path.dirname(__file__)
    fullpath = os.path.abspath(os.path.join(directory, filename))
   
    with open(fullpath, 'r', encoding='utf-8') as fin:
        filedata = json.load(fin)
    return filedata


def loadvarsfromfiles(characterfile,movefile):
    # load info from files
    chardata = loaddata(characterfile)
    movedata = loaddata(movefile)

    # get all stats from the first character
    allstats = tuple(chardata.get(list(chardata.keys())[0]).get("stats").keys())

    logging.info(f"{characterfile} and {movefile} loaded for session.")

    return chardata,movedata,allstats




# saves whatever is in the chardata dict into json file, doesn't reload any of the other variables
def savechardata(chardata,characterfile):
    directory = os.path.dirname(__file__)
    fullpath = os.path.abspath(os.path.join(directory, characterfile))
   
    now = datetime.now().strftime("%Y%m%d-%H%M%S-")
    newfilename = now + characterfile

    newfullpath = os.path.abspath(os.path.join(directory,'backup', newfilename))

    copyfile(fullpath,newfullpath)

    with open(characterfile, 'w', encoding='utf-8') as fout:
        json.dump(chardata,fout,indent=4) 
    
    logging.warning(f"Saved over existing character data. Backup character data saved at {newfullpath}.")

    return f"Save successful!"

if __name__ == "__main__":
    print(matchabbr('vit',['vitality', 'composure', 'reason', 'presence', 'sensitivity'],True))
    