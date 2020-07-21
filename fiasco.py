import random

def fiascosetup(numplayers):
    # add something to quit if the number of players is wrong
    players = dict()

    for x in range(numplayers):
        p = 'p'+str(x+1)
        players[p] = {
            "username":None,
            "playername":None,
            "dice":{"black":[],"white":[],"stunt":[]},
            "relationship1":{
                "category":None,
                "element":None,
                "detailtype":None,
                "detailcategory":None,
                "detailelement":None,
                "withwho":None
                },
            "relationship2":{
                "category":None,
                "element":None,
                "detailtype":None,
                "detailcategory":None,
                "detailelement":None,
                "withwho":None
                }
        }

    # add something to auto-set relationships

    tabledice = {"black":[],"white":[],"stunt":[]}

    for y in range(2 * numplayers):
        tabledice["black"].append(random.randint(1,6))
        tabledice["white"].append(random.randint(1,6))
    
    return players,tabledice

def defineplayer(players,playername,username,overwriteplayer=0):

    # catch an exception here if needed
    if overwriteplayer:
        p = 'p'+str(overwriteplayer)
        players[p]["username"] = username
        players[p]["playername"] = playername
        return f"{p.title()} has been force-set to {playername}, with username {username}."

    setplayer = 0

    for player in players:
        if not players[player].get("username"):
            players[player]["username"] = username
            players[player]["playername"] = playername
            setplayer = player
            break
    
    if setplayer:
        return f"{player.title()} has been set to {playername}, with username {username}."
    else:
        return "All players already set, no new player has been added."

def parsediestring(die):
 # get color and number of die from string
    color = die[:-1]
    dienum = die[-1]
    
    if color:
        color = color.lower()
        if color == 'b':
            color = 'black'
        elif color == 'w':
            color = 'white'
        
        if color not in ['black','white']:
            return None,None
    else:
        color = None
    
    try:
        dienum = int(dienum)
        if dienum > 0 and dienum <= 6:
            return color,dienum
        else:
            return None,None
    except TypeError:
        return None,None

    return color,dienum

def defaultrelationships(players):
    # count number of players

# before passing to this func, need to have the player alias
# helper func that can be used to take a die at any point in the game
def takedie(players,tabledice,player,die): #returns string,tabledice array,diecolor,dienumber

    color,dienum = parsediestring(die)
    if not dienum:
        return "Invalid dice input. Try again.",tabledice,None,None

    if color:
        if dienum in tabledice[color]:
            players[player]['dice'][color].append(dienum)
            tabledice[color].remove(dienum)
            return f"{players[player]['playername'].title()} took a {color} {dienum}.",tabledice,color,dienum
        else:
            return f"There is no {color} {dienum}. Try again.",tabledice,None,None
    else:

        for pool in ['black','white']:
            if dienum in tabledice[pool]:
                players[player]['dice'][pool].append(dienum)
                tabledice[pool].remove(dienum)
                return f"{players[player]['playername'].title()} took a {pool} {dienum}.",tabledice,pool,dienum
            else:
                return f"There is no {dienum} available. Try again.",tabledice,None,None

if __name__ == "__main__":
    players,tabledice = fiascosetup(3)
    print(defineplayer(players,"karl","karl123"))
    print(defineplayer(players,"sara","sara123"))
    print(tabledice)
    print(takedie(players,tabledice,"p1","w4"))