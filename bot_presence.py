import discord
from discord.ext import commands, tasks
import asyncio
import datetime

intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True

# Désactivation de la commande help par défaut
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Stockage temporaire des présences et absences
presence_data = {}
absences = {}

CHANNEL_ID = 1399882872588075149  # Remplace par l'ID du salon
ROLE_ID = 1324230604266537023     # ID du rôle à ping

@bot.event
async def on_ready():
    print(f'✅ Connecté comme {bot.user}')
    if not relance.is_running():
        relance.start()


# Listener global : supprime automatiquement les messages de commande
@bot.listen("on_message")
async def delete_command_message(message):
    if message.author.bot:
        return
    if message.content.startswith("!"):  # détecte une commande
        try:
            await message.delete()
        except discord.Forbidden:
            print("❌ Impossible de supprimer le message (permissions manquantes).")


# Commande pour envoyer le message de présence
@bot.command()
async def presence(ctx):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        await ctx.send("Salon non trouvé.")
        return

    today = datetime.datetime.now().strftime("%d/%m")

    embed = discord.Embed(
        title="📌 Présence ce soir",
        color=discord.Color.blue()
    )

    embed.set_image(url="https://media.discordapp.net/attachments/1390841211769585675/1406112363827957830/Crime_Syndicate.png?ex=68a147af&is=689ff62f&hm=1d18c229474e5015baca885a460f44ab4cf7b592dd3cd79f7732ed0d097637af&=&width=550&height=309")

    embed.add_field(
        name="",
        value=f"Présence ({today}) à 21h15, planning à voir en rp\n\n"
              "Réagissez avec : ✅ = présent, ❌ = absent, ❓ = incertain",
        inline=False
    )

    message = await channel.send(embed=embed)

    for emoji in ["✅", "❌", "❓"]:
        await message.add_reaction(emoji)

    presence_data[message.id] = {"✅": [], "❌": [], "❓": [], "message": message}

    today_date = datetime.date.today()
    role = ctx.guild.get_role(ROLE_ID)
    if role:
        to_ping = []
        for m in role.members:
            if m.bot:
                continue
            name = m.name
            if name in absences:
                start, end = absences[name]
                start = datetime.date.fromisoformat(start)
                end = datetime.date.fromisoformat(end)
                if start <= today_date <= end:
                    continue
            to_ping.append(m.mention)

        if to_ping:
            await channel.send(f"{' '.join(to_ping)}, merci de réagir au message de présence !")


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    msg_id = reaction.message.id
    if msg_id in presence_data:
        for k in ["✅", "❌", "❓"]:
            if user.name in presence_data[msg_id][k]:
                presence_data[msg_id][k].remove(user.name)
        if str(reaction.emoji) in ["✅", "❌", "❓"]:
            presence_data[msg_id][str(reaction.emoji)].append(user.name)


@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return
    msg_id = reaction.message.id
    if msg_id in presence_data:
        if str(reaction.emoji) in ["✅", "❌", "❓"]:
            if user.name in presence_data[msg_id][str(reaction.emoji)]:
                presence_data[msg_id][str(reaction.emoji)].remove(user.name)


# Commande pour déclarer une absence
@bot.command()
async def absence(ctx, start_date, end_date):
    """Exemple: !absence 2025-08-16 2025-08-20"""
    user = ctx.author.name
    absences[user] = (start_date, end_date)
    await ctx.send(f"{user}, ton absence du {start_date} au {end_date} est enregistrée.")


# Commande pour retirer une absence
@bot.command()
async def retirer_absence(ctx):
    user = ctx.author.name
    if user in absences:
        del absences[user]
        await ctx.send(f"✅ {user}, ton absence a été retirée.")
    else:
        await ctx.send(f"ℹ️ {user}, aucune absence n'était enregistrée pour toi.")


# Commande pour afficher le récapitulatif
@bot.command()
async def recap(ctx, message_id: int):
    if message_id not in presence_data:
        await ctx.send("Message ID invalide.")
        return
    data = presence_data[message_id]
    embed = discord.Embed(title="📊 Récapitulatif présences", color=discord.Color.green())
    for emoji in ["✅", "❌", "❓"]:
        users = ", ".join(data[emoji]) if data[emoji] else "Aucun"
        embed.add_field(name=emoji, value=users, inline=False)
    await ctx.send(embed=embed)


# Commande pour lister toutes les absences enregistrées
@bot.command()
async def liste_absences(ctx):
    if not absences:
        await ctx.send("📭 Aucune absence enregistrée.")
        return

    embed = discord.Embed(title="📅 Liste des absences", color=discord.Color.red())
    for user, (start, end) in absences.items():
        start_fmt = datetime.datetime.fromisoformat(start).strftime("%d/%m")
        end_fmt = datetime.datetime.fromisoformat(end).strftime("%d/%m")
        embed.add_field(name=user, value=f"Du **{start_fmt}** au **{end_fmt}**", inline=False)

    await ctx.send(embed=embed)


# Commande d'aide personnalisée
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 Commandes disponibles",
        description="Voici la liste des commandes et leur fonctionnement :",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="!presence",
        value="Envoie le message de présence du soir avec les réactions ✅ ❌ ❓.\n"
              "Le bot ping les membres du rôle choisi qui n'ont pas d'absence enregistrée.",
        inline=False
    )

    embed.add_field(
        name="!absence <début> <fin>",
        value="Déclare une absence.\nFormat des dates : YYYY-MM-DD (exemple : `!absence 2025-08-16 2025-08-20`).",
        inline=False
    )

    embed.add_field(
        name="!retirer_absence",
        value="Supprime ton absence si elle a été enregistrée.",
        inline=False
    )

    embed.add_field(
        name="!recap <message_id>",
        value="Affiche le récapitulatif des présences pour un message précis.\n"
              "Astuce : fais un clic droit sur le message pour copier son ID.",
        inline=False
    )

    embed.add_field(
        name="!liste_absences",
        value="Affiche toutes les absences actuellement enregistrées.",
        inline=False
    )

    embed.add_field(
        name="!help",
        value="Affiche ce message d'aide avec la liste de toutes les commandes.",
        inline=False
    )

    await ctx.send(embed=embed)


# Relance automatique (toutes les heures)
@tasks.loop(minutes=60)
async def relance():
    for msg_id, data in presence_data.items():
        message = data["message"]
        channel = message.channel
        role = message.guild.get_role(ROLE_ID)
        if not role:
            continue

        reacted = data["✅"] + data["❌"] + data["❓"]
        today = datetime.date.today()
        to_ping = []

        for m in role.members:
            if m.bot:
                continue
            name = m.name
            if name in reacted:
                continue
            if name in absences:
                start, end = absences[name]
                start = datetime.date.fromisoformat(start)
                end = datetime.date.fromisoformat(end)
                if start <= today <= end:
                    continue
            to_ping.append(m.mention)

        if to_ping:
            await channel.send(f"{' '.join(to_ping)}, merci de réagir au message de présence !")


# ⚠️ Mets ton token ici (pense à le régénérer si tu l'as posté publiquement)
bot.run("MTQwNjEwNTM3OTMzMDMyNjU0OA.GyDjq3.eA0A_lA45ZHTT-shwkpomMmLm9fN6BymHrlLW4")
