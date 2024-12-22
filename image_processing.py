import json
import random
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# 讀取圖片分類 JSON 文件
with open("dealwcare_pic.json", "r") as file:
    image_urls = json.load(file)

# 隨機選擇圖片
def get_random_image(category):
    if category not in image_urls:
        raise ValueError("無效的圖片類型")
    selected_image_url = random.choice(image_urls[category])
    response = requests.get(selected_image_url)
    return Image.open(BytesIO(response.content)).convert("RGB")

# 添加文字到圖片
def add_text_to_image(image, text, font_path="BiauKai.ttf", text_fill="blue", outline_color="yellow", outline_width=3):
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size

    try:
        # 根據圖片大小動態調整字體大小（取圖片高度的 1/10 作為字體大小）
        font_size = max(image_height // 10, 20)  # 字體大小至少為 20
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
        
        # 自動換行
        def wrap_text(text, font, max_width):
            """將文字根據最大寬度自動換行"""
            lines = []
            words = text.split(' ')
            line = ''
            for word in words:
                test_line = f"{line} {word}".strip()
                test_width = draw.textlength(test_line, font=font)
                if test_width <= max_width:
                    line = test_line
                else:
                    lines.append(line)
                    line = word
            lines.append(line)
            return lines

        # 將文字換行
        wrapped_text = wrap_text(text, font, image_width * 0.9)
        text_height = draw.textbbox((0, 0), "A", font=font)[3]  # 單行文字高度
        total_text_height = len(wrapped_text) * text_height

        # 計算整體文字的垂直起始位置，確保居中
        current_y = image_height * 0.8
        
        for line in wrapped_text:
            text_width = draw.textlength(line, font=font)
            text_x = (image_width - text_width) / 2

            # 繪製文字邊框
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text(
                            (text_x + dx, current_y + dy),
                            line,
                            font=font,
                            fill=outline_color
                        )

            # 繪製主要文字
            draw.text((text_x, current_y), line, font=font, fill=text_fill)
            current_y += text_height  # 移動到下一行位置

    except Exception as e:
        print("Error in add_text_to_image:", e)
        raise e

    return image

# 上傳圖片到 Cloudinary
def upload_to_cloudinary(image):
    try:
        with BytesIO() as image_buffer:
            image.save(image_buffer, format="PNG", optimize=True)
            image_buffer.seek(0)

            upload_url = "https://api.cloudinary.com/v1_1/djbamsijq/image/upload"
            payload = {"upload_preset": "linebot_upload"}
            files = {"file": image_buffer}
            
            response = requests.post(upload_url, data=payload, files=files)
            response.raise_for_status()
            
            image_url = response.json().get("secure_url")
            print("Uploaded Image URL:", image_url)
            return image_url

    except requests.exceptions.RequestException as e:
        print("Error uploading image to Cloudinary:", e)
        raise e
