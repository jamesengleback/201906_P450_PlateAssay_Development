#This script is used for creating xml files for use with the labcyte echo
#Note:  this script assumes you are using 384 well plates with layouts
#       written in a particular format: "5:50" from well 5 of source plate
#       transfer 50nl, with the target well being the corresponding well of the layout
#P.S.   The script goes to minimal effort to only select for those cells with valid entries,
#       but relies on the user to be vigilant for much of the accuracy. I may add more over time

#commands are written as 20:4, which translates to "20nl from source well 4"
#MAKE SURE EXCEL DOESN'T CHANGE YOUR COMMANDS BY BEING "HELPFUL"

#To do: +take a source plate with named compounds and allow the source IDs to be accessible using the name
#       +Make a symbol/bool for having equal ID for src and dest, or possibly sequential source
#       +Learn more about global functions to cut down on repeated code

#--Ver.2 changes--
# + Added option for having single addition to a full row or column
# + Added the ability to assign a well as "Null", showing it should have no additions
#   The script naturally skips over these as part of the rest of it, so only needed to be added for the full row/col sections
import csv
import collections

#USER--INPUT--SECTION

#This if the file for your plate layout
platefilepath = 'C:\\Users\\josep\\Documents\\work\\Big Mechanism\\echo\\180918 mda mba compounds.csv'
outputpath = 'C:\\Users\\josep\\Documents\\work\\Big Mechanism\\echo\\180918 mda mba compounds.xml'

datsep = '&' #the symbol used for splitting the data in each cell
comsep = '-' #the symbol for separating commands where a command includes source and volume
nullval = 'Null'

#--FUNCTION--SECTION--
#--START--
#This is a function used for opening the csv file and converting it into a dictionary
#The column headers are the dictionary keys
#Note: this function is in the adalabfunctions script, but I include it here to avoid needing a second script
def changecsvintouseful(fileandpath):
    #fileandpath = the name of the file including its path
    #now, we need to separate each file into a list of lists, splitting each csv file row into individual elements for easier iteration
    datatable = []                              #an empty list that'll be our highest heirarchy
    #start by reading the file
    with open(fileandpath, newline='') as csvfile:          #opens the file for reading
        filereader = csv.reader(csvfile,delimiter=' ', quotechar='|')   #gets the file in a form we can read it as
        for row in filereader:      #iterates through each row of the excel file
            templist = []           #just a temporary list we're going to use
            templist = row[0].split(',') #we're going to split the row string object by the commas
            datatable.append(templist)
    #datatable should now be the csv file infor converted into a list of lists
    #next we are going to convert the list into a dictionary
    masterdict = collections.OrderedDict()        #the main dictionary for our things 
    i = 0                           #used for iterating
    while i < len(datatable[0]):    #iterates through the upper list, as these are our column indexes
        masterdict[datatable[0][i]]=[]  #creates the list for them
        for elem in datatable[1:]:
            masterdict[datatable[0][i]].append(elem[i])
        i += 1
    #dictionary done
    return masterdict

def getNullList(layout_dict, nullval):   #Function to get the wells designated null for the full row or column additions
    nullList = []
    layout = layout_dict.copy()
    #some housekeeping to make iteration easier
    for i in layout:
        del layout[i]
        break
    
    for i in layout:        #Section for check "WholeRow" for Nulls
        for index, val in enumerate(layout[i][1:]): #checks if any whole rows have been designated as null
            if nullval in val:
                for wellID in range(int(index*24+1),int(index*24+25)):
                    nullList.append(wellID)
        del layout[i]
        break
    for col in layout:
        #First checks if this column has been designated
        if nullval in layout[col][0]:
            for wellID in range(int(col),int(col)+362,24):
                nullList.append(wellID)
        #Now checks individual cells, script runs fast enough there's no reason to skip this when unneeded
        for index, val in enumerate(layout[col][1:]):
            if nullval in val: #checks if the nullval is contained in it anywhere
                nullList.append(index*24 + int(col))
    return nullList
#--END----


