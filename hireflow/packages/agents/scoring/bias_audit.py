"""
Bias audit — SC-008.

Compares the demographic distribution of the shortlisted candidates
against the full applicant pool.  For MVP, gender is the only dimension
(inferred from first name using a lightweight heuristic when recruiter
consent is obtained).

Flags if a demographic group is under- or over-represented by more than
20 percentage points versus the applicant pool baseline.
"""

import re

_FEMALE_NAMES = {
    # Common Indian female names (subset — extend with a proper dataset)
    "priya", "anjali", "neha", "pooja", "shruti", "kavya", "ananya", "divya",
    "deepa", "meera", "radhika", "simran", "riya", "tanvi", "swati", "nisha",
    "rekha", "sunita", "geeta", "shweta", "pallavi", "sneha", "ritika", "asha",
    "suman", "usha", "savita", "archana", "rani", "shilpa", "vandana", "manisha",
    "bhavna", "ruchi", "gayatri", "sudha", "lalitha", "radha", "kamla", "pushpa",
    "lakshmi", "revathi", "sridevi", "padmaja", "harini", "keerthi", "sowmya",
    "nithya", "deepthi", "saranya", "ramya", "brinda", "hema", "vijayalakshmi",
    "nandita", "tara", "champa", "preeti", "jasmine", "fatima", "zara", "ayesha",
    "sara", "aisha", "noor", "mariam", "shabana", "zainab", "rosy", "mary",
    "alice", "angel", "grace", "mercy", "sharon", "diana",
}

_MALE_NAMES = {
    "rahul", "amit", "raj", "arun", "vijay", "suresh", "ravi", "kumar", "ajay",
    "sanjay", "deepak", "vikram", "ankit", "manish", "nitin", "rohit", "mohit",
    "arjun", "karan", "akash", "vishal", "tushar", "gaurav", "pranav", "shubham",
    "aman", "varun", "harsh", "yash", "sidharth", "kartik", "abhinav", "abhishek",
    "vikas", "dinesh", "ramesh", "ganesh", "sunil", "anil", "mahesh", "pradeep",
    "rakesh", "naresh", "girish", "harish", "rajesh", "umesh", "ashok", "pramod",
    "manoj", "santosh", "satish", "lokesh", "mukesh", "rakesh", "devesh", "umesh",
    "sachin", "kapil", "rohan", "nikhil", "ritesh", "hitesh", "rajat", "lalit",
    "saurabh", "sumit", "tarun", "vivek", "pankaj", "sandeep", "naveen", "praveen",
    "rajan", "sohan", "mohan", "krishna", "balaji", "venkat", "subramaniam",
    "murali", "senthil", "karthik", "selvam", "mani", "durai", "balachandran",
    "ali", "hassan", "ibrahim", "imran", "farhan", "adil", "sahil", "zaid",
}

_DISPARITY_THRESHOLD = 0.20   # 20 pp


def infer_gender(name: str | None) -> str:
    """Return 'female', 'male', or 'unknown'."""
    if not name:
        return "unknown"
    first = re.split(r"[\s,]+", name.strip())[0].lower()
    if first in _FEMALE_NAMES:
        return "female"
    if first in _MALE_NAMES:
        return "male"
    return "unknown"


def run_bias_audit(
    all_candidate_names: list[str | None],
    shortlisted_names: list[str | None],
) -> dict:
    """Compare gender distribution between all applicants and shortlist.

    Returns:
        {
            "passed": bool,
            "disparity_detected": bool,
            "pool": {"female": %, "male": %, "unknown": %},
            "shortlist": {"female": %, "male": %, "unknown": %},
            "max_disparity": float,
        }
    """
    pool_dist = _distribution([infer_gender(n) for n in all_candidate_names])
    shortlist_dist = _distribution([infer_gender(n) for n in shortlisted_names])

    max_disparity = 0.0
    for gender in ("female", "male"):
        disparity = abs(shortlist_dist.get(gender, 0) - pool_dist.get(gender, 0))
        max_disparity = max(max_disparity, disparity)

    # Don't flag if we have too little data
    has_enough_data = (
        len(all_candidate_names) >= 5
        and sum(1 for n in all_candidate_names if infer_gender(n) != "unknown") >= 3
    )

    disparity_detected = has_enough_data and max_disparity > _DISPARITY_THRESHOLD
    passed = not disparity_detected

    return {
        "passed": passed,
        "disparity_detected": disparity_detected,
        "pool": pool_dist,
        "shortlist": shortlist_dist,
        "max_disparity": round(max_disparity, 3),
    }


def _distribution(genders: list[str]) -> dict:
    total = len(genders)
    if total == 0:
        return {"female": 0.0, "male": 0.0, "unknown": 0.0}
    counts: dict[str, int] = {"female": 0, "male": 0, "unknown": 0}
    for g in genders:
        counts[g] = counts.get(g, 0) + 1
    return {k: round(v / total, 3) for k, v in counts.items()}
