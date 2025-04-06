import os
import glob

POLICY_ROOT_DIR = "transparency_hub_documents"

def get_available_companies():
    return sorted([
        name for name in os.listdir(POLICY_ROOT_DIR)
        if os.path.isdir(os.path.join(POLICY_ROOT_DIR, name, "privacy"))
    ])

def get_latest_txt_file(company):
    privacy_dir = os.path.join(POLICY_ROOT_DIR, company, "privacy")
    txt_files = glob.glob(os.path.join(privacy_dir, "*.txt"))
    if not txt_files:
        return None
    return sorted(txt_files, key=os.path.getmtime, reverse=True)[0]

def read_file_contents(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
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
