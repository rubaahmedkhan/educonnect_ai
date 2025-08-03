import streamlit as st
import pandas as pd
import tempfile
import sys
import asyncio
import re
from pathlib import Path

# Add project root to sys.path for agent access
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from agents import Runner
from agent.app import agent, config
from agent.email import send_email_report

st.title("🎓 Student Feedback Generator & Emailer!")

uploaded_file = st.file_uploader("Upload student CSV file", type="csv")

if uploaded_file:
    # Save uploaded file to a temporary path
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name

    st.session_state['temp_file_path'] = temp_file_path
    st.success("✅ CSV uploaded successfully!")
    df = pd.read_csv(temp_file_path)
    # Clean 'Student Name' column to remove extra spaces
    df['Student Name'] = df['Student Name'].str.strip()
    st.session_state['df'] = df  # Save cleaned DataFrame for email sending
    st.dataframe(df)

    if st.button("📄 Generate Feedback Report"):
        # Pass the temporary file path
        input_str = f"generate a report of students giving in excel file {st.session_state['temp_file_path']}"

        try:
            # Run agent with asyncio loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(Runner.run(agent, input_str, run_config=config))
            loop.close()

            # Parse the agent's text-based output
            feedback_data = []
            # Split by student blocks (double newlines)
            student_blocks = result.final_output.strip().split("\n\n")
            # Regex to match "Name (ID: <ID>, Class: <Class>):"
            name_pattern = re.compile(r"^\s*(\w+)\s*\(ID:\s*\d+\s*,\s*Class:\s*[\w\d]+\):", re.MULTILINE)

            for block in student_blocks:
                try:
                    # Skip header
                    if block.startswith("Here are the student reports:"):
                        continue
                    # Extract name using regex
                    name_match = name_pattern.match(block)
                    if not name_match:
                        st.warning(f"⚠️ Skipping block (no name match): {block[:50]}...")
                        continue
                    name = name_match.group(1).strip()

                    # The entire block is the feedback text
                    feedback_text = block.strip()

                    feedback_data.append({
                        "name": name,
                        "email": None,
                        "feedback": feedback_text
                    })
                except Exception as e:
                    st.warning(f"⚠️ Skipping malformed student block: {str(e)}")
                    continue

            if not feedback_data:
                st.error("❌ Error: No valid student feedback parsed from agent output.")
                st.write(f"Raw output: {result.final_output}")
                st.stop()

            # Match feedbacks with emails from DataFrame
            unmatched_names = []
            for feedback in feedback_data:
                matched = False
                for _, row in df.iterrows():
                    if row.get("Student Name") == feedback["name"]:
                        feedback["email"] = row.get("Email")
                        matched = True
                        break
                if not matched:
                    unmatched_names.append(feedback["name"])

            if unmatched_names:
                st.warning(f"⚠️ No email found for students: {', '.join(unmatched_names)}")

            st.session_state['feedback_data'] = feedback_data  # Save for email sending

            # Display feedback
            st.markdown("### 🧾 Student Report:")
            for feedback in feedback_data:
                st.markdown(f"**{feedback['name']}**:")
                st.write(feedback['feedback'])
                if not feedback['email']:
                    st.warning(f"No email found for {feedback['name']}")
                st.markdown("---")

        except Exception as e:
            st.error(f"❌ Error generating feedback: {str(e)}")
            st.write(f"Raw output: {result.final_output}")
            st.stop()

    # Button to send emails after report is generated
    if 'feedback_data' in st.session_state and st.button("📧 Send Feedback Emails to Students"):
        try:
            send_email_report(st.session_state['df'], st.session_state['feedback_data'])
            st.success("✅ Emails sent successfully to all students!")
        except Exception as e:
            st.error(f"❌ Error sending emails: {str(e)}")





