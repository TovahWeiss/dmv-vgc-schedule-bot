import discord
from discord import ui

class DynamicView(ui.View):
  def __init__(self, items):
    super().__init__(timeout=180)
    self.value = None

    for item in items:
        button = discord.ui.Button(
            label=item["id"],
            custom_id=item["id"],
            style=discord.ButtonStyle.primary,
            row=item.get("row", 0),  # Row placement: 0 to 4
        )
        
        async def cb(interaction: discord.Interaction, btn=button):
            self.value = btn.label
            await interaction.respond(f"Removed {btn.label}", ephemeral=True, delete_after=15)
            self.stop()
            
        button.callback = cb
        self.add_item(button)