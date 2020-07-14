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
    allmovedata = loaddata(movefile)
    movedata = allmovedata

    # get all character abbrevs
    allchars = tuple(chardata.keys())
    charabbrs = loadabbrs(allchars)

    # get all stats from the first character
    allstats = tuple(chardata.get(allchars[0]).get("stats").keys())
    statabbrs = loadabbrs(allstats)

    # get all move names
    allmoves = tuple(movedata.keys())
    moveabbrs = loadabbrs(allmoves)

    logging.info(f"{characterfile} and {movefile} loaded for session.")

    return chardata,movedata,charabbrs,allstats,statabbrs,moveabbrs

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
    
    finaldict = dedupabbrs(finaldict)
                
    return finaldict

def dedupabbrs(finaldict):
    for key, value in finaldict.items():
        for key2, value2 in finaldict.items():
            if key != key2:
                intersect = finaldict[key].intersection(finaldict[key2])
                finaldict[key] = finaldict[key].difference(intersect)
                finaldict[key2] = finaldict[key2].difference(intersect)
                
    return finaldict

# temporarily add character moves to moveabbrs and movedata
def addcharmoves(charinfo,movedata,moveabbrs):
    cmovedata = dict()

    for key,cmove in charinfo["custom moves"].items():
        cmovedata[key] = cmove

    cmoveabbrs = loadabbrs(cmovedata.keys())
    cmovedata.update(movedata)
    cmoveabbrs.update(moveabbrs)
    cmoveabbrs = dedupabbrs(cmoveabbrs)
    
    return cmovedata,cmoveabbrs

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
