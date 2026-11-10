from datetime import datetime, timedelta
import json
import subprocess
import time
import uuid
import zoneinfo
import discord
import os
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
from modules.MessageConfig import MessageConfig, MessageEmbedConfig, MessageImageConfig
from modules.CalendarConfig import CalendarConfig
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
defaultTitle = "Upcoming Premier Events"
shareBaseUrl = "https://calendar.google.com/calendar/u/0/r?cid="

messageListFile = 'configs/messageConfigs.json'

with open("configs/calendarConfigs.json") as cfg:
    calendarConfigs = [CalendarConfig.from_dict(item) for item in json.load(cfg)]
    print(f"Loaded {len(calendarConfigs)} calendar configs from file")
    
with open("configs/graphicConfig.json") as cfg:
    graphicConfig = GraphicConfig.from_dict(json.load(cfg))
    print(f"Loaded graphic config from file")

with open("configs/states.json") as stateFile:
    stateOptions = json.load(stateFile)
    
def getEventCalId(e: LocatorEvent) -> str:
    cal = [x for x in calendarConfigs if e.state == x.state]
    if cal and len(cal) > 0:
        return cal[0].friendlyCalId if e.isNonPremier() else cal[0].calendarId

def isEmpty(s:str)->bool:
    return s is None or len(s.strip()) == 0

def getSACreds():
    return service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

def makeEmptyConfig(guildId: int, channelId: int, messageId: int)-> MessageConfig:
    embed = MessageEmbedConfig(defaultTitle,"","","")
    image = MessageImageConfig.from_dict({
        "title": defaultTitle,
        "headerGradientStartColor": "#D0EEF5",
        "headerGradientEndColor": "#21B7D9",
        "imageBackgroundColor": "black",
        "textPrimaryColor": "black",
        "headerTextColor": "black",
        "locationTextColor": "grey",
        "rowBackgroundColor": "white",
        "highlightColor": "dodgerblue"
    })
    return MessageConfig(guildId, channelId, messageId, defaultStates, embed, image)
    
def addConfigFile(guildId: int, channelId: int, messageId: int):
    channels = []
   
    with open(messageListFile, 'r+') as file:
        channels = [MessageConfig.from_dict(item) for item in json.load(file)]
        matches = [x for x in channels if x.channelId == channelId]
        if not matches or len(matches) == 0:
            channels.append(makeEmptyConfig(guildId, channelId, messageId))
        
    # create randomly named temporary file to avoid 
    # interference with other thread/asynchronous request
    tempfile = os.path.join(os.path.dirname(messageListFile), str(uuid.uuid4()))
    with open(tempfile, 'w') as f:
        json.dump([c.to_dict() for c in channels], f, indent=4)

    # rename temporary file replacing old file
    os.replace(tempfile, messageListFile)

def buildCalendarSyncUrls(config: MessageConfig)-> dict:
    friendly = shareBaseUrl
    premier = shareBaseUrl
    calsForConfig = [cal for cal in calendarConfigs if cal.state in config.stateSelections]
    friendly += "&cid=".join([cal.friendlyCalId for cal in calsForConfig])
    premier += "&cid=".join([cal.calendarId for cal in calsForConfig]) 
    return dict(premier=premier, friendly=friendly)    

async def getVGEvents()-> list[LocatorEvent]:
    url = "https://www.pokedata.ovh/events/tableapi/index_table.php"

    # this should be sweeping so subscribers get updates regardless of a server using the calendar or not
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
    
    print(f"Fetched {len(data)} individual events from pokedata.ovh")
    await bot.change_presence(activity=discord.Game(name=f"Currently tracking {len(data)} future events"))
    return [LocatorEvent.from_dict(item) for item in data]    
   
