from datetime import datetime, timedelta
import json
import subprocess
import time
import uuid
import zoneinfo
from certifi.__main__ import args
from certifi.__main__ import args
import discord
import os # default module
from dotenv import load_dotenv
import requests
import os.path
import re
from discord.ext import tasks
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import drawsvg as draw
from modules.CalendarConfig import CalendarConfig
from modules.CalendarViewsConfig import CalendarViewsConfig
from modules.GraphicConfig import GraphicConfig
from modules.GoogleCalendarEvent import GoogleCalendarEvent
from modules.LocatorEvent import LocatorEvent
from modules.DynamicView import DynamicView

load_dotenv() # load all the variables from the env file
bot = discord.Bot()

# If modifying these scopes, delete the file token.json.
SERVICE_ACCOUNT_FILE = "svcAcct.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

guidRegex = r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"

defaultStates = ["Maryland", "Virginia", "District of Columbia"]

messageListFile = 'configs/messageConfigs.json'

with open("configs/calendarConfigs.json") as cfg:
    calendarConfigs = [CalendarConfig.from_dict(item) for item in json.load(cfg)]
    print(f"Loaded {len(calendarConfigs)} calendar configs from file")

with open("configs/calendarViewsConfig.json") as cfg:
    calendarViewsConfig = CalendarViewsConfig.from_dict(json.load(cfg))
    print(f"Loaded calendar views config from file")
    
with open("configs/graphicConfig.json") as cfg:
    graphicConfig = GraphicConfig.from_dict(json.load(cfg))
    print(f"Loaded graphic config from file")

with open("configs/states.json") as states:
    stateOptions:list[str] = json.load(states)
    print(f"Loaded {len(stateOptions)} state options from file")

def getEventCalId(e: LocatorEvent) -> str:
    cal = [x for x in calendarConfigs if e.state == x.state]
    if cal and len(cal) > 0:
        return cal[0].friendlyCalId if e.isNonPremier() else cal[0].calendarId

def getSACreds():
    return service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

def addOrUpdateConfigFile(channelId: int, messageId: int, states: list[str] =None):
    channels = []
    if(states is None or len(states) == 0):
        states = defaultStates
    with open(messageListFile, 'r+') as file:
        channels = json.load(file)
        matches = [x for x in channels if x['channelId'] == channelId]
        if not matches or len(matches) == 0:
            channels.append({"channelId":channelId, "messageId":messageId, "stateSelections": defaultStates})
        
    for c in channels:
        if c['channelId'] == channelId:
            c['stateSelections'] = states
            
    # create randomly named temporary file to avoid 
    # interference with other thread/asynchronous request
    tempfile = os.path.join(os.path.dirname(messageListFile), str(uuid.uuid4()))
    with open(tempfile, 'w') as f:
        json.dump(channels, f, indent=4)

    # rename temporary file replacing old file
    os.replace(tempfile, messageListFile)

