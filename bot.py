from datetime import datetime, timedelta
import json
import time
import uuid
import zoneinfo
import discord
import os # default module
from dotenv import load_dotenv
import requests
import os.path
from playwright.async_api import async_playwright, Playwright
import re
from discord.ext import tasks
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import drawsvg as draw
import tkinter as tk
from tkinter import font
import base64

load_dotenv() # load all the variables from the env file
bot = discord.Bot()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
schedView ='https://calendar.google.com/calendar/embed?height=600&wkst=1&ctz=America%2FNew_York&showPrint=0&title=Premier%20Schedule&mode=AGENDA&src=MzQzYjc1MmFlOGIyOTQyZGJlOWEyZjJhYTMyYTA0NzBkNTBlY2ZjNDQwOWRmZmQxODM4NTFkN2Y0ZDM1YjI1YkBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=OTI3MTI0ZmI3MTA5Y2U0YWRlNGMwOTgyNzc5NTFjZGRjODViMWIzZWM5NmYzYWY1M2Q0MjI3MmQwZjNiMGRmY0Bncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=YjM5NWVlNGRkZDY0NzRkNjBhNjljOTExZDc2YzA0YmFkZjY0NDUxZTI2YTFkZmIxMDEyZjU2NDgyZGZmNTM4MUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&color=%237986cb&color=%23d50000&color=%23c0ca33'
friendlySchedView ='https://calendar.google.com/calendar/embed?height=600&wkst=1&ctz=America%2FNew_York&showPrint=0&title=VGC%20Friendly%20Leagues&mode=AGENDA&src=ZWI1ZDljNDZlODU3ODBjYmU5YjBkZjM2NTg1YWI1MmZjOTMyYTU5ZTFjNWU0OTc2MDEzNWU3ZjI2NjA2ZGE0YUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=ODczZmE4MTNkNzFkOTljNzM1MWU0MDcwODZlYjBlOWQ3MjA4YzcwNTMzZGM4Y2ExMWUzNTY0ODUyZTA1MzQ0OEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=YWQ1MWRjMTgwZjEzMzdjY2MyMjhmOGY2MTk3MzQwOGQ5Y2M3ZTc0ODcxY2I2MWU4ZmMwZWEyNzIwM2U0ZTIxMEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&color=%23ad1457&color=%23e4c441&color=%23e67c73'


allCalView = 'https://calendar.google.com/calendar/embed?height=600&wkst=1&ctz=America%2FNew_York&showPrint=0&title=All%20DMV%20VGC%20Events&src=ZWI1ZDljNDZlODU3ODBjYmU5YjBkZjM2NTg1YWI1MmZjOTMyYTU5ZTFjNWU0OTc2MDEzNWU3ZjI2NjA2ZGE0YUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=ODczZmE4MTNkNzFkOTljNzM1MWU0MDcwODZlYjBlOWQ3MjA4YzcwNTMzZGM4Y2ExMWUzNTY0ODUyZTA1MzQ0OEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=YWQ1MWRjMTgwZjEzMzdjY2MyMjhmOGY2MTk3MzQwOGQ5Y2M3ZTc0ODcxY2I2MWU4ZmMwZWEyNzIwM2U0ZTIxMEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=MzQzYjc1MmFlOGIyOTQyZGJlOWEyZjJhYTMyYTA0NzBkNTBlY2ZjNDQwOWRmZmQxODM4NTFkN2Y0ZDM1YjI1YkBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=OTI3MTI0ZmI3MTA5Y2U0YWRlNGMwOTgyNzc5NTFjZGRjODViMWIzZWM5NmYzYWY1M2Q0MjI3MmQwZjNiMGRmY0Bncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=YjM5NWVlNGRkZDY0NzRkNjBhNjljOTExZDc2YzA0YmFkZjY0NDUxZTI2YTFkZmIxMDEyZjU2NDgyZGZmNTM4MUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&color=%23ad1457&color=%23e4c441&color=%23e67c73&color=%237986cb&color=%23d50000&color=%23c0ca33'
friendlyCalView = 'https://calendar.google.com/calendar/embed?height=600&wkst=1&ctz=America%2FNew_York&showPrint=0&title=VGC%20Friendly%20Leagues&src=ZWI1ZDljNDZlODU3ODBjYmU5YjBkZjM2NTg1YWI1MmZjOTMyYTU5ZTFjNWU0OTc2MDEzNWU3ZjI2NjA2ZGE0YUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=ODczZmE4MTNkNzFkOTljNzM1MWU0MDcwODZlYjBlOWQ3MjA4YzcwNTMzZGM4Y2ExMWUzNTY0ODUyZTA1MzQ0OEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=YWQ1MWRjMTgwZjEzMzdjY2MyMjhmOGY2MTk3MzQwOGQ5Y2M3ZTc0ODcxY2I2MWU4ZmMwZWEyNzIwM2U0ZTIxMEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&color=%23ad1457&color=%23e4c441&color=%23e67c73'

