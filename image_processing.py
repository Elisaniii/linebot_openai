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
    #font = ImageFont.truetype(font_path, font_size)
    image_width, image_height = image.size

    try:
        # 根據圖片大小動態調整字體大小（取圖片高度的 1/10 作為字體大小）
        font_size = max(image_height // 10, 20)  # 字體大小至少為 20
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
        # 計算文字大小和位置
        text_size = draw.textsize(text, font=font)
        text_position = ((image_width - text_size[0]) / 2, (image_height - text_size[1]) / 2)
        
    #text_bbox = draw.textbbox((0, 0), text, font=font)
    #text_width = text_bbox[2] - text_bbox[0]
    #text_height = text_bbox[3] - text_bbox[1]
    #image_width, image_height = image.size
    #text_x = (image_width - text_width) / 2
    #text_y = image_height - text_height - 100

        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text(
                        (text_position[0] + dx, text_position[1] + dy),
                        text,
                        font=font,
                        fill=outline_color
                    )

        draw.text((text_x, text_y), text, font=font, fill=text_fill)
    except Exception as e:
        print("Error in add_text_to_image:", e)
        raise e
    return image

# 上傳圖片到 Cloudinary
def upload_to_cloudinary(image):
    try:
        image_buffer = BytesIO()
        image.save(image_buffer, format="PNG")
        image_buffer.seek(0)

        upload_url = "https://api.cloudinary.com/v1_1/djbamsijq/image/upload"
        payload = {"upload_preset": "linebot_upload"}
        files = {"file": image_buffer}
        
        response = requests.post(upload_url, data=payload, files=files)
        response.raise_for_status()  # 確保請求成功
        
        image_url = response.json().get("secure_url")
        print("Uploaded Image URL:", image_url)
        return image_url

    except requests.exceptions.RequestException as e:
        print("Error uploading image to Cloudinary:", e)
        raise e