async def getExistingCalItems(cals:list[CalendarConfig] = None) -> list[GoogleCalendarEvent]:
    now = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).astimezone().isoformat() #dont delete possibly in progress events from the calendar
    creds = getSACreds() 
    events = []
    if(cals is None or len(cals) == 0):
        cals = calendarConfigs
    
    try:
        service = build("calendar", "v3", credentials=creds)
        for cal in cals:
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
                    'dateTime': startTime.astimezone(zoneinfo.ZoneInfo(e.getEventTz())).isoformat(),
                },
                'end': {
                    'dateTime': endTime.astimezone(zoneinfo.ZoneInfo(e.getEventTz())).isoformat(),
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
                popWhenAdjusted = datetime.strptime(popEvent.when, '%Y-%m-%d %H:%M:%S').replace(tzinfo=zoneinfo.ZoneInfo(popEvent.getEventTz()))
                calWhen = datetime.strptime(calEvent.start.dateTime, '%Y-%m-%dT%H:%M:%S%z')
                # no update needed
                if popWhenAdjusted == calWhen:
                    continue
                
                endTime = popWhenAdjusted + timedelta(0,0,0,0,0,3)
                calId = getEventCalId(popEvent)                
                    
                event = {
                    'start': {
                        'dateTime': popWhenAdjusted.isoformat(),
                    },
                    'end': {
                        'dateTime': endTime.isoformat(),
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

async def makeGraphicForChannel(msgConfig: MessageConfig): 
    calConfigForChannel = [x for x in calendarConfigs if x.state in msgConfig.stateSelections]   
    existingEvents = await getExistingCalItems(calConfigForChannel)
    if(existingEvents is None or len(existingEvents) == 0):
        return
        
    premierCalIds = [x.calendarId for x in calConfigForChannel]
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
    gradient.add_stop(0, msgConfig.image.headerGradientStartColor, 1)
    gradient.add_stop(1, msgConfig.image.headerGradientEndColor, 1)
    d.append(draw.Rectangle(graphicConfig.margin, 0, graphicConfig.embedW - (2*graphicConfig.margin), graphicConfig.headerHeight, fill='white', rx=graphicConfig.cornerRadius, ry=graphicConfig.cornerRadius))
    d.append(draw.Rectangle(graphicConfig.margin, 0, graphicConfig.embedW - (2*graphicConfig.margin), graphicConfig.headerHeight, fill=gradient, rx=graphicConfig.cornerRadius, ry=graphicConfig.cornerRadius))
    
    d.append(draw.Image( x=graphicConfig.margin + 20, y=graphicConfig.margin, width=graphicConfig.logoSize, height=graphicConfig.logoSize,  path=graphicConfig.logoPath, embed=True) )
    d.append(draw.Text(msgConfig.image.title, 54, 640, 50, fill=msgConfig.image.headerTextColor, center=True, class_='title-text', font_family=graphicConfig.headerFont)) 
    
    rowIndex = 0
    for i in range(graphicConfig.headerHeight, graphicConfig.embedH - graphicConfig.rowHeight, graphicConfig.rowHeight):
        if rowIndex > len(existingEvents)-1: 
            continue
        e = existingEvents[rowIndex]
        rowBaseline = i + 26
        
        #draw dividers if dif date from last and write date
        currentStart = datetime.strptime(e.start.dateTime, '%Y-%m-%dT%H:%M:%S%z')
        d.append(draw.Rectangle(5, i, graphicConfig.embedW-10, graphicConfig.rowHeight, fill=msgConfig.image.rowBackgroundColor,  rx=graphicConfig.cornerRadius, ry=graphicConfig.cornerRadius))
            
        if(rowIndex != 0):
            previousStartDate = datetime.strptime(existingEvents[rowIndex-1].start.dateTime, '%Y-%m-%dT%H:%M:%S%z').date()
            if(currentStart.date() != previousStartDate):
                d.append(draw.Line(graphicConfig.margin, i, graphicConfig.embedW-graphicConfig.margin, i, stroke=msgConfig.image.imageBackgroundColor, stroke_width=2))          
                d.append(draw.Text(currentStart.strftime("%d"), 18, 16, rowBaseline, fill= msgConfig.image.textPrimaryColor))
                d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, rowBaseline, fill= msgConfig.image.textPrimaryColor))
            else:
                d.append(draw.Rectangle(graphicConfig.margin, i-10, graphicConfig.embedW-10, graphicConfig.rowHeight, fill=msgConfig.image.rowBackgroundColor))
        else:
            # line 1
            if(currentStart.date() == datetime.now().date()):
                d.append(draw.Circle(26, i + 20, 16, fill=msgConfig.image.highlightColor))
                d.append(draw.Text(currentStart.strftime("%d"), 18, 16, rowBaseline, fill=msgConfig.image.imageBackgroundColor))
                d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, rowBaseline, fill=msgConfig.image.highlightColor))
            else:
                d.append(draw.Text(currentStart.strftime("%d"), 18, 16, rowBaseline, fill= msgConfig.image.textPrimaryColor))
                d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, rowBaseline, fill= msgConfig.image.textPrimaryColor))
        
        
        color = msgConfig.image.textPrimaryColor
        calConfig = [x for x in calendarConfigs if e.organizer.email == x.calendarId]
        if calConfig and len(calConfig) > 0:
            color = calConfig[0].color
                
        rowGroup = draw.Group()
        
    # schedule data
        schedGroup = draw.Group()  
        bullet = draw.Circle(0, -4 , 6, fill=color)
        schedGroup.append(bullet) # Draw a circle
        startTime = currentStart.strftime("%I:%M%p")
        schedGroup.append(draw.Text(startTime, 12, 20, 0, fill= msgConfig.image.textPrimaryColor))
            
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
        titleWidth = 8.25 * len(title)
        eventGroup.append(draw.Text(title, rowFontSize, titleStart, 0, fill= msgConfig.image.textPrimaryColor))
        eventGroup.append(draw.Text(e.location, rowFontSize, titleStart + titleWidth, 0, fill=msgConfig.image.locationTextColor))
        
        rowGroup.append(draw.Use(schedGroup, 0, 0))
        rowGroup.append(draw.Use(eventGroup, 120, 0))
        
        d.append(draw.Use(rowGroup, graphicConfig.rowScheduleStart, rowBaseline))
        rowIndex += 1

    d.set_pixel_scale(2)  
    d.save_svg('output/schedule.svg')
    d.save_png('output/schedule.png')
 
