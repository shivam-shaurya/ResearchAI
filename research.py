import streamlit as st
import pandas as pd
import PyPDF2
import time
from collections import defaultdict
from textblob import TextBlob
import re
import hashlib

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

# Enhanced keyword-based filtering for relevant extraction
def extract_data(text, data_type):
    keyword_mapping = {
        "Key findings": ["result", "finding", "conclude", "study shows", "evidence", "reveals"],
        "Research gaps": ["gap", "lack", "not explored", "unaddressed", "unanswered question"],
        "Methodology": ["method", "approach", "experiment", "procedure", "technique", "framework"],
        "Limitations": ["limitation", "challenge", "shortcoming", "issue", "constraint"],
        "Future work": ["future", "further research", "next step", "potential research", "ongoing study"],
        "Contributions": ["contribution", "novelty", "impact", "advancement", "significance"],
        "Practical implications": ["real-world", "application", "practical use", "industry impact", "commercial potential"],
        "Custom data": []
    }
    
    keywords = keyword_mapping.get(data_type, [])
    if not keywords:
        return "No relevant data found."
    
    blob = TextBlob(text)
    sentences = [str(sentence) for sentence in blob.sentences]
    
    extracted_sentences = [sent for sent in sentences if any(re.search(rf"\b{k}\b", sent, re.IGNORECASE) for k in keywords)]
    
    return extracted_sentences[:5] if extracted_sentences else ["No relevant data found."]

# Streamlit UI Enhancements
st.set_page_config(page_title="PDF Research Extractor", layout="wide")
st.sidebar.title("Uploaded PDFs")

# Sidebar showing uploaded PDFs
uploaded_files = st.sidebar.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
if uploaded_files:
    for file in uploaded_files:
        st.sidebar.write(f"📄 {file.name}")

# Main UI Header
st.title("Research Paper Parser 📑")
st.markdown("### A tool to help PhD students & researchers extract key insights from research papers.")

data_types = [
    "Key findings", "Research gaps", "Methodology", "Limitations",
    "Future work", "Contributions", "Practical implications", "Custom data"
]
selected_data_types = st.multiselect("Select data types to extract", data_types)

if st.button("Start Extraction", key="extract_button") and uploaded_files:
    extracted_data = defaultdict(list)
    progress_bar = st.progress(0)
    
    for i, pdf_file in enumerate(uploaded_files):
        text = extract_text_from_pdf(pdf_file)
        for data_type in selected_data_types:
            extracted_data[data_type].append((pdf_file.name, extract_data(text, data_type)))
        progress_bar.progress((i + 1) / len(uploaded_files))
        time.sleep(0.5)
    
    st.session_state["extracted_data"] = extracted_data
    st.session_state["cart"] = set()
    st.success("Extraction completed!")

if "extracted_data" in st.session_state:
    extracted_data = st.session_state["extracted_data"]
    cart = st.session_state.get("cart", set())
    
    for data_type, results in extracted_data.items():
        with st.expander(f"📌 {data_type}"):
            for file_name, content_list in results:
                st.markdown(f"**{file_name}**")
                for content in content_list:
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    key = f"{file_name}-{data_type}-{content_hash}"
                    if st.checkbox(content, key=key, value=key in cart):
                        cart.add(key)
                    else:
                        cart.discard(key)
    
    # Store updated cart in session state
    st.session_state["cart"] = cart
    
    # Allow downloading selected findings
    if cart:
        selected_data = [key.split("-", 2) for key in cart]
        df_selected = pd.DataFrame(selected_data, columns=["File", "Category", "Extracted Info"])
        csv_selected = df_selected.to_csv(index=False)
        st.download_button(
            label="📥 Download Selected Findings",
            data=csv_selected,
            file_name="selected_findings.csv",
            mime="text/csv",
            key="download_selected_csv_button"
        )
        st.success("Selected findings exported successfully!")