vaCalId = 'b395ee4ddd6474d60a69c911d76c04badf64451e26a1dfb1012f56482dff5381@group.calendar.google.com'
mdCalId = '927124fb7109ce4ade4c098277951cddc85b1b3ec96f3af53d42272d0f3b0dfc@group.calendar.google.com'
dcCalId = '343b752ae8b2942dbe9a2f2aa32a0470d50ecfc4409dffd183851d7f4d35b25b@group.calendar.google.com'

friendlyVaCalId = 'ad51dc180f1337ccc228f8f61973408d9cc7e74871cb61e8fc0ea27203e4e210@group.calendar.google.com'
friendlyMdCalId = '873fa813d71d99c7351e407086eb0e9d7208c70533dc8ca11e3564852e053448@group.calendar.google.com'
friendlyDcCalId = 'eb5d9c46e85780cbe9b0df36585ab52fc932a59e1c5e49760135e7f26606da4a@group.calendar.google.com'

guidRegex = r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
nonPremierEventType = 'nonpremier VG'

messageListFile = 'updateMessages.json'

def isNonPremier(e):
    try:
        if(e['type']):
            return e['type'] == nonPremierEventType
        return nonPremierEventType in str(e['description'])
    except:
        print('could not determine type of event for:' + e)
        return False

def hasSanctionedUrl(e):
    tournamentUrlEnding = r"/[0-9]{2}-[0-9]{1,2}-[0-9]*/"
    if(e['pokemon_url']):
        guidSearch = re.search(tournamentUrlEnding,  str(e['pokemon_url']))
        if guidSearch:
           return True
    elif(e['description']):
        guidSearch = re.search(tournamentUrlEnding,  str(e['pokemon_url']))
        if guidSearch:
            return True
    return False
        
def getEventTz(e):
    if isNonPremier(e):
       if not hasSanctionedUrl(e):
        return 'UTC'
    return 'America/New_York'

def getEventCalId(e):
    if(isNonPremier(e)):
        match e['state']:
            case 'Virginia':
                return friendlyVaCalId
            case 'Maryland':
                return friendlyMdCalId
            case 'District of Columbia':
                return friendlyDcCalId
    else:
        match e['state']:
            case 'Virginia':
                return vaCalId
            case 'Maryland':
                return mdCalId
            case 'District of Columbia':
                return dcCalId
    
    return ''