async def buildEmbedForChannel(msgCfg: MessageConfig) -> discord.embed:
    if(msgCfg.stateSelections is None or len(msgCfg.stateSelections) == 0):
        return
    
    await makeGraphicForChannel(msgCfg)
     
    embedCfg = msgCfg.embed
    if isEmpty(embedCfg.title):
        embedCfg.title = defaultTitle
         
    embed = discord.Embed(
        title=embedCfg.title,
        color=discord.Color.yellow()
    )
    
    calendarSyncUrls = buildCalendarSyncUrls(msgCfg)
    
    if not isEmpty(calendarSyncUrls["premier"]):
        embed.add_field(
            name="Premier Events", 
            value=f"[Click here to sync to your calendar]({calendarSyncUrls["premier"]})"
            , inline=True
        )
    if not isEmpty(embedCfg.schedView):
        embed.add_field(
            name="Upcoming Premier Events", 
            value=f"[View Premier Schedule]({embedCfg.schedView})"
            , inline=True
        )
    
    if not isEmpty(calendarSyncUrls["premier"]) or not isEmpty(embedCfg.schedView):
        embed.add_field(
            name="", 
            value=""
            , inline=False
        )
    
    if not isEmpty(calendarSyncUrls["friendly"]):
        embed.add_field(
            name="League/Friendly Events", 
            value=f"[Click here to sync to your calendar]({calendarSyncUrls["friendly"]})"
            , inline=True
        )
        
    if not isEmpty(embedCfg.friendlySchedView):
        embed.add_field(
            name="Upcoming Friendly Events",
            value=f"[View Friendly Schedule]({embedCfg.friendlySchedView})"
            ,inline=True
        )
    
    embed.add_field(
        name="Last updated at", 
        value=f"{str(time.strftime('%I:%M %p on %b %d, %Y'))}"
        , inline=False
    )
    
    embed.url = embedCfg.allCalView
    
    # Display images or graphical assets
    embed.set_image(url="attachment://output/schedule.png")
    return embed
     
