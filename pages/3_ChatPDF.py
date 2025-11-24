import streamlit as st
from openai import OpenAI

# -------------------------------
# 4. ChatPDF 페이지
# -------------------------------

st.title("4. ChatPDF - PDF로 대화하기")

# --- API Key 처리 (다른 페이지와 동일한 방식) ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.text_input(
    "OpenAI API Key를 입력하세요 (필요시 다시 입력)",
    type="password",
    value=st.session_state.api_key,
)

if api_key_input and api_key_input != st.session_state.api_key:
    st.session_state.api_key = api_key_input

if not st.session_state.api_key:
    st.warning("먼저 API Key를 입력하세요.")
    st.stop()

client = OpenAI(api_key=st.session_state.api_key)

# --- Vector Store & 상태 변수들 ---
if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = None

if "uploaded_pdf_name" not in st.session_state:
    st.session_state.uploaded_pdf_name = None

if "pdf_chat_history" not in st.session_state:
    # [{"role": "user"/"assistant", "content": "..."}...]
    st.session_state.pdf_chat_history = []

# -------------------------------
# 1) PDF 업로드 영역 (항상 맨 위에 보이도록)
# -------------------------------
st.markdown("### 1) PDF 파일 업로드")

uploaded_file = st.file_uploader(
    "분석할 PDF 파일을 업로드하세요 (한 개만)",
    type=["pdf"],
)

col1, col2 = st.columns(2)
with col1:
    create_vs = st.button("📥 Vector Store 생성/갱신", use_container_width=True)
with col2:
    clear_vs = st.button("🧹 Vector Store 삭제", use_container_width=True)

# --- Vector Store 생성/갱신 ---
if create_vs:
    if not uploaded_file:
        st.warning("먼저 PDF 파일을 업로드하세요.")
    else:
        with st.spinner("Vector Store 생성 중... (PDF 임베딩 중입니다)"):
            # 새 Vector Store 생성
            vs = client.vector_stores.create(name="chatpdf_vector_store")

            # 업로드한 PDF를 Vector Store에 등록
            file_batch = client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vs.id,
                files=[uploaded_file],
            )

            st.session_state.vector_store_id = vs.id
            st.session_state.uploaded_pdf_name = uploaded_file.name
            st.session_state.pdf_chat_history = []  # 새 파일이면 대화도 초기화

        st.success(f"Vector Store 생성 완료! (파일: {uploaded_file.name})")

# --- Vector Store 삭제 ---
if clear_vs and st.session_state.vector_store_id is not None:
    with st.spinner("Vector Store 삭제 중..."):
        client.vector_stores.delete(st.session_state.vector_store_id)

    st.session_state.vector_store_id = None
    st.session_state.uploaded_pdf_name = None
    st.session_state.pdf_chat_history = []

    st.success("Vector Store가 삭제되었습니다.")

# --- 현재 상태 표시 ---
if st.session_state.vector_store_id:
    st.info(
        f"📄 현재 Vector Store 사용 중\n\n"
        f"- ID: `{st.session_state.vector_store_id}`\n"
        f"- 파일 이름: **{st.session_state.uploaded_pdf_name}**"
    )
else:
    st.info("현재 활성화된 Vector Store가 없습니다. PDF를 업로드하고 'Vector Store 생성/갱신' 버튼을 눌러주세요.")

st.markdown("---")

# -------------------------------
# 2) PDF 기반 질의응답 (챗봇 UI)
# -------------------------------
st.markdown("### 2) PDF 내용으로 질의응답")

# 이전 대화 보여주기
for msg in st.session_state.pdf_chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 채팅 입력창 (항상 맨 아래)
user_q = st.chat_input("업로드한 PDF 내용에 대해 궁금한 것을 질문해 보세요.")

if user_q:
    if not st.session_state.vector_store_id:
        st.warning("먼저 PDF를 업로드하고 Vector Store를 생성하세요.")
    else:
        # 유저 메시지 저장/표시
        st.session_state.pdf_chat_history.append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.write(user_q)

        with st.chat_message("assistant"):
            with st.spinner("PDF 내용을 검색하고 답변 작성 중..."):
                response = client.responses.create(
                    model="gpt-5-mini",
                    input=[
                        {
                            "role": "system",
                            "content": (
                                "너는 업로드된 PDF 파일의 내용을 바탕으로만 답변하는 어시스턴트다. "
                                "모르겠거나 PDF에 없는 내용이면 모른다고 말해."
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
                            "vector_store_ids": [st.session_state.vector_store_id],
                            "max_num_results": 10,
                        }
                    ],
                )

                answer = response.output_text
                st.write(answer)

        st.session_state.pdf_chat_history.append(
            {"r
