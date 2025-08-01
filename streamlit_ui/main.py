import streamlit as st
import pandas as pd
import tempfile
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path for agent access
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from agents import Runner
from agent.main import agent, config

st.title("🎓 Student Feedback Generator")

uploaded_file = st.file_uploader("Upload student CSV file", type="csv")

if uploaded_file:
    # Save uploaded file to a temporary path
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name

    st.session_state['temp_file_path'] = temp_file_path
    st.success("✅ CSV uploaded successfully!")
    df = pd.read_csv(temp_file_path)
    st.dataframe(df)

    if st.button("📄 Generate Feedback Report"):
        input_str = f"generate a report of students giving in excel file {st.session_state['temp_file_path']}"

        try:
            # Fix: Streamlit needs a manual asyncio loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(Runner.run(agent, input_str, run_config=config))
            loop.close()

            st.markdown("### 🧾 Student Report:")
            st.write(result.final_output)

        except Exception as e:
            st.error(f"❌ Error generating feedback: {str(e)}")