async def clearFutureForState(cals:list[CalendarConfig]):
    items = await getExistingCalItems(cals)
    try:
        service = build("calendar", "v3", credentials=getSACreds())
        for calEvent in items:
            now = datetime.now().astimezone().isoformat()
            service.events().delete(calendarId=calEvent.organizer.email, eventId=calEvent.id).execute()
            print ('Event deleted: %s at %s' % (calEvent.summary, now))                   
    except HttpError as error:
        print(error)      
                   
@bot.event
async def on_ready():
    print(f"{bot.user} is online, pid is: {os.getpid()}")
    if not Path(messageListFile).is_file():
        with open(messageListFile, "w") as file:
            file.write("[]")
    os.makedirs('output', exist_ok=True)
    # if not runUpdate.is_running():
        # runUpdate.start()
    print(f"{bot.user} has initialized!")

@tasks.loop(hours=1)
async def runUpdate():
    print(f"running update at {(datetime.now()).astimezone().isoformat()}")
    data = await getVGEvents()
    existingEvents = await getExistingCalItems()
    
    await pushToCal(data, existingEvents)
    await checkAndUpdateEvents(data, existingEvents)
    await checkAndDeleteEvents(data, existingEvents)
    
    curChannel = None
    curMessage = None
    
    channels = []
    with open(messageListFile, 'r+', encoding='utf-8') as file:
        channels = [MessageConfig.from_dict(item) for item in json.load(file)]
    if not channels:
        return
    
    for msg in channels:
        curChannel = msg.channelId
        curMessage = msg.messageId
        try: 
            embed = await buildEmbedForChannel(msg)
            channel = await bot.fetch_channel(curChannel)
            msg = await channel.fetch_message(curMessage)
            await msg.edit(file=discord.File("output/schedule.png", filename="output/schedule.png"), embed=embed)
        except discord.errors.NotFound as error:
            with open(messageListFile, 'r+') as file:
                channels = [MessageConfig.from_dict(item) for item in json.load(file)]
                valids = [x for x in channels if x.channelId != curChannel]
                    
            tempfile = os.path.join(os.path.dirname(messageListFile), str(uuid.uuid4()))
            with open(tempfile, 'w') as f:
                json.dump([c.to_dict() for c in valids], f, indent=4)

            # rename temporary file replacing old file
            os.replace(tempfile, messageListFile)
    print(f"update finished at {(datetime.now()).astimezone().isoformat()}")
        
