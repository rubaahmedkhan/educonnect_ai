import streamlit as st
import sys
from pathlib import Path
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, ModelSettings,function_tool
from agents.run import RunConfig


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from file_reader.main import read_csv_file
from agent.main import get_agent_runner_with_data

st.title("🎓 Student Feedback Generator")

uploaded_file = st.file_uploader("Upload student CSV file", type="csv")

if uploaded_file:
    df = read_csv_file(uploaded_file)
    st.success("CSV loaded successfully!")
    st.dataframe(df)

    if st.button("Generate Feedback"):
        runner = get_agent_runner_with_data(df)

        result =  Runner.run_sync("show all students data")
        st.write("📝 Feedback & Recommendations:")
        st.write(result.final)



