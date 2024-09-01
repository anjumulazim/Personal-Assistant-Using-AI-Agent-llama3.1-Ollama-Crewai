from crewai import Task
import my_agents

# Task to summarize the email
email_summary_task = Task(
    description="Search for the latest mail and summarise it in 7-bullet points.",
    expected_output="7 bullet point summary of email.",
    agent=my_agents.email_summarizer,
)

# Task to create google calendar event
create_event_task = Task(
    description="Get the email summary and then create a google calendar event based on the context.",
    expected_output="A confirmation if the event was creates successfully along with the event link",
    agent=my_agents.event_creater,
)
