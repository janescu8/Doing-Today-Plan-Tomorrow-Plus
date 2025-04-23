# 在 Streamlit App 中新增修改日記紀錄的功能

import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google_auth"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("迷惘但想搞懂的我").sheet1

def get_user_data(username):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    df_user = df[df['使用者'] == username].reset_index(drop=True)
    return df_user

def update_row(row_index, values):
    # +2 是因為 Google Sheets 的資料從第2列開始（第一列是標題），而 DataFrame 是從 0 開始
    sheet.update(f"A{row_index+2}:H{row_index+2}", [values])

# 使用者登入狀態檢查
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("請先登入使用者。")
    st.stop()

user = st.session_state.user
st.header("📝 編輯過去紀錄 / Edit Past Entries")

df_user = get_user_data(user)

if df_user.empty:
    st.info("目前沒有紀錄可編輯。")
    st.stop()

selected_date = st.selectbox("請選擇要編輯的日期：", df_user['日期'])
entry = df_user[df_user['日期'] == selected_date].iloc[0]

st.markdown("---")
st.subheader(f"編輯 {selected_date} 的紀錄")

doing_today = st.text_area("📌 今天你做了什麼 / What did you do today?", entry['今天你做了什麼'])
feeling_event = st.text_input("🎯 今天有感覺的事 / What felt meaningful today?", entry['今天有感覺的事'])
overall_feeling = st.slider("📊 今天整體感受 (1-10)", 1, 10, int(entry['今天整體感受']))
self_choice = st.text_input("🧠 是自主選擇嗎？/ Was it your choice?", entry['今天做的事，是自己選的嗎？'])
dont_repeat = st.text_input("🚫 今天最不想再來的事 / What you wouldn't repeat?", entry['今天最不想再來一次的事'])
plan_tomorrow = st.text_input("🌱 明天想做什麼 / Plans for tomorrow?", entry['明天你想做什麼'])

if st.button("更新紀錄 / Update Entry"):
    update_row(df_user[df_user['日期'] == selected_date].index[0], [user, selected_date, doing_today, feeling_event, overall_feeling, self_choice, dont_repeat, plan_tomorrow])
    st.success("紀錄已更新！")
