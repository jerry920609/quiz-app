import streamlit as st
import PyPDF2
import re
import random

# 設定網頁標題與排版
st.set_page_config(page_title="題庫測驗系統", page_icon="📝", layout="centered")

@st.cache_data # 使用快取，這樣切換頁面時不用每次都重新解析 PDF
def load_and_parse_pdf(file_obj):
    all_text = ""
    try:
        # Streamlit 的上傳檔案物件可以直接讓 PyPDF2 讀取
        reader = PyPDF2.PdfReader(file_obj)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                all_text += page_text + "\n"
    except Exception as e:
        st.error(f"讀取檔案失敗: {e}")
        return []

    # 沿用你原本精準的正則表達式
    pattern = r'\((\d)\)\s*(\d+)\.(.*?)(?=\(\d\)\s*\d+\.|$)'
    clean_text = re.sub(r'\n(?!\(\d\)\d+\.)', '', all_text)
    matches = re.findall(pattern, clean_text, re.DOTALL)
    
    questions = []
    for ans, num, content in matches:
        questions.append({
            "id": num.strip(),
            "ans": ans.strip(),
            "text": content.strip()
        })
    return questions

# 網頁主標題
st.title("📝 題庫測驗系統")
st.write("上傳題庫 PDF 檔，隨時隨地進行刷題練習！")

# 1. 檔案上傳區
uploaded_file = st.file_uploader("請上傳題庫 (例如：甲級廢水_1.pdf)", type="pdf")

if uploaded_file is not None:
    with st.spinner('解析題目中，請稍候...'):
        qs = load_and_parse_pdf(uploaded_file)
    
    if not qs:
        st.error("❌ 抓不到題目。請確認：1. 檔案是否加密？ 2. 檔案是否為純圖片（掃描檔）？")
    else:
        st.success(f"🎉 成功解析！共偵測到 {len(qs)} 個題目。")
        
        # 建立兩個頁籤
        tab1, tab2 = st.tabs(["🎲 隨機測驗", "🔍 查看特定題號"])
        
        # --- 頁籤 1：隨機測驗 ---
        with tab1:
            num_q = st.number_input("想練習幾題？", min_value=1, max_value=len(qs), value=min(10, len(qs)))
            
            # 按下按鈕產生考卷
            if st.button("產生測驗卷"):
                st.session_state.test_set = random.sample(qs, num_q)
                
            # 如果已經抽好題目，就顯示作答表單
            if 'test_set' in st.session_state:
                with st.form("quiz_form"):
                    user_answers = {}
                    for i, q in enumerate(st.session_state.test_set, 1):
                        st.markdown(f"**【第 {i} 題 / 題號 {q['id']}】**")
                        st.write(q['text'])
                        # 產生 1~4 的單選題選項
                        user_answers[q['id']] = st.radio(
                            "請選擇答案：", 
                            options=["1", "2", "3", "4"], 
                            key=f"q_{q['id']}",
                            horizontal=True
                        )
                        st.divider() # 視覺分隔線
                        
                    # 交卷按鈕
                    submit_button = st.form_submit_button("交卷看成績")
                    
                    if submit_button:
                        score = 0
                        for q in st.session_state.test_set:
                            if user_answers[q['id']] == q['ans']:
                                score += 1
                            else:
                                st.error(f"❌ 題號 {q['id']} 答錯了。正確答案是：({q['ans']})")
                                
                        st.success(f"💯 測驗結束！您的得分：{score} / {len(st.session_state.test_set)}")

        # --- 頁籤 2：查看特定題號 ---
        with tab2:
            target = st.text_input("請輸入要查詢的題號：")
            if st.button("搜尋"):
                if target:
                    found = next((q for q in qs if q['id'] == target), None)
                    if found:
                        st.info(f"**題號 {found['id']}**\n\n{found['text']}\n\n**解答：({found['ans']})**")
                    else:
                        st.warning("找不到該題號，請確認輸入是否正確。")
                else:
                    st.warning("請先輸入題號！")