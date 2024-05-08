import os, requests
from dotenv import load_dotenv
from flask import Flask, request, abort, render_template
from model.user import User
from model.message_queue import MessageQueue
from view.dashboard import get_id
from view.process_form import ProcessForm
from controller.recommendation import Recommendation
from controller.report_glucose import ReportGlucose

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)
load_dotenv() #load .env file content

# LINE Bot token
line_bot_api = LineBotApi(os.environ['channel_access_token'])
handler = WebhookHandler(os.environ['channel_secret'])
liffid = os.environ['liffid']
# 到時候會拿掉
richmenu_a = os.environ['richmenu_a']
richmenu_b = os.environ['richmenu_b']

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
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@app.route('/signup')
def signup():
    return render_template('signup.html', liffid = liffid)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    morning_glucose_chart,noon_glucose_chart,evening_glucose_chart,max_glucose,min_glucose,avg_glucose,lage_glucose,tir_glucose = get_id(user_id)
    return render_template('index.html',morning_glucose_chart=morning_glucose_chart,noon_glucose_chart=noon_glucose_chart
                           ,evening_glucose_chart=evening_glucose_chart,max_glucose=max_glucose,min_glucose=min_glucose,avg_glucose=avg_glucose,lage_glucose=lage_glucose,tir_glucose=tir_glucose)   

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 尚未註冊的用戶
    user = User(event)
    msg=event.message.text
    try:
        #檢查使用者是否註冊
        print(user.user_id)
    except AttributeError:
        #尚未註冊的使用者
        if msg[:3] == "###" and len(msg) > 3:
            return_msg = ProcessForm(event.source.user_id, msg)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=return_msg)
            )
        else:
            response = [f"{line_bot_api.get_profile(event.source.user_id).display_name} 您好！",
                        "我們發現您尚未註冊本公司的服務，請麻煩填寫註冊表單來開啟服務功能","如有任何想要先了解的資訊麻煩與客服聯繫，謝謝！"]
            line_bot_api.reply_message(
                    reply_token=event.reply_token,
                    messages=[TextSendMessage(text=message)
                            for message in response]
                    )
        return
    
    # 已經註冊的使用者才能使用下列功能
    if MessageQueue.handle(event,user.user_id):
        return
    
    # 測試用，到時候會刪除
    # if msg[:3] == "###" and len(msg) > 3:
    #     return_msg = ProcessForm("104", msg, event.source.user_id) # 需要調整
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text=return_msg)
    #     )
    if msg == "請推薦食品給我":
        Recommendation(event,user.user_id,user.diab_type, user.calories)
    elif msg == "我要記錄血糖":
        ReportGlucose(event,user.user_id)
    elif msg == "我要生成報表":
        domain_url = "https://asia-east1-wits-finalproject.cloudfunctions.net/DiabeEats"
        chart_url = f"{domain_url}/dashboard/{user.user_id}" #替換user_id
        morning_glucose_chart,noon_glucose_chart,evening_glucose_chart,max_glucose,min_glucose,avg_glucose,lage_glucose,tir_glucose = get_id(user.user_id)
        if max_glucose != None:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="這是您的血糖報表：\n"+ chart_url)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="您尚未輸入資料，請輸入資料後再使用生成報表功能")
            )
    elif msg == "查看個人資訊":
        line_bot_api.reply_message(
            reply_token=event.reply_token,
            messages=FlexSendMessage(
                alt_text="user_info",
                contents={
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "text": "User Info",
                            "weight": "bold",
                            "color": "#1DB446",
                            "size": "sm"
                        },
                        {
                            "type": "text",
                            "text": user.user_name,
                            "weight": "bold",
                            "size": "xxl",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "size": "xs",
                            "color": "#aaaaaa",
                            "wrap": True,
                            "text": user.user_id
                        },
                        {
                            "type": "separator",
                            "margin": "xxl"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "xxl",
                            "spacing": "sm",
                            "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "性別",
                                    "size": "sm",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": user.gender,
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "size": "sm",
                                    "color": "#555555",
                                    "flex": 0,
                                    "text": "年齡"
                                },
                                {
                                    "type": "text",
                                    "text": f"{user.age}歲",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "身高",
                                    "size": "sm",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": f"{round(user.height)}公分",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "體重",
                                    "size": "sm",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": f"{round(user.weight)}公斤",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                                ]
                            },
                            {
                                "type": "separator",
                                "margin": "xxl"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "每周的運動次數",
                                    "size": "sm",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": f"{user.exercise_freq}",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "每日建議熱量",
                                    "size": "sm",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": f"{round(user.calories)}大卡",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "是否為糖尿病患者",
                                    "size": "sm",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": user.diab_text,
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                                ]
                            }
                            ]
                        }
                        ]
                    },
                    "styles": {
                        "footer": {
                        "separator": True
                        }
                    }
                    }
            )
        )
    elif msg == "切換richmenu a":
        headers = {'Authorization':f"Bearer {os.environ['channel_access_token']}"}
        ### 註冊頁面
        req = requests.request('POST', f'https://api.line.me/v2/bot/user/{user.user_id}/richmenu/{richmenu_a}', headers=headers)
        print(req.text)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="切換成功")
        )
    elif msg == "切換richmenu b":
        headers = {'Authorization':f"Bearer {os.environ['channel_access_token']}"}
        ### 完整功能頁面
        req = requests.request('POST', f'https://api.line.me/v2/bot/user/{user.user_id}/richmenu/{richmenu_b}', headers=headers)
        print(req.text)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="切換成功")
        )
    else:
        response = [f"{line_bot_api.get_profile(user.user_id).display_name} 您好!",
                    "我是專為糖尿病患者設計的智能飲食建議機器人","需要什麼功能都可以透過下方圖文選單來啟動，謝謝！"]
        line_bot_api.reply_message(
                reply_token=event.reply_token,
                messages=[TextSendMessage(text=message)
                        for message in response]
                )

if __name__ == "__main__":
    app.run()