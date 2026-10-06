"""
UI and Styling Refinements for English Self-Assessment (Phase 18).
Provides consistent design tokens, responsive card structures,
and accessible color palettes across the platform.
"""

import streamlit as st


def inject_global_ui_styles() -> None:
    """Inject subtle, accessible CSS enhancements across participant and admin views."""
    st.markdown(
        """
        <style>
        /* Wide, balanced and responsive layout across all pages */
        .main .block-container,
        [data-testid="stMainBlockContainer"],
        .block-container {
            max-width: 1400px !important;
            width: 100% !important;
            padding: 2rem 3rem 3rem 3rem !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }

        @media (max-width: 1200px) {
            .main .block-container,
            [data-testid="stMainBlockContainer"],
            .block-container {
                padding: 1.5rem 2rem 2.5rem 2rem !important;
            }
        }

        @media (max-width: 768px) {
            .main .block-container,
            [data-testid="stMainBlockContainer"],
            .block-container {
                padding: 1rem 1rem 2rem 1rem !important;
            }
        }

        /* Smooth transitions & consistent font styling */
        html, body, [class*="css"] {
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* Modern interactive radio option cards */
        div[role="radiogroup"] > label {
            background: #FFFFFF !important;
            border: 1.5px solid #E2E8F0 !important;
            border-radius: 10px !important;
            padding: 12px 18px !important;
            margin-bottom: 10px !important;
            transition: all 0.18s ease-in-out !important;
            cursor: pointer !important;
            width: 100% !important;
        }
        div[role="radiogroup"] > label:hover {
            border-color: #3B82F6 !important;
            background-color: #F8FAFC !important;
            box-shadow: 0 2px 6px rgba(59, 130, 246, 0.1) !important;
            transform: translateY(-1px);
        }
        div[role="radiogroup"] > label:has(input:checked) {
            border-color: #2563EB !important;
            background-color: #EFF6FF !important;
            box-shadow: 0 0 0 1px #2563EB !important;
        }

        /* Primary and secondary button polish */
        .stButton > button {
            font-weight: 600 !important;
            border-radius: 8px !important;
            padding: 0.5rem 1.2rem !important;
            transition: all 0.15s ease-in-out !important;
        }
        .stButton > button:hover {
            box-shadow: 0 4px 8px -1px rgba(0, 0, 0, 0.12) !important;
        }

        /* Metric cards polish */
        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 14px 18px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        }

        /* Progress bar styling */
        .stProgress > div > div > div > div {
            background-color: #2563EB !important;
            border-radius: 8px !important;
        }

        /* Responsive container adjustments */
        @media (max-width: 768px) {
            .stButton > button {
                width: 100% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