async def getVGEvents()-> list[LocatorEvent]:
    url = "https://www.pokedata.ovh/events/tableapi/index_table.php"

    states = "["
    for x in calendarConfigs:
        states += f"\"{x.state}\","
    states = states.rstrip(",") + "]"
    
    page = 0
    data = []
    while True:
        try:
            payload = {
                "past": False,
                "country": "US",
                "city": "",
                "shop": "",
                "league": "",
                "states": states,
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
                "page": page,
            }

            headers = {
                "accept": "application/json",
                "content-type": "application/json; charset=UTF-8",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
                "origin": "https://www.pokedata.ovh",
                "referer": "https://www.pokedata.ovh/events/"
            }

    
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            pageData = response.json()
            if(pageData is None or len(pageData) == 0):
                break
            else:
                data = data + pageData
                page += 1
        
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            break
                
    # pokedata sucks at deleting old info, best option i could think of
    data = sorted(data, key=lambda event: ( datetime.strptime(event['when'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo(LocatorEvent.from_dict(event).getEventTz())), event['guid']))
    for d in data:
        d["dupeKey"] = d["shop"] + '~|~' + d["type"] + '~|~' + d["street_address"] + '~|~' +d["when"]  + '~|~' + d["name"]
    seen = set()
    data = [obj for obj in data if obj["dupeKey"]  not in seen and not seen.add(obj["dupeKey"])]
        
    for obj in data:
        del obj["dupeKey"]
    return [LocatorEvent.from_dict(item) for item in data]    
   
async def getExistingCalItems() -> list[GoogleCalendarEvent]:
    now = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).astimezone().isoformat() #dont delete possibly in progress events from the calendar
    creds = getSACreds() 
    events = []
    try:
        service = build("calendar", "v3", credentials=creds)
        for cal in calendarConfigs:
            events_result = (
                service.events()
                .list(
                    calendarId=cal.calendarId,
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
                        calendarId=cal.friendlyCalId,
                        timeMin=now,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
            events = events + events_result.get("items", [])
                
        if not events:
            return []
        return [GoogleCalendarEvent.from_dict(event) for event in events]
    except HttpError as error:
        print(f"An error occurred: {error}")
                 
async def pushToCal(data: list[LocatorEvent], existingEvents: list[GoogleCalendarEvent]):
    creds = getSACreds() 

    guids = []
    for e in existingEvents:
        guidSearch = re.search(guidRegex,  e.description)
        if guidSearch:
            guids.append(guidSearch.group(0))  

    now = datetime.now().astimezone()
    try:
        service = build("calendar", "v3", credentials=creds)
                
        data = [x for x in data if x.guid not in guids]
        for e in data:
            startTime = datetime.strptime(e.when, '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo(e.getEventTz()))
            if startTime < now:
                continue
            
            endTime = startTime + timedelta(0,0,0,0,0,3)
            calId = getEventCalId(e)                
            
            
            typeLabel = ''
            emoji = ''
            if e.isNonPremier():
                if(e.hasSanctionedUrl()):
                    typeLabel = 'Friendly Tournament'
                    emoji = '👥' 
                else:
                    typeLabel = 'Open Play'
                    emoji = '🅾️🅿️'
            else :
                typeLabel = e.type
                if e.type == 'League Challenge VG':
                    emoji = '🥊'
                else:
                    emoji = '🏆'
                    
            event = {
                'summary': emoji + ' ' + e.shop + ' ('+ e.state+')',
                'location': e.street_address,
                'description': typeLabel + ('\n<a href="' + e.pokemon_url+ '">Official Event Page</a>' if e.hasSanctionedUrl() else '') + '\n\n\n' + e.guid,
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

async def checkAndUpdateEvents(playListings: list[LocatorEvent], existingCalEvents: list[GoogleCalendarEvent]):
    creds = creds = getSACreds() 
        
    try:
        service = build("calendar", "v3", credentials=creds)
        
        for calEvent in existingCalEvents:
            guidSearch = re.search(guidRegex, calEvent.description)
            if guidSearch:
                popId = guidSearch.group(0)
                popEventMatches = [x for x in playListings if x.guid == popId]
                                
                if len(popEventMatches) != 1:
                    continue
                
                popEvent = popEventMatches[0]
                popWhenAdjusted = datetime.strptime(popEvent.when, '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo(popEvent.getEventTz())).astimezone()
                
                # no update needed
                if str(calEvent.start.dateTime).replace('T', ' ') == str(popWhenAdjusted):
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
                calEvent = service.events().patch(calendarId=calId, eventId=calEvent.id, body=event).execute()
                print ('Event updated: %s at %s' % (calEvent.get('htmlLink'), now))
                          
    except HttpError as error:
        print(error)
 
async def checkAndDeleteEvents(playListings: list[LocatorEvent], existingCalEvents: list[GoogleCalendarEvent]):
    creds = getSACreds() 
    
    try:
        service = build("calendar", "v3", credentials=creds)
        existingCalendarGuids = []
        for calEvent in existingCalEvents:
            guidSearch = re.search(guidRegex, calEvent.description)
            if guidSearch:
                existingCalendarGuids.append(guidSearch.group(0))
                
        popGuids = [x.guid for x in playListings]
        canceledEvents = [x for x in existingCalendarGuids if x not in popGuids]
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).astimezone()
        futureEvents = [x for x in existingCalEvents if datetime.strptime(x.start.dateTime, '%Y-%m-%dT%H:%M:%S%z') > tomorrow]

        for calEvent in futureEvents:
            guidSearch = re.search(guidRegex, calEvent.description)
            if guidSearch and guidSearch.group(0) in canceledEvents:                   
                now = datetime.now().astimezone().isoformat()
                service.events().delete(calendarId=calEvent.organizer.email, eventId=calEvent.id).execute()
                print ('Event deleted: %s at %s' % (calEvent.summary, now))
                          
    except HttpError as error:
        print(error)      

async def makeGraphic():    
    existingEvents = await getExistingCalItems()
    if(existingEvents is None or len(existingEvents) == 0):
        return
    
    premierCalIds = [x.calendarId for x in calendarConfigs]
    existingEvents = [x for x in existingEvents if x.organizer.email in premierCalIds]
    existingEvents = sorted(existingEvents, key=lambda event: datetime.strptime(event.start.dateTime, '%Y-%m-%dT%H:%M:%S%z'))
    
    d = draw.Drawing(graphicConfig.embedW, graphicConfig.embedH, origin='top-left', font_family=graphicConfig.fontFamily)
    
    #header branding
    css_rules = f"""
        .title-text {{
            font-size: 54px;
            font-style: italic;
            font-width: expanded;
        }}
    """
    d.append_css(css_rules)
    
    gradient = draw.LinearGradient(1, graphicConfig.embedW/6, graphicConfig.embedW/2, graphicConfig.embedW/3)
    gradient.add_stop(0, graphicConfig.headerGradientStartColor, 1)
    gradient.add_stop(1, graphicConfig.headerGradientEndColor, 1)
    d.append(draw.Rectangle(graphicConfig.margin, 0, graphicConfig.embedW - (2*graphicConfig.margin), graphicConfig.headerHeight, fill='white', rx=graphicConfig.cornerRadius, ry=graphicConfig.cornerRadius))
    d.append(draw.Rectangle(graphicConfig.margin, 0, graphicConfig.embedW - (2*graphicConfig.margin), graphicConfig.headerHeight, fill=gradient, rx=graphicConfig.cornerRadius, ry=graphicConfig.cornerRadius))
    
    d.append(draw.Image( x=graphicConfig.margin + 20, y=graphicConfig.margin, width=graphicConfig.logoSize, height=graphicConfig.logoSize,  path=graphicConfig.logoPath, embed=True) )
    d.append(draw.Text(graphicConfig.graphicTitle, 54, 640, 50, fill=graphicConfig.headerTextColor, center=True, class_='title-text', font_family=graphicConfig.headerFont)) 
    
    rowIndex = 0
    for i in range(graphicConfig.headerHeight, graphicConfig.embedH - graphicConfig.rowHeight, graphicConfig.rowHeight):
        if rowIndex > len(existingEvents)-1: 
            continue
        e = existingEvents[rowIndex]
        rowBaseline = i + 26
        
        #draw dividers if dif date from last and write date
        currentStart = datetime.strptime(e.start.dateTime, '%Y-%m-%dT%H:%M:%S%z')
        d.append(draw.Rectangle(5, i, graphicConfig.embedW-10, graphicConfig.rowHeight, fill=graphicConfig.rowBackground,  rx=graphicConfig.cornerRadius, ry=graphicConfig.cornerRadius))
            
        if(rowIndex != 0):
            previousStartDate = datetime.strptime(existingEvents[rowIndex-1].start.dateTime, '%Y-%m-%dT%H:%M:%S%z').date()
            if(currentStart.date() != previousStartDate):
                d.append(draw.Line(graphicConfig.margin, i, graphicConfig.embedW-graphicConfig.margin, i, stroke=graphicConfig.imageBackground, stroke_width=2))          
                d.append(draw.Text(currentStart.strftime("%d"), 18, 16, rowBaseline, fill= graphicConfig.textPrimaryColor))
                d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, rowBaseline, fill= graphicConfig.textPrimaryColor))
            else:
                d.append(draw.Rectangle(graphicConfig.margin, i-10, graphicConfig.embedW-10, graphicConfig.rowHeight, fill=graphicConfig.rowBackground))
        else:
            # line 1
            if(currentStart.date() == datetime.now().date()):
                d.append(draw.Circle(26, i + 20, 16, fill=graphicConfig.highlightColor))
                d.append(draw.Text(currentStart.strftime("%d"), 18, 16, rowBaseline, fill=graphicConfig.imageBackground))
                d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, rowBaseline, fill=graphicConfig.highlightColor))
            else:
                d.append(draw.Text(currentStart.strftime("%d"), 18, 16, rowBaseline, fill= graphicConfig.textPrimaryColor))
                d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, rowBaseline, fill= graphicConfig.textPrimaryColor))
        
        
        color = graphicConfig.textPrimaryColor
        calConfig = [x for x in calendarConfigs if e.organizer.email == x.calendarId]
        if calConfig and len(calConfig) > 0:
            color = calConfig[0].color
                
        rowGroup = draw.Group()
        
    # schedule data
        schedGroup = draw.Group()  
        bullet = draw.Circle(0, -4 , 6, fill=color)
        schedGroup.append(bullet) # Draw a circle
        startTime = currentStart.strftime("%I:%M%p")
        schedGroup.append(draw.Text(startTime, 12, 20, 0, fill= graphicConfig.textPrimaryColor))
            
    # event data
        eventGroup = draw.Group()
        rowFontSize = 14
        emojiStart = 20
        emojiWidth = 20
        
        icon = graphicConfig.unknownIconPath
        if e.summary.startswith('🥊'):
            icon = graphicConfig.chalIconPath                    
        elif e.summary.startswith('🏆'):
            icon = graphicConfig.cupIconPath
        eventGroup.append(draw.Image( x=emojiStart, y= -20, width=emojiWidth, height=30,  path=icon, embed=True) )               
        
        titleStart = emojiStart + emojiWidth + 5
        title = e.summary[1:]
        titleWidth = 8 * len(title)
        eventGroup.append(draw.Text(title, rowFontSize, titleStart, 0, fill= graphicConfig.textPrimaryColor))
        eventGroup.append(draw.Text(e.location, rowFontSize, titleStart + titleWidth, 0, fill=graphicConfig.locationTextColor))
        
        rowGroup.append(draw.Use(schedGroup, 0, 0))
        rowGroup.append(draw.Use(eventGroup, 120, 0))
        
        d.append(draw.Use(rowGroup, graphicConfig.rowScheduleStart, rowBaseline))
        rowIndex += 1

    d.set_pixel_scale(2)  
    d.save_svg('output/schedule.svg')
    d.save_png('output/schedule.png')
                     
