import plotly.graph_objs as go
import pandas as pd
import os,sys

CURRENT_DIR= os.path.split(os.path.abspath(__file__))[0]
config_path = CURRENT_DIR.rsplit('\\',1)[0]

sys.path.append(config_path)
from model.database import DataBase

#生成折線圖後轉json
def create_glucose_plot(data, title):
    
    trace = go.Scatter(
        x=data['insertime_min'],
        y=data['glucose'],
        mode='lines+markers',
        name=title,
        line=dict(width=3),
        fill='tozeroy',
        fillcolor='rgba(208, 208, 208, 0.2)',
        text=data['insertime_min'],
        hovertemplate='%{text}<br>血糖值: %{y}'
    )

    lower_bound_trace = go.Scatter(
        x=data['insertime_min'],
        y=[80] * len(data),
        mode='lines',
        name='下界血糖',
        line=dict(color='#01B468')
    )

    upper_bound_trace = go.Scatter(
        x=data['insertime_min'],
        y=[130] * len(data),
        mode='lines',
        name='上界血糖',
        line=dict(color='#AE0000')
    )

    layout = go.Layout(
        title=dict(text=title+'值紀錄', x=0.5, xanchor='center'),
        xaxis=dict(title='日期', tickformat='%Y-%m-%d',gridcolor='rgba(128, 128, 128, 0.2)'),
        yaxis=dict(title='血糖值',gridcolor='rgba(128, 128, 128, 0.2)'),
        plot_bgcolor='rgba(0, 0, 0, 0)'
    )

    fig = go.Figure(data=[trace, lower_bound_trace, upper_bound_trace], layout=layout)
    fig_json = fig.to_json()
    return fig_json

def get_id(userid):
    print("get the data of id {}".format(userid))

    #連接資料庫
    db = DataBase()
    sql1 = f'SELECT * FROM diabetes_info WHERE user_id = "{userid}" AND EXTRACT(HOUR FROM insertime ) BETWEEN 4 AND 10 ORDER BY insertime ASC;'
    sql2 = f'SELECT * FROM diabetes_info WHERE user_id = "{userid}" AND EXTRACT(HOUR FROM insertime ) BETWEEN 11 AND 15 ORDER BY insertime ASC;'
    sql3 = f'SELECT * FROM diabetes_info WHERE user_id = "{userid}" AND EXTRACT(HOUR FROM insertime ) BETWEEN 16 AND 23 ORDER BY insertime ASC;'

    sql_data=f'SELECT MAX(glucose) AS max_glucose, MIN(glucose) AS min_glucose, round(AVG(glucose),2) AS avg_glucose, SUM(CASE WHEN glucose < 80 OR glucose > 130 THEN 1 ELSE 0 END) AS count_glucose,ROUND((SUM(CASE WHEN glucose >= 80 AND glucose <= 130 THEN 1 ELSE 0 END) / count(*)) * 100, 2) AS TIR FROM diabetes_info WHERE (user_id, DATE(insertime)) IN (SELECT user_id, MAX(DATE(insertime)) FROM diabetes_info WHERE user_id = "{userid}" GROUP BY user_id) AND user_id = "{userid}";'

    morning_glucose=pd.DataFrame(db.read(sql1))
    noon_glucose=pd.DataFrame(db.read(sql2))
    evening_glucose=pd.DataFrame(db.read(sql3))

    if not morning_glucose.empty:
        morning_glucose['insertime_min']=morning_glucose['insertime'].dt.strftime('%Y-%m-%d %H:%M')
        morning_glucose_no_duplicates = morning_glucose.drop_duplicates(subset=['insertime_min'], keep='last')
        morning_glucose_chart=create_glucose_plot(morning_glucose_no_duplicates, '早晨血糖')
    else:
        morning_glucose_chart='None'

    if not noon_glucose.empty:
        noon_glucose['insertime_min']=noon_glucose['insertime'].dt.strftime('%Y-%m-%d %H:%M')
        noon_glucose_no_duplicates = noon_glucose.drop_duplicates(subset=['insertime_min'], keep='last')       
        noon_glucose_chart=create_glucose_plot(noon_glucose_no_duplicates, '午間血糖')
    else:
        noon_glucose_chart = 'None'
        
    if not evening_glucose.empty:
        evening_glucose['insertime_min']=evening_glucose['insertime'].dt.strftime('%Y-%m-%d %H:%M')
        evening_glucose_no_duplicates = evening_glucose.drop_duplicates(subset=['insertime_min'], keep='last')
        evening_glucose_chart=create_glucose_plot(evening_glucose_no_duplicates, '晚間血糖')
    else:
        evening_glucose_chart = 'None'

    charts_data = {
    'morning_glucose_chart': morning_glucose_chart,
    'noon_glucose_chart': noon_glucose_chart,
    'evening_glucose_chart': evening_glucose_chart
    }

    sql_data=pd.DataFrame(db.read(sql_data))

    if morning_glucose.empty and noon_glucose.empty and evening_glucose.empty:
        max_glucose=None
        min_glucose=None
        avg_glucose=None
        lage_glucose=None
        tir_glucose=None
    else:
        max_glucose=sql_data['max_glucose'][0]
        min_glucose=sql_data['min_glucose'][0]
        avg_glucose=sql_data['avg_glucose'][0]
        lage_glucose=max_glucose-min_glucose
        tir_glucose=sql_data['TIR'][0]


    return charts_data,max_glucose,min_glucose,avg_glucose,lage_glucose,tir_glucose
