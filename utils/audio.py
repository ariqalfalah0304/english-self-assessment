"""
Audio feedback and listening playback utility for English Self-Assessment.
Handles:
- Immediate voice feedback sound playback (good_job.mp3, sorry_try_again.mp3)
- Listening prompt audio playback for listening comprehension questions
- Non-crashing graceful notices when audio assets are missing
"""

import base64
from pathlib import Path
from typing import Optional
import streamlit as st

from config.settings import FEEDBACK_AUDIO_DIR, BASE_DIR


AUDIO_GOOD_JOB_NAME = "good_job.mp3"
AUDIO_SORRY_TRY_AGAIN_NAME = "sorry_try_again.mp3"


def get_feedback_audio_path(is_correct: bool) -> Path:
    """Return the expected Path for correct or incorrect feedback audio."""
    filename = AUDIO_GOOD_JOB_NAME if is_correct else AUDIO_SORRY_TRY_AGAIN_NAME
    return FEEDBACK_AUDIO_DIR / filename


def render_feedback_audio(is_correct: bool) -> None:
    """
    Play feedback sound invisibly in the background without rendering a visible audio control bar.
    Supports MP3, WAV, and M4A formats with graceful fallback.
    """
    # Priority list of audio candidates for correct / incorrect sounds
    if is_correct:
        candidates = [
            FEEDBACK_AUDIO_DIR / "good_job.mp3",
            FEEDBACK_AUDIO_DIR / "floraphonic-positive-tone-man-says-excellent-184040.mp3",
            FEEDBACK_AUDIO_DIR / "good_job.wav",
            FEEDBACK_AUDIO_DIR / "good_job.m4a",
        ]
    else:
        candidates = [
            FEEDBACK_AUDIO_DIR / "sorry_try_again.wav",
            FEEDBACK_AUDIO_DIR / "sorry_try_again.m4a",
            FEEDBACK_AUDIO_DIR / "sory, try again.m4a",
            FEEDBACK_AUDIO_DIR / "sorry_try_again.mp3",
        ]

    chosen_path: Optional[Path] = None
    for cand in candidates:
        if cand.exists() and cand.is_file():
            chosen_path = cand
            break

    if chosen_path and chosen_path.exists():
        ext = chosen_path.suffix.lower()
        if ext in (".m4a", ".mp4", ".aac"):
            mime_type = "audio/mp4"
        elif ext == ".wav":
            mime_type = "audio/wav"
        else:
            mime_type = "audio/mp3"

        try:
            with open(chosen_path, "rb") as f:
                audio_bytes = f.read()
            b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            st.markdown(
                f"""
                <audio autoplay style="display:none;" id="feedback_audio_player">
                    <source src="data:{mime_type};base64,{b64_audio}" type="{mime_type}">
                </audio>
                """,
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.warning(f"⚠️ Could not play feedback audio '{chosen_path.name}': {str(e)}")
    else:
        rel_path = f"audio/feedback/{AUDIO_GOOD_JOB_NAME if is_correct else AUDIO_SORRY_TRY_AGAIN_NAME}"
        st.markdown(
            f"""
            <div style="background: #F3F4F6; border: 1px dashed #9CA3AF; border-radius: 8px; padding: 8px 12px; margin: 8px 0; font-size: 0.82rem; color: #4B5563;">
                🔇 <strong>Audio Asset Notice:</strong> Feedback sound file <code>{rel_path}</code> is not found. Place the sound file in <code>audio/feedback/</code> to enable voice feedback.
            </div>
            """,
            unsafe_allow_html=True,
        )


from utils.security import is_safe_audio_path


def render_listening_audio(file_path: Optional[str]) -> bool:
    """
    Render audio player for a listening comprehension question.
    Resolves relative paths safely against BASE_DIR.
    Prevents path traversal and forbidden file read.
    If the audio asset is missing, displays an informative non-crashing alert.
    Returns True if audio file was found and rendered, False otherwise.
    """
    if not file_path:
        st.warning("⚠️ No audio asset specified for this listening question.")
        return False

    is_safe, resolved_path, sec_err = is_safe_audio_path(file_path, BASE_DIR)
    if not is_safe or not resolved_path:
        st.error(f"⛔ Insecure audio file reference rejected: {sec_err}")
        return False

    if resolved_path.exists() and resolved_path.is_file():
        try:
            with open(resolved_path, "rb") as f:
                audio_bytes = f.read()
            st.markdown("##### 🎧 Audio Prompt:")
            st.audio(audio_bytes, format="audio/mp3", autoplay=False)
            return True
        except Exception as e:
            st.error(f"❌ Error loading audio file '{file_path}': {str(e)}")
            return False
    else:
        st.markdown(
            f"""
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-left: 5px solid #F59E0B; border-radius: 8px; padding: 12px 16px; margin: 12px 0; color: #92400E;">
                <div style="font-weight: 700; margin-bottom: 4px;">⚠️ Missing Listening Audio Asset</div>
                <div style="font-size: 0.88rem; line-height: 1.4;">
                    The expected audio file <code>{file_path}</code> could not be found in <code>audio/listening/</code>.<br>
                    Please upload the corresponding MP3 file to enable listening audio playback for this prompt.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return False
