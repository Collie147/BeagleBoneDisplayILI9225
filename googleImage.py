from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from shutil import copyfile
from PIL import Image, ImageDraw, ImageFont
import BHack_ILI9225 as TFT
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import sys, time, os, random, psutil
from memory_profiler import profile

# BeagleBone Black configuration.
RS = 'P9_15'
RST = 'P9_12'
SPI_PORT = 1
SPI_DEVICE = 0

#Connect LCD screen to pins below
# SPI0_CS0 = P9_17
# SPI0_SLCK = P9_22
# SPI0_D1 (MOSI) = P9_18

# Create TFT LCD display class.
disp = TFT.ILI9225(RS, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))

#setup the fonts
font = ImageFont.truetype('./KeepCalm.ttf', 26)
font_small = ImageFont.truetype('./metal.ttf', 20)

#create basic colors
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0 , 0)
green = (0, 255, 0)
blue = (0, 0, 255)

#set the size of the display
size = (220, 176)

# Initialize display.
disp.begin()


#set the image file name to copy the google pic into
imagename = 'image1.jpg'


#create a blank background to start - i.e. clear the display!
testImage = Image.new('RGB', (176, 220), black)

disp.display(testImage)

#setup some basic variables
count = 0 #a total count of the pictures displayed
totalPics = 0 #the total number of files available
oldRandom = 0 #get the old random number so we're not displaying the same one twice
file_list = None #variable for the list of files (this will be in JSON array format)
imageheight = 0 #variable for the image height (might be used later)
imagewidth = 0 #variable for the image width (might be used later)
googlePhotosFolderName = "Google Photos" #name of the folder where the images are stored in google drive
delay = 20 #set the time to leave the image on screen before getting a new picture
def connectToGoogleDrive():
    global file_list #link the variable to the global one
    global totalPics
    try:
        gauth = GoogleAuth()                             # Google drive API
        gauth.LoadCredentialsFile("mycreds.txt")         # Try to load saved client credentials
        if gauth.credentials is None:                    # Authenticate if they're not there
            auth.LocalWebserverAuth()
        elif gauth.access_token_expired:                 # Refresh them if expired
            gauth.Refresh()
        else:                                            # Initialize the saved creds
            gauth.Authorize()
        gauth.SaveCredentialsFile("mycreds.txt")         # Save the current credentials to a file
        drive = GoogleDrive(gauth)                       # Set drive location using .json file
        #list all the folders to find the ID for the "Google Photos" folder
        folder_list = drive.ListFile({"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
        googlePhotosFolderId = None #set a blank variable for the ID
        for folder in folder_list:  #for each folder
            if folder['title'] == googlePhotosFolderName: #if the folders title is teh same as the google photos folder above
                googlePhotosFolderId = folder['id'] #set the id
                break #break so we dont keep running the query for the rest of the values
        #set the file list to the files within the google photos folder		
        file_list = drive.ListFile({'q': "'" + googlePhotosFolderId + "' in parents and trashed=false"}).GetList()
        totalPics = len(file_list) #get a total pics so we can select them at random later
    except:
        print ("ERROR connecting to google drive: ", sys.exc_info()[0]) #if there are any exceptions print the error 
        connectToGoogleDrive() #start again

connectToGoogleDrive() #run the function above
#@profile 

#function to draw the text over the image
def draw_rotated_text(image, text, position, angle, font, fill=(255,255,255), bgtext=(255,255,255,255)):
    draw = ImageDraw.Draw(image) #draw the image
    width, height = draw.textsize(text, font=font) #set the width and the height of the text image
    textimage = Image.new('RGBA', (width, height), bgtext) #create a new image with the text 
    textdraw = ImageDraw.Draw(textimage) #set it as an ImageDraw 
    textdraw.text((0,0), text, font=font, fill=fill)
    rotated = textimage.rotate(angle, expand=1) #rotate it 
    image.paste(rotated, position, rotated) # paste it over the original image

#@profile
def getGooglePhoto(number, imagefile):
    global count #set the variables to the global values
    global oldRandom
    global imageheight
    global imagewidth
    try:
        downloadFile = file_list[number] #grab the file from the list using the number specified
        #print (downloadFile)
        filename = downloadFile['originalFilename'] #get the filename
        filesize = downloadFile['fileSize'] #get the file size
        filetype = downloadFile['mimeType'] # get the file type
        
        mem = psutil.virtual_memory() # get the available memory
        #print(filename, " | ", filesize, " | ", mem[4])
        #print (mem)
        #print('filesize:',type(filesize), " | mem[4]:", type(mem[4]))
        if filetype == 'image/jpeg': #if the file is a jpeg
            metaData = downloadFile['imageMediaMetadata'] #get any meta data for the file
            imagewidth = metaData['width'] #get the height
            imageheight = metaData['height'] #get the width
            if int(filesize) < mem[4]/2 and imageheight < 4000 and imagewidth < 4000: #if the file isnt more than half the available memory or its got a lot of pixels (beaglebone doesnt have a lot of memory to do image adjustments)
                downloadFile.GetContentFile(imagefile) #download the file and save it as the imagefile variable value (image1.jpg)
                count = count+1 #increment the counter
                print('Count: ', count, " | filename: ", filename, " | imageheight: ", imageheight, " | imagewidth: ", imagewidth) # print the values
            else : #image is too big either by size or memory available
                print ("image file too big for BeagleBone - imageheight: ", imageheight, " | imagewidth: ", imagewidth)
                print ("getting a new image")
                getGooglePhoto(getRandom(0,totalPics-1), imagefile) #start again
        else : # its not a jpeg
            print ("not a JPEG getting a new image")
            getGooglePhoto(getRandom(0,totalPics-1), imagefile) # start again
    except:
        print("ERROR getting Google Photo ", downloadFile['originalFilename'],": ",sys.exc_info())
        #copyfile('backme1.jpg','image1.jpg')
        getGooglePhoto(getRandom(0,totalPics-1), imagefile) # start again

#@profile
def getRandom(firstNum, lastNum): #function to get a random number
    global oldRandom # get the global variable
    randomNumber = random.randint(firstNum, lastNum) # get the random number
    if randomNumber == oldRandom: # if the value is the same as the last one
        randomNumber = getRandom(firstNum, lastNum) #go again
    else: #if its different
       oldRandom = randomNumber # save the value for the next run
    return randomNumber #return the number

#@profile
def openAndRotateImage(): #function to open the image, rotate and resize
    newImage = Image.open(imagename)
    newImage = newImage.rotate(90)
	
	#this is a function to resize but keep the aspect ratio.
	#it only seems to work when pasted onto a background as throws the rest askew with the ILI9225 library
	#will look at this further down the line
	
    #if imageheight > imagewidth:
    #    heightRatio = imageheight / 220
    #    newImageWidth = imagewidth / heightRatio
    #    newImage = newImage.resize((int(newImageWidth),220))
    #    print("new width: ", int(newImageWidth), " | height: 220")
    #elif imagewidth > imageheight:
    #    widthRatio = imagewidth / 176
    #    newImageHeight = imageheight / widthRatio
    #    newImage = newImage.resize((176,int(newImageHeight)))
    #    print("width: 176 | new height: ", int(newImageHeight))
    #else:
	
    newImage = newImage.resize((176,220), Image.ANTIALIAS) # resize
    #print ("pasting image")
    #testImage.paste(newImage)
    #newImage = newImage.rotate(90)
    disp.buffer = newImage #set the display buffer as the new image - load it into memory
    newImage = None #make sure the variable is clear (so there are no memory leaks)

while (True):

    randomNum = getRandom(0, totalPics-1) # get a random number
    getGooglePhoto(randomNum, imagename) # get the google photo of that number and save it to the imagename
    #disp.buffer = Image.new("RGB", (176, 220), (0,0,0))
    try:
        print("opening image and resizing")
        openAndRotateImage() #open the image and rotate it correctly
    except:
        print("ERROR resizing image: ", sys.exc_info()[0]) 
        getGooglePhoto(randomNum, imagename)
        openAndRotateImage()
    print ('Drawing time/date with image as background')
    #draw the date over the image
    draw_rotated_text(disp.buffer, time.strftime("%d/%m/%y "), (4, 0), 90, font, fill=(255,255,255), bgtext=(0,0,0,0))
    #draw the time over the image
    draw_rotated_text(disp.buffer, time.strftime("%H:%M "), (5, 130), 90, font, fill=(255,255,255), bgtext=(0,0,0,0))
    disp.display() #display the buffer
    disp.buffer = None # clear the buffer
    time.sleep(delay) #wait the delay set before getting another one
