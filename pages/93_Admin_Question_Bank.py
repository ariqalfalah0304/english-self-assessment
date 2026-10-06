"""
Admin Question Bank Management Page (Phase 11).
Features:
- List questions with pagination and item count
- Keyword search across question text, topics, and explanations
- Multi-dimensional filters: Category, Difficulty, Status, Topic
- View full question details (options, correct answer, explanation, passage, audio)
- Add new question (Grammar, Reading with passage, Listening with audio)
- Edit existing question
- Quick status change: Activate, Deactivate (Inactive), Archive
- Strict input validation preventing creation of invalid questions
Protected by require_admin_auth().
"""

import streamlit as st
import pandas as pd
from config.settings import APP_NAME
from services.admin_service import require_admin_auth
from services.question_service import (
    fetch_questions,
    fetch_question_by_id,
    add_question,
    update_question_record,
    deactivate_question,
    archive_question,
    activate_question,
    fetch_passages_list,
    fetch_distinct_topics_list,
    delete_question_record,
    delete_questions_bulk,
    activate_questions_bulk,
    update_questions_status_bulk,
    fetch_category_question_limits,
    save_category_question_limits,
    fetch_skills_for_category,
    update_skill_passing_grade,
    fetch_distinct_skill_numbers,
    VALID_CATEGORIES,
    VALID_DIFFICULTIES,
    VALID_STATUSES,
    VALID_ANSWERS,
)
from utils.excel_parser import export_questions_to_excel
from components.navigation import inject_custom_navigation_css, render_admin_header
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Question Bank — {APP_NAME}",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply route protection & navigation separation
inject_custom_navigation_css()
inject_global_ui_styles()
require_admin_auth()

# Administrative Header
render_admin_header(
    title="Question Bank Management",
    subtitle="Create, Inspect, Filter, Edit, and Manage Question Statuses",
)

# Top Tabs: 1. Directory & Filters, 2. Question Limits, 3. Add Question, 4. Edit Question
tab_list, tab_settings, tab_add, tab_edit = st.tabs([
    "📋 Question Directory & Search",
    "⚙️ Jumlah Soal Per Kategori",
    "➕ Add New Question",
    "✏️ Edit Selected Question",
])


