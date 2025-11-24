import streamlit as st
from openai import OpenAI

# 4. ChatPDF 페이지

st.title("4. ChatPDF - PDF로 대화하기")

# --- API Key 입력 및 저장 ---
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

api_key_input = st.text_input(
    "OpenAI API Key를 입력하세요 (필요시 다시 입력)",
    type="password",
    value=st.session_state["api_key"],
)

if api_key_input and api_key_input != st.session_state["api_key"]:
    st.session_state["api_key"] = api_key_input

if not st.session_state["api_key"]:
    st.warning("먼저 API Key를 입력하세요.")
    st.stop()

client = OpenAI(api_key=st.session_state["api_key"])

# --- 상태 변수 초기화 ---
if "vector_store_id" not in st.session_state:
    st.session_state["vector_store_id"] = None

if "uploaded_pdf_name" not in st.session_state:
    st.session_state["uploaded_pdf_name"] = None

if "pdf_chat_history" not in st.session_state:
    # [{"role": "user" or "assistant", "content": "..."}]
    st.session_state["pdf_chat_history"] = []

# ============================
# 1) PDF 업로드 영역
# ============================

st.subheader("1) PDF 파일 업로드")

uploaded_file = st.file_uploader(
    "분석할 PDF 파일을 업로드하세요 (한 개만 선택)",
    type=["pdf"],
)

col1, col2 = st.columns(2)
with col1:
    create_vs = st.button("Vector Store 생성/갱신")
with col2:
    clear_vs = st.button("Vector Store 삭제")

# --- Vector Store 생성/갱신 ---
if create_vs:
    if uploaded_file is None:
        st.warning("먼저 PDF 파일을 업로드하세요.")
    else:
        with st.spinner("Vector Store 생성 및 PDF 임베딩 중..."):
            # 새 Vector Store 생성
            vs = client.vector_stores.create(name="chatpdf_vector_store")

            # 업로드한 PDF 파일을 Vector Store에 추가
            file_batch = client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vs.id,
                files=[uploaded_file],
            )

            st.session_state["vector_store_id"] = vs.id
            st.session_state["uploaded_pdf_name"] = uploaded_file.name
            st.session_state["pdf_chat_history"] = []  # 새 파일이면 대화 초기화

        st.success("Vector Store 생성 완료! (파일: " + uploaded_file.name + ")")

# --- Vector Store 삭제 ---
if clear_vs and st.session_state["vector_store_id"] is not None:
    with st.spinner("Vector Store 삭제 중..."):
        client.vector_stores.delete(st.session_state["vector_store_id"])

    st.session_state["vector_store_id"] = None
    st.session_state["uploaded_pdf_name"] = None
    st.session_state["pdf_chat_history"] = []

    st.success("Vector Store가 삭제되었습니다.")

# --- 현재 상태 표시 ---
if st.session_state["vector_store_id"] is not None:
    st.info(
        "현재 Vector Store가 활성화되어 있습니다.\n"
        + "- ID: " + st.session_state["vector_store_id"] + "\n"
        + "- 파일 이름: " + str(st.session_state["uploaded_pdf_name"])
    )
else:
    st.info("현재 활성화된 Vector Store가 없습니다.\nPDF를 업로드하고 'Vector Store 생성/갱신' 버튼을 눌러주세요.")

st.markdown("---")

# ============================
# 2) PDF 기반 질의응답 (챗봇)
# ============================

st.subheader("2) PDF 내용으로 질의응답")

# 지금까지 대화 내용 출력
for msg in st.session_state["pdf_chat_history"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 사용자 질문 입력
user_q = st.chat_input("업로드된 PDF 내용에 대해 궁금한 점을 질문해 보세요.")

if user_q:
    if st.session_state["vector_store_id"] is None:
        st.warning("먼저 PDF를 업로드하고 Vector Store를 생성하세요.")
    else:
        # 사용자 메시지 저장 및 출력
        st.session_state["pdf_chat_history"].append(
            {"role": "user", "content": user_q}
        )
        with st.chat_message("user"):
            st.write(user_q)

        # OpenAI Responses API + File Search 호출
        with st.chat_message("assistant"):
            with st.spinner("PDF 내용을 검색하고 답변 생성 중..."):
                response = client.responses.create(
                    model="gpt-5-mini",
                    input=[
                        {
                            "role": "system",
                            "content": (
                                "너는 업로드된 PDF 파일의 내용만을 바탕으로 답변하는 도우미이다. "
                                "PDF에 없는 내용이면 모른다고 대답해라."
                            ),
                        },
                        {
                            "role": "user",
                            "content": user_q,
                        },
                    ],
                    tools=[
                        {
                            "type": "file_search",
                            "vector_store_ids": [st.session_state["vector_store_id"]],
                            "max_num_results": 10,
                        }
                    ],
                )

                answer = response.output_text
                st.write(answer)

        st.session_state["pdf_chat_history"].append(
            {"role": "assistant", "content": answer}
        )
