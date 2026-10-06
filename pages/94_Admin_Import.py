"""
Admin Question Bank Import Page (Phase 12).
Implements the complete Word (.docx) question bank import workflow:
1. Upload .docx file
2. Parse document with tolerant python-docx extractor
3. Detect questions, options A-D, answers, and explanations
4. Validation & error reporting (does not silently lose data)
5. Interactive preview & Level Review (Admin sets Final Level)
6. Safe batch insertion (imported questions default to 'Draft', never published automatically)
7. Audit record stored in import_history
Protected by require_admin_auth().
"""

from pathlib import Path
import streamlit as st
import pandas as pd
from config.settings import APP_NAME
from services.admin_service import require_admin_auth, get_active_admin_session
from services.import_service import execute_import_batch, fetch_import_history_logs
from utils.docx_parser import parse_docx_content
from utils.excel_parser import parse_excel_content, generate_excel_import_template
from utils.security import sanitize_filename, validate_uploaded_file
from components.navigation import inject_custom_navigation_css, render_admin_header
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Import Question Bank — {APP_NAME}",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enforce Route Guard & Navigation separation
inject_custom_navigation_css()
inject_global_ui_styles()
require_admin_auth()

admin_session = get_active_admin_session()
admin_name = admin_session.get("username", "admin") if admin_session else "admin"

render_admin_header(
    title="Import Question Bank",
    subtitle="Automated Ingestion, Parsing & Validation from Word (.docx) and Excel (.xlsx) Workbooks",
)

# --------------------------------------------------------
# 1. IMPORT PARAMETERS CONFIGURATION
# --------------------------------------------------------
st.markdown("### Step 1: Configure Import Parameters")

col_cat, col_status = st.columns(2)
with col_cat:
    target_category = st.selectbox(
        "Assign Target / Default Category *",
        options=["Grammar", "Reading", "Listening"],
        index=0,
        help="Default category applied if not specified per row in the uploaded file.",
    )
with col_status:
    import_status = st.selectbox(
        "Default Initial Status *",
        options=["Draft", "Active"],
        index=0,
        help="Draft status is recommended. Imported questions require admin review before active test publishing.",
    )

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------------
# 2. FILE UPLOAD & PARSING
# --------------------------------------------------------
st.markdown("### Step 2: Upload Document (.docx or .xlsx)")

up_col1, up_col2 = st.columns([3, 1.2])
with up_col1:
    uploaded_file = st.file_uploader(
        "Choose a .docx or .xlsx file containing question items:",
        type=["docx", "xlsx"],
        key="admin_file_uploader",
        help="Supports formatted Word documents or Excel workbooks (with Reading passages and Listening audio links).",
    )
with up_col2:
    st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
    sample_candidates = [
        Path("data/contoh_soal_berbasis_skill.xlsx"),
        Path(__file__).resolve().parent.parent / "data" / "contoh_soal_berbasis_skill.xlsx",
    ]
    sample_file_path = next((p for p in sample_candidates if p.exists()), None)
    if sample_file_path:
        with open(sample_file_path, "rb") as f:
            sample_bytes = f.read()
        st.download_button(
            label="📗 Download Contoh Soal (.xlsx)",
            data=sample_bytes,
            file_name="contoh_soal_berbasis_skill.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Download file Excel berisi kumpulan contoh soal Grammar, Reading, dan Listening berbasis Skill.",
        )
    
    template_data = generate_excel_import_template()
    st.download_button(
        label="📑 Download Template Kosong (.xlsx)",
        data=template_data,
        file_name="question_bank_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        help="Download template kosong Excel dengan kolom skill_number dan question_order.",
    )

