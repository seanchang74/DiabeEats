import pymysql, os
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv() #load .env file content
class DataBase:
    def __init__(self):
        self.host=os.environ['db_host']
        self.user=os.environ['db_user']
        self.password=os.environ['db_password']
        self.database=os.environ['db_name']
    
    def connect(self):
        self.conn = pymysql.connect(host=self.host, 
                                    user=self.user,
                                    password=self.password,
                                    database=self.database,
                                    cursorclass=pymysql.cursors.DictCursor)
        cur = self.conn.cursor()
        if not cur:
            raise(NameError, "database connection failed")
        else:
            # print("connection success!")
            return cur

    def create(self, sql:str):
        try:
            cur = self.connect()
            cur.execute(sql)
            self.conn.commit()
            self.conn.close()
            return "ok"
        except Exception as e:
            print(e)
            return "error"

    def read(self, sql:str):
        try:
            cur = self.connect()
            cur.execute(sql)
            result = cur.fetchall()
            self.conn.close()
            return result
        except Exception as e:
            print(e)
            return "error"
    
    # def update(self, table):
    #     try:
    #         pass
    #     except Exception as e:
    #         pass
    
    # def delete(self, table):
    #     try:
    #         pass
    #     except Exception as e:
    #         pass