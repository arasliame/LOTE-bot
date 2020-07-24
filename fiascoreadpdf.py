import PyPDF4
import json
import re
from pathlib import Path


def loadpdf(fileobj):
    #fullpath = Path(__file__).parent.joinpath(filename)
    reader = PyPDF4.PdfFileReader(fileobj.open(mode="rb"))
    return reader

# for each part in the ToC, create dictionary with start and end pages
def tableofcontents(pdffile):
    outline = pdffile.getOutlines()
    toc = dict()
    prevdest = None
    for dest in outline: 
        print(dest)
        toc[dest.title] = {"startpage":reader.getDestinationPageNumber(dest)}
        if prevdest:
            toc[prevdest.title]["endpage"] = reader.getDestinationPageNumber(dest)
        prevdest = dest
    return toc


def cleanstr(inpstr):
    inpstr = inpstr.strip().replace(u"\u2122","'").replace(u"\u02dc","fi")
    inpstr = inpstr.replace(u"\ufb01","\"").replace(u"\ufb02","\"").replace(u"\u0160"," - ")
    inpstr = inpstr.replace(u"\u2013","...").replace(u"\u02da","fl")
    return inpstr

def getsection(pdfreader,startpage,endpage=None):
    # from startpage to endpage, get that all into a big ol string
    sectiontext = ''
    if not endpage:
        endpage = pdfreader.getNumPages()

    for x in range(startpage,endpage):
        page = pdfreader.getPage(x)
        sectiontext += page.extractText()

    lines = list(filter(lambda x: x != ' ', sectiontext.splitlines()))
    return lines  

def loadplaybook(lineslist):
    if not lineslist:
        return
    categories = {'relationships':{},'needs':{},'locations':{},'objects':{}}
    index = 0
    for category in categories:
        while categories[category] == {}:
            mydict = dict()
            parent = 1
            while parent < 7:
                
                if lineslist[index] == str(parent):
                    index += 1
                    catname = cleanstr(lineslist[index]).upper()
                    mydict[parent] = {"category":catname}
                    index += 1
                    element = 1
                    while element < 7:
                    
                        if lineslist[index] == str(element):
                            index += 1
                            z = cleanstr(lineslist[index])
                            mydict[parent][element] = z 
                            index += 1
                            element += 1
                        else:
                            index += 1
                    parent += 1
                else:
                    index += 1
            if mydict:
                categories[category] = mydict
            index += 1

    return categories



def savetojson(mydict,filename):
    if mydict:
        fullpath = Path(__file__).parent.joinpath('playbooks',filename)
    
        with open(fullpath,'w', encoding='utf-8') as fout:
            json.dump(mydict,fout,indent=4) 

        return f"Save successful!"
    else:
        return f"Nothing to save."


if __name__ == "__main__":
    # load all pdf files in the readpdf directory, in which is in same parent dir as this script
    curdir = Path(__file__).parent.joinpath('readpdf')

    for file in curdir.glob('*.pdf'):
        reader = loadpdf(file)
        toc = tableofcontents(reader)
        for section in toc:
            if section not in ['Boilerplate','Table of Contents','Foreword']:
                sectionlines = getsection(reader,toc[section].get("startpage"),toc[section].get("endpage"))
                #print(sectionlines)
                playbookdict = loadplaybook(sectionlines)
                playbookdict["playbookname"] = section
                print(section)
                print(savetojson(playbookdict,f'{file.stem}-{re.sub("[^0-9a-zA-Z]+", "", section)}.json'))
            