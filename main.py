import os
# Crewai imports
from crewai import Crew, Process
# Tools
import my_tasks
# Agents
import my_agents

# Define the Crew with the agent and tasks
crew = Crew(
    agents=[my_agents.email_summarizer, my_agents.event_creater],
    tasks=[my_tasks.email_summary_task, my_tasks.create_event_task],
    process=Process.sequential,
    verbose=True,
)

# Start the Crew
result = crew.kickoff()
print(result)
