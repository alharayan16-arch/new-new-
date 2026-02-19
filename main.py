import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import datetime
import aiohttp
import io
import os
import math

TOKEN = os.getenv("TOKEN")
WELCOME_CHANNEL_ID = 1468431324539781145

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


async def create_welcome_gif(member):
    width, height = 1000, 400
    frames = []

    # Fonts
    font_title = ImageFont.truetype("Montserrat-Bold.ttf", 70)
    font_user = ImageFont.truetype("Montserrat-Regular.ttf", 42)
    font_small = ImageFont.truetype("Montserrat-Regular.ttf", 26)
    font_logo = ImageFont.truetype("Montserrat-Bold.ttf", 110)
    font_link = ImageFont.truetype("Montserrat-Regular.ttf", 22)

    # Smooth gradient background
    gradient = Image.linear_gradient("L").resize((width, height)).rotate(45)
    base_dark = Image.new("RGBA", (width, height), (15, 0, 35, 255))
    purple_overlay = Image.new("RGBA", (width, height), (100, 0, 180, 200))
    base_bg = Image.composite(purple_overlay, base_dark, gradient)
    base_bg = base_bg.filter(ImageFilter.GaussianBlur(2))

    # Avatar
    async with aiohttp.ClientSession() as session:
        async with session.get(member.display_avatar.url) as resp:
            avatar_bytes = await resp.read()

    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar = avatar.resize((120, 120))

    mask = Image.new("L", (120, 120), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 120, 120), fill=255)
    avatar.putalpha(mask)

    username = member.display_name
    member_count = f"Member #{member.guild.member_count}"
    join_time = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M UTC")

    welcome_words = ["WELCOME", "WILLKOMMEN", "BENVENUTO"]

    total_frames = 120  # smooth loop

    # Pre-render logo glow
    logo_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    logo_draw = ImageDraw.Draw(logo_layer)

    a_width = logo_draw.textlength("A", font=font_logo)
    s_width = logo_draw.textlength("S", font=font_logo)
    letter_spacing = -10

    as_total_width = a_width + s_width + letter_spacing
    as_x = width - as_total_width - 120
    as_y = 40

    logo_draw.text((as_x, as_y - 12), "A", font=font_logo, fill=(255, 255, 255, 220))
    logo_draw.text((as_x + a_width + letter_spacing, as_y),
                   "S", font=font_logo, fill=(255, 255, 255, 220))

    logo_glow = logo_layer.filter(ImageFilter.GaussianBlur(35))

    spacing = 60

    for frame in range(total_frames):
        img = base_bg.copy()

        # XO Pattern
        pattern_layer = Image.new("RGBA", (width * 2, height), (0, 0, 0, 0))
        p_draw = ImageDraw.Draw(pattern_layer)

        for y in range(0, height, spacing):
            for x in range(0, width * 2, spacing):
                p_draw.text((x, y), "X", font=font_small, fill=(255, 255, 255, 40))
                p_draw.text((x + 25, y + 25), "O", font=font_small, fill=(255, 255, 255, 40))

        offset = (frame * 3) % spacing
        cropped_pattern = pattern_layer.crop((offset, 0, offset + width, height))
        img = Image.alpha_composite(img, cropped_pattern)

        draw = ImageDraw.Draw(img)

        # Glass panel
        panel = Image.new("RGBA", (720, 240), (255, 255, 255, 30))
        panel = panel.filter(ImageFilter.GaussianBlur(8))
        img.paste(panel, (40, 50), panel)

        # ---------- ULTRA SMOOTH TYPEWRITER ----------
        word_index = (frame // 80) % len(welcome_words)
        current_word = welcome_words[word_index]

        cycle = frame % 80

        # Ease-in typing
        typed_length = int(len(current_word) *
                           min(1, (cycle / 40) ** 1.5))

        display_text = current_word[:typed_length]

        # Hold full word
        if cycle > 45:
            display_text = current_word

        # Delete smoothly
        if cycle > 60:
            delete_progress = int((cycle - 60) * 1.2)
            display_text = current_word[:max(0, len(current_word) - delete_progress)]

        # Modern blinking cursor
        if (frame // 10) % 2 == 0:
            display_text += "│"

        # Glow pulse when completed
        pulse = 0
        if typed_length == len(current_word):
            pulse = int(50 * abs(math.sin(frame * 0.2)))

        # Micro shake on completion
        shake_x = 0
        shake_y = 0
        if typed_length == len(current_word):
            shake_x = math.sin(frame * 2) * 1.5
            shake_y = math.cos(frame * 2) * 1.5

        # Draw glow text
        glow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        glow_draw.text((80 + shake_x, 80 + shake_y),
                       display_text,
                       font=font_title,
                       fill=(255, 255, 255, 180 + pulse))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(8))
        img = Image.alpha_composite(img, glow_layer)

        draw = ImageDraw.Draw(img)
        draw.text((80 + shake_x, 80 + shake_y),
                  display_text,
                  font=font_title,
                  fill=(255, 255, 255))

        # Avatar shadow
        shadow = Image.new("RGBA", (150, 150), (0, 0, 0, 180))
        shadow = shadow.filter(ImageFilter.GaussianBlur(20))
        img.paste(shadow, (50, 180), shadow)
        img.paste(avatar, (60, 170), avatar)

        # User info
        draw.text((220, 180), username, font=font_user, fill=(255, 255, 255))
        draw.text((220, 230), member_count, font=font_small, fill=(230, 230, 255))
        draw.text((220, 260), join_time, font=font_small, fill=(230, 230, 255))

        # Logo
        img = Image.alpha_composite(img, logo_glow)
        draw = ImageDraw.Draw(img)

        draw.text((as_x, as_y - 12), "A", font=font_logo, fill=(255, 255, 255))
        draw.text((as_x + a_width + letter_spacing, as_y),
                  "S", font=font_logo, fill=(255, 255, 255))

        draw.text((as_x - 90, as_y + 120),
                  "https://discord.gg/arabsstudio",
                  font=font_link,
                  fill=(255, 255, 255, 160))

        frames.append(img)

    gif_path = f"welcome_{member.id}.gif"

    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=55,
        loop=0,
        disposal=2,
        optimize=True
    )

    return gif_path


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    gif = await create_welcome_gif(member)

    await channel.send(
        content=f"{member.mention}, Welcome to Arab’s Studio — we’re glad to have you here!",
        file=discord.File(gif)
    )

    os.remove(gif)


@bot.command()
async def testwelcome(ctx):
    gif = await create_welcome_gif(ctx.author)

    await ctx.send(
        content=f"{ctx.author.mention}, Welcome to Arab’s Studio — we’re glad to have you here!",
        file=discord.File(gif)
    )

    os.remove(gif)


bot.run(TOKEN)
