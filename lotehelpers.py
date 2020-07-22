import random
import os
import json
from shutil import copyfile
from datetime import datetime
import logging


# roll plus a modifier
def rollmod(mod=0):
    d1 = random.randint(1,6)
    d2 = random.randint(1,6)
    total = d1 + d2 + mod
    modsign = '+' if mod >= 0 else ''
    return (total,f'({d1}+{d2}){modsign}{mod} = **{total}**')

# check for roll result based on PbTA tiers
def checksuccess(roll):
    if roll < 7:
        return "Failure","f"
    elif roll >= 7 and roll < 10:
        return "Mild success","ms"
    elif roll >= 10:
        return "Great success!","gs"

def matchabbr(inp,inputlist):
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
    cmovedata = charinfo["custom moves"].copy()
    cmovedata.update(movedata)
    
    return cmovedata

# check if bot has been passed a valid character
def botgetcharinfo(ctx,character,chardata):
    response = None

    if character == "user":
        character = matchuser(str(ctx.message.author),chardata)
        if not character:
            response = f'{ctx.message.author.mention}: No character linked to user, specify a character to roll.'
            return None,response

    info = chardata.get(character.lower())

    if not info:
        response = f'{ctx.message.author.mention}: Invalid character, try again.'  
    return info,response

# match discord user with a character
def matchuser(username,chardata): 
    for character,info in chardata.items():
        if info.get("username") == username:
            return character

# roll a specific move based on a character sheet
def charmove(moveinfo,charinfo):
    if not moveinfo or not charinfo:
        return

    stat = moveinfo["stat"]
    roll = rollmod(charinfo.get("stats").get(stat))

    return roll

# get the result of a move given the move and the roll
def moveresult(moveinfo,roll):
    movetier = checksuccess(roll[0])[1]
    if movetier == 'f':
        moveresult = "Gain 1 Chi. The MC may respond."
    else:
        moveresult = moveinfo.get("results").get(movetier)

    return moveresult

# make the bot roll a character move
def botcharmove(ctx,moveinfo,charinfo):
    roll = charmove(moveinfo, charinfo)
    mod = f'{moveinfo.get("name").title()} (+{moveinfo.get("stat").title()})'
    response = responsestr(ctx,charinfo,mod,roll,moveinfo)

    return response

# roll for bot when a numeric modifier is passed
def botrollint(ctx,mod,info):
    roll = rollmod(mod)
    modsign = '+' if mod >= 0 else ''
    mod = f'{modsign}{mod}'

    response = responsestr(ctx,info,mod,roll)

    return response

# roll for bot when passed stat is a string
def botrollstring(ctx,stat,info):  
    roll = rollmod(info.get("stats").get(stat))
    stat = f'{stat.title()}!'

    response = responsestr(ctx,info,stat,roll)
        
    return response

# build the response string for a roll
def responsestr(ctx,charinfo,mod,roll,moveinfo=None):
    
    response = (
            f'{ctx.message.author.mention}: {charinfo.get("character name")} rolled {mod} \n'
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
