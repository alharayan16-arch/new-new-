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

MAX_FILE_SIZE = 7_500_000  # 7.5MB safety buffer

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"SAFE MAX SYSTEM ONLINE — Logged in as {bot.user}")


async def create_welcome_gif(member):
    width, height = 800, 320  # Reduced resolution (big size drop)
    total_frames = 120       # Reduced frames (half size)
    frames = []

    font_title = ImageFont.truetype("Montserrat-Bold.ttf", 60)
    font_user = ImageFont.truetype("Montserrat-Regular.ttf", 34)
    font_small = ImageFont.truetype("Montserrat-Regular.ttf", 20)

    # Avatar
    async with aiohttp.ClientSession() as session:
        async with session.get(member.display_avatar.url) as resp:
            avatar_bytes = await resp.read()

    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar = avatar.resize((110, 110))

    mask = Image.new("L", (110, 110), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 110, 110), fill=255)
    avatar.putalpha(mask)

    username = member.display_name
    member_count = f"Member #{member.guild.member_count}"

    words = ["WELCOME", "WILLKOMMEN", "BENVENUTO"]

    # Pre-render XO pattern once
    spacing = 60
    pattern_layer = Image.new("RGBA", (width * 2, height), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(pattern_layer)

    for y in range(0, height, spacing):
        for x in range(0, width * 2, spacing):
            p_draw.text((x, y), "X", font=font_small, fill=(255, 255, 255, 30))
            p_draw.text((x + 25, y + 25), "O", font=font_small, fill=(255, 255, 255, 30))

    for frame in range(total_frames):

        # Animated gradient
        gradient = Image.linear_gradient("L").resize((width, height))
        gradient = gradient.rotate(frame * 0.3)

        base_dark = Image.new("RGBA", (width, height), (20, 0, 40, 255))
        purple_overlay = Image.new("RGBA", (width, height), (100, 0, 180, 180))
        bg = Image.composite(purple_overlay, base_dark, gradient)

        img = bg

        # XO movement
        offset = (frame * 2) % spacing
        cropped_pattern = pattern_layer.crop((offset, 0, offset + width, height))
        img = Image.alpha_composite(img, cropped_pattern)

        draw = ImageDraw.Draw(img)

        # Glass panel
        panel = Image.new("RGBA", (600, 180), (255, 255, 255, 25))
        panel = panel.filter(ImageFilter.GaussianBlur(8))
        img.paste(panel, (40, 50), panel)

        # Smooth type animation
        word_index = (frame // 40) % len(words)
        word = words[word_index]
        cycle = frame % 40

        typed = int(len(word) * min(1, (cycle / 25) ** 1.5))
        text = word[:typed]

        if (frame // 10) % 2 == 0:
            text += "│"

        draw.text((80, 80), text,
                  font=font_title,
                  fill=(255, 255, 255))

        # Avatar + shadow
        shadow = Image.new("RGBA", (130, 130), (0, 0, 0, 180))
        shadow = shadow.filter(ImageFilter.GaussianBlur(15))
        img.paste(shadow, (50, 170), shadow)
        img.paste(avatar, (60, 160), avatar)

        draw.text((200, 170), username,
                  font=font_user, fill=(255, 255, 255))
        draw.text((200, 210), member_count,
                  font=font_small, fill=(230, 230, 255))

        # Convert to palette mode (MAJOR size reduction)
        img = img.convert("P", palette=Image.ADAPTIVE, colors=128)

        frames.append(img)

    gif_path = f"welcome_{member.id}.gif"

    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=40,
        loop=0,
        optimize=True,
        disposal=2
    )

    # Safety check
    if os.path.getsize(gif_path) > MAX_FILE_SIZE:
        print("GIF too large — falling back to static image")

        static_path = f"welcome_static_{member.id}.png"
        frames[-1].convert("RGBA").save(static_path)
        os.remove(gif_path)
        return static_path

    return gif_path


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    try:
        file_path = await create_welcome_gif(member)

        await channel.send(
            content=f"{member.mention}, Welcome to Arab’s Studio!",
            file=discord.File(file_path)
        )

        os.remove(file_path)

    except Exception as e:
        print("Error:", e)


bot.run(TOKEN)
