import streamlit as st
import os
import glob

# Set up page
st.set_page_config(page_title="Privacy Policy Explorer", layout="centered")

st.title("Researchers Privacy Policy Explorer")
st.write("Select a company to view its most recent privacy policy (.txt) file.")

POLICY_ROOT_DIR = "transparency_hub_documents"

# --------------------------------------------------------------------
# Get list of companies
# --------------------------------------------------------------------
def get_available_companies():
    return sorted([
        name for name in os.listdir(POLICY_ROOT_DIR)
        if os.path.isdir(os.path.join(POLICY_ROOT_DIR, name, "privacy"))
    ])

# --------------------------------------------------------------------
# Get most recent .txt file in privacy/ folder for a company
# --------------------------------------------------------------------
def get_latest_txt_file(company):
    privacy_dir = os.path.join(POLICY_ROOT_DIR, company, "privacy")
    txt_files = glob.glob(os.path.join(privacy_dir, "*.txt"))
    if not txt_files:
        return None
    return sorted(txt_files, key=os.path.getmtime, reverse=True)[0]

# --------------------------------------------------------------------
# Read a file and clean up excessive blank lines
# --------------------------------------------------------------------
def read_file_contents(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Remove lines that are entirely blank (more than one newline)
        cleaned = []
        last_line_blank = False
        for line in lines:
            if line.strip() == "":
                if not last_line_blank:
                    cleaned.append("\n")
                    last_line_blank = True
            else:
                cleaned.append(line)
                last_line_blank = False
        return "".join(cleaned)
    except Exception as e:
        return f"Error reading file: {e}"

# --------------------------------------------------------------------
# Main App
# --------------------------------------------------------------------
companies = get_available_companies()
selected_company = st.selectbox("Choose a company:", companies)

if selected_company:
    latest_file = get_latest_txt_file(selected_company)

    if latest_file:
        filename = os.path.basename(latest_file)
        st.markdown(f"**Most recent .txt file:** `{filename}`")
        content = read_file_contents(latest_file)
        st.text_area("📄 Policy Text", content, height=400)
    else:
        st.warning(f"No .txt privacy files found for {selected_company}.")