# ========================================================
# TAB 1: QUESTION DIRECTORY & SEARCH
# ========================================================
with tab_list:
    st.markdown("###  Filter & Search Questions")

    # Filter row
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)

    with f_col1:
        cat_filter = st.selectbox(
            "Category:",
            options=["All"] + VALID_CATEGORIES,
            index=0,
            key="qb_cat_filter",
        )

    with f_col2:
        distinct_skills = fetch_distinct_skill_numbers(category_name=cat_filter if cat_filter != "All" else None)
        max_skill = max(distinct_skills) if distinct_skills else 25
        limit_num = max(max_skill, 25)
        skill_opts = ["All"] + [f"Skill {i}" for i in range(1, limit_num + 1)]
        skill_filter = st.selectbox(
            "Skill:",
            options=skill_opts,
            index=0,
            key="qb_skill_filter",
        )
        selected_skill_num = int(skill_filter.replace("Skill ", "")) if skill_filter != "All" else None

    with f_col3:
        status_filter = st.selectbox(
            "Status:",
            options=["All"] + VALID_STATUSES,
            index=0,
            key="qb_status_filter",
        )

    with f_col4:
        topics_available = fetch_distinct_topics_list()
        topic_filter = st.selectbox(
            "Topic / Subtopic:",
            options=["All"] + topics_available,
            index=0,
            key="qb_topic_filter",
        )

    # Search bar
    s_col1, s_col2 = st.columns([3, 1])
    with s_col1:
        search_query = st.text_input(
            "Search Questions:",
            placeholder="Search by keywords in question text, explanation, or topic...",
            label_visibility="collapsed",
            key="qb_search_input",
        )
    with s_col2:
        if st.button("🔄 Refresh Bank", use_container_width=True, key="qb_refresh_btn"):
            st.rerun()

    # Query questions
    questions = fetch_questions(
        category=cat_filter,
        skill_number=selected_skill_num,
        status=status_filter,
        topic=topic_filter,
        search=search_query,
        limit=500,
    )

    col_cnt, col_exp = st.columns([3, 1])
    with col_cnt:
        st.markdown(f"**Found {len(questions)} matching question(s)**")
    with col_exp:
        if questions:
            excel_bytes = export_questions_to_excel(questions)
            st.download_button(
                label="📥 Export Bank (.xlsx)",
                data=excel_bytes,
                file_name="filtered_question_bank.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="qb_export_excel_btn",
            )

    if not questions:
        st.info("No questions match the current filter and search criteria.")
    else:
        all_q_ids = [q["id"] for q in questions]
        draft_qs = [q for q in questions if q.get("status") == "Draft"]

        # Universal Bulk Actions Bar for all filtered questions
        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 5px solid #3B82F6; border-radius: 8px; padding: 10px 16px; margin: 10px 0 12px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: #1E293B; font-size: 0.95rem;">
                        ⚡ Tindakan Massal untuk Seluruh {len(all_q_ids)} Soal Terfilter
                    </span>
                    <span style="font-size: 0.82rem; color: #64748B;">
                        Dapat digunakan untuk semua status soal (Active, Draft, Inactive, Archived, atau All)
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        b_act, b_deact, b_arch, b_del = st.columns([1.5, 1.5, 1.5, 1.8])

        with b_act:
            btn_act_label = f"🟢 Aktifkan Semua ({len(all_q_ids)})"
            if st.button(btn_act_label, use_container_width=True, key="bulk_act_all_btn", help="Ubah status seluruh soal yang tampil menjadi Active agar langsung siap diujikan"):
                ok, msg = update_questions_status_bulk(all_q_ids, "Active")
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with b_deact:
            if st.button(f"⏸️ Nonaktifkan Semua ({len(all_q_ids)})", use_container_width=True, key="bulk_deact_all_btn", help="Ubah status seluruh soal yang tampil menjadi Inactive"):
                ok, msg = update_questions_status_bulk(all_q_ids, "Inactive")
                if ok:
                    st.warning(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with b_arch:
            if st.button(f"📦 Arsipkan Semua ({len(all_q_ids)})", use_container_width=True, key="bulk_arch_all_btn", help="Ubah status seluruh soal yang tampil menjadi Archived"):
                ok, msg = update_questions_status_bulk(all_q_ids, "Archived")
                if ok:
                    st.info(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with b_del:
            with st.popover(f"🗑️ Hapus Massal ({len(all_q_ids)}) Soal", use_container_width=True):
                st.error(f"⚠️ **Hapus Massal Seluruh {len(all_q_ids)} Soal?**")
                st.write(f"Tindakan ini akan menghapus seluruh **{len(all_q_ids)}** soal yang tampil secara permanen dari database.")
                if st.button("❌ Ya, Konfirmasi Hapus", type="primary", key="btn_confirm_bulk_del_all", use_container_width=True):
                    deleted, _ = delete_questions_bulk(all_q_ids)
                    st.success(f"Berhasil menghapus seluruh {deleted} soal dari database!")
                    st.rerun()

        # Overview Table
        table_rows = []
        for q in questions:
            passage_badge = "📜 Attached" if q["passage_id"] else "-"
            audio_badge = "🎧 Attached" if q["audio_file"] else "-"
            s_label = f"Skill {q['skill_number']}" if q.get("skill_number") else "-"
            table_rows.append({
                "ID": q["id"],
                "Category": q["category_name"],
                "Skill": s_label,
                "Skill Name": q.get("skill_name") or "-",
                "Order": q.get("question_order") or "-",
                "Status": q["status"],
                "Topic": q["subtopic"],
                "Question": q["question_text"][:75] + ("..." if len(q["question_text"]) > 75 else ""),
                "Answer": q["correct_answer"],
                "Passage": passage_badge,
                "Audio": audio_badge,
            })

        df_q = pd.DataFrame(table_rows)
        st.dataframe(df_q, use_container_width=True, hide_index=True)

        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown("### Inspect & Manage Individual Question")

        # Question selector
        q_options = {q["id"]: f"ID #{q['id']} — [{q['category_name']} • Skill {q.get('skill_number') or '-'}] {q['question_text'][:80]}..." for q in questions}
        inspect_id = st.selectbox(
            "Select a question to inspect details or change status:",
            options=list(q_options.keys()),
            format_func=lambda x: q_options[x],
            key="qb_inspect_select",
        )

        if inspect_id:
            q_detail = fetch_question_by_id(inspect_id)
            if q_detail:
                # Color code status
                status_color = {
                    "Active": "#16A34A",
                    "Inactive": "#DC2626",
                    "Draft": "#D97706",
                    "Archived": "#6B7280",
                }.get(q_detail["status"], "#3B82F6")

                detail_card = f"""<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 6px solid {status_color}; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
<div style="display: flex; gap: 8px; margin-bottom: 0.8rem; align-items: center; flex-wrap: wrap;">
<span style="background: #EEF2FF; color: #4338CA; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700;">{q_detail['category_name']}</span>
<span style="background: #EFF6FF; color: #1D4ED8; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700;">Skill {q_detail.get('skill_number') or '-'}: {q_detail.get('skill_name') or 'N/A'}</span>
<span style="background: #F3F4F6; color: #374151; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">Urutan #{q_detail.get('question_order') or '-'}</span>
<span style="background: #FEF3C7; color: #92400E; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">Status: {q_detail['status']}</span>
<span style="color: #64748B; font-size: 0.85rem; margin-left: auto;">Topic: <strong>{q_detail['subtopic']}</strong></span>
</div>
<h4 style="margin: 0.5rem 0 1rem 0; color: #0F172A; font-size: 1.25rem;">{q_detail['question_text']}</h4>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; font-size: 0.95rem; margin-bottom: 1rem;">
<div style="padding: 8px 12px; background: {'#DCFCE7' if q_detail['correct_answer'] == 'A' else '#F8FAFC'}; border: 1px solid #E2E8F0; border-radius: 6px;"><strong>A:</strong> {q_detail['option_a']}</div>
<div style="padding: 8px 12px; background: {'#DCFCE7' if q_detail['correct_answer'] == 'B' else '#F8FAFC'}; border: 1px solid #E2E8F0; border-radius: 6px;"><strong>B:</strong> {q_detail['option_b']}</div>
<div style="padding: 8px 12px; background: {'#DCFCE7' if q_detail['correct_answer'] == 'C' else '#F8FAFC'}; border: 1px solid #E2E8F0; border-radius: 6px;"><strong>C:</strong> {q_detail['option_c']}</div>
<div style="padding: 8px 12px; background: {'#DCFCE7' if q_detail['correct_answer'] == 'D' else '#F8FAFC'}; border: 1px solid #E2E8F0; border-radius: 6px;"><strong>D:</strong> {q_detail['option_d']}</div>
</div>
<div style="background: #F1F5F9; border-radius: 6px; padding: 10px 14px; font-size: 0.9rem; color: #334155;">
<strong>Explanation:</strong> {q_detail['explanation']}
</div>
</div>"""
                st.markdown(detail_card, unsafe_allow_html=True)

                # Show Reading Passage if associated
                if q_detail.get("passage_text"):
                    passage_card = f"""<div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
<div style="font-weight: 700; color: #0F172A; margin-bottom: 0.4rem;">📜 Reading Passage: {q_detail.get('passage_title', 'Untitled')}</div>
<div style="color: #475569; font-size: 0.88rem; line-height: 1.5; white-space: pre-line;">{q_detail['passage_text']}</div>
</div>"""
                    st.markdown(passage_card, unsafe_allow_html=True)

                # Show Listening Audio info if associated
                if q_detail.get("audio_file"):
                    transcript_html = f"<div style='color: #78350F; font-size: 0.85rem;'>Transcript: <em>{q_detail['audio_transcript']}</em></div>" if q_detail.get('audio_transcript') else ""
                    audio_card = f"""<div style="background: #FFFBEB; border: 1px dashed #FDE68A; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
<div style="font-weight: 700; color: #92400E; margin-bottom: 0.4rem;">🎧 Audio Asset: <code>{q_detail['audio_file']}</code></div>
{transcript_html}
</div>"""
                    st.markdown(audio_card, unsafe_allow_html=True)

                # Status Transition Action Buttons
                st.markdown("##### ⚡ Quick Status Actions:")
                btn_act, btn_deact, btn_arch, btn_del = st.columns([1.5, 1.5, 1.5, 1.8])

                with btn_act:
                    if st.button("🟢 Activate", use_container_width=True, disabled=(q_detail["status"] == "Active")):
                        ok, msg = activate_question(inspect_id)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                with btn_deact:
                    if st.button("⏸️ Deactivate", use_container_width=True, disabled=(q_detail["status"] == "Inactive")):
                        ok, msg = deactivate_question(inspect_id)
                        if ok:
                            st.warning(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                with btn_arch:
                    if st.button("📦 Archive", use_container_width=True, disabled=(q_detail["status"] == "Archived")):
                        ok, msg = archive_question(inspect_id)
                        if ok:
                            st.info(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                with btn_del:
                    if st.button("🗑️ Hapus Soal", type="secondary", use_container_width=True):
                        st.session_state[f"confirm_del_{inspect_id}"] = True

                if st.session_state.get(f"confirm_del_{inspect_id}", False):
                    st.warning(f"⚠️ **Hapus Permanen Soal #{inspect_id}?** Tindakan ini tidak dapat dibatalkan.")
                    c_del_yes, c_del_no, _ = st.columns([1.5, 1.5, 4])
                    with c_del_yes:
                        if st.button("❌ Ya, Hapus", type="primary", key=f"btn_yes_del_{inspect_id}", use_container_width=True):
                            ok, msg = delete_question_record(inspect_id)
                            st.session_state[f"confirm_del_{inspect_id}"] = False
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with c_del_no:
                        if st.button("Batal", key=f"btn_cancel_del_{inspect_id}", use_container_width=True):
                            st.session_state[f"confirm_del_{inspect_id}"] = False
                            st.rerun()


# ========================================================
# TAB 2: PENGATURAN JUMLAH SOAL PER KATEGORI
# ========================================================
with tab_settings:
    st.markdown("### Pengaturan Jumlah Soal Per Kategori Ujian")
    st.write(
        "Tentukan berapa banyak jumlah soal yang akan dimunculkan ke peserta pada setiap kategori (Grammar, Reading, Listening) "
        "saat mereka memulai sesi tes. Setiap kategori dapat memiliki kuota jumlah soal yang berbeda."
    )

    cat_data = fetch_category_question_limits()

    with st.form("category_limits_form"):
        new_limits = {}
        cols = st.columns(len(cat_data) if cat_data else 3)

        category_icons = {
            "Grammar": "📖",
            "Reading": "📜",
            "Listening": "🎧",
        }

        for idx, cat in enumerate(cat_data):
            c_name = cat["name"]
            c_icon = category_icons.get(c_name, "📚")
            current_limit = cat["question_limit"]
            active_cnt = cat["active_question_count"]
            total_cnt = cat["total_question_count"]

            with cols[idx % len(cols)]:
                st.markdown(
                    f"""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-top: 4px solid #3B82F6; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px;">
                        <div style="font-weight: 700; font-size: 1.1rem; color: #1E293B;">
                            {c_icon} {c_name}
                        </div>
                        <div style="font-size: 0.82rem; color: #64748B; margin: 4px 0 10px 0;">
                            Soal Aktif Tersedia: <strong style="color: #10B981;">{active_cnt}</strong> (Total: {total_cnt})
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                val = st.number_input(
                    f"Jumlah Soal {c_name}:",
                    min_value=1,
                    max_value=100,
                    value=int(current_limit),
                    step=1,
                    key=f"limit_input_{c_name}",
                    help=f"Peserta kuis {c_name} akan mendapatkan sejumlah soal ini pada saat ujian.",
                )
                new_limits[c_name] = val

        st.markdown("<br>", unsafe_allow_html=True)
        btn_save_col, _ = st.columns([2.5, 3])
        with btn_save_col:
            if st.form_submit_button("💾 Simpan Pengaturan Jumlah Soal", type="primary", use_container_width=True):
                ok, msg = save_category_question_limits(new_limits)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("### Pengaturan Passing Grade & Nama Skill")
    st.write("Kelola nama skill dan batas nilai kelulusan (*passing score*, standar 70%) agar peserta dapat membuka skill berikutnya.")

    sel_cat_skill = st.selectbox("Pilih Kategori untuk Mengatur Skill:", options=VALID_CATEGORIES, key="admin_skill_cat_select")
    cat_skills = fetch_skills_for_category(sel_cat_skill)

    if not cat_skills:
        st.info(f"Belum ada skill yang terdaftar untuk {sel_cat_skill}. Skill akan otomatis terdaftar saat Anda mengimpor atau menambahkan soal.")
    else:
        skill_table_data = []
        for s in cat_skills:
            skill_table_data.append({
                "Skill #": f"Skill {s['skill_number']}",
                "Nama Skill": s["skill_name"],
                "Passing Grade (%)": f"{s['passing_score']}%",
                "Soal Aktif": s.get("active_question_count", 0),
                "Total Soal": s.get("total_question_count", 0),
            })
        st.dataframe(pd.DataFrame(skill_table_data), use_container_width=True, hide_index=True)

        with st.expander("✏️ Ubah Nama Skill / Passing Grade", expanded=False):
            skill_edit_map = {s["id"]: f"Skill {s['skill_number']}: {s['skill_name']}" for s in cat_skills}
            chosen_s_id = st.selectbox("Pilih Skill:", options=list(skill_edit_map.keys()), format_func=lambda x: skill_edit_map[x], key="select_skill_to_edit")
            chosen_s = next(s for s in cat_skills if s["id"] == chosen_s_id)

            with st.form("form_edit_skill_config"):
                c_sn1, c_sn2 = st.columns([2.5, 1])
                with c_sn1:
                    new_sname = st.text_input("Nama Skill:", value=chosen_s["skill_name"])
                with c_sn2:
                    new_pscore = st.number_input("Passing Grade (%):", min_value=10.0, max_value=100.0, value=float(chosen_s["passing_score"]), step=5.0)

                if st.form_submit_button("💾 Perbarui Skill", type="primary"):
                    ok, msg = update_skill_passing_grade(chosen_s_id, new_sname, new_pscore)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)



# ========================================================
# TAB 3: ADD NEW QUESTION
# ========================================================
with tab_add:
    st.markdown("### Author New Assessment Question")
    st.write("Fill in all required fields. Validation rules strictly prevent the creation of incomplete or invalid questions.")

    with st.form("add_question_form"):
        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            add_cat = st.selectbox("Category *", options=VALID_CATEGORIES, key="add_cat")
        with col_c2:
            add_status = st.selectbox("Initial Status *", options=VALID_STATUSES, index=1, key="add_status")
        with col_c3:
            add_topic = st.text_input("Topic / Area *", placeholder="e.g. Subject-Verb Agreement, Main Idea", key="add_topic")

        col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
        with col_s1:
            add_skill_num = st.number_input("Skill Number *", min_value=1, max_value=50, value=1, step=1, key="add_skill_num")
        with col_s2:
            add_skill_name = st.text_input("Skill Name *", placeholder="e.g. Identifying Subject & Verb", value="Skill 1", key="add_skill_name")
        with col_s3:
            add_q_order = st.number_input("Question Order", min_value=1, max_value=200, value=1, step=1, key="add_q_order")

        add_diff = "Standard"
        add_qtype = "Multiple Choice"

        # Category specific fields
        add_passage_id = None
        new_pass_title = ""
        new_pass_text = ""
        add_audio_path = ""
        add_transcript = ""

        if add_cat == "Reading":
            st.markdown("##### Reading Passage Association")
            passages = fetch_passages_list()
            pass_options = {p.id: f"#{p.id} — {p.title or 'Untitled'} ({p.passage_text[:60]}...)" for p in passages}
            pass_options[0] = "➕ Create New Passage on-the-fly"

            chosen_pass = st.selectbox(
                "Link to Existing Passage or Create New:",
                options=list(pass_options.keys()),
                format_func=lambda x: pass_options[x],
                key="add_pass_choice",
            )
            if chosen_pass == 0:
                new_pass_title = st.text_input("New Passage Title", placeholder="e.g. Coral Reef Ecosystems")
                new_pass_text = st.text_area("New Passage Text *", placeholder="Enter full reading passage text here...", height=120)
            else:
                add_passage_id = chosen_pass

        elif add_cat == "Listening":
            st.markdown("#####  Listening Audio Asset")
            col_a1, col_a2 = st.columns([1.5, 2])
            with col_a1:
                add_audio_path = st.text_input(
                    "Audio File Path *",
                    placeholder="audio/listening/sample_01.mp3",
                    help="Relative path under audio/listening/",
                )
            with col_a2:
                add_transcript = st.text_area(
                    "Optional Spoken Audio Transcript",
                    placeholder="Enter transcript for admin review and student result review...",
                    height=80,
                )

        st.markdown("#####  Question Text & Choices")
        add_qtext = st.text_area("Question Text *", placeholder="Enter the complete question prompt...", height=90)

        col_o1, col_o2 = st.columns(2)
        with col_o1:
            add_opt_a = st.text_input("Option A *", placeholder="Option A text", key="add_opt_a")
            add_opt_c = st.text_input("Option C *", placeholder="Option C text", key="add_opt_c")
        with col_o2:
            add_opt_b = st.text_input("Option B *", placeholder="Option B text", key="add_opt_b")
            add_opt_d = st.text_input("Option D *", placeholder="Option D text", key="add_opt_d")

        col_ans, col_exp = st.columns([1, 3])
        with col_ans:
            add_correct = st.selectbox("Correct Answer *", options=VALID_ANSWERS, key="add_correct")
        with col_exp:
            add_explanation = st.text_area("Explanation *", placeholder="Detailed pedagogical reason why the correct answer is right...", height=80)

        st.markdown("<br>", unsafe_allow_html=True)
        submit_add = st.form_submit_button("💾 Save New Question to Bank", type="primary", use_container_width=True)

        if submit_add:
            payload = {
                "category": add_cat,
                "difficulty": add_diff,
                "status": add_status,
                "subtopic": add_topic or "General",
                "question_type": add_qtype or "Multiple Choice",
                "question_text": add_qtext,
                "option_a": add_opt_a,
                "option_b": add_opt_b,
                "option_c": add_opt_c,
                "option_d": add_opt_d,
                "correct_answer": add_correct,
                "explanation": add_explanation,
                "passage_id": add_passage_id,
                "new_passage_title": new_pass_title,
                "new_passage_text": new_pass_text,
                "audio_file": add_audio_path,
                "audio_transcript": add_transcript,
                "skill_number": int(add_skill_num),
                "skill_name": add_skill_name.strip() if add_skill_name else f"Skill {add_skill_num}",
                "question_order": int(add_q_order),
            }
            ok, new_id, msg = add_question(payload)
            if ok:
                st.success(f"🎉 {msg}")
                st.rerun()
            else:
                st.error(f"❌ Could not create question: {msg}")


# ========================================================
# TAB 3: EDIT EXISTING QUESTION
# ========================================================
with tab_edit:
    st.markdown("###  Edit Existing Question")

    all_q_for_edit = fetch_questions(limit=500)
    if not all_q_for_edit:
        st.info("No questions in bank to edit.")
    else:
        edit_opts = {q["id"]: f"ID #{q['id']} — [{q['category_name']} • {q['difficulty']}] {q['question_text'][:70]}..." for q in all_q_for_edit}
        chosen_edit_id = st.selectbox(
            "Select Question to Edit:",
            options=list(edit_opts.keys()),
            format_func=lambda x: edit_opts[x],
            key="edit_q_select",
        )

        if chosen_edit_id:
            curr = fetch_question_by_id(chosen_edit_id)
            if curr:
                with st.form("edit_question_form"):
                    st.markdown(f"##### Editing Question #{curr['id']}")

                    col_ec1, col_ec2, col_ec3 = st.columns(3)
                    with col_ec1:
                        cat_idx = VALID_CATEGORIES.index(curr["category_name"]) if curr["category_name"] in VALID_CATEGORIES else 0
                        edit_cat = st.selectbox("Category *", options=VALID_CATEGORIES, index=cat_idx)
                    with col_ec2:
                        status_idx = VALID_STATUSES.index(curr["status"]) if curr["status"] in VALID_STATUSES else 0
                        edit_status = st.selectbox("Status *", options=VALID_STATUSES, index=status_idx)
                    with col_ec3:
                        edit_topic = st.text_input("Topic / Area *", value=curr.get("subtopic", "General"))

                    col_es1, col_es2, col_es3 = st.columns([1, 2, 1])
                    with col_es1:
                        edit_skill_num = st.number_input("Skill Number *", min_value=1, max_value=50, value=int(curr.get("skill_number") or 1), step=1, key="edit_skill_num")
                    with col_es2:
                        edit_skill_name = st.text_input("Skill Name *", value=curr.get("skill_name") or f"Skill {curr.get('skill_number') or 1}", key="edit_skill_name")
                    with col_es3:
                        edit_q_order = st.number_input("Question Order", min_value=1, max_value=200, value=int(curr.get("question_order") or 1), step=1, key="edit_q_order")

                    edit_diff = curr.get("difficulty", "Standard")
                    edit_qtype = curr.get("question_type", "Multiple Choice")

                    # Category specific fields for edit
                    edit_pass_id = curr.get("passage_id")
                    edit_audio_path = curr.get("audio_file", "") or ""
                    edit_transcript = curr.get("audio_transcript", "") or ""

                    if edit_cat == "Reading":
                        st.markdown("##### 📜 Linked Passage")
                        passages = fetch_passages_list()
                        pass_opts = {p.id: f"#{p.id} — {p.title or 'Untitled'} ({p.passage_text[:50]}...)" for p in passages}
                        if curr.get("passage_id") and curr["passage_id"] not in pass_opts:
                            pass_opts[curr["passage_id"]] = f"Current Passage #{curr['passage_id']}"

                        sel_pass_idx = list(pass_opts.keys()).index(curr["passage_id"]) if curr.get("passage_id") in pass_opts else 0
                        edit_pass_id = st.selectbox("Associated Passage *", options=list(pass_opts.keys()), index=sel_pass_idx, format_func=lambda x: pass_opts[x])

                    elif edit_cat == "Listening":
                        st.markdown("##### 🎧 Linked Audio Asset")
                        col_ea1, col_ea2 = st.columns([1.5, 2])
                        with col_ea1:
                            edit_audio_path = st.text_input("Audio File Path *", value=edit_audio_path)
                        with col_ea2:
                            edit_transcript = st.text_area("Spoken Transcript", value=edit_transcript, height=70)

                    st.markdown("##### Question Text & Choices")
                    edit_qtext = st.text_area("Question Text *", value=curr["question_text"], height=90)

                    col_eo1, col_eo2 = st.columns(2)
                    with col_eo1:
                        edit_opt_a = st.text_input("Option A *", value=curr["option_a"])
                        edit_opt_c = st.text_input("Option C *", value=curr["option_c"])
                    with col_eo2:
                        edit_opt_b = st.text_input("Option B *", value=curr["option_b"])
                        edit_opt_d = st.text_input("Option D *", value=curr["option_d"])

                    col_eans, col_eexp = st.columns([1, 3])
                    with col_eans:
                        ans_idx = VALID_ANSWERS.index(curr["correct_answer"]) if curr["correct_answer"] in VALID_ANSWERS else 0
                        edit_correct = st.selectbox("Correct Answer *", options=VALID_ANSWERS, index=ans_idx)
                    with col_eexp:
                        edit_explanation = st.text_area("Explanation *", value=curr.get("explanation", ""), height=80)

                    st.markdown("<br>", unsafe_allow_html=True)
                    submit_edit = st.form_submit_button("💾 Save Modifications", type="primary", use_container_width=True)

                    if submit_edit:
                        edit_payload = {
                            "category": edit_cat,
                            "difficulty": edit_diff,
                            "status": edit_status,
                            "subtopic": edit_topic,
                            "question_type": edit_qtype,
                            "question_text": edit_qtext,
                            "option_a": edit_opt_a,
                            "option_b": edit_opt_b,
                            "option_c": edit_opt_c,
                            "option_d": edit_opt_d,
                            "correct_answer": edit_correct,
                            "explanation": edit_explanation,
                            "passage_id": edit_pass_id,
                            "audio_file": edit_audio_path,
                            "audio_transcript": edit_transcript,
                            "skill_number": int(edit_skill_num),
                            "skill_name": edit_skill_name.strip() if edit_skill_name else f"Skill {edit_skill_num}",
                            "question_order": int(edit_q_order),
                        }
                        ok, msg = update_question_record(chosen_edit_id, edit_payload)
                        if ok:
                            st.success(f"🎉 {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ Update failed: {msg}")

st.markdown("<br><hr>", unsafe_allow_html=True)

# Navigation Buttons
c_dash, c_users, c_res = st.columns([1.5, 1.5, 1.5])
with c_dash:
    if st.button("📊 Back to Dashboard", use_container_width=True):
        st.switch_page("pages/91_Admin_Dashboard.py")
with c_users:
    if st.button("👥 Participant Directory", use_container_width=True):
        st.switch_page("pages/92_Admin_Users.py")
with c_res:
    if st.button("📈 Assessment Results", use_container_width=True):
        st.switch_page("pages/96_Admin_Results.py")
