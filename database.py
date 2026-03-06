import pandas as pd
import os

FILE = "products.csv"

def init_db():
    if not os.path.exists(FILE):
        df = pd.DataFrame(columns=["product","url","email","current_price","last_price","ai_decision"])
        df.to_csv(FILE,index=False)

def load_products():
    return pd.read_csv(FILE)

def save_products(df):
    df.to_csv(FILE,index=False)

def add_product(product,url,email):

    df = load_products()

    new_row = {
        "product":product,
        "url":url,
        "email":email,
        "current_price":0,
        "last_price":0,
        "ai_decision":"Unknown"
    }

    df = pd.concat([df,pd.DataFrame([new_row])],ignore_index=True)

    save_products(df)
