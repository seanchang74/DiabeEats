import os,sys
from .food_recommendation import recommendation
from dotenv import load_dotenv
load_dotenv() #load .env file content

CURRENT_DIR= os.path.split(os.path.abspath(__file__))[0]
config_path = CURRENT_DIR.rsplit('\\',1)[0]
sys.path.append(config_path)
from model.message_queue import MessageQueue, RequestTimout

from linebot import LineBotApi
from linebot.models import TextSendMessage
line_bot_api = LineBotApi(os.environ['channel_access_token'])

class Recommendation:
    '''start food recommendation process'''
    def __init__(self, event, user_id, type, calories):
        self.event = event
        self.user_id = user_id
        self.diab_type = type
        self.calories = calories

        try:
            self.recommend()
        except RequestTimout:
            self.reply('輸入時間過久，請點選下方主選單重新開始!')

    def recommend(self):
        '''Ask about requirements'''
        vegen_ask = self.ask('餐點是否有素食需求?如有請回覆茹素類別(例如五辛素、全素或蛋奶素)，若無請回答否')
        food = self.ask('餐點希望包含什麼?')
        allergic = self.ask('餐點不希望包含什麼?')
        calories_per_meal = self.calories / 3

        if self.diab_type == 1:
            glucose = self.ask_number('請提供目前血糖值方便我調整菜單')

            if vegen_ask in ['否', '無', '葷']:
                msg = f'好的，將推薦適合血糖值在{glucose}時，每餐約{round(calories_per_meal,2)}大卡，包含{food}且不包含{allergic}的套餐\n\n如果資訊正確請輸入1 有誤請輸入其他數字'
            else:
                msg = f'好的，將推薦適合血糖值在{glucose}時，每餐約{round(calories_per_meal,2)}大卡，包含{food}且不包含{allergic}的{vegen_ask}套餐\n\n如果資訊正確請輸入1 有誤請輸入其他數字'
        
        elif self.diab_type == 2 or self.diab_type == 0:
            glucose = None
            
            if vegen_ask in ['否', '無', '葷']:
                msg = f'好的，將根據您的基礎代謝率，推薦每餐約{round(calories_per_meal,2)}大卡，包含{food}且不包含{allergic}的套餐\n\n如果資訊正確請輸入1 有誤請輸入其他數字'
            else:
                msg = f'好的，將根據您的基礎代謝率，推薦每餐約{round(calories_per_meal,2)}大卡，包含{food}且不包含{allergic}的{vegen_ask}套餐\n\n如果資訊正確請輸入1 有誤請輸入其他數字'
        
        good = 1
        answer = self.ask_number(msg)
        if answer == 1:
            while True:
                recommend = recommendation(glucose,vegen_ask,calories_per_meal,allergic,food,self.diab_type)
                if recommend in ["無",'找不到']:
                    good = 0
                    break
                else:
                    recommend += "\n\n如果喜歡請按1，需要重新推薦請輸入其他數字"
                    choice = self.ask_number(recommend)

                    if choice == 1:
                        break
                    else:
                        continue
            
            if good == 0:
                self.reply("很抱歉，找不到符合需求的商品\n麻煩您點選下方主選單重新調整餐點條件")
            elif good == 1:
                self.reply("很感謝您喜歡我們的推薦，祝你用餐愉快")
        else:
            self.reply("很抱歉剛才的資料有誤，請重新點選下方主選單重新輸入資料!")

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

    def reply(self, *msg):
        '''Reply words to user'''
        line_bot_api.reply_message(
            self.event.reply_token,
            messages=[TextSendMessage(text=message)
                    for message in msg]
        )
