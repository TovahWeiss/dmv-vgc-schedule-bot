
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
    fFamily = "Arial"
    font_path = "Montserrat-Italic-VariableFont_wght.ttf"
    with open(font_path, 'rb') as f:
        ttf_bytes = f.read()

    b64_encoded = base64.b64encode(ttf_bytes).decode('utf-8')
    data_uri = f'data:font/ttf;base64,{b64_encoded}'
    
    existingEvents = await getExistingCalItems()
  
    if(existingEvents is None or len(existingEvents) == 0):
            return
        
    existingEvents = [x for x in existingEvents if x['organizer']['email'] in [vaCalId, mdCalId, dcCalId]]
  
    d = draw.Drawing(1280, 720, origin='top-left', font_family=fFamily)
    d.append(draw.Rectangle(0, 0, 1280, 720, fill='white'))
   
    #header branding
    css_rules = f"""
        @font-face {{
            font-family: 'Montserrat';
            src: url('{data_uri}') format('truetype');
        }}
        .title-text {{
            font-family: 'Montserrat';
            font-weight: 900;
            font-size: 54px;
            fill: #333333;
        }}
    """
    d.append_css(css_rules)
    d.append(draw.Rectangle(0, 0, 1280, 100, fill='lightgray'))
    d.append(
        draw.Image(
            x=5,
            y=5,
            width=90,
            height=90,
            path="DMV_Falinks.png",
            embed=True,
        )
    )
    d.append(draw.Text('DMV Upcoming Premier Events', 54, 640, 50, fill='Black', center=True, class_='title-text')) 
        
    index = 0
    for i in range(100, 720, 44):
        if index > len(existingEvents)-1: 
            continue
        e = existingEvents[index]
        
        currentStart = datetime.strptime(e['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
                    
        #draw dividers if dif date from last
        if(index != 0):
            previousStartDate = datetime.strptime(existingEvents[index-1]['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z').date()
            if(currentStart.date() != previousStartDate):
                d.append(draw.Line(0, i, 1280, i, stroke='lightgray', stroke_width=1))
                d.append(draw.Text(currentStart.strftime("%d"), 18, 16, i + 26, fill='black'))
                d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, i + 26, fill='black'))
        else:
            # line 1
            d.append(draw.Line(0, i, 1280, i, stroke='lightgray', stroke_width=1))
            if(currentStart.date() == datetime.now().date()):
                d.append(draw.Circle(26, i + 20, 16, fill='dodgerblue'))
                d.append(draw.Text(currentStart.strftime("%d"), 18, 16, i + 26, fill='white'))
                d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, i + 26, fill='dodgerblue'))
            else:
                d.append(draw.Text(currentStart.strftime("%d"), 18, 16, i + 26, fill='black'))
                d.append(draw.Text(currentStart.strftime("%b, %a"), 14, 50, i + 26, fill='black'))
        
        color = 'black'
        if(e['organizer']['email'] == vaCalId):
            color = 'green'
        elif(e['organizer']['email'] == dcCalId):
            color = 'lightblue'
        elif(e['organizer']['email'] == mdCalId):
            color = 'red'
                
        bulletStart = 140
        bullet = draw.Circle(bulletStart, i + 22, 6, fill=color)
        d.append(bullet) # Draw a circle
        startTime = currentStart.strftime("%I:%M%p")
        d.append(draw.Text(startTime, 12, bulletStart + 20, i + 26, fill='black'))
        
        rowFontSize = 14
        fsPixels = font.Font(family= fFamily, size=rowFontSize-2)
        titleStart = bulletStart + 120
        titleWidth = fsPixels.measure(e['summary'])
        d.append(draw.Text(e['summary'], rowFontSize, titleStart, i + 26, fill='Black'))
        d.append(draw.Text(e['location'], rowFontSize, titleStart + titleWidth, i + 26, fill='grey'))
        index += 1

    d.set_pixel_scale(2)  # Set number of pixels per geometry unit
    #d.set_render_size(400, 200)  # Alternative to set_pixel_scale
    d.save_svg('schedule.svg')
    # cairosvg.svg2png(url="schedule.svg", write_to="schedule.png")
    d.save_png('schedule.png')
 
asyncio.run(main())