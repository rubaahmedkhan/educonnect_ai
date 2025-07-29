from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, ModelSettings, function_tool
from agents.run import RunConfig
import pandas as pd
import asyncio

gemini_api_key = "gemini_api_key"

# Check if the API key is present; if not, raise an error
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")

# Reference: https://ai.google.dev/gemini-api/docs/openai
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
model_settings = ModelSettings()

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

# Threshold average marks per subject
THRESHOLD = 50  # aap isay customize kar sakte hain

# 
@function_tool
def generate_student_report(excel_path: str) -> str:
    df = pd.read_csv("file_reader/excel_sheet.csv")

    # Strip column names to avoid hidden spaces
    df.columns = df.columns.str.strip()

    # Feedback threshold
    THRESHOLD = 50

    # Group by student
    reports = []
    grouped = df.groupby(["Student_id", "Student Name", "Class"])

    for (student_id, name, class_), group in grouped:
        report = f"📘 Student: {name} (Class {class_})\n"
        weak_subjects = []

        for _, row in group.iterrows():
            subject = row["Subject"].strip().lower()
            obtained = row["Obtained  Marks"]  # watch out for double space
            total = row["Total  Marks"]

            if (obtained / total) * 100 < THRESHOLD:
                weak_subjects.append(f"{subject.title()} ({obtained}/{total})")

        if weak_subjects:
            report += "⚠ Needs improvement in: " + ", ".join(weak_subjects)
        else:
            report += "✅ Performing well in all subjects."

        reports.append(report)

    return "\n\n".join(reports)


   
agent=Agent(name="admin",
            instructions="you are creating student report with the help of tool generate_student_report",
            tools=[generate_student_report])

async def main():
    result=await Runner.run(agent,input="generate a report of students giving in excel file file_reader/excel_sheet.csv ",run_config=config)
    print (result.final_output)

asyncio.run(main())
