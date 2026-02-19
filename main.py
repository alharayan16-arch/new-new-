import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
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
    print(f"MAX SYSTEM ONLINE — Logged in as {bot.user}")


async def create_welcome_gif(member):
    width, height = 1000, 400
    frames = []
    total_frames = 240  # 8 seconds @ 30 FPS

    # ---------- FONTS ----------
    font_title = ImageFont.truetype("Montserrat-Bold.ttf", 75)
    font_user = ImageFont.truetype("Montserrat-Regular.ttf", 44)
    font_small = ImageFont.truetype("Montserrat-Regular.ttf", 26)
    font_logo = ImageFont.truetype("Montserrat-Bold.ttf", 115)
    font_link = ImageFont.truetype("Montserrat-Regular.ttf", 22)

    # ---------- AVATAR ----------
    async with aiohttp.ClientSession() as session:
        async with session.get(member.display_avatar.url) as resp:
            avatar_bytes = await resp.read()

    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar = avatar.resize((130, 130))

    mask = Image.new("L", (130, 130), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 130, 130), fill=255)
    avatar.putalpha(mask)

    username = member.display_name
    member_count = f"Member #{member.guild.member_count}"
    join_time = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M UTC")

    words = ["WELCOME", "WILLKOMMEN", "BENVENUTO"]

    # ---------- PRE RENDER XO PATTERN ----------
    spacing = 60
    pattern_layer = Image.new("RGBA", (width * 2, height * 2), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(pattern_layer)

    for y in range(0, height * 2, spacing):
        for x in range(0, width * 2, spacing):
            p_draw.text((x, y), "X", font=font_small, fill=(255, 255, 255, 25))
            p_draw.text((x + 30, y + 30), "O", font=font_small, fill=(255, 255, 255, 25))

    # ---------- PRE RENDER LOGO ----------
    logo_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    logo_draw = ImageDraw.Draw(logo_layer)

    a_width = logo_draw.textlength("A", font=font_logo)
    s_width = logo_draw.textlength("S", font=font_logo)
    letter_spacing = -12

    as_total = a_width + s_width + letter_spacing
    as_x = width - as_total - 120
    as_y = 40

    logo_draw.text((as_x, as_y - 12), "A", font=font_logo, fill=(255, 255, 255))
    logo_draw.text((as_x + a_width + letter_spacing, as_y),
                   "S", font=font_logo, fill=(255, 255, 255))

    logo_glow = logo_layer.filter(ImageFilter.GaussianBlur(40))

    # ---------- FRAME LOOP ----------
    for frame in range(total_frames):

        # Animated gradient
        gradient = Image.linear_gradient("L").resize((width, height))
        gradient = gradient.rotate(frame * 0.4)

        base_dark = Image.new("RGBA", (width, height), (10, 0, 30, 255))
        purple_overlay = Image.new("RGBA", (width, height), (120, 0, 200, 200))
        bg = Image.composite(purple_overlay, base_dark, gradient)

        # Cinematic camera drift
        drift_x = math.sin(frame * 0.02) * 10
        drift_y = math.cos(frame * 0.015) * 6

        bg = bg.transform(
            bg.size,
            Image.AFFINE,
            (1, 0, drift_x, 0, 1, drift_y)
        )

        img = bg

        # Parallax XO
        offset_x = int(frame * 2)
        offset_y = int(frame * 1.2)

        cropped_pattern = pattern_layer.crop(
            (offset_x, offset_y,
             offset_x + width, offset_y + height)
        )

        img = Image.alpha_composite(img, cropped_pattern)

        draw = ImageDraw.Draw(img)

        # Glass UI panel
        panel = Image.new("RGBA", (750, 250), (255, 255, 255, 28))
        panel = panel.filter(ImageFilter.GaussianBlur(12))
        img.paste(panel, (40, 60), panel)

        # ---------- ULTRA TYPE ENGINE ----------
        word_index = (frame // 80) % len(words)
        word = words[word_index]
        cycle = frame % 80

        typed = int(len(word) * min(1, (cycle / 40) ** 1.6))
        text = word[:typed]

        if cycle > 50:
            text = word

        if cycle > 65:
            delete = int((cycle - 65) * 1.5)
            text = word[:max(0, len(word) - delete)]

        if (frame // 12) % 2 == 0:
            text += "│"

        # Pulse glow
        pulse = int(80 * abs(math.sin(frame * 0.15)))

        glow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow_layer)

        g_draw.text((85, 90),
                    text,
                    font=font_title,
                    fill=(255, 255, 255, 180 + pulse))

        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(12))
        img = Image.alpha_composite(img, glow_layer)

        draw = ImageDraw.Draw(img)
        draw.text((85, 90),
                  text,
                  font=font_title,
                  fill=(255, 255, 255))

        # Avatar shadow + reflection
        shadow = Image.new("RGBA", (160, 160), (0, 0, 0, 200))
        shadow = shadow.filter(ImageFilter.GaussianBlur(25))
        img.paste(shadow, (50, 200), shadow)
        img.paste(avatar, (60, 180), avatar)

        reflection = avatar.copy().transpose(Image.FLIP_TOP_BOTTOM)
        reflection = reflection.filter(ImageFilter.GaussianBlur(6))
        reflection.putalpha(80)
        img.paste(reflection, (60, 320), reflection)

        # User info
        draw.text((230, 190), username,
                  font=font_user, fill=(255, 255, 255))
        draw.text((230, 240), member_count,
                  font=font_small, fill=(230, 230, 255))
        draw.text((230, 270), join_time,
                  font=font_small, fill=(230, 230, 255))

        # Logo glow
        img = Image.alpha_composite(img, logo_glow)
        draw = ImageDraw.Draw(img)

        draw.text((as_x, as_y - 12), "A",
                  font=font_logo, fill=(255, 255, 255))
        draw.text((as_x + a_width + letter_spacing, as_y),
                  "S", font=font_logo, fill=(255, 255, 255))

        draw.text((as_x - 90, as_y + 130),
                  "https://discord.gg/arabsstudio",
                  font=font_link,
                  fill=(255, 255, 255, 170))

        frames.append(img)

    gif_path = f"welcome_{member.id}.gif"

    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=33,
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
        content=f"{member.mention}, Welcome to Arab’s Studio — MAX EXPERIENCE.",
        file=discord.File(gif)
    )

    os.remove(gif)


bot.run(TOKEN)
