import streamlit as st
import pandas as pd
from database import init_db,load_products,add_product

init_db()

st.title("AI Price Drop Agent")

st.header("Add Product")

product = st.text_input("Product Name")

url = st.text_input("Product URL")

email = st.text_input("Your Email")

if st.button("Track Product"):

    add_product(product,url,email)

    st.success("Product added for tracking")


st.header("Tracked Products")

df = load_products()

st.dataframe(df)
