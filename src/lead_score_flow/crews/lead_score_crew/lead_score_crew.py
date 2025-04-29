from crewai import Agent, Crew, Process, Task
# from crewai.project import CrewBase, agent, crew, task
from src.lead_score_flow.type import CandidateScore

from src.lead_score_flow.crews.lead_score_crew.config.agents import hr_evaluation_agent
from src.lead_score_flow.crews.lead_score_crew.config.tasks import evaluate_candidate

class LeadScoreCrew:
    """Lead Score Crew"""
    def __init__(self):
        self.evaluator_agent = hr_evaluation_agent
        self.evaluator = evaluate_candidate

    
    def crew(self) -> Crew:
        """Creates the Lead Score Crew"""
        # Assigning agents to the task 

        self.evaluator.agent=self.evaluator_agent

        return Crew(
            agents=[self.evaluator_agent],
            tasks=[self.evaluator],
            process=Process.sequential,
            verbose=True,
        )
