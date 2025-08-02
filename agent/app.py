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
    You are an intelligent education assistant. You receive structured student performance data.
    For each student, write a helpful feedback based on:
    - their subject-wise marks
    - their overall percentage
    - weak or strong subjects

    Your feedback must be constructive and encouraging.
    """,
    tools=[generate_student_report]
)

async def main():
    result=await Runner.run(agent,input="generate a report of students giving in excel file file_reader/excel_sheet.csv ",run_config=config)
    print (result.final_output)

# asyncio.run(main())