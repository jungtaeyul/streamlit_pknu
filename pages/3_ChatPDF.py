import streamlit as st
from openai import OpenAI

st.title("4. ChatPDF - 업로드한 PDF로 질의응답")

# --- session_state 기본값 ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "pdf_vector_store_id" not in st.session_state:
    st.session_state.pdf_vector_store_id = None
if "pdf_file_name" not in st.session_state:
    st.session_state.pdf_file_name = None

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

st.write("PDF 파일을 업로드하면, 해당 내용으로 질의응답을 할 수 있습니다.")

# PDF 업로더
uploaded_file = st.file_uploader(
    "PDF 파일 하나를 업로드하세요",
    type=["pdf"],
    accept_multiple_files=False,
)

col1, col2 = st.columns(2)

with col1:
    if st.button("PDF 업로드 & 인덱싱"):
        if uploaded_file is None:
            st.warning("먼저 PDF 파일을 선택해 주세요.")
        else:
            with st.spinner("Vector store 생성 및 파일 업로드 중..."):
                # 1) vector store 생성
                vs = client.beta.vector_stores.create(
                    name=f"chatpdf-{uploaded_file.name}"
                )
                # 2) 파일 업로드 + vector store에 연결
                file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vs.id,
                    files=[uploaded_file],
                )
                st.session_state.pdf_vector_store_id = vs.id
                st.session_state.pdf_file_name = uploaded_file.name

            st.success(f"Vector store 생성 완료! (파일: {uploaded_file.name})")

with col2:
    if st.button("Clear (Vector store 삭제)"):
        vs_id = st.session_state.pdf_vector_store_id
        if vs_id:
            with st.spinner("Vector store 삭제 중..."):
                try:
                    client.beta.vector_stores.delete(vector_store_id=vs_id)
                except Exception:
                    pass
            st.session_state.pdf_vector_store_id = None
            st.session_state.pdf_file_name = None
            st.success("Vector store 및 상태가 초기화되었습니다.")
        else:
            st.info("삭제할 Vector store가 없습니다.")

# 현재 상태 표시
if st.session_state.pdf_vector_store_id:
    st.info(
        f"현재 사용 중인 PDF: **{st.session_state.pdf_file_name}** "
        f"(vector_store_id: {st.session_state.pdf_vector_store_id})"
    )
else:
    st.warning("현재 활성화된 PDF / Vector store가 없습니다.")

st.markdown("---")

question = st.text_input(
    "업로드한 PDF 내용에 대해 질문해 보세요.",
    placeholder="예: 이 논문의 주요 아이디어를 요약해 줘.",
)

if st.button("PDF에 질문하기"):
    if not question.strip():
        st.warning("질문을 입력해 주세요.")
    elif not st.session_state.pdf_vector_store_id:
        st.error("먼저 PDF를 업로드하고 인덱싱을 해 주세요.")
    else:
        vs_id = st.session_state.pdf_vector_store_id
        with st.spinner("PDF를 검색하여 답변 생성 중..."):
            resp = client.responses.create(
                model="gpt-5-mini",
                input=question,
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vs_id],
                    }
                },
            )
            answer = resp.output_text
        st.subheader("PDF 기반 답변")
        st.write(answer)