@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    if not Path(messageListFile).is_file():
        with open(messageListFile, "w") as file:
            file.write("[]")
    os.makedirs('output', exist_ok=True)
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
    
    await makeGraphic()
    
    embed = discord.Embed(
        title="DMV VGC Schedule",
        color=discord.Color.yellow()
    )
    
    
    embed.add_field(
        name="Premier Events", 
        value=f"[Click here to sync to your calendar]({calendarViewsConfig.premierSync})"
        , inline=True
    )
    
    embed.add_field(
        name="Upcoming Premier Events", 
        value=f"[View Premier Schedule]({calendarViewsConfig.schedView})"
        , inline=True
    )
    
    embed.add_field(
        name="", 
        value=""
        , inline=False
    )
    
    embed.add_field(
        name="League/Friendly Events", 
        value=f"[Click here to sync to your calendar]({calendarViewsConfig.friendlySync})"
        , inline=True
    )
    
    embed.add_field(
        name="Upcoming Friendly Events",
        value=f"[View Friendly Schedule]({calendarViewsConfig.friendlySchedView})"
        ,inline=True
    )
    
    embed.add_field(
        name="Last updated at", 
        value=f"{str(time.strftime('%I:%M %p on %b %d, %Y'))}"
        , inline=False
    )
    
    embed.url = calendarViewsConfig.allCalView
    
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
    print(f"update finished at {(datetime.now()).astimezone().isoformat()}")
        
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
       
    embed.url = calendarViewsConfig.allCalView
    await ctx.respond(content="Come on Barbie let's go party!", ephemeral=True)
    message = await ctx.send(embed=embed) 
    
    channelId = ctx.channel_id
    messageId = message.id

    addOrUpdateConfigFile(channelId, messageId)
    
    runUpdate.start()

