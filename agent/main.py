from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, ModelSettings, function_tool
from agents.run import RunConfig
import pandas as pd
import asyncio
import os

gemini_api_key = ""

# Initialize model
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

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
        report_lines = []
        total_obtained = 0
        total_marks = 0
        weak_subjects = []

        report_lines.append(f"===============================")
        report_lines.append(f"📘 Student Report")
        report_lines.append(f"👤 Name: {name}")
        report_lines.append(f"🆔 ID: {student_id}")
        report_lines.append(f"🏫 Class: {class_}")
        report_lines.append(f"-------------------------------")
        report_lines.append(f"📊 Subject-wise Performance:")

        for _, row in group.iterrows():
            subject = row["Subject"].strip()
            obtained = row["Obtained  Marks"]
            total = row["Total  Marks"]
            percentage = (obtained / total) * 100

            report_lines.append(f" - {subject}: {obtained}/{total} ({percentage:.1f}%)")

            total_obtained += obtained
            total_marks += total

            if percentage < 50:
                weak_subjects.append((subject, percentage))

        overall_percent = (total_obtained / total_marks) * 100
        report_lines.append(f"-------------------------------")
        report_lines.append(f"📈 Total: {total_obtained}/{total_marks} ({overall_percent:.1f}%)")
        report_lines.append(f"===============================")
        report_lines.append(f"📝 Review:")

        # Generate review
        if weak_subjects:
            subjects_str = ", ".join([f"{s} ({p:.1f}%)" for s, p in weak_subjects])
            report_lines.append(f"⚠ {name} needs to improve in: {subjects_str}.")
            report_lines.append(f"📌 Recommendation: Study at least 1-2 hours more daily focusing on weak areas. Try practicing past papers and stay consistent.")
        else:
            report_lines.append(f"✅ Excellent performance. No weak subjects identified.")
            report_lines.append(f"🎯 Keep up the consistency. Continue regular study habits to maintain this performance.")

        reports.append("\n".join(report_lines))

    return "\n\n".join(reports)

# Define the agent with improved instructions
agent = Agent(
    name="admin",
    instructions="""
    You are a report generating assistant. You help teachers by creating student performance reports from Excel files.
    You MUST include: Student Name, ID, Class, Subject-wise marks, Total percentage, and a review.
    The review should be clear, helpful, and tailored to student needs.
    """,
    tools=[generate_student_report]
)

async def main():
    result=await Runner.run(agent,input="generate a report of students giving in excel file file_reader/excel_sheet.csv ",run_config=config)
    print (result.final_output)

# asyncio.run(main())