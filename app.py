from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageSendMessage, TextSendMessage
import openai
from image_processing import get_random_image, add_text_to_image, upload_to_cloudinary

#======python的函數庫==========
import os
import traceback
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

user_states={}

def GPT_response(text):
    try:
         #呼叫 OpenAI API
        response = openai.ChatCompletion.create(
            model="ft:gpt-3.5-turbo-0125:personal::Ag2qoEbN",
            messages=[
                {"role": "system", "content": "你是一個講話有點刻薄但又不失禮貌的男同志，回答的目的是要讓長輩不要再煩了，要真切且搞笑。回答的語句要在10字內。"},
                {"role": "user", "content": text}
            ],
            temperature=0.5
        )
        print("OpenAI API 回應成功:", response)
        # 正確提取內容
        answer = response['choices'][0]['message']['content'].strip()
        return answer
    
    except Exception as e:
        print("Error in GPT_response:", e)
        return "抱歉，目前無法提供回應，請稍後再試。"

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    app.logger.info("handle_message called")
    user_id = event.source.user_id
    user_message = event.message.text.strip().lower()
    app.logger.info(f"user_id: {user_id}, user_message: {user_message}")

    try:

        if user_id not in user_states:
            response_text = "沒問題！我來幫你解決。請先確認想要的圖片類型！（慈祥款/基本款/佳節款/風景款/溫馨款）"
            user_states[user_id] = "waiting_for_category"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))
            return
        
        if user_states[user_id] == "waiting_for_category":
            if user_message in ["buddha", "flowers", "hands", "landscape", "new year"]:
                # 調用 GPT 生成回應
                gpt_response = GPT_response(user_message)
        
                #生成圖片
                image = get_random_image(user_message)
                image = add_text_to_image(image, gpt_response)
                image_url = upload_to_cloudinary(image)

                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))
                del user_states[user_id]
                return
        else:
            response_text = "請輸入有效的圖片類型！"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))
            return
    except Exception as e:
        app.logger.error(f"Error in handle_message: {traceback.format_exc()}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='發生錯誤，請稍後再試！')
        )
        return

# 根目錄測試路徑
@app.route("/", methods=['GET'])
def index():
    return "LINE Bot is running successfully!", 200

# 啟動 Flask 應用
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
