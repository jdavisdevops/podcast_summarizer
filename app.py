import streamlit as st
from datetime import datetime
import collector as co

# --- Page Configuration ---
st.set_page_config(
    page_title="Podcast Transcriber",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #262730;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #1A3A26;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #4B1E21;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .search-result {
        padding: 0.75rem;
        border-radius: 0.5rem;
        border: 1px solid #4A4A4A;
        margin-bottom: 0.5rem;
        transition: background-color 0.3s;
    }
    .search-result:hover {
        background-color: #262730;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'sp_client' not in st.session_state:
    try:
        st.session_state.sp_client = co.get_spotify_client()
    except Exception as e:
        st.session_state.sp_client = None
        st.error(f"Could not connect to Spotify: {e}")

if 'transcription_result' not in st.session_state:
    st.session_state.transcription_result = None
if 'episode_to_transcribe' not in st.session_state:
    st.session_state.episode_to_transcribe = None

# --- Helper Functions ---
def transcribe_episode(url, model_size):
    st.session_state.transcription_result = None
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_status(message, progress=None):
        status_text.text(message)
        if progress is not None:
            progress_bar.progress(progress)

    try:
        transcription, info = co.get_transcript_from_url(url, model_size, update_status, progress_bar.progress)
        st.session_state.transcription_result = (info, transcription)
        status_text.empty()
        progress_bar.empty()
    except Exception as e:
        status_text.empty()
        progress_bar.empty()
        st.error(f"An error occurred: {e}")

# --- UI Layout ---
st.markdown('<h1 class="main-header">🎙️ Podcast Transcriber</h1>', unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    model_size = st.selectbox(
        "Whisper Model",
        ("base", "small", "medium"),
        help="Select the Whisper model size. Larger models are more accurate but slower."
    )

    st.header("🔗 Quick Links")
    st.markdown(
        """
        <a href="https://chat.openai.com" target="_blank" style="display: inline-block; width: 100%; padding: 8px; background-color: #667eea; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">
            Open ChatGPT
        </a>
        """,
        unsafe_allow_html=True
    )

    st.header("ℹ️ About")
    st.info("This app uses Spotify and iTunes APIs to find and download podcast audio, then transcribes it using OpenAI's Whisper model.")


# --- Main Content ---
# Two main tabs: URL input and Search
tab1, tab2 = st.tabs(["🔗 Transcribe from URL", "🔍 Search for Episode"])

with tab1:
    st.subheader("Paste a Spotify Episode URL")
    with st.form("url_form"):
        spotify_url = st.text_input("Episode URL", placeholder="https://open.spotify.com/episode/...")
        submit_url = st.form_submit_button("Start Transcription", use_container_width=True)

    if submit_url and spotify_url:
        transcribe_episode(spotify_url, model_size)

with tab2:
    if st.session_state.episode_to_transcribe:
        item = st.session_state.episode_to_transcribe
        st.subheader("Confirm Transcription")
        st.markdown(f"You are about to transcribe:")
        
        col1, col2 = st.columns([1,4])
        with col1:
            st.image(item['images'][0]['url'], width=100)
        with col2:
            st.write(f"**{item['name']}**")
            st.write(f"_{item['show']['name']}_")

        confirm_col, cancel_col, _ = st.columns([1,1,3])
        if confirm_col.button("✅ Yes, Transcribe", use_container_width=True):
            transcribe_episode(item['external_urls']['spotify'], model_size)
            st.session_state.episode_to_transcribe = None
            st.experimental_rerun()
        if cancel_col.button("❌ Cancel", use_container_width=True):
            st.session_state.episode_to_transcribe = None
            st.experimental_rerun()

    else:
        st.subheader("Search for a Podcast Episode")
        with st.form("search_form"):
            search_query = st.text_input("Search Query", placeholder="e.g., 'Lex Fridman #400'")
            submit_search = st.form_submit_button("Search", use_container_width=True)

        if submit_search and search_query and st.session_state.sp_client:
            with st.spinner("Searching..."):
                results = co.search_spotify_episodes(search_query, st.session_state.sp_client)
                st.session_state.search_results = results
        
        if 'search_results' in st.session_state and st.session_state.search_results:
            st.markdown("---")
            st.subheader("Search Results")
            for item in st.session_state.search_results:
                if not item:  # Handle cases where an episode might not be available
                    continue
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.image(item['images'][0]['url'], width=100)
                with col2:
                    st.write(f"**{item['name']}**")
                    st.write(f"_{item['show']['name']}_")
                    if st.button("Select to Transcribe", key=item['id'], use_container_width=True):
                        st.session_state.episode_to_transcribe = item
                        st.session_state.search_results = None # Clear results after selection
                        st.experimental_rerun()


# --- Display Transcription Result ---
if st.session_state.transcription_result:
    info, transcription = st.session_state.transcription_result
    st.markdown("---")
    st.header("📄 Transcription Result")
    
    st.markdown(f'<div class="success-box"><b>Episode:</b> {info["episode_title"]}<br><b>Podcast:</b> {info["show_name"]}</div>', unsafe_allow_html=True)

    safe_title = co.sanitize_filename(info["episode_title"])
    filename = f"{safe_title}.txt"
    
    st.download_button(
        label="📥 Download Transcript",
        data=transcription,
        file_name=filename,
        mime="text/plain",
        use_container_width=True,
        key=f"download_{safe_title}"
    )
    
    with st.expander("📖 View Full Transcript", expanded=True):
        st.text_area("Transcript", transcription, height=400) 