import streamlit as st
from pdf2image import convert_from_bytes
from io import BytesIO
import zipfile
import base64
import random
import itertools


st.set_page_config(page_title="PDF to PNG Converter", layout="wide")

# Light pastel background colors (safe & readable)
LIGHT_COLORS = [
    "rgba(250, 245, 222, 0.5)",
    "rgba(243, 241, 248, 0.5)",
    "rgba(247, 248, 234, 0.5)",
    "rgba(239, 244, 241, 0.5)",
    "rgba(245, 237, 243, 0.5)",    
]


# --- Page Header ---
st.markdown("""
    <style>
        .page-title { font-size: 2.4rem; font-weight: 700; margin-bottom: 0.5rem; }
        .subtle { color: gray; font-size: 0.9rem; }
        .preview-icon { font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='page-title'>📄 PDF to PNG Converter</div>", unsafe_allow_html=True)
st.markdown("<div class='subtle'>Convert and selectively download PDF pages as PNG images.</div>", unsafe_allow_html=True)


# --- Mode Toggle ---
st.text("")
with st.container(border=True):
    mode = st.radio("$ \\large \\textrm {\\color{#F94C10} Processing Mode} $", ["Single PDF", "Multiple PDFs"], horizontal=True)

# --- File Upload ---
with st.container(border=True):
    if mode == "Single PDF":
        uploaded_files = st.file_uploader("$ \\large \\textrm {\\color{#F94C10} Upload a PDF file} $", type="pdf")
        if uploaded_files:
            uploaded_files = [uploaded_files]
    else:
        uploaded_files = st.file_uploader("$ \\large \\textrm {\\color{#F94C10} Upload multiple PDF files} $", type="pdf", accept_multiple_files=True)

if uploaded_files:
    image_data = []

    with st.spinner("Converting PDF(s) to PNG..."):
        for uploaded_file in uploaded_files:
            images = convert_from_bytes(uploaded_file.read())
            for i, img in enumerate(images):
                img_bytes = BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                size_kb = len(img_bytes.getvalue()) // 1024

                base64_img = base64.b64encode(img_bytes.getvalue()).decode()
                preview_url = f"data:image/png;base64,{base64_img}"

                image_data.append({
                    "pdf_name": uploaded_file.name,
                    "index": i + 1,
                    "filename": f"{uploaded_file.name.replace('.pdf', '')}_page_{i + 1}.png",
                    "bytes": img_bytes,
                    "size_kb": size_kb,
                    "preview_url": preview_url
                })

    st.success(f"✅ Converted {len(uploaded_files)} PDF(s), {len(image_data)} pages extracted.")

    
    with st.container(border=True):
        st.markdown("$ \\large \\textrm {\\color{#F94C10} Select Pages to Download}$")

        # --- Select All / Deselect All ---
        all_selected = st.checkbox("Select/Deselect - All Pages", value=True, key="select_all_toggle")

        selected_pages = []

        # --- Table Header ---
        header_cols = st.columns([1, 4, 3, 2, 1])
        header_cols[0].markdown("**Select**")
        header_cols[1].markdown("**Filename**")
        header_cols[2].markdown("**Source PDF**")
        header_cols[3].markdown("**Size (KB)**")
        header_cols[4].markdown("**Preview**")

        # Shuffle color palette so it varies each time
        random.shuffle(LIGHT_COLORS)
        color_cycle = itertools.cycle(LIGHT_COLORS)

        # Assign light colors to each unique PDF
        pdf_color_map = {}
        for item in image_data:
            if item['pdf_name'] not in pdf_color_map:
                pdf_color_map[item['pdf_name']] = next(color_cycle)

        # --- Page Rows with colored background ---
        for idx, item in enumerate(image_data):
            bg_color = pdf_color_map[item['pdf_name']]
            row_style = f"background-color: {bg_color}; padding: 0.5rem; border-radius: 6px;"

            with st.container():
                cols = st.columns([1, 4, 3, 2, 1])
                with cols[0]:
                    is_selected = st.checkbox("", value=all_selected, key=f"sel_{idx}")
                with cols[1]:
                    st.markdown(
                        f"<div style='{row_style}'>{item['filename']}</div>",
                        unsafe_allow_html=True
                    )
                with cols[2]:
                    st.markdown(
                        f"<div style='{row_style}'><small>{item['pdf_name']}</small></div>",
                        unsafe_allow_html=True
                    )
                with cols[3]:
                    st.markdown(f"<div style='{row_style}'>{item['size_kb']} KB</div>", unsafe_allow_html=True)
                with cols[4]:
                    st.markdown(
                        f"<div style='{row_style}'><a href='{item['preview_url']}' target='_blank'>🔍</a></div>",
                        unsafe_allow_html=True
                    )

                if is_selected:
                    selected_pages.append(item)



        # --- ZIP Download ---
        if selected_pages:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for item in selected_pages:
                    item["bytes"].seek(0)
                    zip_file.writestr(item["filename"], item["bytes"].read())
            zip_buffer.seek(0)

            st.download_button(
                label=f"📦 Download {len(selected_pages)} Selected Page(s) as ZIP",
                data=zip_buffer,
                file_name="selected_pages.zip",
                mime="application/zip"
            )
        else:
            st.info("Select at least one page to enable ZIP download.")
