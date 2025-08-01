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
    model_settings=ModelSettings(tool_choice="required"),
    tracing_disabled=True,
)

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

    df.columns = df.columns.str.strip()  # Clean headers

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

# Runner
# async def main():
#     result = await Runner.run(
#         agent,
#         input="Generate a detailed student report using the Excel file at file_reader/excel_sheet.csv",
#         run_config=config
#     )
#     print(result.final_output)

# asyncio.run(main())