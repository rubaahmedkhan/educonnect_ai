from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, ModelSettings, function_tool
from agents.run import RunConfig
import pandas as pd
import os
import asyncio

# === Model Setup ===
gemini_api_key = ""

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model_settings = ModelSettings(tool_choice="required")

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    model_settings=model_settings,
    tracing_disabled=True,
)

# === Tool Function ===
@function_tool
def generate_student_report(input_str: str) -> str:
    # Extract file path from input
    try:
        if "excel file" in input_str:
            file_path = input_str.split("excel file")[-1].strip()
        elif input_str.endswith(".csv") and os.path.exists(input_str):
            file_path = input_str
        else:
            return f"❌ Error: Could not detect file path in input: {input_str}"
    except Exception as e:
        return f"❌ Error parsing file path: {str(e)}"

    if not os.path.exists(file_path):
        return f"❌ Error: File not found at path: {file_path}"

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"

    required_columns = ["Student_id", "Student Name", "Class", "Subject", "Obtained  Marks", "Total  Marks"]
    df.columns = df.columns.str.strip()

    if not all(col.strip() in df.columns for col in required_columns):
        return f"❌ Error: Required columns missing. Expected: {', '.join(required_columns)}"


    # Group by student
    grouped = df.groupby(["Student_id", "Student Name", "Class"])

    summaries = []
    for (student_id, name, class_), group in grouped:
        student_data = {
            "name": name,
            "id": student_id,
            "class": class_,
            "subjects": [],
            "total_obtained": 0,
            "total_marks": 0
        }
        for _, row in group.iterrows():
            subject = row["Subject"].strip()
            obtained = row["Obtained  Marks"]
            total = row["Total  Marks"]
            student_data["subjects"].append({
                "subject": subject,
                "obtained": obtained,
                "total": total
            })
            student_data["total_obtained"] += obtained
            student_data["total_marks"] += total

        percent = (student_data["total_obtained"] / student_data["total_marks"]) * 100
        student_data["overall_percent"] = round(percent, 1)
        summaries.append(student_data)

    return str(summaries)  # or json.dumps if needed

    
# Define the agent with improved instructions
agent = Agent(
    name="admin",
    instructions="""
    You are a feedback generator for student performance based on a CSV file containing student data. The CSV has the following columns: S.NO, Student_id, Student Name, Class, Subject, Total Marks, Obtained Marks, Email.

When given an input like 'generate a report of students giving in excel file <path>' or 'generate a report of students with the following CSV content: <content>', you must:
1. Read the CSV file or content.
2. For each student, generate feedback based on their Obtained Marks, Total Marks, and Subject.
3. Calculate the overall percentage as (Obtained Marks / Total Marks) * 100.
4. Provide feedback in the following exact format for each student, with no variations:
   <Student Name> (ID: <Student_id>, Class: <Class>):
   Overall Percentage: <percentage>%
   Subject: <Subject> (<Obtained Marks>/<Total Marks>)
   Feedback: <Feedback text based on performance>
5. Separate each student's feedback with a blank line.
6. Do not include headers like 'Here are the student reports' or 'Okay, I have the student performance data'.
7. Use the exact 'Student Name' from the CSV without altering capitalization.
8. Provide constructive feedback tailored to the student's performance (e.g., praise for high marks, suggestions for improvement for low marks).

Example output for one student:
Ali (ID: 201, Class: 8):
Overall Percentage: 75.0%
Subject: English (75/100)
Feedback: Ali is performing well in English. Consistent effort will help him excel further.

""",
    
    tools=[generate_student_report]
)

async def main():
    result=await Runner.run(agent,input="generate a report of students giving in excel file file_reader/excel_sheet.csv ",run_config=config)
    print (result.final_output)

#asyncio.run(main())