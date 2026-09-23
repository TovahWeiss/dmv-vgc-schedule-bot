from datetime import datetime, timedelta
import time
import zoneinfo
import discord
import os # default module
from dotenv import load_dotenv
import requests
import os.path
from playwright.async_api import async_playwright, Playwright
import re
from discord.ext import tasks

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


load_dotenv() # load all the variables from the env file
bot = discord.Bot()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
schedView ='https://calendar.google.com/calendar/embed?height=702&wkst=1&ctz=America%2FNew_York&title=DMV&mode=AGENDA&showPrint=0&showTz=0&showTabs=0&src=MzQzYjc1MmFlOGIyOTQyZGJlOWEyZjJhYTMyYTA0NzBkNTBlY2ZjNDQwOWRmZmQxODM4NTFkN2Y0ZDM1YjI1YkBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=OTI3MTI0ZmI3MTA5Y2U0YWRlNGMwOTgyNzc5NTFjZGRjODViMWIzZWM5NmYzYWY1M2Q0MjI3MmQwZjNiMGRmY0Bncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=YjM5NWVlNGRkZDY0NzRkNjBhNjljOTExZDc2YzA0YmFkZjY0NDUxZTI2YTFkZmIxMDEyZjU2NDgyZGZmNTM4MUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&color=%237986cb&color=%23d50000&color=%23c0ca33'
calView = 'https://calendar.google.com/calendar/u/0/embed?height=600&wkst=1&ctz=America/New_York&showPrint=0&src=MzQzYjc1MmFlOGIyOTQyZGJlOWEyZjJhYTMyYTA0NzBkNTBlY2ZjNDQwOWRmZmQxODM4NTFkN2Y0ZDM1YjI1YkBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=OTI3MTI0ZmI3MTA5Y2U0YWRlNGMwOTgyNzc5NTFjZGRjODViMWIzZWM5NmYzYWY1M2Q0MjI3MmQwZjNiMGRmY0Bncm91cC5jYWxlbmRhci5nb29nbGUuY29t&src=YjM5NWVlNGRkZDY0NzRkNjBhNjljOTExZDc2YzA0YmFkZjY0NDUxZTI2YTFkZmIxMDEyZjU2NDgyZGZmNTM4MUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t&color=%237986cb&color=%23d50000&color=%23c0ca33'
vaCalId = 'b395ee4ddd6474d60a69c911d76c04badf64451e26a1dfb1012f56482dff5381@group.calendar.google.com'
mdCalId = '927124fb7109ce4ade4c098277951cddc85b1b3ec96f3af53d42272d0f3b0dfc@group.calendar.google.com'
dcCalId = '343b752ae8b2942dbe9a2f2aa32a0470d50ecfc4409dffd183851d7f4d35b25b@group.calendar.google.com'
channelId: int
messageId: int
guidRegex = r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"


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

        futureCap = datetime.today().replace(tzinfo=zoneinfo.ZoneInfo('UTC')) + timedelta(30)

        data = response.json()
        data = [x for x in data if datetime.strptime(x['when'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo('UTC')) < futureCap]
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
        now = datetime.now().astimezone().isoformat()
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

    try:
        service = build("calendar", "v3", credentials=creds)
                
        data = [x for x in data if x['guid'] not in guids]
        for e in data:
            endTime = datetime.strptime(e['when'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo('UTC')) + timedelta(0,0,0,0,0,3)
            calId = ''
            match e['state']:
                case 'Virginia':
                    calId = vaCalId
                case 'Maryland':
                    calId = mdCalId
                case 'District of Columbia':
                    calId = dcCalId                
                
            event = {
                'summary': e['shop'] + ' ('+ e['state']+')',
                'location': e['street_address'],
                'description': e['type'] + '\n\n\n' + e['guid'],
                'start': {
                    'dateTime': datetime.strptime(e['when'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo('UTC')).isoformat(),
                },
                'end': {
                    'dateTime': endTime.astimezone().isoformat(),
                }
            }
            now = datetime.now().astimezone().isoformat()
            calEvent = service.events().insert(calendarId=calId, body=event).execute()
            print ('Event created: %s at %s' % (calEvent.get('htmlLink'), now))
        
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
                popWhenAdjusted = datetime.strptime(popEvent['when'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo('UTC')).astimezone()
                
                # no update needed
                if(str(calEvent['start']['dateTime']).replace('T', ' ') == str(popWhenAdjusted)):
                    continue
                       
                endTime = datetime.strptime(popEvent['when'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo('UTC')) + timedelta(0,0,0,0,0,3)
                calId = ''
                match popEvent['state']:
                    case 'Virginia':
                        calId = vaCalId
                    case 'Maryland':
                        calId = mdCalId
                    case 'District of Columbia':
                        calId = dcCalId                
                    
                event = {
                    'start': {
                        'dateTime': datetime.strptime(popEvent['when'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo('UTC')).isoformat(),
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
        
async def getScreenshot(playwright: Playwright):
    browser = await playwright.chromium.launch()
    page = await browser.new_page()
    await page.goto(schedView)
    await page.wait_for_timeout(2000)
    await page.screenshot(path='schedule.png', full_page=True)
    await browser.close()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@tasks.loop(hours=1)
async def runUpdate():
    global runContext    
    data = await getVGEvents()
    existingEvents = await getExistingCalItems()
    
    # await pushToCal(data, existingEvents)
    await checkAndUpdateEvents(data, existingEvents)
    
    async with async_playwright() as playwright:
        await getScreenshot(playwright)
    
    embed = discord.Embed(
        title="DMV VGC Schedule",
        color=discord.Color.yellow()
    )
    
    embed.add_field(
        name="Add to Google Calendar", 
        value="[Click here to sync to your calendar](https://calendar.google.com/calendar/u/0/r?cid=343b752ae8b2942dbe9a2f2aa32a0470d50ecfc4409dffd183851d7f4d35b25b@group.calendar.google.com&cid=927124fb7109ce4ade4c098277951cddc85b1b3ec96f3af53d42272d0f3b0dfc@group.calendar.google.com&cid=b395ee4ddd6474d60a69c911d76c04badf64451e26a1dfb1012f56482dff5381@group.calendar.google.com)"
        , inline=True
    )
    
    embed.add_field(
        name="Whats happening this week?", 
        value=f"[View Schedule]({schedView})"
        , inline=True
    )
    
    embed.add_field(
        name="Last updated at", 
        value=f"{str(time.strftime('%I:%M %p on %b %d, %Y'))}"
        , inline=False
    )
    
    embed.url = calView
    
    # Display images or graphical assets
    embed.set_image(url="attachment://schedule.png")
    
    try:
        channel = await bot.fetch_channel(channelId)
        msg = await channel.fetch_message(messageId)
        await msg.edit(file=discord.File("schedule.png", filename="schedule.png"), embed=embed)
    except HttpError as error:
        runUpdate.cancel()
        print(f"the message got deleted at {str(time.strftime('%I:%M %p on %b %d, %Y'))}: {error}")

@bot.slash_command(name="sync", description="get dmv vgc schedule data")
async def sync(ctx: discord.ApplicationContext):
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
       
    embed.url = calView
    await ctx.respond(content="Come on Barbie let's go party!", ephemeral=True)
    message = await ctx.send(embed=embed) 
    
    global channelId
    channelId = ctx.channel_id
    
    global messageId
    messageId = message.id
    
    runUpdate.start()

bot.run(os.getenv('TOKEN')) # run the bot with the token