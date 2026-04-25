import streamlit as st
from google import genai
from PIL import Image
from gtts import gTTS
import io
import re
import datetime

# --- 1. INITIAL SETUP ---
st.set_page_config(
    page_title="3.1 Reality Auditor Pro",
    page_icon="🕵️",
    layout="wide"
)

# Connect to the 2026 standard API
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
MODEL_ID = "gemini-3.1-flash-lite-preview"

# Initialize Session States
if "memory" not in st.session_state:
    st.session_state.memory = "Environment unknown. Please perform your first scan."
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

# --- 2. VOICE FUNCTION ---
def speak(text):
    # Clean text: remove Markdown bolding and AI 'thought' tags
    clean_text = re.sub(r'\*|\[.*?\]', '', text)
    tts = gTTS(text=clean_text, lang='en', slow=False)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp, format="audio/mp3", autoplay=True)

# --- 3. SIDEBAR (The Control Center) ---
with st.sidebar:
    st.header("🧠 Agent Control")
    st.info(f"**Model:** {MODEL_ID}")
    
    st.divider()
    # FEATURE: Area of Interest
    st.subheader("🎯 Area of Interest")
    aoi = st.text_input("What should the Agent watch?", placeholder="e.g. the water bottle, the door, my laptop")
    st.caption("The Agent will prioritize changes to this specific object/area.")
    
    st.divider()
    voice_on = st.toggle("🔊 Enable Voice Alerts", value=True)
    
    if st.button("🗑️ Wipe Memory"):
        st.session_state.memory = "Memory wiped."
        st.session_state.audit_log = []
        st.rerun()

# --- 4. MAIN INTERFACE ---
st.title("🕵️ Reality Auditor Agent")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📸 Visual Input")
    cam_image = st.camera_input("Capture Scene", label_visibility="collapsed")

with col2:
    st.subheader("📊 Audit Results")
    if cam_image:
        if st.button("🔍 Run Anomaly Detection", use_container_width=True):
            img = Image.open(cam_image)
            img.thumbnail((500, 500)) 
            
            with st.status("🕵️ Agent comparing realities...", expanded=True) as status:
                try:
                    # Logic: If AOI is empty, watch everything.
                    target_focus = aoi if aoi else "the entire scene"
                    
                    prompt = f"""
                    You are a spatial security agent. Compare this image to your memory:
                    MEMORY: {st.session_state.memory}
                    
                    SPECIAL FOCUS: You are specifically assigned to monitor {target_focus}.
                    
                    TASK:
                    1. Identify if {target_focus} has changed, moved, or been tampered with.
                    2. Note any other major environmental anomalies.
                    3. Provide a 'Confidence Score' (0-100%).
                    4. Keep your answer to 2 short sentences for voice output.
                    """
                    
                    response = client.models.generate_content(
                        model=MODEL_ID,
                        contents=[prompt, img]
                    )
                    
                    # Update History and Memory
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    result_text = response.text
                    st.session_state.memory = result_text
                    st.session_state.audit_log.append({"time": timestamp, "result": result_text})
                    
                    status.update(label="Audit Complete!", state="complete", expanded=False)
                    
                    # Display Result
                    st.success(f"Audit Logged at {timestamp}")
                    st.markdown(result_text)
                    
                    # Trigger Voice
                    if voice_on:
                        speak(result_text)
                        
                except Exception as e:
                    status.update(label="System Error", state="error")
                    st.error(f"Error: {e}")
    else:
        st.info("Awaiting visual input from camera...")

# --- 5. LOG HISTORY ---
st.divider()
st.subheader("📜 Audit History")
if st.session_state.audit_log:
    for entry in reversed(st.session_state.audit_log):
        with st.expander(f"🕒 {entry['time']} - View Details"):
            st.write(entry['result'])