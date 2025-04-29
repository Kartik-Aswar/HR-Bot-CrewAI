from typing import List

from src.lead_score_flow.type import Candidate, CandidateScore, ScoredCandidate
import csv

"""LIst of candidate be like :
[
  Candidate(id="1", name="Alice", email="alice@email.com", bio="Data Scientist", skills="Python, ML"),
  Candidate(id="2", name="Bob", email="bob@email.com", bio="Web Developer", skills="HTML, CSS")
]

list of candidate score be like : 
[
  CandidateScore(id="1", score=90, reason="Excellent ML skills"),
  CandidateScore(id="2", score=75, reason="Good front-end skills")
]
"""
def combine_candidates_with_scores(
    candidates: List[Candidate], candidate_scores: List[CandidateScore]
) -> List[ScoredCandidate]:
    """
    Combine the candidates with their scores using a dictionary for efficient lookups.
    """
    print("\n" + "#" * 80)
    print("COMBINING CANDIDATES WITH SCORES")
    print("#" * 80 + "\n")

    # Print candidate scores
    print(">>> SCORES:")
    for score in candidate_scores:
        print(f"ID: {score.id}\n | Score: {score.score}\n | Reason: {score.reason}\n")
    print("\n" + "-" * 80 + "\n")

    # Print candidates
    print(">>> CANDIDATES:")
    for candidate in candidates:
        print(f"ID: {candidate.id}\n | Name: {candidate.name}\n | Email: {candidate.email}\n")
    print("\n" + "-" * 80 + "\n")

    # Create a dictionary to map score IDs to their corresponding CandidateScore objects
    score_dict = {score.id: score for score in candidate_scores}

    """ score_dict is like              
    {
    "1": CandidateScore(id="1", score=90, reason="Excellent ML skills"),
    "2": CandidateScore(id="2", score=75, reason="Good front-end skills")
    }
    """
    print(">>> SCORE DICT (id -> CandidateScore):")
    for id, score in score_dict.items():
        print(f"\n{id}: {score}\n")
    print("\n" + "=" * 80 + "\n")

    scored_candidates = []
    for candidate in candidates:
        score = score_dict.get(candidate.id)
        if score:
            scored_candidates.append(
                ScoredCandidate(
                    id=candidate.id,
                    name=candidate.name,
                    email=candidate.email,
                    bio=candidate.bio,
                    skills=candidate.skills,
                    score=score.score,
                    reason=score.reason,
                )
            )

    # Print scored candidates
    print(">>> SCORED CANDIDATES:")
    for sc in scored_candidates:
        print(
            f"ID: {sc.id}\n"
            f"Name: {sc.name}\n"
            f"Email: {sc.email}\n"
            f"Score: {sc.score}\n"
            f"Reason: {sc.reason}\n" + "-" * 80
        )
    print("\n" + "#" * 80 + "\n")

    # Write scored candidates to CSV
    with open("lead_scores.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "email", "score"])
        for candidate in scored_candidates:
            writer.writerow(
                [
                    candidate.id,
                    candidate.name,
                    candidate.email,
                    candidate.score
                ]
            )

    print("✅ Lead scores saved to lead_scores.csv\n")
    return scored_candidates
