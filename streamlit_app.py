import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="PKNU Multi-page App", layout="wide")

# --- session_state 기본값 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# --- cache_data: 같은 질문이면 캐시 사용 ---
@st.cache_data(show_spinner=False)
def get_single_answer(api_key: str, question: str) -> str:
    client = OpenAI(api_key=api_key)
    resp = client.responses.create(
        model="gpt-5-mini",  # 과제 요구 모델명
        input=question,
    )
    return resp.output[0].content[0].text


st.title("1. gpt-5-mini 단일 질문 페이지 (Home)")

# API Key 입력 (session_state에 저장)
api_key_input = st.text_input(
    "OpenAI API Key를 입력하세요",
    type="password",
    value=st.session_state.api_key,
)
if api_key_input:
    st.session_state.api_key = api_key_input

question = st.text_input("질문을 입력하세요")

if st.button("질문 보내기"):
    if not st.session_state.api_key:
        st.error("먼저 OpenAI API Key를 입력하세요.")
    elif not question.strip():
        st.warning("질문을 입력해 주세요.")
    else:
        with st.spinner("응답 생성 중..."):
            answer = get_single_answer(st.session_state.api_key, question)
        st.subheader("모델 응답")
        st.write(answer)

st.info("왼쪽 위 메뉴(☰)에서 다른 페이지(Chat, Chatbot, ChatPDF)로 이동할 수 있습니다.")