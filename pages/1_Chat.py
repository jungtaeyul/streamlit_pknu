import streamlit as st
from openai import OpenAI

st.title("2. Chat 페이지 (Responses API 챗봇)")

# --- session_state 기본값 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # [{role, content}, ...]

# API Key 표시/변경 가능 (Home에서 설정해도 여기서 그대로 보임)
api_key_input = st.text_input(
    "OpenAI API Key",
    type="password",
    value=st.session_state.api_key,
)
if api_key_input:
    st.session_state.api_key = api_key_input

if not st.session_state.api_key:
    st.warning("먼저 OpenAI API Key를 입력하세요.")
    st.stop()

client = OpenAI(api_key=st.session_state.api_key)

# Clear 버튼
if st.button("Clear(대화 초기화)"):
    st.session_state.chat_history = []
    st.success("대화가 초기화되었습니다.")

# 기존 대화 출력
chat_container = st.container()
with chat_container:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"**👤 사용자:** {msg['content']}")
        else:
            st.markdown(f"**🤖 챗봇:** {msg['content']}")

user_msg = st.text_input("메시지를 입력하세요", key="chat_input")

if st.button("보내기"):
    if not user_msg.strip():
        st.warning("메시지를 입력해 주세요.")
    else:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_msg}
        )

        # Responses API에 보낼 input (대화 전체 컨텍스트)
        messages_for_api = [
            {"role": "system", "content": "You are a helpful assistant."}
        ] + st.session_state.chat_history

        with st.spinner("응답 생성 중..."):
            resp = client.responses.create(
                model="gpt-5-mini",
                input=messages_for_api,
            )
            bot_reply = resp.output[0].content[0].text

        st.session_state.chat_history.append(
            {"role": "assistant", "content": bot_reply}
        )

        # 바로 출력
        with chat_container:
            st.markdown(f"**👤 사용자:** {user_msg}")
            st.markdown(f"**🤖 챗봇:** {bot_reply}")