@bot.slash_command(name="init", description="initalize calendar to this channel")
async def init(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator and not await ctx.bot.is_owner(ctx.author):
        await ctx.respond("I don't make deals with peasants!", ephemeral=True, delete_after=15)
        return
    
    with open(messageListFile, 'r+') as file:
        channels = [MessageConfig.from_dict(item) for item in json.load(file)]
        valids = [x for x in channels if x.channelId == ctx.channel_id]

    if valids is not None and len(valids) != 0:
        await ctx.respond("A calendar was found for this channel. Please run /detach to remove the current calendar reference then rerun /init", ephemeral=True, delete_after=15)
        return
    
    runUpdate.cancel()
    embed = discord.Embed(
        title="DMV VGC Schedule",
        color=discord.Color.yellow()
    )
    
    embed.add_field(
        name="Initalizing", 
        value="Hold tight for a while please",
        inline=True
    )
       
    await ctx.respond(content="Come on Barbie let's go party! Making you a new graphic. Please configure it via the web page.", ephemeral=True, delete_after=15)
    message = await ctx.send(embed=embed) 
    
    guildId = ctx.guild_id
    channelId = ctx.channel_id
    messageId = message.id

    addConfigFile(guildId, channelId, messageId)
    
    if not runUpdate.is_running():  
        runUpdate.start()

@bot.slash_command(name="force", description="force all instances to update")
async def force(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator and not await ctx.bot.is_owner(ctx.author):
        await ctx.respond("I don't make deals with peasants!", ephemeral=True, delete_after=15)
        return
    
    runUpdate.cancel()
    
    with open("configs/calendarConfigs.json") as cfg:
        global calendarConfigs
        calendarConfigs = [CalendarConfig.from_dict(item) for item in json.load(cfg)]
        print(f"Loaded {len(calendarConfigs)} calendar configs from file")
        
    with open("configs/graphicConfig.json") as cfg:
        global graphicConfig
        graphicConfig = GraphicConfig.from_dict(json.load(cfg))
        print(f"Loaded graphic config from file")
    
    content = f"Loaded {len(calendarConfigs)} calendar configs from file!\n"
    # content += "Loaded calendar views config from file!\n"
    content += f"Loaded graphic config from file!\n"
    await ctx.respond(content= content + "\nforcing schedule update!", ephemeral=True, delete_after=15)
    
    if not runUpdate.is_running():  
            runUpdate.start()

@bot.slash_command(name="updatelog", description="prints bot update log")
async def updatelog(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator and not await ctx.bot.is_owner(ctx.author):
        await ctx.respond("I don't make deals with peasants!", ephemeral=True, delete_after=15)
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
    
    await ctx.respond(message, ephemeral=True, delete_after=60)
   
@bot.slash_command(name="clearfuture", description="Clears a states future events to full refresh for next cycle(debug use)")
@discord.ext.commands.is_owner()
async def clearfuture(ctx: discord.ApplicationContext, state: str):
    if state is None:
        await ctx.respond(f"Please enter a state, make sure to use the official 2 letter state code or proper name (case insensitve)", ephemeral=True, delete_after=15)
        return
    state  = state.strip().lower()
    foundValue = next((k for k, v in stateOptions.items() if (k.lower() == state) or (v.lower() == state)), None)
    if foundValue is None:
        await ctx.respond(f"No state found named '{state}', make sure to use the official 2 letter state code or proper name (case insensitve)", ephemeral=True, delete_after=15)     
        return
    cal = [x for x in calendarConfigs if foundValue == x.state]
    if len(cal) == 0:
        await ctx.respond(f"No calendar configured for '{foundValue}'", ephemeral=True, delete_after=15)
        return
    await ctx.respond(f"Clearing calendars for {foundValue}", ephemeral=True, delete_after=15)
    
    await clearFutureForState(cal)
    await ctx.respond(f"Cleared calendars for {foundValue}", ephemeral=True, delete_after=15)

@bot.slash_command(name="refresh", description="refresh the calendar image in this channel")
async def refresh(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator and not await ctx.bot.is_owner(ctx.author):
        await ctx.respond("I don't make deals with peasants!", ephemeral=True, delete_after=15)
        return
          
    await ctx.respond(content="Refreshing calendar graphic", ephemeral=True, delete_after=15)
    
    with open(messageListFile, 'r+') as file:
        channels = [MessageConfig.from_dict(item) for item in json.load(file)]
        valids = [x for x in channels if x.channelId == ctx.channel_id]

    if valids is None or len(valids) == 0:
        await ctx.respond("No calendar was found for this channel. Please run /init to create one", ephemeral=True, delete_after=15)
        return
    
    msgConfig = valids[0]
    embed = await buildEmbedForChannel(msgConfig)
    channel = await bot.fetch_channel(msgConfig.channelId)
    msg = await channel.fetch_message(msgConfig.messageId)
    await msg.edit(file=discord.File("output/schedule.png", filename="output/schedule.png"), embed=embed)

@bot.slash_command(name="detach", description="Detach the current embed to reinitalize it and stop it from updating")
async def detach(ctx: discord.ApplicationContext):
    with open(messageListFile, 'r+') as file:
        channels = [MessageConfig.from_dict(item) for item in json.load(file)]
        valids = [x for x in channels if x.channelId == ctx.channel_id]

    if valids is None or len(valids) == 0:
        await ctx.respond("No calendar was found for this channel. Please run /init to create one", ephemeral=True, delete_after=15)
        return
    
    channels = [cfg for cfg in channels if cfg.channelId != ctx.channel_id]
    
    tempfile = os.path.join(os.path.dirname(messageListFile), str(uuid.uuid4()))
    with open(tempfile, 'w') as f:
        json.dump([c.to_dict() for c in channels], f, indent=4)

    # rename temporary file replacing old file
    os.replace(tempfile, messageListFile)
    await ctx.respond("Removed current channel calndar config. Please run /init to make a new one. You may delete the existing instance", ephemeral=True, delete_after=15)
    
bot.run(os.getenv('TOKEN')) # run the bot with the token