import streamlit as st

st.set_page_config(page_title="회원정보 입력", page_icon="🌱", 
                   layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* 사이드바를 숨겨줄거긔 */
section[data-testid="stSidebar"] { display: none !important; }
div[data-testid="stSidebarNav"] { display: none !important; }
button[data-testid="collapsedControl"] { display: none !important; }

/* 파란 테두리 */
div[data-testid="stVerticalBlockBorderWrapper"]{
    border: 4px solid #5BA4A4 !important;
    border-radius: 25px !important;
    background-color: #F5F5F5 !important;
    padding: 40px 60px !important;
    margin-top: 30px !important;
}

/* 버튼 스타일 */
div[data-testid="stButton"] > button {
    width: 160px !important;
    height: 50px !important;
    font-size: 18px !important;
    border-radius: 10px !important;
    border: 2px solid !important;
    font-weight: 600 !important;
    background-color: white !important;
}
</style>
""", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<span id="bluebox-anchor"></span>', unsafe_allow_html=True)

    st.title("회원정보 입력")

    name = st.text_input("이름", placeholder="이름을 입력하세요")
    gender = st.radio("성별", ["남", "여"], horizontal=True)
    age = st.number_input("나이", min_value=0, max_value=120, step=1)

    
    _, btn_col = st.columns([7, 3])
    with btn_col:
        submitted = st.button("입력")


if submitted:
    if not name:
        st.error("이름을 입력해주세요.")
    elif age == 0:
        st.error("나이를 입력해주세요.")
    else:
        st.session_state["user_name"] = name
        st.session_state["user_gender"] = gender
        st.session_state["user_age"] = age
        st.switch_page("D:\\p_project\\UI\\pages\\Dashboard.py")
