import typing
import discord
from discord.ext import commands
import json

class ChillBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="cb!", intents=discord.Intents.all())
        self.add_cog(Core(self))
        self.add_cog(Sniping(self))

class Core(commands.Cog):
    def __init__(self, bot : ChillBot) -> None:
        self.bot = bot

class LIFO:
    """ Implementation of the LIFO (last in, first out caching strategy """
    def __init__(self, *, max_size : int = 20) -> None:
        self._list : typing.List[typing.Any] = []

    def push(self, item : typing.Any):
        """ 
        Pushes an item to the top of the stack.
        Removes the bottom-most item if the stack
        exceeds the given `max_size` limit. 
        """

        if len(self._list) >= 20:
            self._list.pop(0)
        
        self._list.append(item)

    def pop(self) -> typing.Any:
        """
        Pop the item at the top of the stack, and return it
        """

        return self._list.pop(self._last_index)

    def peek(self) -> typing.Any:
        """
        Returns the item at the top of the stack
        """

        return self._list[0]

    @property
    def _last_index(self):
        return len(self._list) - 1

    @property
    def stack(self) -> typing.List[typing.Any]:
        """ Returns the underlying list object """

        return self._list

    @property
    def size(self):
        return len(self._list)

class SnipeView(discord.ui.View):
    def __init__(self, *, pages : typing.List[discord.Embed], author : discord.Member):
        super().__init__()
        self.pages = pages
        self.current = 0
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message('That menu is not for you.', ephemeral=True)
            return False

        return True

    @discord.ui.button(emoji='⬅️', style=discord.ButtonStyle.green)
    async def prev(self, button : discord.ui.Button, interaction : discord.Interaction):
        if self.current == 0:
            self.current = len(self.pages) - 1
        else:
            self.current -= 1
        
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(emoji='⏹️', style=discord.ButtonStyle.red)
    async def next(self, button : discord.ui.Button, interaction : discord.Interaction):
        await interaction.response.defer()
        await interaction.delete_original_message()

    @discord.ui.button(emoji='➡️', style=discord.ButtonStyle.green)
    async def next(self, button : discord.ui.Button, interaction : discord.Interaction):
        if self.current == len(self.pages) - 1:
            self.current = 0
        else:
            self.current += 1

        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    

class Sniping(commands.Cog):
    def __init__(self, bot : ChillBot) -> None:
        self.bot = bot
        self.lifo = LIFO()
    
    @commands.Cog.listener()
    async def on_message_edit(self, before : discord.Message, after : discord.Message):
        self.lifo.push((before, after))

    @commands.Cog.listener()
    async def on_message_delete(self, message : discord.Message):
        pass

    @commands.command()
    async def editsnipe(self, ctx : commands.Context):
        embeds = []
        page_number = 1
        for before, after in self.lifo.stack:
            embed = discord.Embed(
                title='Edit snipe',
                description=f'[Jump to message]({after.jump_url})',
                color=discord.Color.blurple()
            )
            embed.add_field(name='Before', value=before.content)
            embed.add_field(name='After', value=after.content)
            embed.set_footer(text=f'Page {page_number} of {self.lifo.size}')
            embeds.append(embed)
            page_number += 1
        
        view = SnipeView(pages=embeds, author=ctx.author)
        await ctx.send(embed=embeds[0], view=view)

with open('config.json', 'r') as f:
    data = json.load(f)

bot = ChillBot()
bot.run(data['TOKEN'])