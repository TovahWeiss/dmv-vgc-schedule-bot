import discord
from discord import ui

from modules.DynamicView import DynamicView

class GroupView(ui.View):
  def __init__(self, states:dict):
    super().__init__(timeout=180)
    self.value = None
    stateOptions = {
        'states A - L': list(states.keys())[0 : 18], 
        'states M - R': list(states.keys())[19:40],
        'states S -': list(states.keys())[41:]
    }
    
    items = [{'id': k, 'subOps': v} for k,v  in list(stateOptions.items())]
    
   
    for item in items:
        button = discord.ui.Button(
            label=item["id"],
            custom_id=item["id"],
            style=discord.ButtonStyle.primary,
            row=item.get("row", 0),  # Row placement: 0 to 4
        )
        
        async def cb(interaction: discord.Interaction, btn=button):
            self.value = btn.label
            row = 0
            subOptions = []
            for index, state in enumerate(stateOptions[btn.custom_id]):
                if(index != 0 and index % 5 == 0):
                    row += 1      
                subOptions.append({'id':state, 'row':row})
                
            v = DynamicView(subOptions)
            await interaction.edit(view=v)
            await v.wait()
            await interaction.delete_original_response()
            self.stop()
            
        button.callback = cb
        self.add_item(button)