if uploaded_file is not None:
    # Reset parsed data if a new file is uploaded
    if "last_imported_file" not in st.session_state or st.session_state.last_imported_file != uploaded_file.name:
        st.session_state.last_imported_file = uploaded_file.name
        st.session_state.active_import_filename = uploaded_file.name
        st.session_state.parsed_data = None

    c_parse, _ = st.columns([1.5, 3])
    with c_parse:
        if st.button("Parse Document Now", type="primary", use_container_width=True):
            clean_filename = sanitize_filename(uploaded_file.name)
            file_bytes = uploaded_file.getvalue()

            is_valid_file, sec_err = validate_uploaded_file(clean_filename, file_bytes)
            if not is_valid_file:
                st.error(f"⛔ Security Rejection: {sec_err}")
                st.stop()

            with st.spinner("Extracting content and validating schema..."):
                try:
                    if clean_filename.lower().endswith(".xlsx"):
                        parsed_result = parse_excel_content(file_bytes, default_category=target_category)
                    else:
                        parsed_result = parse_docx_content(file_bytes)

                    parsed_result["file_name"] = clean_filename
                    st.session_state.active_import_filename = clean_filename
                    st.session_state.parsed_data = parsed_result
                    st.toast("Document parsing completed successfully!", icon="✅")
                except Exception as e:
                    st.error(f"❌ Failed to parse document: {str(e)}")

# --------------------------------------------------------
# 3. PARSING RESULTS, VALIDATION & LEVEL REVIEW
# --------------------------------------------------------
parsed = st.session_state.get("parsed_data")

