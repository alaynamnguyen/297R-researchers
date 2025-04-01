import streamlit as st
from backend import (
    create_or_load_vectorstore,
    get_retrieval_chain,
    answer_question,
    verify_answer_with_sources,
    summarize_policy_file,
    map_policy_to_regulations
)

def main():
    st.title("Privacy Policy Chatbot Demo")
    st.write("A simple LLM-based assistant for privacy policy researchers.")

    # Build/load vectorstore
    st.sidebar.title("Settings")
    policies_dir = st.sidebar.text_input("Policies Directory", value="privacy_policies")
    if st.sidebar.button("Initialize Vector Store"):
        st.session_state.vectorstore = create_or_load_vectorstore(policies_dir)
        st.success("Vector store initialized or reloaded!")
    
    # If vector store is not in session, create it by default
    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = create_or_load_vectorstore(policies_dir)

    # Chat Interface
    query = st.text_input("Ask a question about the policies:", value="")
    if st.button("Ask"):
        qa_chain = get_retrieval_chain(st.session_state.vectorstore)
        result = answer_question(query, qa_chain)
        st.write("**Answer:**", result["answer"])
        st.write("**Sources:**", result["sources"])

        # Example verification step
        # For demonstration, we won't do anything with the result's source docs
        # except display the placeholder verification:
        is_verified = verify_answer_with_sources(result["answer"], [])
        st.write(f"**Verification**: {is_verified}")

        # Simple regulation mapping demonstration
        regs = map_policy_to_regulations(result["answer"])
        if regs:
            st.write("**Potentially relevant regulations**:", regs)
        else:
            st.write("No specific regulation matches found.")
    
    # Summarize a specific policy
    st.subheader("Summarize a Policy")
    policy_file = st.text_input("Policy filename to summarize (in directory)", value="policy1.txt")
    if st.button("Summarize Policy"):
        summary = summarize_policy_file(f"{policies_dir}/{policy_file}")
        st.write("**Summary:**")
        st.write(summary)

if __name__ == "__main__":
    main()
