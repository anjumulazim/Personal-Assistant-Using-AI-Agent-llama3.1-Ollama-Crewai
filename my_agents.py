# Crewai imports
from crewai import Agent
# Import tools
import my_tools
# Imports for LLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms.ollama import Ollama

# Configuring the LLM
llm = Ollama(
    base_url="http://localhost:11434",
    model="llama3.1",  # Use the model that works best
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
    temperature=0.0,
)


# Define the Email Summarizer Agent
email_summarizer = Agent(
    role="Email summariser",
    goal="To summarise email in bullet points",
    backstory="You go through mails and write easy to understand bullet point summary of it.",
    llm=llm,  # Replace with your LLM instance
    tools=[my_tools.getGmail],  # List of tools the agent can use
    verbose=True,
)

event_creater = Agent(
    role="Google calendar event creater.",
    goal="To create the event based on the email.",
    backstory="You create google calendar events based on the email summary provided by the email summariser",
    llm=llm,
    tools=[my_tools.create_event],
    verbose=True,
)
