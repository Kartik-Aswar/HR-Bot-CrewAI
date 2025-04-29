from crewai import Crew, Process

from src.lead_score_flow.crews.lead_response_crew.config.agents import email_followup_agent
from src.lead_score_flow.crews.lead_response_crew.config.tasks import send_followup_email


class LeadResponseCrew:
    """Lead Response Crew"""

    def __init__(self):
        self.email_agent = email_followup_agent
        self.email_task = send_followup_email

    
    def crew(self) -> Crew:
        """Creates the Lead Response Crew"""

        # assigning agent to task

        self.email_task.agent = self.email_agent
        return Crew(
            agents=[self.email_agent],
            tasks=[self.email_task],
            process=Process.sequential,
            verbose=True,
        )
