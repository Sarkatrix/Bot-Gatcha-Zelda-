import discord
from discord.ext import commands
from discord import app_commands
import json
import random
from datetime import datetime
import os

# Charger les données JSON
with open("entities.json", "r", encoding="utf-8") as f:
    data = json.load(f)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

summon_tracker = {}         # Pour limiter à 5 invocations/jour
user_collections = {}       # Pour stocker les invocations des joueurs
equipped_relics = {}        # Pour stocker les reliques équipées

MAX_SUMMONS_PER_DAY = 5

regions = [
    "Ordinn", "Lanelle", "Forêt Korogu", "Necluda", "Akkala", "Neige d'Hébra"
]

relics_list = [
    "Bombe Sheikah", "Grappin", "Miroir des Ombres", "Ocarina du Temps", "Cape de Feu"
]

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur de sync : {e}")

# /summon
@bot.tree.command(name="summon", description="Invoque un personnage, objet ou créature aléatoire")
async def summon(interaction: discord.Interaction):
    user_id = interaction.user.id
    today = datetime.utcnow().strftime("%Y-%m-%d")
    user_data = summon_tracker.get(user_id)

    if user_data is None or user_data["date"] != today:
        summon_tracker[user_id] = {"count": 0, "date": today}

    if summon_tracker[user_id]["count"] >= MAX_SUMMONS_PER_DAY:
        await interaction.response.send_message(
            f"⛔ Tu as déjà utilisé tes {MAX_SUMMONS_PER_DAY} invocations pour aujourd'hui !",
            ephemeral=True)
        return

    summon_tracker[user_id]["count"] += 1
    category = random.choice(["characters", "items", "creatures"])
    entity = random.choice(data[category])

    # Ajouter à la collection du joueur
    if user_id not in user_collections:
        user_collections[user_id] = []
    user_collections[user_id].append(entity["name"])

    embed = discord.Embed(
        title=f"🎉 Invocation : {entity['name']}",
        description=f"Catégorie : **{category.capitalize()}**",
        color=discord.Color.gold()
    )
    embed.add_field(name="🎮 Jeu", value=entity["game"], inline=True)
    embed.add_field(name="🌟 Rareté", value=entity["rarity"], inline=True)

    if category == "items":
        embed.add_field(name="✨ Effets", value="\n".join(entity["effects"]), inline=False)
    else:
        embed.add_field(name="✨ Capacités", value="\n".join(entity["abilities"]), inline=False)

    await interaction.response.send_message(embed=embed)

# /collection (privée)
@bot.tree.command(name="collection", description="Affiche ta collection d'invocations")
async def collection(interaction: discord.Interaction):
    user_id = interaction.user.id

    if user_id not in user_collections or not user_collections[user_id]:
        await interaction.response.send_message(
            "📭 Ta collection est vide pour le moment.",
            ephemeral=True
        )
        return

    collection_list = user_collections[user_id]
    display = "\n".join(f"• {name}" for name in collection_list[-20:])  # Les 20 dernières

    embed = discord.Embed(
        title=f"📚 Ta collection d'invocations",
        description=display,
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Total : {len(collection_list)} invocations")

    await interaction.response.send_message(embed=embed, ephemeral=True)

# /explore
@bot.tree.command(name="explore", description="Explore une région et découvre des trésors ou des événements.")
async def explore(interaction: discord.Interaction):
    region = random.choice(regions)
    outcome = random.choice(["trésor", "événement", "piège", "rien"])

    description = {
        "trésor": f"✨ Tu as trouvé un artefact ancien dans la région de **{region}** !",
        "événement": f"⚠️ Un événement inattendu survient dans **{region}** !",
        "piège": f"💥 Un piège a été déclenché dans **{region}** ! Tu perds un peu d’énergie.",
        "rien": f"🌫️ Rien d'intéressant dans **{region}** aujourd'hui..."
    }

    await interaction.response.send_message(description[outcome])

# /duel
@bot.tree.command(name="duel", description="Défie un autre invocateur au combat !")
@app_commands.describe(opposant="Mentionne un joueur pour l'affronter")
async def duel(interaction: discord.Interaction, opposant: discord.Member):
    if opposant.id == interaction.user.id:
        await interaction.response.send_message("❌ Tu ne peux pas te battre contre toi-même !", ephemeral=True)
        return

    participants = [interaction.user, opposant]
    winner = random.choice(participants)

    await interaction.response.send_message(
        f"⚔️ {interaction.user.mention} défie {opposant.mention} !\n"
        f"🎉 Le gagnant est **{winner.display_name}** !")

# /relics
@bot.tree.command(name="relics", description="Équipe une relique spéciale.")
@app_commands.describe(relique="Choisis une relique à équiper")
async def relics(interaction: discord.Interaction, relique: str):
    user_id = interaction.user.id

    if relique not in relics_list:
        await interaction.response.send_message(
            f"❌ Relique inconnue. Choisis parmi : {', '.join(relics_list)}", ephemeral=True)
        return

    equipped_relics[user_id] = relique
    await interaction.response.send_message(f"✅ Tu as équipé la relique : **{relique}**", ephemeral=True)

# Lancement du bot
bot.run(os.getenv("DISCORD_TOKEN"))
