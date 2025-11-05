import nextcord
from nextcord.ext import commands
from nextcord import Interaction, ui
import os

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


class PermissionMenu(ui.View):
    def __init__(self, author, roles, categories):
        super().__init__(timeout=240)
        self.author = author
        self.selected_role = None
        self.selected_category = None
        self.permission_settings = {}

        # Select de cargos
        self.role_select = ui.Select(placeholder="Select a role", min_values=1, max_values=1)
        for r in roles:
            self.role_select.add_option(label=r.name, value=str(r.id))
        self.role_select.callback = self.role_selected
        self.add_item(self.role_select)

        # Select de categorias
        self.category_select = ui.Select(placeholder="Select a category", min_values=1, max_values=1)
        for c in categories:
            self.category_select.add_option(label=c.name, value=str(c.id))
        self.category_select.callback = self.category_selected
        self.add_item(self.category_select)

        # Botões
        btn_basic = ui.Button(label="Basic Permissions", style=nextcord.ButtonStyle.blurple)
        btn_basic.callback = self.basic_perm
        self.add_item(btn_basic)

        btn_advanced = ui.Button(label="Advanced Permissions", style=nextcord.ButtonStyle.blurple)
        btn_advanced.callback = self.advanced_perm
        self.add_item(btn_advanced)

        btn_create = ui.Button(label="Create Channel", style=nextcord.ButtonStyle.green)
        btn_create.callback = self.create_channel
        self.add_item(btn_create)

    async def interaction_check(self, interaction: Interaction):
        """Impede que pessoas diferentes usem o painel."""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "❌ Only the command author can use this panel.",
                ephemeral=True
            )
            return False
        return True

    async def role_selected(self, interaction: Interaction):
        if not interaction.data:
            return await interaction.response.send_message("Error.", ephemeral=True)

        role_id = int(interaction.data["values"][0])
        self.selected_role = interaction.guild.get_role(role_id)
        await interaction.response.defer()

    async def category_selected(self, interaction: Interaction):
        if not interaction.data:
            return await interaction.response.send_message("Error.", ephemeral=True)

        category_id = int(interaction.data["values"][0])
        self.selected_category = nextcord.utils.get(interaction.guild.categories, id=category_id)
        await interaction.response.defer()

    async def basic_perm(self, interaction: Interaction):
        await interaction.response.send_modal(BasicPermissionModal(self))

    async def advanced_perm(self, interaction: Interaction):
        await interaction.response.send_modal(AdvancedPermissionModal(self))

    async def create_channel(self, interaction: Interaction):
        if not self.selected_role or not self.selected_category:
            return await interaction.response.send_message(
                "❌ Select a role and category first.",
                ephemeral=True
            )

        channel_name = self.permission_settings.get("channel_name", "new-channel")

        overwrites = {
            interaction.guild.default_role: nextcord.PermissionOverwrite(
                view_channel=self.permission_settings.get("everyone_view", False),
                send_messages=self.permission_settings.get("everyone_send", False),
                attach_files=self.permission_settings.get("everyone_images", False),
                use_external_stickers=self.permission_settings.get("everyone_stickers", False),
                use_slash_commands=self.permission_settings.get("everyone_commands", False),
                add_reactions=self.permission_settings.get("everyone_react", False)
            ),
            self.selected_role: nextcord.PermissionOverwrite(
                view_channel=self.permission_settings.get("role_view", True),
                send_messages=self.permission_settings.get("role_send", True),
                attach_files=self.permission_settings.get("role_images", True),
                use_external_stickers=self.permission_settings.get("role_stickers", True),
                use_slash_commands=self.permission_settings.get("role_commands", True),
                add_reactions=self.permission_settings.get("role_react", True)
            )
        }

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=self.selected_category,
            overwrites=overwrites
        )

        await interaction.response.send_message(
            f"✅ Channel created: {channel.mention}",
            ephemeral=True
        )


class BasicPermissionModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Basic Permissions")
        self.view_ref = view

        self.channel_name = ui.TextInput(label="Channel name", required=True)
        self.everyone_view = ui.TextInput(label="Everyone can view? yes/no")
        self.everyone_send = ui.TextInput(label="Everyone can send? yes/no")
        self.role_view = ui.TextInput(label="Role can view? yes/no")
        self.role_send = ui.TextInput(label="Role can send? yes/no")

        for item in [
            self.channel_name,
            self.everyone_view,
            self.everyone_send,
            self.role_view,
            self.role_send
        ]:
            self.add_item(item)

    async def callback(self, interaction: Interaction):
        self.view_ref.permission_settings.update({
            "channel_name": str(self.channel_name.value),
            "everyone_view": self.everyone_view.value.lower() == "yes",
            "everyone_send": self.everyone_send.value.lower() == "yes",
            "role_view": self.role_view.value.lower() == "yes",
            "role_send": self.role_send.value.lower() == "yes",
        })

        await interaction.response.send_message("✅ Basic permissions updated.", ephemeral=True)


class AdvancedPermissionModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Advanced Permissions")
        self.view_ref = view

        self.everyone_images = ui.TextInput(label="Everyone images? yes/no")
        self.everyone_stickers = ui.TextInput(label="Everyone stickers? yes/no")
        self.everyone_commands = ui.TextInput(label="Everyone bot commands? yes/no")
        self.everyone_react = ui.TextInput(label="Everyone reactions? yes/no")
        self.role_images = ui.TextInput(label="Role images? yes/no")

        for item in [
            self.everyone_images,
            self.everyone_stickers,
            self.everyone_commands,
            self.everyone_react,
            self.role_images
        ]:
            self.add_item(item)

    async def callback(self, interaction: Interaction):

        self.view_ref.permission_settings.update({
            "everyone_images": self.everyone_images.value.lower() == "yes",
            "everyone_stickers": self.everyone_stickers.value.lower() == "yes",
            "everyone_commands": self.everyone_commands.value.lower() == "yes",
            "everyone_react": self.everyone_react.value.lower() == "yes",
            "role_images": self.role_images.value.lower() == "yes",
            "role_stickers": True,
            "role_commands": True,
            "role_react": True,
        })

        await interaction.response.send_message("✅ Advanced permissions updated.", ephemeral=True)


@bot.command()
async def admin(ctx):
    roles = [r for r in ctx.guild.roles if r.name != "@everyone" and r < ctx.guild.me.top_role]
    categories = ctx.guild.categories

    view = PermissionMenu(ctx.author, roles, categories)
    await ctx.send("✅ Admin panel loaded.", view=view)


# ✅ Token via variável de ambiente
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("❌ ERROR: DISCORD_TOKEN not found. Add it in Render → Environment Variables.")

bot.run(TOKEN)                add_reactions=self.permission_settings.get("role_react", True)
            )
        }

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=self.selected_category,
            overwrites=overwrites
        )

        await interaction.response.send_message(f"Channel created: {channel.mention}", ephemeral=True)


class BasicPermissionModal(ui.Modal):
    def __init__(self, view: PermissionMenu):
        super().__init__(title="Basic Permissions")
        self.view_ref = view

        self.channel_name = ui.TextInput(label="Channel name")
        self.everyone_view = ui.TextInput(label="Everyone can view? yes/no")
        self.everyone_send = ui.TextInput(label="Everyone can send? yes/no")
        self.role_view = ui.TextInput(label="Role can view? yes/no")
        self.role_send = ui.TextInput(label="Role can send? yes/no")

        self.add_item(self.channel_name)
        self.add_item(self.everyone_view)
        self.add_item(self.everyone_send)
        self.add_item(self.role_view)
        self.add_item(self.role_send)

    async def callback(self, interaction: Interaction):
        self.view_ref.permission_settings["channel_name"] = str(self.channel_name.value)
        self.view_ref.permission_settings["everyone_view"] = self.everyone_view.value.lower() == "yes"
        self.view_ref.permission_settings["everyone_send"] = self.everyone_send.value.lower() == "yes"
        self.view_ref.permission_settings["role_view"] = self.role_view.value.lower() == "yes"
        self.view_ref.permission_settings["role_send"] = self.role_send.value.lower() == "yes"

        await interaction.response.send_message("Basic permissions updated.", ephemeral=True)


class AdvancedPermissionModal(ui.Modal):
    def __init__(self, view: PermissionMenu):
        super().__init__(title="Advanced Permissions")
        self.view_ref = view

        self.everyone_images = ui.TextInput(label="Everyone images? yes/no")
        self.everyone_stickers = ui.TextInput(label="Everyone stickers? yes/no")
        self.everyone_commands = ui.TextInput(label="Everyone bot commands? yes/no")
        self.everyone_react = ui.TextInput(label="Everyone reactions? yes/no")
        self.role_images = ui.TextInput(label="Role images? yes/no")

        self.add_item(self.everyone_images)
        self.add_item(self.everyone_stickers)
        self.add_item(self.everyone_commands)
        self.add_item(self.everyone_react)
        self.add_item(self.role_images)

    async def callback(self, interaction: Interaction):
        self.view_ref.permission_settings["everyone_images"] = self.everyone_images.value.lower() == "yes"
        self.view_ref.permission_settings["everyone_stickers"] = self.everyone_stickers.value.lower() == "yes"
        self.view_ref.permission_settings["everyone_commands"] = self.everyone_commands.value.lower() == "yes"
        self.view_ref.permission_settings["everyone_react"] = self.everyone_react.value.lower() == "yes"
        self.view_ref.permission_settings["role_images"] = self.role_images.value.lower() == "yes"

        self.view_ref.permission_settings["role_stickers"] = True
        self.view_ref.permission_settings["role_commands"] = True
        self.view_ref.permission_settings["role_react"] = True

        await interaction.response.send_message("Advanced permissions updated.", ephemeral=True)


@bot.command()
async def admin(ctx):
    guild = ctx.guild
    roles = [r for r in guild.roles if r.name != "@everyone" and r < guild.me.top_role]
    categories = guild.categories

    view = PermissionMenu(ctx.author, roles, categories)
    await ctx.send("Admin panel loaded.", view=view)


# ✅ TOKEN VIA VARIÁVEL DE AMBIENTE
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    raise ValueError("❌ ERRO: Variável DISCORD_TOKEN não encontrada no Render!")

bot.run(TOKEN)
