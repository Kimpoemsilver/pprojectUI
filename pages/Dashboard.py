import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Arc, Circle
import pandas as pd
import plotly.express as px
import matplotlib as mpl
from openai import OpenAI


mpl.rcParams["font.family"] = "Malgun Gothic"  # 윈도우 한글 폰트
mpl.rcParams["axes.unicode_minus"] = False  

st.set_page_config(
    page_title="스트레스 측정 결과",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== CSS (페이지 전체 박스 스타일 제거 + 카드만 테두리) =====
st.markdown("""
<style>
/* 사이드바 숨겨주긔 */
section[data-testid="stSidebar"] { display: none !important; }
div[data-testid="stSidebarNav"] { display: none !important; }
button[data-testid="collapsedControl"] { display: none !important; }

/* 카드 wrapper */
div[data-testid="stVerticalBlockBorderWrapper"]:has(span#card-level),
div[data-testid="stVerticalBlockBorderWrapper"]:has(span#card-score){
    border: 3px solid #5BA4A4 !important;
    border-radius: 22px !important;
    background-color: #EAF6F6 !important;
    padding: 14px 14px !important;
}

/* 카드 내부(자식 div)까지 배경 적용 + 라운드 유지 */
div[data-testid="stVerticalBlockBorderWrapper"]:has(span#card-level) > div,
div[data-testid="stVerticalBlockBorderWrapper"]:has(span#card-score) > div{
    background-color: #EAF6F6 !important;
    border-radius: 22px !important;
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

# ===== 피규어 생성 함수 =====
def plot_stress_level_gauge(level: str):
    level = (level or "").upper()
    pos_map = {"LOW": 0, "AVERAGE": 1, "HIGH": 2}
    idx = pos_map.get(level, 1)

    # 각 구간(좌->우): LOW / AVERAGE / HIGH
    # 각도: 180(왼쪽) -> 0(오른쪽)
    bounds = [(180, 120), (120, 60), (60, 0)]
    colors = ["#2ecc71", "#f1c40f", "#e74c3c"]

    fig, ax = plt.subplots(figsize=(5.2, 3.2), dpi=160)
    ax.set_aspect("equal")
    ax.axis("off")

    # 구간 채우기 (반원)
    for (a1, a2), c in zip(bounds, colors):
        ax.add_patch(Wedge((0, 0), 1.0, a2, a1, width=0.28, facecolor=c, edgecolor="none"))

    # 바깥/안쪽 원 라인
    ax.add_patch(Arc((0, 0), 2.0, 2.0, fill=False, linewidth=2, edgecolor="#000"))
    ax.add_patch(Arc((0, 0), 1.44, 1.44, fill=False, linewidth=2, edgecolor="#000"))
    # 헥스 컬러는 3자리거나 6자리여야 함(헥스 컬러: 색을 숫자로 표현하는 방법으로 # 뒤에 16진수 숫자 6개로 색을 정함).
    # Arc(호)를 그릴 땐 가로 지름, 세로 지름 모두 줘야 함. (원은 가로 지름만 줘도 ok)
    # 원을 그릴 때 했던 가로 지름의 2배로 입력해줘야 함

    # 레이블
    ax.text(-0.86, 0.12, "LOW", fontsize=10, weight="bold", ha="center", va="center")
    ax.text(0.00, 0.80, "AVERAGE", fontsize=10, weight="bold", ha="center", va="center")
    ax.text(0.86, 0.12, "HIGH", fontsize=10, weight="bold", ha="center", va="center")
    # 침(needle) 각도: 각 구간 중앙을 가리키게
    centers = [150, 90, 30]  # LOW/AVG/HIGH 중앙각
    ang = np.deg2rad(centers[idx])
    x, y = 0.72 * np.cos(ang), 0.72 * np.sin(ang)
    ax.plot([0, x], [0, y], linewidth=4, color="#222", solid_capstyle="round")
    ax.add_patch(Circle((0, 0), 0.05, color="#222"))

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.6, 1.2)
    return fig


def plot_stress_score_circle(score: float):
 
    s = float(np.clip(score, 0, 1500))
    frac = s / 1500.0

    if s <= 150:
        color = "#2ecc71"
    elif s <= 300:
        color = "#f1c40f"
    else:
        color = "#e74c3c"

    fig, ax = plt.subplots(figsize=(1.8, 1.8), dpi=120)
    ax.set_aspect("equal")
    ax.axis("off")

    # 배경 링
    ax.add_patch(Wedge((0, 0), 1.0, 0, 360, width=0.18, facecolor="#e6e6e6", edgecolor="none"))

    # 진행 링: 위(90도)부터 시계방향으로 채우기
    start = 90
    end = 90 - 360 * frac
    ax.add_patch(Wedge((0, 0), 1.0, end, start, width=0.18, facecolor=color, edgecolor="none"))


    # 가운데 텍스트
    ax.text(0, -0.05, f"{int(round(s))}점", ha="center", va="center", fontsize=10, weight="bold")

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    return fig


# ====== (여기부터 실제 화면) ======
user_name = st.session_state.get("user_name", "희찬띠니")
st.markdown(
    f"""
    <div style='font-size:44px; font-weight:800; margin:10px 0 18px 0;'>
        {user_name} 님 스트레스 측정 결과
    </div>
    """,
    unsafe_allow_html=True
)


# 여기 값은 나중에 모델/DB에서 받아서 넣어야
stress_level = "HIGH"   # "LOW" / "AVERAGE" / "HIGH"
stress_score = 329       # 0~1500

col1, col2 = st.columns(2, gap="small")

with col1:
    with st.container(border=True):
        st.markdown('<span id="card-level"></span>', unsafe_allow_html=True)
        st.markdown("### STRESS LEVEL")
        fig1 = plot_stress_level_gauge(stress_level)
        st.pyplot(fig1, use_container_width=True)

with col2:
    with st.container(border=True):
        st.markdown('<span id="card-score"></span>', unsafe_allow_html=True)
        st.markdown("### STRESS SCORE")
        fig2 = plot_stress_score_circle(stress_score)
        st.pyplot(fig2, use_container_width=True)

# 한줄 조언 메세지
st.markdown("""
<style>
.advice-box {
background-color: #EFEFEF;
padding: 12px;
border-radius: 6px;
font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<br>
<div class='advice-box'>
<b>한줄 조언</b> &nbsp;&nbsp; 
회찬님! 하시던거 멈추시고 5분만 주변을 천천히 걸어보세요.  
움직임이 스트레스를 내려주는 데 큰 도움이 됩니다!
</div>
<br>
""", unsafe_allow_html=True)


# -------더미 변수-------
stress_trend = [300, 311, 210, 256, 329]  
dates = ["12월 01일", "12월 03일", "12월 05일", "12월 07일", "12월 09일"]
change_rate = 17.0

# 5회 측정 그래프
df = pd.DataFrame({
    "날짜": dates,
    "스트레스": stress_trend
})

fig = px.line(df, x="날짜", y="스트레스", markers=True)
fig.update_layout(
    height=300,
    margin=dict(l=20, r=20, t=20, b=20),
    yaxis_title="",
    xaxis_title=""
)

graph_col, stat_col = st.columns([3, 1], gap="large")

with graph_col:
    st.subheader("스트레스 추이")
    st.plotly_chart(fig, use_container_width=True)

with stat_col:
    # 아래로 내리기
    st.markdown("<div style='height:210px;'></div>", unsafe_allow_html=True)

    # 박스
    st.markdown(
        f"""
        <div style="
            display:inline-flex;
            align-items:center;
            gap:10px;
            padding:12px 18px;
            border-radius:999px;
            border:3px solid #5BA4A4;
            background:#EAF6F6;
            font-size:22px;
            font-weight:800;
            white-space:nowrap;
        ">
            <span style="color:#1f2937;">평균 대비</span>
            <span style="color:#FF5733;">{change_rate:.1f}%</span>
            <span style="color:#1f2937;">증가</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)


# 결과 해석 링크 / 지피티 연결하기
if "OPENAI_API_KEY" not in st.secrets:
    st.error("OPENAI_API_KEY가 Secrets에 없습니다. Streamlit Cloud > Secrets 설정을 확인하세요.")
    client = None
else:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def build_gpt_prompt(
    user_name: str,
    stress_level: str,
    stress_score: float,
    stress_trend: list,
    dates: list,
    change_rate: float
) -> str:
    return f"""
너는 스트레스 측정 결과를 사용자가 이해하기 쉬운 한국어로 설명("~입니다."의 문체 사용)하는 도우미야. 
과장하거나 진단하지 말고, 안전하고 현실적인 조언을 제공해줘. 

아래 형식으로 답변해줘:
1) 한 줄 요약(1문장)
2) 현재 상태 해석(2~3문장)
3) 추이 해석(2~3문장)
4) 오늘 할 수 있는 행동 3가지(불릿 3개)
5) 주의가 필요한 경우(1~2문장)

[사용자]
이름: {user_name}

[결과]
스트레스 레벨: {stress_level}
스트레스 점수(SI): {stress_score} (범위 0~1500)
최근 5회 추이: {list(zip(dates, stress_trend))}
평균 대비 변화율: {change_rate:.1f}%
""".strip()

# 버튼 스타일
st.markdown("""
<style>
.result-button-wrap {
    display:flex;
    justify-content:flex-end;
}
</style>
""", unsafe_allow_html=True)


st.markdown("<div class='result-button-wrap'>", unsafe_allow_html=True)
run_gpt = st.button("결과 해석 바로가기 ➜")
st.markdown("</div>", unsafe_allow_html=True)

result_area = st.empty()  # 버튼 눌렀을 때 같은 위치에 결과 표시

# 버튼 눌렀을 때만 GPT 호출
if run_gpt:
    if client is None:
        result_area.error("GPT 해석을 위한 API 키가 설정되지 않았습니다. Secrets를 확인하세요.")
    else:
        prompt = build_gpt_prompt(
            user_name=user_name,
            stress_level=stress_level,
            stress_score=stress_score,
            stress_trend=stress_trend,
            dates=dates,
            change_rate=change_rate
        )

        with st.spinner("결과를 해석 중입니다..."):
            try:
                res = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": "너는 친절하고 차분한 스트레스 결과 해석 도우미입니다."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.4,
                )
                answer = res.choices[0].message.content
                result_area.markdown("### 📌 결과 해석\n\n" + answer)
            except Exception as e:
                result_area.error("GPT 해석 생성 중 오류가 발생했습니다. (API 키/모델/requirements 확인)")
                result_area.exception(e)