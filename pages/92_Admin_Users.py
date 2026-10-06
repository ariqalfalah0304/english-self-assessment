"""
Admin Users Management Page (Phase 10).
Features:
- Search participants by name, email, institution, or program
- Directory list with registration date, total attempts, and average score
- Individual user profile details inspection
- Complete assessment attempt history review for any participant
- Read-only historical data (no score tampering)
Protected by require_admin_auth().
"""

import streamlit as st
import pandas as pd
from config.settings import APP_NAME
from services.admin_service import require_admin_auth
from services.admin_dashboard_service import (
    fetch_users_directory,
    fetch_user_details_and_history,
    delete_user_account,
)
from utils.excel_parser import export_users_to_excel
from components.navigation import inject_custom_navigation_css, render_admin_header
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Participants — {APP_NAME}",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply route protection & navigation separation
inject_custom_navigation_css()
inject_global_ui_styles()
require_admin_auth()

# Administrative Header
render_admin_header(
    title="Participant Management",
    subtitle="User Directory, Institutional Affiliation & Complete Assessment Logs",
)

# --------------------------------------------------------
# 1. SEARCH & DIRECTORY CONTROLS
# --------------------------------------------------------
st.markdown("### Search & Directory")

col_search, col_action = st.columns([3, 1])

with col_search:
    search_term = st.text_input(
        "Search Participants:",
        placeholder="Filter by name, email address, institution, or academic program...",
        label_visibility="collapsed",
    )

with col_action:
    if st.button("🔄 Refresh Directory", use_container_width=True):
        st.rerun()

# Fetch users
users_list = fetch_users_directory(search_query=search_term)

col_cnt, col_exp = st.columns([3, 1])
with col_cnt:
    st.markdown(f"**Found {len(users_list)} registered participant(s)**")
with col_exp:
    if users_list:
        users_excel = export_users_to_excel(users_list)
        st.download_button(
            label="📥 Export Data User (.xlsx)",
            data=users_excel,
            file_name="data_users_directory.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="export_users_excel_btn",
        )

if not users_list:
    st.info("No participants found matching the search criteria.")
else:
    # Build clean DataFrame for display
    display_rows = []
    for u in users_list:
        avg_display = f"{u['average_score']}%" if u['average_score'] is not None else "No scores yet"
        created_display = u['created_at'][:10] if u.get('created_at') else "-"
        display_rows.append({
            "User ID": u["id"],
            "Full Name": u["name"],
            "Email Address": u["email"],
            "Institution": u["institution"],
            "Program / Role": u["program"],
            "Registered": created_display,
            "Total Tests": u["total_attempts"],
            "Average Score": avg_display,
        })

    df_users = pd.DataFrame(display_rows)
    st.dataframe(df_users, use_container_width=True, hide_index=True)

# Quick Cleanup Expander for Unused Accounts (0 tests)
unused_users = [u for u in users_list if u["total_attempts"] == 0]
if unused_users:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander(f"🧹 Quick Cleanup: Unused Accounts Without Test Logs ({len(unused_users)})", expanded=False):
        st.write("Daftar akun peserta yang belum pernah mengerjakan ujian:")
        unused_options = {u["id"]: f"ID #{u['id']} — {u['name']} ({u['email']})" for u in unused_users}
        selected_unused = st.multiselect(
            "Pilih Akun yang Ingin Dihapus:",
            options=list(unused_options.keys()),
            format_func=lambda x: unused_options[x],
            key="multi_select_unused_users",
        )
        if selected_unused:
            if st.button(f"🗑️ Hapus {len(selected_unused)} Akun Terpilih", type="primary", key="btn_del_batch_unused"):
                deleted_cnt = 0
                for uid in selected_unused:
                    if delete_user_account(uid):
                        deleted_cnt += 1
                st.toast(f"{deleted_cnt} akun peserta tidak terpakai berhasil dihapus!", icon="✅")
                st.rerun()

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 2. PARTICIPANT DETAILS & ASSESSMENT HISTORY
# --------------------------------------------------------
st.markdown("### Participant Profile & Assessment History")

if not users_list:
    st.write("No participants available to inspect.")
