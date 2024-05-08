import os,sys, requests
from dotenv import load_dotenv
load_dotenv()

CURRENT_DIR= os.path.split(os.path.abspath(__file__))[0]
config_path = CURRENT_DIR.rsplit('\\',1)[0]

sys.path.append(config_path)
from model.database import DataBase

def ProcessForm(user_id, user_data):
    try:
        flist = user_data[3:].split('/')
        cname = flist[0]
        cbirth = flist[1]
        cgender = flist[2]
        cheight = flist[3]
        cweight = flist[4]
        cexercise = flist[5]
        cdietary = flist[6]
        
        # 將資料塞入DB
        result = writedb(user_id, cname, cbirth, cgender, cheight, cweight, cexercise, cdietary)
        if result == "ok":
            # 回傳使用者的資料給使用者確認
            # (性別/是否為糖尿病患者)這兩個欄位 需要將數字轉換成文字再回傳給使用者
            text1 = "已成功註冊，資料如下:"
            text1 +="\n姓名: " + cname
            text1 +="\n年齡: " + f"{cbirth}歲"
            if cgender == '1':
                gender = "男"
                text1 +="\n性別: " + f"{gender}"
            elif cgender == '2':
                gender = "女"
                text1 +="\n性別: " + f"{gender}"
            text1 +="\n身高: " + f"{cheight}公分"
            text1 +="\n體重: " + f"{cweight}公斤"

            if cexercise == '0':
                exer_text = "無運動"
                text1 +="\n每周的運動次數: " + exer_text
            elif cexercise == '2':
                exer_text = "1~3次"
                text1 +="\n每周的運動次數: " + exer_text
            elif cexercise == '4':
                exer_text = "4~5次"
                text1 +="\n每周的運動次數: " + exer_text
            elif cexercise == '6':
                exer_text = "6~7次"
                text1 +="\n每周的運動次數: " + exer_text
            elif cexercise == '8':
                exer_text = "7次以上"
                text1 +="\n每周的運動次數: " + exer_text

            if cdietary == '0':
                diab_text = "否(正常飲食)"
                text1 +="\n是否為糖尿病患者: " + diab_text
            elif cdietary == '1':
                diab_text = "一型糖尿病患者"
                text1 +="\n是否為糖尿病患者: " + diab_text
            elif cdietary == '2':
                diab_text = "二型糖尿病患者"
                text1 +="\n是否為糖尿病患者: " + diab_text

            # 切換RichMenu(完整功能頁面)
            headers = {'Authorization':f"Bearer {os.environ['channel_access_token']}"}
            req = requests.request('POST', f'https://api.line.me/v2/bot/user/{user_id}/richmenu/{os.environ["richmenu_b"]}', headers=headers)
            print(req.text) #如果req.text是{}，則API運作正常
            text1 += "\n\n請按查看更多功能選擇您要的功能"

        elif result == "error":
            text1 = '資料庫寫入時發生錯誤\n請再次點選我要註冊填入您的資料'
        return text1
    except Exception as e:
        print(e)
        return '資料處理發生錯誤\n請再次點選我要註冊填入您的資料'
    
def writedb(user_id, name, age, gender, height, weight, exercise, dietary):
    db = DataBase()
    # INSERT 註冊資料進入 DB
    sql = f"INSERT INTO basic_info (user_id, user_name, age, gender, height_, weight_, exercise_freq, diab_type) VALUES ('{user_id}', '{name}', {age}, '{gender}', {height}, {weight}, {exercise}, {dietary});"
    result = db.create(sql)
    return result