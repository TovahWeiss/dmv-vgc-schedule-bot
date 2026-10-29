
import drawsvg as draw
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
SCOPES = ["https://www.googleapis.com/auth/calendar"]
vaCalId = 'b395ee4ddd6474d60a69c911d76c04badf64451e26a1dfb1012f56482dff5381@group.calendar.google.com'
mdCalId = '927124fb7109ce4ade4c098277951cddc85b1b3ec96f3af53d42272d0f3b0dfc@group.calendar.google.com'
dcCalId = '343b752ae8b2942dbe9a2f2aa32a0470d50ecfc4409dffd183851d7f4d35b25b@group.calendar.google.com'

friendlyVaCalId = 'ad51dc180f1337ccc228f8f61973408d9cc7e74871cb61e8fc0ea27203e4e210@group.calendar.google.com'
friendlyMdCalId = '873fa813d71d99c7351e407086eb0e9d7208c70533dc8ca11e3564852e053448@group.calendar.google.com'
friendlyDcCalId = 'eb5d9c46e85780cbe9b0df36585ab52fc932a59e1c5e49760135e7f26606da4a@group.calendar.google.com'

nonPremierEventType = 'nonpremier VG'

# lifted
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

# new
import asyncio
import tkinter as tk
from tkinter import font
import base64


async def main():
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
    graphicTitle = config['graphicTitle']
    unknownIconPath = config['unknownIconPath']
    
    existingEvents = await getExistingCalItems()
    if(existingEvents is None or len(existingEvents) == 0):
        return
    existingEvents = [x for x in existingEvents if x['organizer']['email'] in [vaCalId, mdCalId, dcCalId]]
    existingEvents = sorted(existingEvents, key=lambda event: datetime.strptime(event['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z'))
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
    
    gradient = draw.LinearGradient(1, embedW/6, embedW/2, embedW/3)
    gradient.add_stop(0, headerGradientStartColor, 1)
    gradient.add_stop(1, headerGradientEndColor, 1)
    d.append(draw.Rectangle(margin, 0, embedW - (2*margin), headerHeight, fill=gradient, rx=cornerRadius, ry=cornerRadius))
    
    d.append(draw.Image( x=margin + 20, y=margin, width=logoSize, height=logoSize,  path=logoPath, embed=True) )
    d.append(draw.Text(graphicTitle, 54, 640, 50, fill=headerTextColor, center=True, class_='title-text', font_family=headerFont)) 
        
    for i in range(headerHeight, embedH - rowHeight, rowHeight):
        if rowIndex > len(existingEvents)-1: 
            continue
        e = existingEvents[rowIndex]
        rowBaseline = i + 26
        
        #draw dividers if dif date from last and write date
        currentStart = datetime.strptime(e['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
        d.append(draw.Rectangle(5, i, embedW-10, rowHeight, fill=rowBackground,  rx=cornerRadius, ry=cornerRadius))
           
        if(rowIndex != 0):
            previousStartDate = datetime.strptime(existingEvents[rowIndex-1]['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z').date()
            if(currentStart.date() != previousStartDate):
                d.append(draw.Line(margin, i, embedW-margin, i, stroke=imageBackground, stroke_width=2))          
                d.append(draw.Text(currentStart.strftime("%d"), 18, 16, rowBaseline, fill= textPrimaryColor))
                d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, rowBaseline, fill= textPrimaryColor))
            else:
                d.append(draw.Rectangle(margin, i-10, embedW-10, rowHeight, fill=rowBackground))
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
        
        icon = unknownIconPath
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
 
asyncio.run(main())