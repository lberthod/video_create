from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor
import numpy as np

# Configuration des paramètres globaux
FONT_TITLE = "arialbd.ttf"
FONT_TEXT = "arialbd.ttf"
FONT_ANSWER = "arialbd.ttf"
START_COLOR = "#ffffff"
END_COLOR = "#e0e0e0"
BORDER_COLOR = "#000000"
BORDER_WIDTH = 10
CLIGNOTEMENT_DUREE = 0.3  # Durée de chaque clignotement
INCREMENT_SIZE_PERCENT = [10, 20, 30]  # Pourcentage d'agrandissement pour chaque clignotement

def create_gradient_background(width, height, start_color=START_COLOR, end_color=END_COLOR, direction='vertical'):
    """Crée un fond dégradé."""
    base = Image.new('RGB', (width, height), start_color)
    top = Image.new('RGB', (width, height), end_color)
    mask = Image.new('L', (width, height))
    
    if direction == 'vertical':
        for y in range(height):
            ratio = y / height
            mask.putpixel((0, y), int(255 * ratio))
    else:
        for x in range(width):
            ratio = x / width
            mask.putpixel((x, 0), int(255 * ratio))
    
    mask = mask.resize(base.size)
    gradient = Image.composite(base, top, mask)
    return gradient

def wrap_text(text, font, max_width):
    """Coupe le texte en plusieurs lignes si nécessaire."""
    lines = []
    words = text.split()
    current_line = words[0]

    for word in words[1:]:
        test_line = f"{current_line} {word}"
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines

def draw_text_with_box(draw, text_lines, font, x, y, width, padding=20, box_fill=(255, 255, 255, 180)):
    """Dessine du texte avec une boîte semi-transparente derrière."""
    text_height = sum(draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in text_lines) + (len(text_lines) - 1) * 10
    box_height = text_height + len(text_lines) * 10 + padding * 2
    box_position = (x - padding, y - padding)
    box_end_position = (x + width + padding, y + box_height - padding)

    draw.rectangle([box_position, box_end_position], fill=box_fill)

    y_text = y
    for line in text_lines:
        text_width = draw.textbbox((0, 0), line, font=font)[2]
        draw.text(((x + width - text_width) / 2, y_text), line, font=font, fill=(0, 0, 0))
        y_text += draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] + 10

    return y_text

def create_text_image(title, question, answer, img_width=1080, img_height=1920, font_size=48, title_size=60, answer_size=48, img_path="image.png", show_answer=False, space_after_title=30, space_after_text=30, border_color=BORDER_COLOR, border_width=BORDER_WIDTH):
    """Crée une image avec un titre, du texte et une réponse avec un fond dégradé et une boîte semi-transparente."""
    gradient_bg = create_gradient_background(img_width, img_height)

    font_title = ImageFont.truetype(FONT_TITLE, title_size)
    font_text = ImageFont.truetype(FONT_TEXT, font_size)
    font_answer = ImageFont.truetype(FONT_ANSWER, answer_size)

    draw = ImageDraw.Draw(gradient_bg)

    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    title_position = ((img_width - title_width) / 2, 50)
    draw.text(title_position, title, font=font_title, fill=(0, 0, 0))

    y_position = title_position[1] + title_bbox[3] + space_after_title

    wrapped_lines = wrap_text(question, font_text, img_width - 100)
    y_position = draw_text_with_box(draw, wrapped_lines, font_text, 50, y_position, img_width - 100)

    y_position += space_after_text

    answer_bbox = draw.textbbox((0, 0), answer, font=font_answer)
    answer_width = answer_bbox[2] - answer_bbox[0]
    answer_position = ((img_width - answer_width) / 2, img_height - answer_bbox[3] - 50)
    if show_answer:
        draw.text(answer_position, answer, font=font_answer, fill=(0, 0, 0))

    bottom_image = Image.open(img_path)
    aspect_ratio = bottom_image.width / bottom_image.height
    new_width = img_width - 100
    new_height = int(new_width / aspect_ratio)

    max_image_height = answer_position[1] - y_position - 50
    if new_height > max_image_height:
        new_height = max_image_height
        new_width = int(new_height * aspect_ratio)

    # Calculer la marge de 10% de la hauteur de l'image
    image_margin = int(new_height * 0.1)

    bottom_image = bottom_image.resize((new_width, new_height))

    image_position_x = (img_width - bottom_image.width) // 2
    image_position_y = y_position + image_margin  # Ajouter la marge ici

    gradient_bg.paste(bottom_image, (image_position_x, image_position_y))

    border_color_rgb = ImageColor.getrgb(border_color)
    gradient_bg = ImageOps.expand(gradient_bg, border=border_width, fill=border_color_rgb)

    return gradient_bg