@bot.slash_command(name="manualsync", description="force all instances to update")
async def manualsync(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator and not await ctx.bot.is_owner(ctx.author):
        await ctx.respond("I don't make deals with peasants!", ephemeral=True)
        return
    
    runUpdate.cancel()
    await ctx.respond(content="forcing schedule update!", ephemeral=True)
    runUpdate.start()

@bot.slash_command(name="updatelog", description="prints bot update log")
async def updatelog(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator and not await ctx.bot.is_owner(ctx.author):
        await ctx.respond("I don't make deals with peasants!", ephemeral=True)
        return
    message = ""
    try:
        # Runs git log and limits the output to the last 5 entries
        result = subprocess.run(
            ["git", "log", "-n", "10", "--reverse", "--format=%ad - %s", "--date=short"],
            capture_output=True,
            text=True,
            check=True
        )
        message = f"```{result.stdout}```"
    except subprocess.CalledProcessError as e:
        message = f"Error running git log: {e.stderr}"
    except FileNotFoundError:
        message = "Git is not installed or not in your system PATH."
    
    await ctx.respond(message, ephemeral=True)


@bot.slash_command(name="addstate", description="Add a state to your channel's calendar")
@discord.option(
    "state_al_ky",
    description="Alabama-Kentucky",
    choices=stateOptions[:18],
    required=False
)
@discord.option(
    "state_lo_oh",
    description="Louisiana-Ohio",
    choices=stateOptions[18:36],
    required=False
)
@discord.option(
    "state_ok_wy",
    description="Oklahoma-Wyoming",
    choices=stateOptions[36:],
    required=False
)
async def addstate(ctx: discord.ApplicationContext, state_al_ky: str = None, state_lo_oh: str = None, state_ok_wy: str = None ):
    states = []
    channelId = ctx.channel_id
    with open(messageListFile, 'r+') as file:
        serverConfig = json.load(file)
        matches = [x for x in serverConfig if x['channelId'] == channelId]
        if not matches or len(matches) == 0:
            await ctx.respond("No configuration found for this channel. Please run /sync first in the channel to host your calendar, then use this command in the channel.", ephemeral=True)
            return
    
    if not matches[0]['stateSelections'] is None:
        states = matches[0]['stateSelections']    
    
    if state_al_ky:
        state = state_al_ky
    if state_lo_oh:
        state = state_lo_oh
    if state_ok_wy:
        state = state_ok_wy

    if(state and state not in states):
        states.append(state)
    states = sorted(states)
    
    addOrUpdateConfigFile(channelId, matches[0]['messageId'], states)
    
    await ctx.respond(f"States for this channel: {', '.join(states)}", ephemeral=True)
    
@bot.slash_command(name="removestate", description="Remove a state from your channel's calendar")
async def removestate(ctx: discord.ApplicationContext):
    states = []
    channelId = ctx.channel_id
    with open(messageListFile, 'r+') as file:
        serverConfig = json.load(file)
        matches = [x for x in serverConfig if x['channelId'] == channelId]
        if not matches or len(matches) == 0:
            await ctx.respond("No configuration found for this channel. Please run /sync first in the channel to host your calendar, then use this command in the channel.", ephemeral=True)
            return
    
    row = 0
    if not matches[0]['stateSelections'] is None:
        for index, state in enumerate(matches[0]['stateSelections']):
            if(index % 5 == 0):
                row += 1
                
            states.append({'id':state, 'row': row})
    inputView = DynamicView(states)
    
    await ctx.response.send_message("Select a state to remove:", view=inputView, ephemeral=True, delete_after=15)   
    timedOut = await inputView.wait()
    if timedOut:
       await ctx.respond("The request timed out.", ephemeral=True, delete_after=15)
       return
    
    matches[0]["stateSelections"].remove(inputView.value)
    print(matches[0]["stateSelections"])
    addOrUpdateConfigFile(channelId, matches[0]['messageId'], matches[0]["stateSelections"])

bot.run(os.getenv('TOKEN')) # run the bot with the token