from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import argparse, time, random, ctypes, os
import urllib.request as url
from PIL import Image, ImageDraw, ImageFont
import BHack_ILI9225 as TFT
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI

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

maxWidth = '176'
maxHeight = '220'
size = (maxWidth, maxHeight)

oldRandom = None
photoName = 'myPhoto.jpg'
timerSet = 0
timerDelay = 3600
black = (0, 0, 0)

testImage = Image.new('RGB', (176, 220), black)

disp.begin()
disp.display(testImage)
googlePhoto = Image.open(photoName).rotate(90).resize((176,220), Image.ANTIALIAS) #resize width, height
albumName = "Google Photos Slideshow" #this is whatever album you want to display photos from on your device
print("displaying photo")
disp.display(googlePhoto)

def Timer():
   now = time.localtime(time.time())
   return now[5]

def ConnectToGoogleImages():
    SCOPES = 'https://www.googleapis.com/auth/photoslibrary.readonly'
    gdriveservice = None
    credsFileName = 'mycredsnew.txt'
    store = file.Storage(credsFileName)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--logging_level', default='ERROR')
        parser.add_argument('--noauth_local_webserver', action='store_true',
           default=True, help='Do not run a local web server.')
        args = parser.parse_args([])
    
        creds = tools.run_flow(flow, store, args)
        gdriveservice = build('photoslibrary', 'v1', http=creds.authorize(Http()))
        credentials_file = open(credsFileName, 'wb')
        store.put(credsFileName)
    else:
        gdriveservice = build('photoslibrary', 'v1', http=creds.authorize(Http()))
    album_results = gdriveservice.albums().list(pageSize=20).execute()
    album_items = album_results.get('albums', [])
    album_id_array = []
    slideshowAlbumId = None
    for item in album_items:
            print(u'{0} ({1})'.format(item['title'].encode('utf8'), item['id']))
            album_id_array.append(item['id'])
            if item['title'] == albumName:
                slideshowAlbumId = item['id']

    nextPageToken = ''
    #media_results = gdriveservice.mediaItems().search(body={}).execute() #search all items
    media_results = gdriveservice.mediaItems().search(body={"albumId": slideshowAlbumId, "pageSize" :10, "pageToken" :nextPageToken}).execute()
    media_list = media_results['mediaItems']
    #while nextPageToken != '':
    while 'nextPageToken' in media_results:    
        #nextPageToken = media_results['nextPageToken']
        #nextPageToken = '' if nextPageToken == 'Dummy' else nextPageToken
        nextPageToken = media_results['nextPageToken']
        media_results = gdriveservice.mediaItems().search(body={"albumId": slideshowAlbumId, "pageSize" :10, "pageToken" : nextPageToken}).execute()
        for item in media_results['mediaItems']:
            media_list.append(item)
    print ("Total: ",len(media_list))
    return media_list
    


def getRandom(firstNum, lastNum): #function to get a random number
    global oldRandom # get the global variable
    randomNumber = random.randint(firstNum, lastNum) # get the random number
    if randomNumber == oldRandom: # if the value is the same as the last one
        randomNumber = getRandom(firstNum, lastNum) #go again
    else: #if its different
       oldRandom = randomNumber # save the value for the next run
    return randomNumber #return the number

def DownloadRandomPhoto(media_list):
    #for item in media_list:
        #print ("filename: ",item['filename'], " | id: ",item['id'])
    downloadFile = media_list[getRandom(0, len(media_list))]
    filetype = downloadFile['mimeType']
    if filetype == 'image/jpeg':
        downloadUrl = downloadFile['baseUrl']+'=w'+maxWidth+'-h'+maxHeight
        url.urlretrieve(downloadUrl, photoName)

    
media_list = None
running = True
while(running):
    if ((Timer() - timerSet) > timerDelay) or (media_list == None): #this timer runs every 60 minutes as google photos api times out after an hour
        timerSet = Timer()
        media_list = ConnectToGoogleImages()
    DownloadRandomPhoto(media_list)
    googlePhoto = Image.open(photoName).rotate(90).resize((176,220), Image.ANTIALIAS)

    disp.buffer = googlePhoto
    print("displaying photo")
    disp.display()
    time.sleep(10)