def create_video_from_text_with_title_image_audio(text_file, output_video, title, img_paths, audio_path, answer_text, border_color=BORDER_COLOR, border_width=BORDER_WIDTH, fps=24):
    """Crée une vidéo avec des animations de texte, un titre, une image, et un fond dégradé."""
    with open(text_file, "r", encoding="utf-8") as file:
        text = file.read()

    words = text.split()

    image_clips = []
    current_line = ""
    lines = []
    image_index = 0
    img_change_interval = 6

    font_text = ImageFont.truetype(FONT_TEXT, 48)
    duration_per_word = 0.5

    for i, word in enumerate(words):
        test_line = f"{current_line} {word}".strip()
        text_bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), test_line, font=font_text)
        text_width = text_bbox[2] - text_bbox[0]

        if text_width <= 1080 - 100:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

        if i % img_change_interval == 0:
            image_index = (image_index + 1) % len(img_paths)

        temp_lines = lines + [current_line]
        img = create_text_image(title, ' '.join(temp_lines), answer_text, img_path=img_paths[image_index], border_color=border_color, border_width=border_width)

        img_np = np.array(img)
        clip = ImageClip(img_np).set_duration(duration_per_word)

        image_clips.append(clip)

    if current_line:
        lines.append(current_line)
        # Créer un clip de pause de 2 secondes avant de montrer la réponse
        pause_duration = 2
        last_image = img_np  # Utiliser la dernière image générée
        pause_clip = ImageClip(last_image).set_duration(pause_duration)

        img = create_text_image(title, ' '.join(lines), answer_text, img_width=1080, img_height=1920, img_path=img_paths[image_index], show_answer=True, border_color=border_color, border_width=border_width)
        img_np = np.array(img)
        answer_clip = ImageClip(img_np).set_duration(duration_per_word + 3)

        image_clips.append(pause_clip)
        image_clips.append(answer_clip)

        # Ajout de l'effet de clignotement pour l'answer_text avec agrandissement progressif
        for increment in INCREMENT_SIZE_PERCENT:
            enlarged_answer_size = int(48 + (48 * increment / 100))
            img_large = create_text_image(title, ' '.join(lines), answer_text, img_width=1080, img_height=1920, font_size=48, title_size=60, answer_size=enlarged_answer_size, img_path=img_paths[image_index], show_answer=True, space_after_title=30, space_after_text=30, border_color=border_color, border_width=border_width)
            img_large_np = np.array(img_large)
            clip_large = ImageClip(img_large_np).set_duration(CLIGNOTEMENT_DUREE)
            image_clips.append(clip_large)

    video = concatenate_videoclips(image_clips, method="compose")

    audio = AudioFileClip(audio_path).subclip(0, sum(clip.duration for clip in image_clips))
    video = video.set_audio(audio)

    video.write_videofile(output_video, fps=fps)

# Utilisation de la fonction
create_video_from_text_with_title_image_audio(
    text_file="example.txt",
    output_video="output_video.mp4",
    title="Qui suis-je ?",
    img_paths=["img1.png", "img2.png", "img3.png", "img4.png"],
    audio_path="audio.mp3",
    answer_text="La Russie",
    border_color=BORDER_COLOR,
    border_width=BORDER_WIDTH,
    fps=24
)
