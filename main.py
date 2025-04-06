import streamlit as st
import os
import glob
from datetime import datetime
from streamlit.components.v1 import html

from utils import (
    get_available_companies,
    get_latest_txt_file,
    read_file_contents
)
from backend import (
    create_or_load_vectorstore,
    get_retrieval_chain,
    answer_question,
    summarize_policy
)

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Set up page
st.set_page_config(page_title="Privacy Policy Explorer", layout="wide")

st.title("🕵️ Researchers Privacy Policy Explorer")
st.write("Select a company to view its most recent privacy policy (.txt) file and ask questions about it.")

# --------------------------------------------------------------------
# Main App
# --------------------------------------------------------------------
companies = get_available_companies()
selected_company = st.selectbox("Choose a company:", companies)

if selected_company:
    latest_file = get_latest_txt_file(selected_company)

    if latest_file:
        filename = os.path.basename(latest_file)
        content = read_file_contents(latest_file)

        col1, col2 = st.columns([1.5, 1])

        with col1:
            st.markdown(f"**Most recent .txt file:** `{filename}`")
            st.text_area("📄 Policy Text", content, height=600, key="policy_display")

        with col2:
            st.subheader("💬 Ask a Question")
            user_question = st.text_input("Type your question here:")

            button_col1, button_col2 = st.columns([1, 1])
            with button_col1:
                ask_clicked = st.button("Ask", use_container_width=True)
            with button_col2:
                summarize_clicked = st.button("Summarize", use_container_width=True)

            if ask_clicked and user_question:
                try:
                    with st.spinner("Thinking..."):
                        vectorstore = create_or_load_vectorstore(content, filename)
                        qa_chain = get_retrieval_chain(vectorstore)
                        result = answer_question(user_question, qa_chain)

                    st.session_state.chat_history.append({
                        "type": "qa",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "question": user_question,
                        "answer": result["answer"],
                        "sources": result["sources"]
                    })

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            if summarize_clicked:
                try:
                    with st.spinner("Summarizing policy..."):
                        summary = summarize_policy(content)
                    st.session_state.chat_history.append({
                        "type": "summary",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "question": "Summarize this policy",
                        "answer": summary,
                        "sources": []
                    })
                except Exception as e:
                    st.error(f"❌ Error while summarizing: {str(e)}")

            # Scrollable chat history (newest first)
            with st.expander("📜 Chat History", expanded=True):
                for i, entry in reversed(list(enumerate(st.session_state.chat_history))):
                    st.markdown(f"**🕒 {entry['timestamp']}**")
                    st.markdown(f"**You asked:** {entry['question']}")
                    st.success(f"{entry['answer']}")
                    
                    # Highlight sources in the policy if any
                    if entry["sources"]:
                        st.caption("📌 Cited Chunks:")
                        for chunk in entry["sources"]:
                            highlighted = content.replace(chunk, f'<mark>{chunk}</mark>')
                            st.markdown(f"<div style='border: 1px solid #ddd; padding: 8px; background: #fefbd8;'>{highlighted}</div>", unsafe_allow_html=True)
                    
                    st.divider()

    else:
        st.warning(f"No .txt privacy files found for {selected_company}.")