#--WRITING--SECTION--
#--START--
#Setup
#This is the section where we read the data and write it to the xml file
layout_dict = changecsvintouseful(platefilepath)
outfile = open(outputpath, 'w')
outfile.write('<?xml version="1.0"?>')
outfile.write('<TransferPlate>')
#these 4 fragments are used to create each command of xml code
fragment1 = '<Transfer SrcID="'
fragment2 = '" DestID="'
fragment3 = '" Volume="'
fragment4 = '"/>'
null_list = getNullList(layout_dict,nullval)

#This is to remove the "Rows" column as the key was not always read correctly (due to encoding?)
for i in layout_dict:
    del layout_dict[i]
    break

#--For simplicity we will read the single addition option separately then remove them from the dictionary
for col in layout_dict:                       #Check the first row which contains those options for the full row addition
    for i, entry in enumerate(layout_dict[col][1:]):   #iterates through elements, skipping first which has no corresponding row
        #dest = range(int(index*24 + 1), int(index*24 + 25))
        #we follow standard process for checking if there are commands, fully commented in next section apart from the differences
        if comsep in entry:
            comlist = entry.split(comsep)
            for com in comlist:
                if datsep in com:
                    temp = com.split(datsep)
                    for wellID in range(int(i*24+1),int(i*24+25)):
                        if wellID not in null_list:
                            outstr = fragment1 + temp[1].lstrip('0') + fragment2 + str(wellID).lstrip('0') + fragment3 + temp[0].lstrip('0') + fragment4
                            outfile.write(outstr)
        elif datsep in entry:
            temp = entry.split(datsep)
            for wellID in range(int(i*24+1),int(i*24+25)):
                if wellID not in null_list:
                    outstr = fragment1 + temp[1].lstrip('0') + fragment2 + str(wellID).lstrip('0') + fragment3 + temp[0].lstrip('0') + fragment4
                    outfile.write(outstr)

    del layout_dict[col]    #remove full row column now as unneeded
    break                   #we only want to do this once, for the first column

#--Now we will do for the full column additions
for col in layout_dict:                 #Check the first row which contains those options for the full row addition
    element = layout_dict[col].pop(0)   #removes the first element of list, only needed here and sets up for next section, and saves it for use here
    if comsep in element:   #Checks if there's a command seperator
        comlist = element.split(comsep)
        for com in comlist:
            if datsep in com:
                temp = com.split(datsep)
                for wellID in range(int(col),int(col)+362,24):
                    if wellID not in null_list:
                        outstr = fragment1 + temp[1].lstrip('0') + fragment2 + str(wellID).lstrip('0') + fragment3 + temp[0].lstrip('0') + fragment4
                        outfile.write(outstr)              
    elif datsep in element:   #Checks if there's a data element seperator for the parts of a single command
        temp = element.split(datsep)
        for wellID in range(int(col),int(col)+362,24):
            if wellID not in null_list:
                outstr = fragment1 + temp[1].lstrip('0') + fragment2 + str(wellID).lstrip('0') + fragment3 + temp[0].lstrip('0') + fragment4
                outfile.write(outstr)




#--Now we will do the individual well additions
for col in layout_dict:                 #iterates through the columns
    for i, entry in enumerate(layout_dict[col]):   #iterates through the colum entries
        if comsep in entry:             #selects for those with multiple commands to treat them separately
            comlist = entry.split(comsep)   #separates out the commands
            for com in comlist:
                if datsep in com:       #selects for those with a valid seperator still, avoiding null entries
                    temp = com.split(datsep)    #separates the 2 parts of the command
                    #now we build our string
                    destID = int(i*24 + float(col)) #we calculate the destination id from our position in the dictionary
                    outstr = fragment1 + temp[1] + fragment2 + str(destID) + fragment3 + temp[0] + fragment4
                    outfile.write(outstr)           #we write our new line
        elif datsep in entry:        #selects for those with a valid seperator still, avoiding null entries
            temp = entry.split(datsep)    #separates the 2 parts of the command
            #now we build our string
            destID = int(i*24 + float(col)) #we calculate the destination id from our position in the dictionary
            outstr = fragment1 + temp[1].lstrip('0') + fragment2 + str(destID).lstrip('0') + fragment3 + temp[0].lstrip('0') + fragment4
            outfile.write(outstr)           #we write our new line

#now to finish up writing out file
outfile.write('</TransferPlate>')
outfile.close()
