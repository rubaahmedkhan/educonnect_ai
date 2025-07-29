from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, ModelSettings,function_tool
from agents.run import RunConfig
import pandas as pd


gemini_api_key = "gemini_key"


# Check if the API key is present; if not, raise an error
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")

#Reference: https://ai.google.dev/gemini-api/docs/openai
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
model_settings = ModelSettings(
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

# Global variable to store dataframe (will be injected)
df: pd.DataFrame = None

@function_tool
def get_student_data() -> dict:
    """Return uploaded student data as dictionary"""
    return df.to_dict()

def get_agent_runner_with_data(dataframe: pd.DataFrame):
    global df
    df = dataframe  # inject CSV data globally

    agent = Agent(
        name="Student Feedback Agent",
        instructions="""
You are an education feedback assistant. You must always use the 'get_student_data' tool to access student data.
Each row in the data is a student with fields like name, class, and obtained marks.
For **each student**, provide a short, personalized **feedback and recommendation** based on their class and obtained marks.
""",
        tools=[get_student_data],
    )

    return Runner(agent,input="give me student feedback",run_config=config)