async def getVGEvents():
    url = "https://www.pokedata.ovh/events/tableapi/index_table.php"

    payload = {
        "past": False,
        "country": "US",
        "city": "",
        "shop": "",
        "league": "",
        "states": "[\"District of Columbia\",\"Maryland\",\"Virginia\"]",
        "postcode": "",
        "cups": False,
        "challenges": False,
        "vcups": True,
        "vchallenges": True,
        "prereleases": False,
        "premier": False,
        "go": False,
        "gocup": False,
        "mss": False,
        "ftcg": False,
        "fvg": True,
        "fgo": False,
        "latitude": "",
        "longitude": "",
        "radius": "",
        "unit": "km",
        "width": 2133,
        "page": 0,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json; charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
        "origin": "https://www.pokedata.ovh",
        "referer": "https://www.pokedata.ovh/events/"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        sorted(data, key=lambda event: event['when'])
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
   
async def getExistingCalItems():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = (datetime.now() -  timedelta(hours=3)).astimezone().isoformat() #dont delete possibly in progress events from the calendar
        events_result = (
            service.events()
            .list(
                calendarId=vaCalId,
                timeMin=now,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        events_result = (
                service.events()
                .list(
                    calendarId=mdCalId,
                    timeMin=now,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        events = events + events_result.get("items", [])
        
        events_result = (
            service.events()
            .list(
                calendarId=dcCalId,
                timeMin=now,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events + events_result.get("items", [])
        
        events_result = (
            service.events()
            .list(
                calendarId=friendlyVaCalId,
                timeMin=now,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events + events_result.get("items", [])
        
        events_result = (
            service.events()
            .list(
                calendarId=friendlyDcCalId,
                timeMin=now,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events + events_result.get("items", [])
        
        events_result = (
            service.events()
            .list(
                calendarId=friendlyMdCalId,
                timeMin=now,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events + events_result.get("items", [])
        
        if not events:
            return []

        return events    
    except HttpError as error:
        print(f"An error occurred: {error}")
                 
async def pushToCal(data, existingEvents):    
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
        token.write(creds.to_json())

    guids = []
    for e in existingEvents:
        guidSearch = re.search(guidRegex,  str(e['description']))
        if guidSearch:
            guids.append(guidSearch.group(0))  

    now = datetime.now().astimezone()
    try:
        service = build("calendar", "v3", credentials=creds)
                
        data = [x for x in data if x['guid'] not in guids]
        for e in data:
            startTime = datetime.strptime(e['when'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo(getEventTz(e)))
            if startTime < now:
                continue
            
            endTime = startTime + timedelta(0,0,0,0,0,3)
            calId = getEventCalId(e)                
            
            
            typeLabel = ''
            emoji = ''
            if isNonPremier(e):
                typeLabel = 'Friendly League'
                emoji = '👥' 
            else :
                typeLabel = e['type']
                if e['type'] == 'League Challenge VG':
                    emoji = '🥊'
                else:
                    emoji = '🏆'
                    
            event = {
                'summary': emoji + ' ' + e['shop'] + ' ('+ e['state']+')',
                'location': e['street_address'],
                'description': typeLabel + ('\n<a href="' + e['pokemon_url']+ '">Official Event Page</a>' if hasSanctionedUrl(e) else '') + '\n\n\n' + e['guid'],
                'start': {
                    'dateTime': startTime.isoformat(),
                },
                'end': {
                    'dateTime': endTime.astimezone().isoformat(),
                }
            }

            calEvent = service.events().insert(calendarId=calId, body=event).execute()
            print ('Event created: %s at %s' % (calEvent.get('htmlLink'), now.isoformat()))
            
    except HttpError as error:
        print(f"An error occurred: {error}")

async def checkAndUpdateEvents(playListings, existingCalEvents):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
        token.write(creds.to_json())
        
    try:
        service = build("calendar", "v3", credentials=creds)
        
        for calEvent in existingCalEvents:
            guidSearch = re.search(guidRegex,  str(calEvent['description']))
            if guidSearch:
                popId = guidSearch.group(0)
                popEventMatches = [x for x in playListings if x['guid'] == popId]
                                
                if len(popEventMatches) != 1:
                    continue
                
                popEvent = popEventMatches[0]
                popWhenAdjusted = datetime.strptime(popEvent['when'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo(getEventTz(popEvent))).astimezone()
                
                # no update needed
                if(str(calEvent['start']['dateTime']).replace('T', ' ') == str(popWhenAdjusted)):
                    continue
                       
                endTime = popWhenAdjusted + timedelta(0,0,0,0,0,3)
                calId = getEventCalId(popEvent)                
                    
                event = {
                    'start': {
                        'dateTime': popWhenAdjusted.isoformat(),
                    },
                    'end': {
                        'dateTime': endTime.astimezone().isoformat(),
                    }
                }
                
                now = datetime.now().astimezone().isoformat()
                calEvent = service.events().patch(calendarId=calId, eventId=calEvent['id'], body=event).execute()
                print ('Event updated: %s at %s' % (calEvent.get('htmlLink'), now))
                          
    except HttpError as error:
        print(error)
 
async def checkAndDeleteEvents(playListings, existingCalEvents):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
        token.write(creds.to_json())
        
    try:
        service = build("calendar", "v3", credentials=creds)
        existingCalendarGuids = []
        for calEvent in existingCalEvents:
            guidSearch = re.search(guidRegex,  str(calEvent['description']))
            if guidSearch:
                existingCalendarGuids.append(guidSearch.group(0))
                
        popGuids = [x['guid'] for x in playListings]
        canceledEvents = [x for x in existingCalendarGuids if x not in popGuids]
        
        for calEvent in existingCalEvents:
            guidSearch = re.search(guidRegex,  str(calEvent['description']))
            if guidSearch and guidSearch.group(0) in canceledEvents:                   
                now = datetime.now().astimezone().isoformat()
                service.events().delete(calendarId=calEvent['organizer']['email'], eventId=calEvent['id']).execute()
                print ('Event deleted: %s at %s' % (calEvent['summary'], now))
                          
    except HttpError as error:
        print(error)      

async def makeGraphic():
        root = tk.Tk()
        
        with open("graphicConfig.json") as cfg:
            config = json.load(cfg)
        embedH = config['embedH']
        embedW = config['embedW']
        headerHeight = config['headerHeight']
        margin = config['margin']
        headerGradientStartColor = config['headerGradientStartColor']
        headerGradientEndColor = config['headerGradientEndColor']
        headerFont = config['headerFont']
        fontFamily = config['fontFamily']
        rowIndex = config['rowIndex']
        rowHeight = config['rowHeight']
        rowScheduleStart = config['rowScheduleStart']
        imageBackground = config['imageBackground']
        textPrimaryColor = config['textPrimaryColor']
        headerTextColor = config['headerTextColor']
        locationTextColor = config['locationTextColor']
        rowBackground = config['rowBackground']
        highlightColor = config['highlightColor']
        logoSize = config['logoSize']
        cornerRadius = config['cornerRadius']
        cupIconPath = config['cupIconPath']
        chalIconPath = config['chalIconPath']
        logoPath = config['logoPath']
        
        existingEvents = await getExistingCalItems()
        if(existingEvents is None or len(existingEvents) == 0):
            return
        existingEvents = [x for x in existingEvents if x['organizer']['email'] in [vaCalId, mdCalId, dcCalId]]
        
        d = draw.Drawing(embedW, embedH, origin='top-left', font_family=fontFamily)
        # d.append(draw.Rectangle(0, 0, embedW, embedH, fill=imageBackground))
        
        #header branding
        css_rules = f"""
            .title-text {{
                font-size: 54px;
                font-style: italic;
                font-width: expanded;
            }}
        """
        d.append_css(css_rules)
        
        gradient2 = draw.LinearGradient(1, embedW/6, embedW/2, embedW/3)
        gradient2.add_stop(0, headerGradientStartColor, 1)
        gradient2.add_stop(1, headerGradientEndColor, 1)
        d.append(draw.Rectangle(margin, 0, embedW - (2*margin), headerHeight, fill='white', rx=cornerRadius, ry=cornerRadius))
        d.append(draw.Rectangle(margin, 0, embedW - (2*margin), headerHeight, fill=gradient2, rx=cornerRadius, ry=cornerRadius))
        
        d.append(draw.Image( x=margin + 20, y=margin, width=logoSize, height=logoSize,  path=logoPath, embed=True) )
        d.append(draw.Text('DMV Upcoming Premier Events', 54, 640, 50, fill=headerTextColor, center=True, class_='title-text', font_family=headerFont)) 
            
        for i in range(headerHeight, embedH, rowHeight):
            if rowIndex > len(existingEvents)-1: 
                continue
            e = existingEvents[rowIndex]
            rowBaseline = i + 26
            
            #draw dividers if dif date from last and write date
            currentStart = datetime.strptime(e['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
            if rowIndex < len(existingEvents)-1: 
                d.append(draw.Rectangle(5, i+10, embedW-10, rowHeight+20, fill=rowBackground))
            d.append(draw.Rectangle(5, i, embedW-10, rowHeight, fill=rowBackground,  rx=cornerRadius, ry=cornerRadius))
                
            if(rowIndex != 0):
                previousStartDate = datetime.strptime(existingEvents[rowIndex-1]['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z').date()
                if(currentStart.date() != previousStartDate):
                    d.append(draw.Line(margin, i, embedW-margin, i, stroke=imageBackground, stroke_width=2))
                    d.append(draw.Text(currentStart.strftime("%d"), 18, 16, rowBaseline, fill= textPrimaryColor))
                    d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, rowBaseline, fill= textPrimaryColor))
            else:
                # line 1
                if(currentStart.date() == datetime.now().date()):
                    d.append(draw.Circle(26, i + 20, 16, fill=highlightColor))
                    d.append(draw.Text(currentStart.strftime("%d"), 18, 16, rowBaseline, fill=imageBackground))
                    d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, rowBaseline, fill=highlightColor))
                else:
                    d.append(draw.Text(currentStart.strftime("%d"), 18, 16, rowBaseline, fill= textPrimaryColor))
                    d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, rowBaseline, fill= textPrimaryColor))
            
            
            color = textPrimaryColor
            if(e['organizer']['email'] == vaCalId):
                color = 'green'
            elif(e['organizer']['email'] == dcCalId):
                color = 'purple'
            elif(e['organizer']['email'] == mdCalId):
                color = 'red'
                    
            rowGroup = draw.Group()
            
        # schedule data
            schedGroup = draw.Group()  
            bullet = draw.Circle(0, -4 , 6, fill=color)
            schedGroup.append(bullet) # Draw a circle
            startTime = currentStart.strftime("%I:%M%p")
            schedGroup.append(draw.Text(startTime, 12, 20, 0, fill= textPrimaryColor))
                
        # event data
            eventGroup = draw.Group()
            rowFontSize = 14
            emojiStart = 20
            emojiWidth = 20
            fsPixels = font.Font(family= fontFamily, size=rowFontSize-2)
            
            icon = ''
            if(str(e['summary']).startswith('🥊')):
                icon = chalIconPath                    
            elif(str(e['summary']).startswith('🏆')):
                icon = cupIconPath
            eventGroup.append(draw.Image( x=emojiStart, y= -20, width=emojiWidth, height=30,  path=icon, embed=True) )               
            
            titleStart = emojiStart + emojiWidth + 5
            title = str(e['summary'])[1:]
            titleWidth = fsPixels.measure(title)
            eventGroup.append(draw.Text(title, rowFontSize, titleStart, 0, fill= textPrimaryColor))
            eventGroup.append(draw.Text(e['location'], rowFontSize, titleStart + titleWidth, 0, fill=locationTextColor))
            
            rowGroup.append(draw.Use(schedGroup, 0, 0))
            rowGroup.append(draw.Use(eventGroup, 120, 0))
            
            d.append(draw.Use(rowGroup, rowScheduleStart, rowBaseline))
            rowIndex += 1
    
        d.set_pixel_scale(2)  # Set number of pixels per geometry unit
        #d.set_render_size(400, 200)  # Alternative to set_pixel_scale
        d.save_svg('output/schedule.svg')
        # cairosvg.svg2png(url="schedule.svg", write_to="schedule.png")
        d.save_png('output/schedule.png')
                     
async def getScreenshot(playwright: Playwright):
    browser = await playwright.chromium.launch()
    page = await browser.new_page()
    await page.goto(schedView)
    await page.wait_for_timeout(2000)
    await page.screenshot(path='output/schedule.png', full_page=True)
    await browser.close()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    if not Path(messageListFile).is_file():
        with open(messageListFile, "w") as file:
            file.write("[]")
    runUpdate.start()
    print(f"{bot.user} has initialized!")

@tasks.loop(hours=1)
async def runUpdate():
    print(f"running update at {(datetime.now()).astimezone().isoformat()}")
    data = await getVGEvents()
    existingEvents = await getExistingCalItems()
    
    await pushToCal(data, existingEvents)
    await checkAndUpdateEvents(data, existingEvents)
    await checkAndDeleteEvents(data, existingEvents)
    
    # async with async_playwright() as playwright:
    #     await getScreenshot(playwright)
    await makeGraphic()
    
    embed = discord.Embed(
        title="DMV VGC Schedule",
        color=discord.Color.yellow()
    )
    
    embed.add_field(
        name="Premier Events", 
        value="[Click here to sync to your calendar](https://calendar.google.com/calendar/u/0/r?cid=343b752ae8b2942dbe9a2f2aa32a0470d50ecfc4409dffd183851d7f4d35b25b@group.calendar.google.com&cid=927124fb7109ce4ade4c098277951cddc85b1b3ec96f3af53d42272d0f3b0dfc@group.calendar.google.com&cid=b395ee4ddd6474d60a69c911d76c04badf64451e26a1dfb1012f56482dff5381@group.calendar.google.com)"
        , inline=True
    )
    
    embed.add_field(
        name="Upcoming Premier Events", 
        value=f"[View Premier Schedule]({schedView})"
        , inline=True
    )
    
    embed.add_field(
        name="", 
        value=""
        , inline=False
    )
    
    embed.add_field(
        name="League/Friendly Events", 
        value="[Click here to sync to your calendar](https://calendar.google.com/calendar/u/0/r?cid=eb5d9c46e85780cbe9b0df36585ab52fc932a59e1c5e49760135e7f26606da4a@group.calendar.google.com&cid=873fa813d71d99c7351e407086eb0e9d7208c70533dc8ca11e3564852e053448@group.calendar.google.com&cid=ad51dc180f1337ccc228f8f61973408d9cc7e74871cb61e8fc0ea27203e4e210@group.calendar.google.com)"
        , inline=True
    )
    
    embed.add_field(
        name="Upcoming Friendly Events",
        value=f"[View Leage Schedule]({friendlySchedView})"
        ,inline=True
    )
    
    embed.add_field(
        name="Last updated at", 
        value=f"{str(time.strftime('%I:%M %p on %b %d, %Y'))}"
        , inline=False
    )
    
    embed.url = allCalView
    
    # Display images or graphical assets
    embed.set_image(url="attachment://output/schedule.png")
    
    curChannel = None
    curMessage = None
    
    
    channels = []
    with open(messageListFile, 'r+', encoding='utf-8') as file:
        channels = json.load(file)
    if not channels:
        return
    
    for msg in channels:
        curChannel = msg['channelId']
        curMessage = msg['messageId']
        try: 
            channel = await bot.fetch_channel(curChannel)
            msg = await channel.fetch_message(curMessage)
            await msg.edit(file=discord.File("output/schedule.png", filename="output/schedule.png"), embed=embed)
        except discord.errors.NotFound as error:
            with open(messageListFile, 'r+') as file:
                channels = json.load(file)
                valids = [x for x in channels if x['channelId'] != curChannel]
                    
            tempfile = os.path.join(os.path.dirname(messageListFile), str(uuid.uuid4()))
            with open(tempfile, 'w') as f:
                json.dump(valids, f, indent=4)

            # rename temporary file replacing old file
            os.replace(tempfile, messageListFile)
        
@bot.slash_command(name="sync", description="get dmv vgc schedule data")
async def sync(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator and not await ctx.bot.is_owner(ctx.author):
        await ctx.respond("I don't make deals with peasants!", ephemeral=True)
        return
    
    runUpdate.cancel()
    embed = discord.Embed(
        title="DMV VGC Schedule",
        color=discord.Color.yellow()
    )
    
    embed.add_field(
        name="Initalizing", 
        value="Hold tight for like 15 seconds pls"
        , inline=True
    )
       
    embed.url = allCalView
    await ctx.respond(content="Come on Barbie let's go party!", ephemeral=True)
    message = await ctx.send(embed=embed) 
    
    channelId = ctx.channel_id
    messageId = message.id

    channels = []
   
    with open(messageListFile, 'r+') as file:
        channels = json.load(file)
        matches = [x for x in channels if x['channelId'] == channelId]
        if not matches or len(matches) == 0:
            channels.append({"channelId":channelId, "messageId":messageId})
            
    # create randomly named temporary file to avoid 
    # interference with other thread/asynchronous request
    tempfile = os.path.join(os.path.dirname(messageListFile), str(uuid.uuid4()))
    with open(tempfile, 'w') as f:
        json.dump(channels, f, indent=4)

    # rename temporary file replacing old file
    os.replace(tempfile, messageListFile)
    
    runUpdate.start()

@bot.slash_command(name="manualsync", description="force all instances to update")
async def manualsync(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator and not await ctx.bot.is_owner(ctx.author):
        await ctx.respond("I don't make deals with peasants!", ephemeral=True)
        return
    
    runUpdate.cancel()
    await ctx.respond(content="forcing schedule update!", ephemeral=True)
    runUpdate.start()

bot.run(os.getenv('TOKEN')) # run the bot with the token