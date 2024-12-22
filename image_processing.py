import json
import random
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

IMAGE_WIDTH = 800
IMAGE_HEIGHT = 800
PADDING = 20

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
def add_text_to_image(image, text, font_path="BiauKai.ttf", font_size=60, text_fill="blue", outline_color="yellow", outline_width=3, padding=20):
    try:
        draw = ImageDraw.Draw(image)

        # 初始化字體
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Warning: 字體檔案 '{font_path}' 無法找到，使用預設字體。")
            font = ImageFont.load_default()
        
        # 自動換行
        def wrap_text(text, font, max_width):
            """將文字根據最大寬度自動換行"""
            lines = []
            current_line = ''
            
            for char in text:
                test_line = current_line + char
                test_width = draw.textbbox((0, 0), test_line, font=font)[2] - draw.textbbox((0, 0), test_line, font=font)[0]
                
                if test_width <= max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = char  # 新的一行從當前字開始
            
            if current_line:
                lines.append(current_line)  # 添加最後一行
            
            return lines

        # 設定最大寬度
        max_text_width = IMAGE_WIDTH - (2 * PADDING)
        
        # 自動換行
        wrapped_text = wrap_text(text, font, max_text_width)
        text_height = draw.textbbox((0, 0), "A", font=font)[3] - draw.textbbox((0, 0), "A", font=font)[1]
        total_text_height = len(wrapped_text) * text_height + (len(wrapped_text) - 1) * 5

        # 垂直居中
        current_y = (IMAGE_HEIGHT - total_text_height) / 2
        
        for line in wrapped_text:
            text_width = draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0]
            #text_x = padding
            text_x = max(PADDING, (IMAGE_WIDTH - text_width) / 2) 
            text_x = min(IMAGE_WIDTH - text_width - PADDING, text_x)

            # 如果文字總寬度小於最大寬度，將其居中顯示（但仍考慮 padding）
            #if text_width < max_text_width:
            #    text_x = (image_width - text_width) / 2
            #    text_x = max(padding, text_x)  # 確保不低於 padding
            #    text_x = min(image_width - text_width - padding, text_x)  # 確保不超過右側 padding

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
            current_y += text_height+5  # 移動到下一行位置

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
