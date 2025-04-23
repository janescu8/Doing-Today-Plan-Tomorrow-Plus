# 在 Streamlit App 中新增修改日記紀錄的功能

import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(page_title="🌀 迷惘但想搞懂的我", layout="centered")

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google_auth"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("迷惘但想搞懂的我").sheet1

# --- Utility: get headers once for cell updates ---
HEADERS = sheet.row_values(1)

# --- Dynamic Users Setup ---
try:
    raw_records = sheet.get_all_records()
    USERS = sorted({rec['使用者'] for rec in raw_records if rec.get('使用者')})
except Exception:
    USERS = []

# --- User Login ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.title("🔒 選擇或新增使用者 / Select or add user")
    username = st.sidebar.selectbox("使用者 / User", USERS)
    new_user = st.sidebar.text_input("或輸入新使用者 / Or type new user")
    if new_user:
        username = new_user.strip()
    if st.sidebar.button("登入 / Login"):
        if username:
            st.session_state.logged_in = True
            st.session_state.user = username
            if username not in USERS:
                sheet.append_row([username, datetime.date.today().strftime("%Y-%m-%d")] + [""]*6)
            components.html("""<script>window.location.reload();</script>""", height=0)
            st.stop()
        else:
            st.sidebar.error("請輸入使用者名稱 / Enter a user name")
    st.stop()
else:
    user = st.session_state.user
    st.sidebar.success(f"已登入: {user}")

# --- Title and Description ---
st.title("🌀 迷惘但想搞懂的我 / Lost but Learning")
st.markdown("黑白極簡，但情緒滿載 / Minimalist B&W, Full of Emotion")

# --- Input Form ---
today = datetime.date.today().strftime("%Y-%m-%d")
doing_today = st.text_area("📌 今天你做了什麼 / What did you do today?", height=150)
feeling_event = st.text_input("🎯 今天有感覺的事 / What felt meaningful today?")
overall_feeling = st.slider("📊 今天整體感受 (1-10)", 1, 10, 5, key="slider_create")
self_choice = st.text_input("🧠 是自主選擇嗎？/ Was it your choice?")
dont_repeat = st.text_input("🚫 今天最不想再來的事 / What you wouldn't repeat?")
plan_tomorrow = st.text_input("🌱 明天想做什麼 / Plans for tomorrow?")

if st.button("提交 / Submit"):
    row = [user, today, doing_today, feeling_event, overall_feeling, self_choice, dont_repeat, plan_tomorrow]
    sheet.append_row(row)
    st.balloons()
    st.success("已送出！明天見🎉")
    st.markdown("---")

# --- 顯示歷史紀錄 ---
st.markdown("---")
st.subheader("📜 歷史紀錄（最近10筆）")
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # 欄位標準化
    col_map = {col:'未知' for col in df.columns}
    for col in df.columns:
        if '使用者' in col:
            col_map[col] = '使用者'
        elif '日期' in col:
            col_map[col] = '日期'
        elif '做了什麼' in col:
            col_map[col] = '今天你做了什麼'
        elif '你有感覺的事' in col:
            col_map[col] = '今天有感覺的事'
        elif '整體感受' in col:
            col_map[col] = '今天整體感受'
        elif '自己選' in col:
            col_map[col] = '今天做的事，是自己選的嗎？'
        elif '不想再' in col:
            col_map[col] = '今天最不想再來一次的事'
        elif '明天' in col:
            col_map[col] = '明天你想做什麼'
    df.rename(columns=col_map, inplace=True)

    if not df.empty:
        df = df[df['使用者'] == user].tail(10)
        for _, row in df.iterrows():
            st.markdown(f"""
            <div style='border:1px solid #ccc; border-radius:10px; padding:10px; margin-bottom:10px;'>
                <strong>🗓️ 日期：</strong> {row['日期']}<br>
                <strong>📌 今天你做了什麼：</strong> {row['今天你做了什麼']}<br>
                <strong>🎯 今天有感覺的事：</strong> {row['今天有感覺的事']}<br>
                <strong>📊 今天整體感受：</strong> {row['今天整體感受']}/10<br>
                <strong>🧠 是自主選擇：</strong> {row['今天做的事，是自己選的嗎？']}<br>
                <strong>🚫 今天最不想再來的事：</strong> {row['今天最不想再來一次的事']}<br>
                <strong>🌱 明天想做什麼：</strong> {row['明天你想做什麼']}
            </div>
            """, unsafe_allow_html=True)

        # 心情趨勢圖
        st.subheader("📈 心情趨勢圖 / Mood Trend")
        mood_df = df[['日期', '今天整體感受']].copy()
        mood_df.columns = ['date', 'mood']
        mood_df['date'] = pd.to_datetime(mood_df['date'])
        mood_df['mood'] = pd.to_numeric(mood_df['mood'], errors='coerce')
        mood_df = mood_df.dropna().sort_values('date')

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(mood_df['date'], mood_df['mood'], marker='o')
        ax.set_title('Mood Trend Over Time')
        ax.set_xlabel('Date')
        ax.set_ylabel('Mood')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        fig.autofmt_xdate()
        st.pyplot(fig)

