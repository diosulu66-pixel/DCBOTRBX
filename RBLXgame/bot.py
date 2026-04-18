import discord
from discord.ext import commands
import os
import io
import time
import json
import datetime
from scraper import get_clothing_template

# Obtener variables de entorno directamente del sistema (Railway)
TOKEN = os.getenv('DISCORD_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
if ADMIN_ID:
    ADMIN_ID = int(ADMIN_ID)

# Archivo de base de datos JSON para Railway (¡Requiere usar un Volumen persistente en Railway!)
DB_FILE = 'data/database.json'

# Asegurar que el directorio de la base de datos exista
os.makedirs('data', exist_ok=True)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {
        "whitelisted_servers": [],
        "whitelisted_users": {}, # Formato: {"user_id_str": {"expiry": timestamp_or_null, "cooldown": 10, "last_used": 0}}
        "allowed_channel": None,
        "default_cooldown": 10
    }

def save_db():
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

db = load_db()

# Configurar intenciones (Intents) necesarias
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- EVENTOS DE SEGURIDAD (SERVIDORES WHITELISTEADOS) ---

@bot.event
async def on_ready():
    print(f'==================================')
    print(f'[+] Bot conectado exitosamente como {bot.user}')
    print(f'==================================')
    await bot.change_presence(activity=discord.Game(name="!clonar <ID_ROPA>"))
    
    # Si la lista de servidores está completamente vacía, no salir de ningún servidor.
    # Esto asume que el primer servidor al que entra es el de setup.
    if len(db["whitelisted_servers"]) == 0:
        print("[!] La whitelist de servidores está vacía. El bot no saldrá de ningún servidor (Modo Setup).")
        return

    # Revisar servidores actuales y salir de los no autorizados
    for guild in bot.guilds:
        if guild.id not in db["whitelisted_servers"]:
            print(f"[!] Saliendo del servidor no autorizado al iniciar: {guild.name} ({guild.id})")
            await guild.leave()

@bot.event
async def on_guild_join(guild):
    # Si la lista de servidores está vacía (modo setup), se queda en el servidor y lo agrega a la whitelist
    if len(db["whitelisted_servers"]) == 0:
        db["whitelisted_servers"].append(guild.id)
        save_db()
        print(f"[+] Modo Setup: Servidor {guild.name} ({guild.id}) agregado automáticamente a la whitelist.")
        return

    # Si invitan al bot a un servidor no whitelistado, se sale automáticamente
    if guild.id not in db["whitelisted_servers"]:
        print(f"[!] Saliendo del servidor no autorizado recién unido: {guild.name} ({guild.id})")
        await guild.leave()

# --- FUNCIONES DE VERIFICACIÓN ---

def is_admin(ctx):
    return ctx.author.id == ADMIN_ID

def check_permissions_and_channel(ctx):
    # 1. El admin siempre puede ejecutar comandos
    if ctx.author.id == ADMIN_ID:
        return True, None
        
    # Si es un mensaje directo (DM), ignorar la regla de canales
    is_dm = isinstance(ctx.channel, discord.DMChannel)
        
    # 2. Verificar canal (solo si estamos en un servidor)
    if not is_dm and db["allowed_channel"] and ctx.channel.id != db["allowed_channel"]:
        return False, " El bot no se puede usar en este canal."
        
    # 3. Verificar usuario en whitelist
    user_id_str = str(ctx.author.id)
    if user_id_str not in db["whitelisted_users"]:
        return False, " No estás en la whitelist para usar este bot."
        
    user_data = db["whitelisted_users"][user_id_str]
    
    # 4. Verificar expiración del usuario
    if user_data.get("expiry") is not None:
        if time.time() > user_data["expiry"]:
            return False, " Tu acceso a la whitelist ha expirado."
            
    # 5. Verificar cooldown
    cooldown_time = user_data.get("cooldown", db["default_cooldown"])
    last_used = user_data.get("last_used", 0)
    time_passed = time.time() - last_used
    
    if time_passed < cooldown_time:
        wait_time = int(cooldown_time - time_passed)
        return False, f"⏳ Debes esperar {wait_time} segundos para volver a usar el bot."
        
    # Actualizar el last_used (se hace aquí para no tener que hacerlo luego)
    db["whitelisted_users"][user_id_str]["last_used"] = time.time()
    save_db()
    
    return True, None

# --- COMANDO PRINCIPAL ---

@bot.command(name='clonar', help="Clona el template de una ropa de Roblox dado su ID.")
async def clonar(ctx, asset_id: int):
    allowed, error_msg = check_permissions_and_channel(ctx)
    if not allowed:
        # Enviar mensaje que se auto-destruye para no hacer spam en el chat
        await ctx.send(error_msg, delete_after=5)
        return

    print(f"[LOG] {ctx.author} solicitó clonar el ID: {asset_id}")

    msg = await ctx.send(f"🔍 Buscando el template original para el ID **{asset_id}**... Por favor espera.")

    img_bytes, error = await get_clothing_template(asset_id)

    if error is not None:
        try:
            await msg.edit(content=f" **Error al clonar el ID {asset_id}:**\n{error}")
        except discord.errors.NotFound:
            await ctx.send(f" **Error al clonar el ID {asset_id}:**\n{error}")
        return

    if img_bytes is not None:
        file = discord.File(fp=io.BytesIO(img_bytes), filename=f"template_{asset_id}.png")
        
        embed = discord.Embed(
            title="Template Clonado :> ",
            description=f"Aquí tienes:",
            color=discord.Color.green()
        )
        embed.add_field(name="ID Original", value=str(asset_id), inline=True)
        embed.add_field(name="Solicitado por", value=ctx.author.mention, inline=True)
        embed.set_footer(text="Roblox Clothing Cloner Bot v1.0")
        embed.set_image(url=f"attachment://template_{asset_id}.png")

        try:
            await msg.delete()
        except discord.errors.NotFound:
            pass
            
        await ctx.send(embed=embed, file=file)
        print(f"[LOG] Imagen enviada correctamente para {asset_id}.")

@clonar.error
async def clonar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ **Falta el ID de la ropa.**\nUso correcto: `!clonar <ID>`\nEjemplo: `!clonar 123456789`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ **El ID debe ser un número entero válido.**\nEjemplo: `!clonar 123456789`")

# --- COMANDOS DE ADMINISTRADOR ---

@bot.command(name='adduser')
@commands.check(is_admin)
async def adduser(ctx, user_id: int, time_type: str = "ind"):
    """Agrega un usuario a la whitelist. Ej: !adduser 1234 7d / !adduser 1234 30d / !adduser 1234 ind"""
    expiry = None
    time_type = time_type.lower()
    
    if time_type.endswith('d'):
        try:
            days = int(time_type[:-1])
            expiry = time.time() + (days * 24 * 60 * 60)
        except ValueError:
            await ctx.send("error")
            return
    elif time_type != "ind":
        await ctx.send("error")
        return

    db["whitelisted_users"][str(user_id)] = {
        "expiry": expiry,
        "cooldown": db["default_cooldown"],
        "last_used": 0
    }
    save_db()
    await ctx.send(f"✅ Usuario `{user_id}` agregado a la whitelist. Tiempo: {time_type}.")

@bot.command(name='removeuser')
@commands.check(is_admin)
async def removeuser(ctx, user_id: int):
    """Elimina un usuario de la whitelist."""
    if str(user_id) in db["whitelisted_users"]:
        del db["whitelisted_users"][str(user_id)]
        save_db()
        await ctx.send(f"✅ Usuario `{user_id}` eliminado de la whitelist.")
    else:
        await ctx.send("⚠️ El usuario no estaba en la whitelist.")

@bot.command(name='setusercooldown')
@commands.check(is_admin)
async def setusercooldown(ctx, user_id: int, cooldown: int):
    """Configura el cooldown (en segundos) específico de un usuario."""
    user_id_str = str(user_id)
    if user_id_str in db["whitelisted_users"]:
        db["whitelisted_users"][user_id_str]["cooldown"] = cooldown
        save_db()
        await ctx.send(f"✅ Cooldown del usuario `{user_id}` configurado a {cooldown} segundos.")
    else:
        await ctx.send("El usuario no está en la whitelist.")

@bot.command(name='addserver')
@commands.check(is_admin)
async def addserver(ctx, server_id: int):
    """Agrega un servidor a la whitelist para que el bot no se salga."""
    if server_id not in db["whitelisted_servers"]:
        db["whitelisted_servers"].append(server_id)
        save_db()
        await ctx.send(f" Servidor `{server_id}` agregado a la whitelist.")
    else:
        await ctx.send("El servidor ya estaba en la whitelist.")

@bot.command(name='removeserver')
@commands.check(is_admin)
async def removeserver(ctx, server_id: int):
    """Elimina un servidor de la whitelist."""
    if server_id in db["whitelisted_servers"]:
        db["whitelisted_servers"].remove(server_id)
        save_db()
        await ctx.send(f" Servidor `{server_id}` eliminado de la whitelist.")
        # Si el bot está actualmente en ese servidor, salirse
        guild = bot.get_guild(server_id)
        if guild:
            await guild.leave()
    else:
        await ctx.send(" El servidor no estaba en la whitelist.")

@bot.command(name='setidchannel')
@commands.check(is_admin)
async def setidchannel(ctx, channel_id: int = 0):
    """Configura en qué canal debe usarse el bot. Usa 0 para permitir en todos los canales."""
    if channel_id == 0:
        db["allowed_channel"] = None
        await ctx.send(" Ahora el bot se puede usar en cualquier canal.")
    else:
        db["allowed_channel"] = channel_id
        await ctx.send(f"Canal de uso configurado a: `<#{channel_id}>`")
    save_db()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(" No tienes permisos de administrador para usar este comando.", delete_after=5)

if __name__ == '__main__':
    if not TOKEN or TOKEN == "TU_DISCORD_TOKEN_AQUI":
        print(" ERROR: No se ha configurado el DISCORD_TOKEN en las variables de entorno")
    else:
        bot.run(TOKEN)
