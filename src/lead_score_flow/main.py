
import asyncio
from typing import List
from uuid import uuid4
from crewai.flow.flow import Flow, listen, or_, router, start
from pydantic import BaseModel

from src.lead_score_flow.constants import JOB_DESCRIPTION
from src.lead_score_flow.crews.lead_response_crew.lead_response_crew import LeadResponseCrew
from src.lead_score_flow.crews.lead_score_crew.lead_score_crew import LeadScoreCrew
from src.lead_score_flow.type import Candidate, CandidateScore, ScoredCandidate
from src.lead_score_flow.utils.candidateUtils import combine_candidates_with_scores


class LeadScoreState(BaseModel):
    id: str = str(uuid4())
    candidates: List[Candidate] = []
    candidate_score: List[CandidateScore] = []
    hydrated_candidates: List[ScoredCandidate] = []
    scored_leads_feedback: str = ""


class LeadScoreFlow(Flow[LeadScoreState]):
    initial_state = LeadScoreState

    @start()
    def load_leads(self):
        import csv
        from pathlib import Path

        # Get the path to leads.csv in the same directory
        current_dir = Path(__file__).parent # .parent is like cd . means moving to the previous folder
        #__file__ is a special Python variable. It automatically contains the path of the Python script that is currently being run means main.py .
        #Path comes from the pathlib module. It's a modern, powerful way to handle file paths in Python. Path(__file__) wraps the file path into a Path object so you can do useful things with it.
        csv_file = current_dir / "leads.csv"
        #it means csv_file is located at the same folder the main.py file is located
        candidates = []
        with open(csv_file, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Create a Candidate object for each row
                print("Row:", row)
                candidate = Candidate(**row)#Create a new Candidate object by filling its fields using the row dictionary.
                #The ** is Python’s "unpacking operator". It unpacks the dictionary into named arguments.
                candidates.append(candidate)

        # Update the state with the loaded candidates
        self.state.candidates = candidates

    @listen(or_(load_leads, "scored_leads_feedback"))#load_leads is a function (you can reference it directly).
    #scored_leads_feedback is a variable inside the LeadScoreState model, NOT a function, so you need to give its name as a string "scored_leads_feedback".
    
    async def score_leads(self):#async means the function can wait for things like API calls without blocking the program.
        print("Scoring leads")
        tasks = []

        async def score_single_candidate(candidate: Candidate):
            try:
                result = await (   # await is used because it is async call
                    LeadScoreCrew()
                    .crew()
                    .kickoff_async(
                        inputs={
                            "candidate_id": candidate.id,
                            "name": candidate.name,
                            "bio": candidate.bio,
                            "job_description": JOB_DESCRIPTION,
                            "additional_instructions": self.state.scored_leads_feedback,
                        }
                    )
                )
                return result
            except Exception as e:
                print(f"Error scoring candidate {candidate.name}: {e}")
                return e
            # Scoring is truly happening inside score_single_candidate() but the candidates are sent by the task below 
            """
            task = asyncio.create_task(score_single_candidate(candidate))
            is just creating async tasks to call score_single_candidate(candidate) for each candidate.

            It does not do the scoring itself —
            it sets up the work.

            And then:

            candidate_scores = await asyncio.gather(*tasks)
            triggers all tasks to run together —
            and they each internally call score_single_candidate() to do scoring."""

            #self.state.candidate_score.append(result.pydantic) #result.pydantic — means the AI result is converted into a Pydantic object (of type CandidateScore).
                #You add this score to the candidate_score list inside the Flow’s state.

        for candidate in self.state.candidates:
            print("Scoring candidate:", candidate.name)
            task = asyncio.create_task(score_single_candidate(candidate))#Create an asynchronous task that will score this candidate in the background.
            #score_single_candidate(candidate) is called inside asyncio.create_task(), which means it starts but doesn't block the program.
            tasks.append(task)
            # Example: For Alice, you create task1 = score_single_candidate(Alice)
                       #For Bob, you create task2 = score_single_candidate(Bob)

        candidate_scores = await asyncio.gather(*tasks)
        for idx, result in enumerate(candidate_scores):
            if isinstance(result, Exception):
                print(f"Scoring failed for candidate {self.state.candidates[idx].name}: {result}")
            else:
                self.state.candidate_score.append(result.pydantic)#result.pydantic — means the AI result is converted into a Pydantic object (of type CandidateScore).
                #You add this score to the candidate_score list inside the Flow’s state.

        print(f"Finished scoring {len(self.state.candidate_score)} leads successfully out of {len(self.state.candidates)}")
        """Run all the tasks at once (concurrently).

            await asyncio.gather(*tasks) means:

            Start all scoring operations

            Wait until all of them are finished.

            After completion, it returns a list of their results into candidate_scores."""

    @router(score_leads)
    def human_in_the_loop(self):
        print("Finding the top 3 candidates for human to review")

        # Combine candidates with their scores using the helper function
        self.state.hydrated_candidates = combine_candidates_with_scores(
            self.state.candidates, self.state.candidate_score
        )

        # Sort the scored candidates by their score in descending order
        sorted_candidates = sorted(
            self.state.hydrated_candidates, key=lambda c: c.score, reverse=True )
            #key → tells Python on what basis it should sort the list.
            #Here,nlambda c: c.score → means: → For each candidate c, use c.score as the value to sort on.
        self.state.hydrated_candidates = sorted_candidates

        # Select the top 3 candidates
        top_candidates = sorted_candidates[:3]

        print("\n")
        print("#####################################################################")
        print("** Human in the Loop **")

        print("Here are the top 3 candidates:")
        for candidate in top_candidates:
            print(
                f"ID: {candidate.id}\nName: {candidate.name}\nScore: {candidate.score}\nReason: {candidate.reason}\n"
            )
            print("#" * 80)


        # Present options to the user
        print("\nPlease choose an option:")
        print("1. Quit\n")
        print("2. Redo lead scoring with additional feedback\n")
        print("3. Proceed with writing emails to all leads\n")

        choice = input("Enter the number of your choice: ")

        if choice == "1":
            print("Exiting the program.")
            exit()
        elif choice == "2":
            feedback = input(
                "\nPlease provide additional feedback on what you're looking for in candidates:\n"
            )
            self.state.scored_leads_feedback = feedback
            print("\nRe-running lead scoring with your feedback...")
            return "scored_leads_feedback"
        elif choice == "3":
            print("\nProceeding to write emails to all leads.")
            return "generate_emails"
        else:
            print("\nInvalid choice. Please try again.")
            return "human_in_the_loop"

    @listen("generate_emails")
    async def write_and_save_emails(self):
        import re
        from pathlib import Path

        print("Writing and saving emails for all leads.")

        # Determine the top 3 candidates to proceed with
        top_candidate_ids = {
            candidate.id for candidate in self.state.hydrated_candidates[:3]
        }

        tasks = []

        # Create the directory 'email_responses' if it doesn't exist
        output_dir = Path(__file__).parent / "email_responses"
        print("output_dir:", output_dir)
        output_dir.mkdir(parents=True, exist_ok=True) #output_dir.mkdir()	Make a new folder at the path output_dir
        #parents=True	If any parent folders in the path are missing, create them too.like if output_dir is a/project/email_responses/ and project is not present then create project folder useless here as the path is taken from the code only above 
        #exist_ok=True	If the folder already exists, don't give an error.

        async def write_email(candidate):
            # Check if the candidate is among the top 3
            proceed_with_candidate = candidate.id in top_candidate_ids

            # Kick off the LeadResponseCrew for each candidate
            result = await (
                LeadResponseCrew()
                .crew()
                .kickoff_async(
                    inputs={
                        "candidate_id": candidate.id,
                        "name": candidate.name,
                        "bio": candidate.bio,
                        "proceed_with_candidate": proceed_with_candidate,
                    }
                )
            )

            # Sanitize the candidate's name to create a valid filename
            safe_name = re.sub(r"[^a-zA-Z0-9_\- ]", "", candidate.name) #re.sub(pattern, replacement, text) → means find all parts matching the pattern and replace them.
            filename = f"{safe_name}.txt"#r"[^a-zA-Z0-9_\- ]" means If any character is not a letter, number, underscore, hyphen, or space, remove it.
            print("Filename:", filename)

            # Write the email content to a text file
            file_path = output_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result.raw)

            # Return a message indicating the email was saved
            return f"Email saved for {candidate.name} as {filename}"

        # Create tasks for all candidates
        for candidate in self.state.hydrated_candidates:
            task = asyncio.create_task(write_email(candidate))
            """ Meaning:
            → Start writing an email for candidate in background (not blocking).
            → Python will schedule it and move to the next candidate immediately."""
            tasks.append(task)

        # Run all email-writing tasks concurrently and collect results
        email_results = await asyncio.gather(*tasks)
        """Now, *await asyncio.gather(tasks) means:

        Wait for all the tasks (email writings) to finish.

        Collect their return values into email_results."""
        # After all emails have been generated and saved
        print("\nAll emails have been written and saved to 'email_responses' folder.")
        for message in email_results:
            print(message)


def kickoff():
    """
    Run the flow.
    """
    lead_score_flow = LeadScoreFlow()
    lead_score_flow.kickoff()


def plot():
    """
    Plot the flow.
    """
    lead_score_flow = LeadScoreFlow()
    lead_score_flow.plot()


if __name__ == "__main__":
    kickoff()
