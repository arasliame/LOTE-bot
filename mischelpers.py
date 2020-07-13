import random
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

def matchabbr(inp,abbrlist):
    if inp:
        for item,abbrevs in abbrlist.items():
            if inp.lower() in abbrevs:
                return item
    return inp 

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
    mod = f'to {moveinfo.get("name").title()} (+{moveinfo.get("stat").title()})'
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