if parsed:
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("###  Step 3: Parsing Summary & Validation Metrics")

    m_tot, m_val, m_inv, m_top = st.columns(4)
    with m_tot:
        st.metric(label="Total Questions Detected", value=parsed["total_detected"])
    with m_val:
        st.metric(label="Valid Questions", value=parsed["valid_count"])
    with m_inv:
        st.metric(label="Questions Requiring Review", value=parsed["invalid_count"])
    with m_top:
        st.metric(label="Detected Document Topic", value=parsed.get("global_topic", "General"))

    # Display Invalid Questions with Reasons
    invalid_qs = [q for q in parsed["questions"] if not q["is_valid"]]
    if invalid_qs:
        with st.expander(f"⚠️ Questions Requiring Review ({len(invalid_qs)})", expanded=True):
            st.warning("The following questions have missing elements or formatting discrepancies and will NOT be imported until corrected in the source document.")
            for inv in invalid_qs:
                inv_html = f"""<div style="background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
<strong style="color: #991B1B;">Question {inv.get('question_number', '?')}:</strong> {inv.get('question_text', 'No prompt text')[:80]}...<br>
<span style="color: #B91C1C; font-size: 0.88rem;">❌ <strong>Reason:</strong> {', '.join(inv['validation_errors'])}</span>
</div>"""
                st.markdown(inv_html, unsafe_allow_html=True)

    # Valid Questions Preview & Confirmation
    valid_qs = [q for q in parsed["questions"] if q["is_valid"]]
    if valid_qs:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🔍 Step 4: Preview Soal Valid & Konfirmasi Import")
        st.write("Periksa pratinjau soal valid di bawah ini sebelum menyimpan ke Question Bank:")

        for idx, vq in enumerate(valid_qs):
            q_num = vq.get("question_number", idx + 1)
            item_cat = vq.get("category", target_category)
            pass_snippet = ""
            if vq.get("passage_text"):
                pass_snippet = f"""<div style="background: #FFFBEB; border-left: 3px solid #D97706; padding: 6px 12px; border-radius: 4px; font-size: 0.83rem; color: #92400E; margin: 6px 0;">
📜 <strong>Passage:</strong> {vq.get('passage_title', 'Attached')} — <em>{vq.get('passage_text')[:120]}...</em>
</div>"""

            audio_snippet = ""
            if vq.get("audio_file"):
                dur_str = f" ({vq.get('duration')}s)" if vq.get("duration") else ""
                audio_snippet = f"""<div style="background: #F0FDF4; border-left: 3px solid #16A34A; padding: 6px 12px; border-radius: 4px; font-size: 0.83rem; color: #166534; margin: 6px 0;">
🎧 <strong>Audio Reference:</strong> <code>{vq.get('audio_file')}</code>{dur_str}
</div>"""

            with st.container():
                card_html = f"""<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px 18px; margin-bottom: 10px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
<span style="font-weight: 700; font-size: 1.05rem; color: #1E293B;">
Question {q_num}
<span style="background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; font-weight: 600; padding: 2px 8px; border-radius: 8px; font-size: 0.8rem; margin-left: 8px;">
{item_cat}
</span>
<span style="background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; font-weight: 600; padding: 2px 8px; border-radius: 8px; font-size: 0.8rem; margin-left: 6px;">
Skill {vq.get('skill_number') or 1}: {vq.get('skill_name') or f"Skill {vq.get('skill_number') or 1}"}
</span>
<span style="background: #F3F4F6; color: #374151; font-weight: 600; padding: 2px 8px; border-radius: 8px; font-size: 0.8rem; margin-left: 6px;">
Urutan #{vq.get('question_order') or q_num}
</span>
</span>
</div>
{pass_snippet}
{audio_snippet}
<p style="margin: 6px 0 10px 0; color: #1E293B; font-size: 1rem; font-weight: 500;">{vq.get('question_text', '')}</p>
<div style="font-size: 0.88rem; color: #64748B; margin-bottom: 4px; line-height: 1.5;">
<strong>A:</strong> {vq.get('option_a', '')} &nbsp;|&nbsp; 
<strong>B:</strong> {vq.get('option_b', '')} &nbsp;|&nbsp; 
<strong>C:</strong> {vq.get('option_c', '')} &nbsp;|&nbsp; 
<strong>D:</strong> {vq.get('option_d', '')} &nbsp;|&nbsp; 
<strong style="color: #059669;">Answer: {vq.get('correct_answer', '')}</strong>
</div>
</div>"""
                st.markdown(card_html, unsafe_allow_html=True)

                # Direct browser audio upload for Listening items
                if item_cat == "Listening":
                    up_aud = st.file_uploader(
                        f"🎧 Upload Audio (.mp3 / .wav) untuk Question {q_num}:",
                        type=["mp3", "wav"],
                        key=f"audio_upload_q_{idx}",
                        help=f"Unggah berkas audio rekaman dari komputer untuk Soal #{q_num}",
                    )
                    if up_aud is not None:
                        vq["uploaded_audio_bytes"] = up_aud.getvalue()
                        vq["uploaded_audio_name"] = up_aud.name
                        st.audio(up_aud)
                    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

        # Batch Import Action
        st.markdown("<br>", unsafe_allow_html=True)
        c_import, _ = st.columns([2, 2])
        with c_import:
            import_button_label = f"📥 Import {len(valid_qs)} Soal Valid ke Question Bank"
            if st.button(import_button_label, type="primary", use_container_width=True):
                with st.spinner("Writing questions to database and logging import batch..."):
                    resolved_file_name = (
                        uploaded_file.name
                        if uploaded_file is not None
                        else st.session_state.get("active_import_filename")
                        or (parsed.get("file_name") if isinstance(parsed, dict) else None)
                        or st.session_state.get("last_imported_file")
                        or "imported_batch.xlsx"
                    )

                    detected, imported, failed = execute_import_batch(
                        file_name=sanitize_filename(resolved_file_name),
                        questions=valid_qs,
                        category_name=target_category,
                        default_status=import_status,
                        imported_by=admin_name,
                    )
                    st.success(
                        f"""
                        🎉 **Import Batch Complete!**
                        - Category: **{target_category}**
                        - Total Valid Imported: **{imported}** questions
                        - Initial Status: **{import_status}**
                        """
                    )
                    st.session_state.parsed_data = None
                    st.session_state.active_import_filename = None
                    st.rerun()

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 4. AUDIT TRAIL: RECENT IMPORT BATCH HISTORY
# --------------------------------------------------------
with st.expander("📜 View Import Batch Audit History", expanded=False):
    logs = fetch_import_history_logs(limit=25)
    if not logs:
        st.info("No prior import batch executions recorded.")
    else:
        log_rows = []
        for l in logs:
            log_rows.append({
                "Batch ID": l.id,
                "File Name": l.file_name,
                "Category": l.category,
                "Detected": l.total_detected,
                "Imported": l.total_imported,
                "Failed": l.total_failed,
                "Imported By": l.imported_by,
                "Timestamp": l.imported_at[:19] if l.imported_at else "-",
            })
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)

# Navigation Buttons
c_dash, c_qbank, _ = st.columns([1.5, 1.5, 3])
with c_dash:
    if st.button("📊 Back to Dashboard", use_container_width=True):
        st.switch_page("pages/91_Admin_Dashboard.py")
with c_qbank:
    if st.button("📚 View Question Bank", use_container_width=True):
        st.switch_page("pages/93_Admin_Question_Bank.py")
