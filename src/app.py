import os
import json
import re
import logging
from flask import Flask, request, abort, render_template, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, 
    PostbackEvent, BubbleContainer, BoxComponent, TextComponent, 
    ButtonComponent, PostbackAction
)
from google import genai
from google.genai import types

# ===== 日誌設定 =====
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ===== 常數定義 =====
class Config:
    LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
    LIFF_ID = os.environ.get('LIFF_ID')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()

# 初始化 LINE Bot
line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)

# 初始化 AI
client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None

# ===== AI 出題功能 =====
def generate_quiz(decade: str, category: str) -> dict:
    """使用 Gemini AI 動態生成 JSON 格式的題目"""
    if not client:
        logger.error("未設定 GEMINI_API_KEY")
        return None

    prompt = (
        f"任務：請幫我出一道「{decade}」的「{category}」猜謎題目，適合 60 歲以上長輩玩。\n"
        "規則：\n"
        "1. 必須有四個選項 (A, B, C, D)。\n"
        "2. 嚴格輸出 JSON 格式，不要包含 ```json 等 markdown 標記。\n"
        "3. JSON 結構如下：\n"
        "{\n"
        '  "question": "題目內容",\n'
        '  "options": ["選項A", "選項B", "選項C", "選項D"],\n'
        '  "answer_index": 2, \n'
        '  "explanation": "答對後的恭喜與補充(請帶有過年喜氣與長輩友善語氣)"\n'
        "}\n"
        "注意：answer_index 是正確答案在 options 陣列中的索引 (0~3)。"
    )

    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7)
        )
        text = response.text.strip()
        clean_json = re.sub(r'```json|```', '', text).strip()
        return json.loads(clean_json)
    except Exception as e:
        logger.error(f"❌ AI 出題失敗: {e}")
        return None

# ===== Flex Message 建構 =====
def get_quiz_flex(quiz_data: dict) -> FlexSendMessage:
    """建立紅包風格的題目卡"""
    
    # 建立四個選項按鈕
    option_buttons = []
    for idx, opt_text in enumerate(quiz_data["options"]):
        is_correct = "1" if idx == quiz_data["answer_index"] else "0"
        # 將資料塞進 postback data
        postback_data = f"ans&c={is_correct}&exp={quiz_data['explanation']}"
        
        btn = ButtonComponent(
            style='primary',
            height='sm',
            color='#FFC107', # 金色
            action=PostbackAction(label=opt_text, data=postback_data, displayText=opt_text)
        )
        # 用 Box 包裝加上 margin
        option_buttons.append(BoxComponent(layout='vertical', margin='sm', contents=[btn]))

    flex_content = BubbleContainer(
        styles={
            'header': {'backgroundColor': '#D32F2F'}, # 喜氣紅
            'body': {'backgroundColor': '#ffffff'}
        },
        header=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text="🏮 財神爺金頭腦 🏮", weight='bold', size='xl', color='#ffffff', align='center')
            ]
        ),
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text=quiz_data["question"], wrap=True, weight='bold', size='md', margin='md', color='#333333'),
                BoxComponent(layout='vertical', margin='xl', spacing='sm', contents=option_buttons)
            ]
        )
    )
    return FlexSendMessage(alt_text="財神爺出題囉！", contents=flex_content)

# ===== LINE Bot 路由與事件 =====
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    text = event.message.text.strip()

    # 1. 攔截來自 LIFF 的隱藏指令
    if text.startswith("#出題"):
        parts = text.split(" ")
        if len(parts) >= 3:
            decade = parts[1]
            category = parts[2]
            
            # 先回覆等待訊息 (消耗 1 則訊息)
            line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=f"🎲 財神爺正在為您準備【{decade} {category}】的題目，請稍候...")
            )
            
            # 呼叫 AI 出題並推送題目卡 (消耗 1 則訊息)
            quiz = generate_quiz(decade, category)
            if quiz:
                flex_msg = get_quiz_flex(quiz)
                line_bot_api.push_message(event.source.user_id, flex_msg)
            else:
                line_bot_api.push_message(event.source.user_id, TextSendMessage(text="哎呀！財神爺打瞌睡了，請再試一次！"))
        return

    # 2. 常規指令引導
    if text in ["開始", "求財神"]:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="🧧 歡迎來到財神爺的金頭腦！\n👉 請點擊下方選單的「開始挑戰」打開設定網頁。")
        )

@handler.add(PostbackEvent)
def handle_postback(event: PostbackEvent):
    data = event.postback.data
    
    if data.startswith("ans&"):
        # 解析 postback (格式: ans&c=1&exp=解釋文字)
        import urllib.parse
        parsed = urllib.parse.parse_qs(data.replace("ans&", ""))
        is_correct = parsed.get('c', ['0'])[0]
        explanation = parsed.get('exp', [''])[0]

        if is_correct == "1":
            reply_text = f"🎉 恭喜老爺/夫人，答對啦！\n\n💡 {explanation}\n\n👉 點擊下方圖文選單再玩一局！"
        else:
            reply_text = f"❌ 哎呀，差一點點！\n\n💡 {explanation}\n\n👉 沒關係，點擊圖文選單再挑戰一次！"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# ===== LIFF 與健康檢查 =====
@app.route("/health")
def health_check():
    return jsonify({"status": "ok", "ai_enabled": client is not None})

@app.route("/liff")
def liff_page():
    return render_template('liff.html', liff_id=Config.LIFF_ID)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))