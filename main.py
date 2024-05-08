import os, requests, traceback, flask
from dotenv import load_dotenv
from flask import Flask, request, abort, render_template
from model.user import User
from model.message_queue import MessageQueue
from view.process_form import ProcessForm
from view.dashboard import get_id
from controller.recommendation import Recommendation
from controller.report_glucose import ReportGlucose

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from linebot.exceptions import InvalidSignatureError

app = flask.current_app
load_dotenv() #load .env file content

# LINE Bot token
line_bot_api = LineBotApi(os.environ['channel_access_token'])
handler = WebhookHandler(os.environ['channel_secret'])
liffid = os.environ['liffid']

def callback(request):
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        return "Invalid signature", 403
    except Exception as e:
        print("Got error in callback: {}".format(e))
        print(traceback.format_exc())
        return "Error", 404
    print("return OK")
    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg=event.message.text
    try:
        # 尚未註冊的用戶
        user = User(event)
        #檢查使用者是否註冊
        print(user.user_name)
    except AttributeError:
        #尚未註冊的使用者
        print("user not found")
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
    
    if MessageQueue.handle(event, user.user_id):
        return

    elif msg == "請推薦食品給我":
        Recommendation(event,user.user_id,user.diab_type, user.calories)
    elif msg == "我要記錄血糖":
        ReportGlucose(event, user.user_id)
    elif msg == "我要生成報表":
        domain_url = "https://asia-east1-wits-finalproject.cloudfunctions.net/DiabeEats"
        chart_url = f"{domain_url}/dashboard/{user.user_id}" #替換user_id
        charts_data,max_glucose,min_glucose,avg_glucose,lage_glucose,tir_glucose = get_id(user.user_id)
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
    
    else:
        response = [f"{line_bot_api.get_profile(event.source.user_id).display_name} 您好！",
                    "我是專為糖尿病患者設計的智能飲食建議機器人","需要什麼功能都可以透過下方圖文選單來啟動，謝謝！"]
        line_bot_api.reply_message(
                reply_token=event.reply_token,
                messages=[TextSendMessage(text=message)
                        for message in response]
                )

@app.route('/signup')
def signup():
    return render_template('signup.html', liffid = liffid)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    charts_data,max_glucose,min_glucose,avg_glucose,lage_glucose,tir_glucose = get_id(user_id)
    return render_template('index.html',charts_data=charts_data,max_glucose=max_glucose,min_glucose=min_glucose,avg_glucose=avg_glucose,lage_glucose=lage_glucose,tir_glucose=tir_glucose)