else:
    # Selector mapping
    user_options = {u["id"]: f"ID #{u['id']} — {u['name']} ({u['email']}) {'[0 Tests]' if u['total_attempts'] == 0 else ''}" for u in users_list}
    selected_id = st.selectbox(
        "Select Participant to View Full History / Delete Account:",
        options=list(user_options.keys()),
        format_func=lambda x: user_options[x],
    )

    if selected_id:
        user_record, history_records = fetch_user_details_and_history(selected_id)

        if user_record:
            # Participant Information Card
            col_p1, col_p2, col_p3, col_del = st.columns([2.5, 2.5, 2.5, 1.8])
            with col_p1:
                st.markdown(f"**Participant Name:** {user_record.name}")
                st.markdown(f"**Email Address:** {user_record.email}")
            with col_p2:
                st.markdown(f"**Institution:** {user_record.institution or '-'}")
                st.markdown(f"**Program / Occupation:** {user_record.program or '-'}")
            with col_p3:
                st.markdown(f"**Registration Date:** {user_record.created_at or '-'}")
                st.markdown(f"**Total Attempts:** {len(history_records)}")
            with col_del:
                st.markdown("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Hapus Akun Ini", key=f"btn_del_init_{user_record.id}", use_container_width=True, type="secondary"):
                    st.session_state[f"show_confirm_del_{user_record.id}"] = True

            # Delete Confirmation Panel
            if st.session_state.get(f"show_confirm_del_{user_record.id}"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.warning(
                    f"⚠️ **Konfirmasi Hapus Akun:** Yakin ingin menghapus akun **{user_record.name}** (`{user_record.email}`) "
                    f"beserta seluruh ({len(history_records)}) data riwayat ujiannya? Tindakan ini permanen dan tidak dapat dibatalkan."
                )
                c_conf_yes, c_conf_no, _ = st.columns([1.5, 1.5, 3])
                with c_conf_yes:
                    if st.button("🔥 Ya, Hapus Akun", type="primary", key=f"btn_do_del_{user_record.id}", use_container_width=True):
                        ok = delete_user_account(user_record.id)
                        if ok:
                            st.toast(f"Akun {user_record.name} berhasil dihapus!", icon="✅")
                            st.session_state[f"show_confirm_del_{user_record.id}"] = False
                            st.rerun()
                        else:
                            st.error("Gagal menghapus akun pengguna dari database.")
                with c_conf_no:
                    if st.button("❌ Batal", key=f"btn_cancel_del_{user_record.id}", use_container_width=True):
                        st.session_state[f"show_confirm_del_{user_record.id}"] = False
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            # Assessment History Table
            if not history_records:
                st.info(f"ℹ️ {user_record.name} has not attempted any assessments yet.")
            else:
                st.markdown(f"##### Assessment Sessions for {user_record.name}:")
                history_rows = []
                for h in history_records:
                    status_str = "Completed" if h["completed_at"] else "In Progress"
                    dur_sec = h.get("duration_seconds")
                    dur_display = f"{dur_sec // 60}m {dur_sec % 60}s" if dur_sec else "N/A"
                    history_rows.append({
                        "Attempt ID": h["id"],
                        "Category": h["category"],
                        "Difficulty": h["difficulty"],
                        "Score (%)": f"{h['score']}%",
                        "Correct Answers": f"{h['correct_answers']} / {h['total_questions']}",
                        "Incorrect Answers": h["incorrect_answers"],
                        "Duration": dur_display,
                        "Started At": h["started_at"][:19] if h.get("started_at") else "-",
                        "Completed At": h["completed_at"][:19] if h.get("completed_at") else "-",
                        "Status": status_str,
                    })

                df_history = pd.DataFrame(history_rows)
                st.dataframe(df_history, use_container_width=True, hide_index=True)

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 3. NAVIGATION
# --------------------------------------------------------
c_dash, c_res, _ = st.columns([1.5, 1.5, 3])
with c_dash:
    if st.button("📊 Back to Dashboard", use_container_width=True):
        st.switch_page("pages/91_Admin_Dashboard.py")
with c_res:
    if st.button("📈 View All Results", use_container_width=True):
        st.switch_page("pages/96_Admin_Results.py")
