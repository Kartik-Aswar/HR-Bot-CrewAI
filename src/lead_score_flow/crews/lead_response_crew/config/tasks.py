from crewai import Task
from src.lead_score_flow.crews.lead_response_crew.config.agents import email_followup_agent


send_followup_email =Task(
  description = """Compose personalized follow-up emails for candidates who applied to a specific job.

    You will use the candidate's name, bio, and whether the company wants to proceed with them to generate the email. 
    If the candidate is proceeding, ask them for their availability for a Zoom call in the upcoming days. 
    If not, send a polite rejection email.

    CANDIDATE DETAILS
    -----------------
    Candidate ID: {candidate_id}
    Name: {name}
    Bio:
    {bio}

    PROCEEDING WITH CANDIDATE: {proceed_with_candidate}

    ADDITIONAL INSTRUCTIONS
    -----------------------
    - If we are proceeding, ask for their availability for a Zoom call within the next few days.
    - If we are not proceeding, send a polite rejection email, acknowledging their effort in applying and appreciating their time.""",

  expected_output = 
    "A personalized email based on the candidate's information. It should be professional and respectful, either inviting them for a Zoom call or letting them know we are pursuing other candidates.",
  agent = email_followup_agent
  
)