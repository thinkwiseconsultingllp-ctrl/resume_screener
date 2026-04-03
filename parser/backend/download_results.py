import csv
from django.http import HttpResponse

def download_results_csv(candidates,resumes):
    if not candidates:
        return HttpResponse("No results available", status=400)

    # Prepare response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="comparison_results.csv"'

    writer = csv.writer(response)

    # Header
    writer.writerow([
        "Name", "Email", "Candidate Snapshot", "Current Job Title",
        "Total Experience", "Skills Match", "Domain Match",
        "Measurable Impact", "Matching Skills", "Missing Skills",
        "Score", "Rating"
    ])
    results=zip(candidates,resumes)
    # Rows
    for result, resume in results:
        job_title = result["career_details"].get("Current_Last_Job_Title") or \
                    result["career_details"].get("Current_Job_Title") or "Not available"

        writer.writerow([
            resume.get("Name", ""),
            resume.get("Email", ""),
            result.get("candidate_snapshot", ""),
            job_title,
            result["career_details"].get("Total_Years_of_Experience", ""),
            result["evaluation"].get("Skills_Match", ""),
            result["evaluation"].get("Domain_Industry_Relevance", ""),
            result["evaluation"].get("Measurable_Impact", ""),
            ", ".join(result.get("matched_skills", [])),
            ", ".join(result.get("missing_skills", [])),
            result["evaluation"].get("Total_score", ""),
            result.get("rating", "")
        ])

    return response
