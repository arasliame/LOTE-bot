import os
import json
from shutil import copyfile
from datetime import datetime
import logging

def loaddata(filename):
    directory = os.path.dirname(__file__)
    fullpath = os.path.abspath(os.path.join(directory, filename))
   
    with open(filename, 'r', encoding='utf-8') as fin:
        filedata = json.load(fin)
    return filedata


def loadvarsfromfiles(characterfile,movefile):
    # load info from files
    chardata = loaddata(characterfile)
    movedata = loaddata(movefile)

    # get all character names
    allchars = tuple(chardata.keys())
    charabbrs = loadabbrs(allchars)

    # get all stats from the first character
    allstats = tuple(chardata.get(allchars[0]).get("stats").keys())
    statabbrs = loadabbrs(allstats)

    # get all move names
    allmoves = tuple(movedata.keys())
    moveabbrs = loadabbrs(allmoves)

    logging.info(f"{characterfile} and {movefile} loaded for session.")

    return chardata,movedata,allchars,charabbrs,allstats,statabbrs,allmoves,moveabbrs

def loadabbrs(allvars):
    finaldict = dict()

    for item in allvars:
        m = item.split()
        firstletters = ''
        for word in m:
            firstletters = firstletters + word[0]

        m.append(item)
        m.append(firstletters)
        m.append(item.replace(" ",""))        
        
        finaldict[item] = set()
        for word in m:
            finaldict[item].add(word)
            y = word
            while y:
                y = y[:-1]
                if y: 
                    finaldict[item].add(y)
                    finaldict[item].add(y.replace(" ",""))
    
    for key, value in finaldict.items():
        for key2, value2 in finaldict.items():
            if key != key2:
                intersect = finaldict[key].intersection(finaldict[key2])
                finaldict[key] = finaldict[key].difference(intersect)
                finaldict[key2] = finaldict[key2].difference(intersect)
                
    return finaldict

# saves whatever is in the chardata dict into json, doesn't reload any of the other variables
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
