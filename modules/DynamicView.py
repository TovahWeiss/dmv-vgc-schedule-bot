import json

import discord
from discord import ui

from modules.CalendarConfig import CalendarConfig

class DynamicView(ui.View):
    def __init__(self, items):
        super().__init__(timeout=180)
        self.value = None
        with open("./configs/calendarConfigs.json") as cfg:
            calendarConfigs = [CalendarConfig.from_dict(item) for item in json.load(cfg)]
        
        for item in items:
            button = discord.ui.Button(
                label=item["id"],
                custom_id=item["id"],
                style=discord.ButtonStyle.primary,
                row=item.get("row", 0),  # Row placement: 0 to 4
            )
            
            async def cb(interaction: discord.Interaction, btn=button):
                self.value = btn.label
                cfg = [cfg for cfg in calendarConfigs if cfg.state == btn.label]
                if(cfg is None):
                    await interaction.respond(content=f"No calendar configuration found for {btn.label}, contact .tovah on discord.", ephemeral=True)
                    self.stop()
                    return
                cfg = cfg[0]
                
                shareBaseUrl = "https://calendar.google.com/calendar/u/0/r?cid="
                friendly = shareBaseUrl + cfg.friendlyCalId
                premier = shareBaseUrl + cfg.calendarId
                
                await interaction.respond(content=f"[{btn.label} - Premier Calendar]({premier})\n[{btn.label} - Friendly Calendar]({friendly})", ephemeral=True)
                self.stop()
                
            button.callback = cb
            self.add_item(button)