except Exception as e:
    st.error(f"讀取紀錄時發生錯誤：{e}")

# --- 編輯功能 ---
st.markdown("---")
st.header("📝 編輯過去紀錄 / Edit Past Entries")

def get_user_data(username):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    # normalize cols same as above
    col_map = {col:'未知' for col in df.columns}
    for col in df.columns:
        if '使用者' in col:
            col_map[col] = '使用者'
        elif '日期' in col:
            col_map[col] = '日期'
        elif '做了什麼' in col:
            col_map[col] = '今天你做了什麼'
        elif '你有感覺的事' in col:
            col_map[col] = '今天有感覺的事'
        elif '整體感受' in col:
            col_map[col] = '今天整體感受'
        elif '自己選' in col:
            col_map[col] = '今天做的事，是自己選的嗎？'
        elif '不想再' in col:
            col_map[col] = '今天最不想再來一次的事'
        elif '明天' in col:
            col_map[col] = '明天你想做什麼'
    df.rename(columns=col_map, inplace=True)
    return df[df['使用者'] == username].reset_index(drop=True)

def update_row(row_index, values):
    # 逐欄更新，確保不新增欄位
    sheet_row = row_index + 2  # data starts at row 2
    for key, val in values.items():
        if key in HEADERS:
            col_idx = HEADERS.index(key) + 1
            sheet.update_cell(sheet_row, col_idx, val)

# load user entries
entries = get_user_data(user)
if not entries.empty:
    selected_date = st.selectbox("請選擇要編輯的日期：", entries['日期'])
    entry = entries[entries['日期'] == selected_date].iloc[0]

    doing_today_e = st.text_area("📌 今天你做了什麼", entry['今天你做了什麼'])
    feeling_event_e = st.text_input("🎯 今天有感覺的事", entry['今天有感覺的事'])
    overall_feeling_e = st.slider("📊 今天整體感受 (1-10)", 1, 10, int(entry['今天整體感受']), key="edit_slider")
    self_choice_e = st.text_input("🧠 是自主選擇嗎？", entry['今天做的事，是自己選的嗎？'])
    dont_repeat_e = st.text_input("🚫 今天最不想再來的事", entry['今天最不想再來一次的事'])
    plan_tomorrow_e = st.text_input("🌱 明天想做什麼", entry['明天你想做什麼'])

    if st.button("更新紀錄 / Update Entry"):
        update_row(entries[entries['日期'] == selected_date].index[0], {
            '使用者': user,
            '日期': selected_date,
            '今天你做了什麼': doing_today_e,
            '今天有感覺的事': feeling_event_e,
            '今天整體感受': overall_feeling_e,
            '今天做的事，是自己選的嗎？': self_choice_e,
            '今天最不想再來一次的事': dont_repeat_e,
            '明天你想做什麼': plan_tomorrow_e
        })
        st.success("紀錄已更新到原本欄位！")
