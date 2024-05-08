import os,sys
from datetime import datetime,timezone,timedelta
from dotenv import load_dotenv
load_dotenv() #load .env file content

CURRENT_DIR= os.path.split(os.path.abspath(__file__))[0]
config_path = CURRENT_DIR.rsplit('\\',1)[0]
sys.path.append(config_path)
from model.message_queue import MessageQueue, RequestTimout
from model.database import *

from linebot import LineBotApi
from linebot.models import TextSendMessage
line_bot_api = LineBotApi(os.environ['channel_access_token'])

class ReportGlucose:
    '''start glucose report process'''
    def __init__(self, event, user_id):
        self.event = event
        self.user_id = user_id
        try:
            self.report()
        except RequestTimout:
            self.reply('輸入時間過久，請點選下方主選單重新開始！')
    
    def report(self):
        '''Ask about requirements'''
        glucose = self.ask_number('請輸入您目前的血糖值')
        result = self.writedb(glucose)
        if result == "ok":
            self.reply("感謝您的回報，可以透過下方生成報告的功能檢視自己的血糖變化趨勢")
        elif result == "error":
            self.reply("不好意思，寫入資料庫時似乎發生問題，麻煩再試一次")

    def ask(self, *msg):
        '''Ask a question to current user'''
        self.reply(*msg)
        self.event = MessageQueue.request(self.user_id)
        return self.event.message.text.strip()
    
    def ask_number(self, *msg):
        '''Ask a number, if not number, ask again'''
        try:
            content = self.ask(*msg)
            return int(content)
        except ValueError:
            return self.ask_number('請輸入數字', *msg)
        
    def writedb(self, value):
        dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
        dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換時區 -> 東八區
        insertime = dt2.strftime("%Y-%m-%d %H:%M:%S")
        db = DataBase()
        # INSERT INTO diabetes_info (user_id, insertime, glucose) VALUES ('U927fc01c15134a9643381b557f831937', '2023-08-01 10:47:35', 100)
        sql = f"INSERT INTO diabetes_info (user_id, insertime, glucose) VALUES ('{self.user_id}', '{insertime}', {value});"
        result = db.create(sql)
        return result
    
    def reply(self, *msg):
        '''Reply words to user'''
        line_bot_api.reply_message(
            self.event.reply_token,
            messages=[TextSendMessage(text=message)
                    for message in msg]
        )
