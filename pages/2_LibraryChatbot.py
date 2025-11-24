import streamlit as st
from openai import OpenAI

st.title("3. 국립부경대학교 도서관 챗봇")

# --- 도서관 규정 문자열 (여기에 실제 규정 복사해서 넣기) ---
LIBRARY_RULES = """
여기에 국립부경대학교 도서관 규정 전체 텍스트를 복사하여 붙여 넣으세요.

예: 휴관일, 대출 권수/기간, 연체, 열람실 이용 규칙 등...
"""

# --- session_state 기본값 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "library_history" not in st.session_state:
    st.session_state.library_history = []  # [{role, content}, ...]

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
if st.button("Clear(도서관 대화 초기화)"):
    st.session_state.library_history = []
    st.success("도서관 챗봇 대화가 초기화되었습니다.")

st.info("※ 이 챗봇은 도서관 규정집 텍스트(LIBRARY_RULES)를 바탕으로만 답변합니다.")

# 기존 대화 출력
lib_container = st.container()
with lib_container:
    for msg in st.session_state.library_history:
        if msg["role"] == "user":
            st.markdown(f"**👤 사용자:** {msg['content']}")
        else:
            st.markdown(f"**📚 도서관 챗봇:** {msg['content']}")

user_msg = st.text_input(
    "도서관 규정에 대해 질문해 보세요.",
    placeholder="예: 도서관 휴관일이 언제인가요?",
)

if st.button("질문 보내기"):
    if not user_msg.strip():
        st.warning("질문을 입력해 주세요.")
    else:
        st.session_state.library_history.append(
            {"role": "user", "content": user_msg}
        )

        # 시스템 프롬프트에 규정 넣기
        messages_for_api = [
            {
                "role": "system",
                "content": (
                    "너는 국립부경대학교 도서관 안내 챗봇이다. "
                    "아래 규정집 내용만을 기반으로 답변해라. "
                    "규정에 없는 내용은 모른다고 답해라.\n\n"
                    f"도서관 규정:\n{LIBRARY_RULES}"
                ),
            }
        ] + st.session_state.library_history

        with st.spinner("도서관 규정을 바탕으로 답변 생성 중..."):
            resp = client.responses.create(
                model="gpt-5-mini",
                input=messages_for_api,
            )
            bot_reply = resp.output[0].content[0].text

        st.session_state.library_history.append(
            {"role": "assistant", "content": bot_reply}
        )

        with lib_container:
            st.markdown(f"**👤 사용자:** {user_msg}")
            st.markdown(f"**📚 도서관 챗봇:** {bot_reply}")
