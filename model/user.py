from .database import DataBase

class User:
    def __init__(self, event):
        self.event = event
        result = self.readdb()
        if len(result) == 0:
            # user not found
            return 
        
        # [{'user_id': 'U927fc01c15134a9643381b557f831937', 'user_name': 'sean', 'gender': '1', 'age': 21, 'height_': 173.0, 'weight_': 65.0, 'exercise_freq': 2, 'calories': 250.0, 'diab_type': 1}]
        self.user_id = self.event.source.user_id
        self.user_name = result[0]['user_name']
        if result[0]['gender'] == '1':
            self.gender = "男"
        elif result[0]['gender'] == '2':
            self.gender = "女"
        self.age = result[0]['age']
        self.height = result[0]['height_']
        self.weight = result[0]['weight_']
        #將運動頻率的數值轉換成文字顯示
        if result[0]['exercise_freq'] == 0:
            self.exercise_freq = "無運動"
        elif result[0]['exercise_freq'] == 2:
            self.exercise_freq = "1~3次"
        elif result[0]['exercise_freq'] == 4:
            self.exercise_freq = "4~5次"
        elif result[0]['exercise_freq'] == 6:
            self.exercise_freq = "6~7次"
        elif result[0]['exercise_freq'] == 8:
            self.exercise_freq = "7次以上"
        self.calories = result[0]['calories']
        self.diab_type = result[0]['diab_type']
        #此欄位用來在顯示個人資訊時，使用者可以知道此數字代表的意義
        if result[0]['diab_type'] == 0:
            self.diab_text = "否(正常飲食)"
        elif result[0]['diab_type'] == 1:
            self.diab_text = "一型糖尿病患者"
        elif result[0]['diab_type'] == 2:
            self.diab_text = "二型糖尿病患者"

    def readdb(self):
        db = DataBase()
        sql = f"SELECT * FROM basic_info WHERE user_id = '{self.event.source.user_id}';"
        result = db.read(sql)
        return result
