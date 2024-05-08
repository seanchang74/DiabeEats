import pandas as pd
import random, json, os, openai, re
from dotenv import load_dotenv
load_dotenv()

openai.organization = os.environ['openai_org_token']
openai.api_key = os.environ['openai_api_token']

def recommendation(required_blood_sugar, vegen, required_calories, not_eat, want_eat, type):
    response = ""
    #串接family資料
    df = pd.read_csv(f"{os.getcwd()}/static/familymart_filtered_add_col.csv")
    df['total_calorie']=df['serving_per_bag']*df['calorie']
    df = df[df['serving_per_bag']!=0]

    # filter
    max_calories=required_calories+50 #熱量上限
    min_calories=required_calories-50 #熱量下限
    max_carbohydrates=(required_calories+50)*0.7/4 #碳水上限

    max_fat=(required_calories+50)*0.1/9 #脂肪上限
    max_protein=(required_calories+50)*0.2/4 #蛋白質上限
    max_sodium=800 #鈉上限

    not_eat_df = df.copy()

    #篩掉超過一餐總量限制食品
    required_calories_df = df[(df['total_calorie']<=max_calories)&
                          (df['carbohydrate']*df['serving_per_bag']<=max_carbohydrates)&
                          (df['saturated fat']*df['serving_per_bag']<=max_fat)&
                          (df['protein']*df['serving_per_bag']<=max_protein)&
                          (df['sodium']*df['serving_per_bag']<=max_sodium)]
    
    if vegen is not None and "素" in vegen:
        if "全素" in vegen:
            not_eat_df = not_eat_df[(not_eat_df["全素"] == 1)]
        elif "蛋素" in vegen:
            not_eat_df = not_eat_df[not_eat_df["蛋素"] == 1]
        elif "奶素" in vegen:
            not_eat_df = not_eat_df[not_eat_df["奶素"] == 1]
        elif "奶蛋素" in vegen or "蛋奶素" in vegen:
            not_eat_df = not_eat_df[not_eat_df["奶蛋素"] == 1]
        elif "五辛素" in vegen:
            not_eat_df = not_eat_df[not_eat_df["植物五辛素"] == 1]
        elif "鍋邊素" in vegen:
            not_eat_df = not_eat_df[(not_eat_df["全素"] == 1)|
                    (not_eat_df["植物五辛素"] == 1)|
                    (not_eat_df["蛋素"] == 1)|
                    (not_eat_df["奶素"] == 1)|
                    (not_eat_df["奶蛋素"] == 1)]

    #自商品名稱篩選掉不吃的食物(全部都不能含有)
    if not_eat_df is not None and "name" in not_eat_df.columns:
        if re.search(r'麵(?!包)', not_eat): #如果只有麵，保留麵包
            not_eat_df = not_eat_df[not_eat_df["name"].str.contains("麵包")|~not_eat_df["name"].str.contains(not_eat, regex=True)]
        else:
            not_eat_df = not_eat_df[~not_eat_df["name"].str.contains(not_eat)]

    #過敏原過濾
    if not_eat_df.shape[0] != 0 and not_eat_df.shape[1] != 0:
        if "牛肉" in not_eat or "牛" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["不含牛肉"] == 1)]
        elif "豬肉" in not_eat or "豬" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["不含豬肉"] == 1)]
        elif "禽肉" in not_eat or "雞" in not_eat or "鴨" in not_eat or "鵝" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["不含禽肉"] == 1)]
        elif "海鮮" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["不含海鮮"] == 1)]
        elif "魚" in not_eat:
            not_eat_df = not_eat_df[not_eat_df["魚類及其製品"] == 0]
        elif "花生" in not_eat:
            not_eat_df = not_eat_df[not_eat_df["花生及其製品"] == 0]
        elif "麩質" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["含麩質之穀物及其製品"] == 0) & (not_eat_df["不含麩質"] == 1)]
        elif "花生" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["花生及其製品"] == 0) & (not_eat_df["不含花生"] == 1)]
        elif "堅果" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["堅果類、種子類及其製品"] == 0) & (not_eat_df["不含堅果"] == 1)]
        elif "大豆" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["大豆及其製品"] == 0) & (not_eat_df["不含大豆"] == 1)]
        elif "奇異果" in not_eat:
            not_eat_df = not_eat_df[not_eat_df["奇異果及其製品"] == 0]
        elif "牛奶" in not_eat or "羊奶" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["牛奶、羊奶及其製品"] == 0) & (not_eat_df["不含牛/羊奶"] == 1)]
        elif "蝦" in not_eat or "蟹" in not_eat or "甲殼" in not_eat or "帶殼海鮮" in not_eat:
            not_eat_df = not_eat_df[not_eat_df["甲殼類及其製品(蝦類、蟹類)"] == 0]
        elif "芒果" in not_eat:
            not_eat_df = not_eat_df[not_eat_df["芒果及其製品"] == 0]
        elif "芝麻" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["芝麻及其製品"] == 0) & (not_eat_df["不含芝麻"] == 1)]
        elif "花生" in not_eat:
            not_eat_df = not_eat_df[not_eat_df["花生及其製品"] == 0]
        elif "蛋" in not_eat or "雞蛋" in not_eat or "鴨蛋" in not_eat:
            not_eat_df = not_eat_df[(not_eat_df["蛋類及其製品"] == 0) & (not_eat_df["不含蛋品"] == 1)]
        elif "螺" in not_eat or "小卷" in not_eat or "花枝" in not_eat:
            not_eat_df = not_eat_df[not_eat_df["軟體動物類及其製品(頭足類、螺貝類)"] == 0]


    #random商品集
    filtered_df = pd.merge(required_calories_df ,not_eat_df,how="inner")
    filtered_df = filtered_df[['name', 'total_calorie', 'carbohydrate', 'saturated fat', 'protein', 'sodium', 'serving_per_bag']]

    meal_food = []
    meal_calories = 0
    meal_carbohydrates = 0
    meal_fat = 0
    meal_sodium = 0
    meal_protein = 0
    added_zero_calorie_item = False

    #先隨機篩選一項符合要求的商品加入推薦list
    if want_eat and want_eat not in ['無','沒有']:
        if re.search(r'麵(?!包)', want_eat):
            want_eat_df = filtered_df[(filtered_df['name'].str.contains(want_eat))&(~filtered_df['name'].str.contains("麵包"))]
        else:
            want_eat_df = filtered_df[filtered_df['name'].str.contains(want_eat)]
        if not want_eat_df.empty:
            random_want_eat_food = want_eat_df.sample(1).iloc[0]
            meal_food.append(random_want_eat_food)
            meal_calories += random_want_eat_food['total_calorie']
            meal_carbohydrates += random_want_eat_food['carbohydrate']*random_want_eat_food['serving_per_bag']
            meal_fat += random_want_eat_food['saturated fat']*random_want_eat_food['serving_per_bag']
            meal_sodium += random_want_eat_food['sodium']*random_want_eat_food['serving_per_bag']
            meal_protein += random_want_eat_food['protein']*random_want_eat_food['serving_per_bag']
        else:
            response+=f'很抱歉未找到符合您想要的"{want_eat}"品項\n'

    # 在熱量未滿需求值時，繼續加入推薦商品
    while not (min_calories <= meal_calories <= max_calories):
        #縮小random範圍
        remaining_calories = max_calories - meal_calories
        remaining_carbohydrate = max_carbohydrates - meal_carbohydrates
        remaining_fat = max_fat - meal_fat
        remaining_protain = max_protein - meal_protein
        remaining_sodium = max_sodium - meal_sodium
        available_foods = filtered_df[
            (filtered_df['total_calorie'] <= remaining_calories) &
            (filtered_df['carbohydrate'] * filtered_df['serving_per_bag'] <= remaining_carbohydrate) &
            (filtered_df['saturated fat'] * filtered_df['serving_per_bag'] <= remaining_fat) &
            (filtered_df['protein'] * filtered_df['serving_per_bag'] <= remaining_protain) &
            (filtered_df['sodium'] * filtered_df['serving_per_bag'] <= remaining_sodium)
        ]        

        if available_foods.empty:
            break

        available_foods = available_foods[~available_foods['name'].isin([food['name'] for food in meal_food])]

        if available_foods.empty:
            break

        random_food = available_foods.sample(1).iloc[0]
        
        if random_food['total_calorie']==0 and added_zero_calorie_item:
            continue

         #讓推薦不重複
        if random_food['name'] not in [food['name'] for food in meal_food]:
            # 食品的卡路里和碳水化合物含量
            food_calories = random_food['total_calorie']
            food_carbohydrates = random_food['carbohydrate']*random_food['serving_per_bag']
            food_fat = random_food['saturated fat']*random_food['serving_per_bag']
            food_sodium = random_food['sodium']*random_food['serving_per_bag']
            food_protein = random_food['protein']*random_food['serving_per_bag']

            # 不超過卡路里+50時，加入推薦商品
            if (meal_calories + food_calories <= max_calories) and (meal_sodium + food_sodium <= max_sodium):
                meal_calories += food_calories
                meal_carbohydrates += food_carbohydrates
                meal_fat += food_fat
                meal_sodium += food_sodium
                meal_protein += food_protein
                meal_food.append(random_food)

            if random_food['total_calorie']==0:
                added_zero_calorie_item = True

    if len(meal_food)==0:
        response='很抱歉，找不到符合需求的商品'

    else:
        response += '為您推薦以下食品：\n'
        for idx, item in enumerate(meal_food, start=1):
            response += f"  {idx}. {item['name']}\n"
        if type == 1:
            insulin_dose = (((meal_carbohydrates / 15) * 30) - (120 - required_blood_sugar)) / 30
            response += f"\n提醒您，在餐前需要施打{round(insulin_dose)}個單位的胰島素"
        elif type == 2:
            response += "\n提醒您，請按照醫師的囑咐按時服藥!"

    messages = [
    {"role": "system", 
     "content": '作為一位具專業營養知識的食品推薦機器人，請在30字以內，以第三人稱且活潑的風格簡單修飾文字，不要在食品名稱前加其他形容詞或修飾語。在有胰島素劑量提醒時，一定要在顯示完所有食品名稱後，顯示胰島素的劑量；沒有胰島素劑量提醒時，不要生成胰島素相關語句'},
    {"role": "user", "content": response}]

    response_new = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=messages,
        max_tokens=300, # 調整生成文本的長度
        temperature=0.7,
        #timeout=10
        )

    modified_response =  response_new['choices'][0]['message']['content']

    return modified_response