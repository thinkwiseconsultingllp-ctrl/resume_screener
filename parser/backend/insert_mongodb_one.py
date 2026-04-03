import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI")

def update_candidate_evaluation(filename, evaluation_data, db_name="resumeDB", collection_name="ai_evaluations"):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    try:
        result = collection.update_one(
            {"filename": filename},
            {"$set": {"filename": filename, "evaluation_result": evaluation_data}},
            upsert=True
        )
        print(f"Saved evaluation for {filename}: modified={result.modified_count}, upserted={result.upserted_id is not None}")
    except Exception as e:
        print(f"Error updating evaluation for {filename}: {e}")

# Your exact JSON results formatted as Python dictionaries
manual_results = {
    "chandana_d_20251231_133628_Pratishtha Bisht_product.pdf": { # <--- CHANGE THIS to actual filename
        "candidate_snapshot": "Pratishtha Bisht is an Associate Product Manager with 2.6 years of experience in product management roles at 91trucks and Blinkit. She possesses skills in product lifecycle management, A/B testing, cross-functional collaboration, and tools like Notion, Jira, and Mixpanel. Her experience aligns with product management in tech but falls short of the 3-6 years required for the role.",
        "career_details": {
            "current_last_job_title": "Senior Executive (Search & Cataloguing)",
            "total_years_of_experience": 2.6,
            "companies": ["91trucks", "Blinkit"],
            "job_titles": ["Associate Product Manager", "Senior Executive (Search & Cataloguing)"],
            "duration_per_role": ["0.5 years", "2.1 years"]
        },
        "role_fit": "The candidate's product management experience and skills align with the role's requirements, but her total experience (2.6 years) is below the 3-6 years specified. Seniority (L4-L5) may require further evaluation.",
        "skill_match": "Strong overlap in core skills like product lifecycle management, A/B testing, cross-functional collaboration, and tools (Notion, Jira, Mixpanel). Missing finance-specific product experience and tools like Figma/Amplitude.",
        "measurable_impact": "No measurable KPIs or result-based statements provided in the resume.",
        "domain": "Limited direct exposure to finance or AI domains. Experience in product management within tech/B2B SaaS.",
        "education_match": "Satisfied",
        "locality": "India (relocation to Hyderabad possible)",
        "red_flags": ["Total experience (2.6 years) below the required 3-6 years", "No direct finance/AI product experience"],
        "matched_skills": ["product lifecycle management", "A/B testing", "cross-functional collaboration", "Notion", "Jira", "Mixpanel"],
        "missing_skills": ["Figma", "Amplitude", "finance-related product experience"],
        "evaluation": {"experience_match": 60, "skills_match": 80, "measurable_impact": 0, "domain_industry_relevance": 50, "total_score": 65},
        "rating": "✅Good Fit"
    },
    "chandana_d_20251231_133627_Nitin_Sharma_14years_exp.docx": { # <--- CHANGE THIS to actual filename
        "candidate_snapshot": "Nitin Sharma is a seasoned QA professional with 14 years of experience in test engineering and management roles. His expertise lies in automation, CI/CD, and technical testing, but lacks direct product management or B2B SaaS product experience. The role requires product management skills, which are not present in his profile.",
        "career_details": {
            "current_last_job_title": "Test Engineering Manager",
            "total_years_of_experience": 7.25,
            "companies": ["Rapido", "TrustingSocial", "WalmartLabs"],
            "job_titles": ["Test Engineering Manager", "Lead SDET", "Senior Test Engineer"],
            "duration_per_role": ["4 years", "1.5 years", "1.75 years"]
        },
        "role_fit": "The candidate's background in QA and testing does not align with the Associate Product Manager role, which requires product management experience. His technical skills are strong but not relevant to the job's core requirements.",
        "skill_match": "The resume lacks product management, customer research, and B2B SaaS product experience required by the JD. Technical skills like CI/CD and automation are present but not applicable to the role.",
        "measurable_impact": "No measurable KPIs or result-based statements related to product management or B2B SaaS are present in the resume.",
        "domain": "No exposure to finance data orchestration, AI-driven B2B SaaS, or similar domains.",
        "education_match": "Satisfied",
        "locality": "Hyderabad (location specified in JD, but resume does not mention relocation willingness)",
        "red_flags": [],
        "matched_skills": [],
        "missing_skills": ["product management", "customer discovery", "B2B SaaS product experience", "roadmapping", "user story creation", "UX validation"],
        "evaluation": {"experience_match": 30, "skills_match": 20, "measurable_impact": 0, "domain_industry_relevance": 10, "total_score": 60},
        "rating": "❌Poor Fit"
    },
    "chandana_d_20251231_133614_Resume Affaf Shaikh.pdf": { # <--- CHANGE THIS to actual filename
        "candidate_snapshot": "Affaf Shaikh candidate has extensive technical experience in backend development and ERPNext integration but lacks direct product management experience. His profile is strong in technical skills but may not align with the product-focused requirements of the role.",
        "career_details": {
            "current_last_job_title": "ERPNext Integration",
            "total_years_of_experience": 5,
            "companies": ["Detente Technologies Pvt Ltd", "Haider Holding", "JMJ Group Holding", "Self"],
            "job_titles": ["Backend Developer", "Python Developer (System Integration - ErpNext)", "Customization & Integration", "Backend Developer", "ERPNext Integration"],
            "duration_per_role": ["1 year", "1 year", "1 year", "1 year", "1 year"]
        },
        "role_fit": "The candidate's experience is primarily in technical roles (backend, ERPNext) rather than product management, which is a core requirement for the Associate Product Manager position. This mismatch reduces role fit.",
        "skill_match": "Limited overlap. The candidate has technical skills (Python, ERPNext) but lacks product management, account/subscription product, or UX tools experience required for the role.",
        "measurable_impact": "No measurable KPIs or performance indicators provided in the resume.",
        "domain": "Yes, exposure to ERPNext (an ERP system) which is relevant to finance data management.",
        "education_match": "Not satisfied. The JD requires 3-6 years in product, engineering, UX, or customer-facing roles. The candidate has engineering education but no product management experience.",
        "locality": "Ambiguous - Needs Clarification. The resume does not specify the candidate's current location or relocation willingness.",
        "red_flags": ["Frequent job changes (5 roles in 2 years)", "Lack of product management experience"],
        "matched_skills": ["ERPNext"],
        "missing_skills": ["Product management", "Account/subscription products", "Figma", "Mixpanel", "Amplitude", "Customer research", "A/B testing"],
        "evaluation": {"experience_match": 50, "skills_match": 40, "measurable_impact": 0, "domain_industry_relevance": 70, "total_score": 41},
        "rating": "❌Average Fit"
    },
    "chandana_d_20251230_143726_GSR_ProdMan.pdf": { # <--- CHANGE THIS to actual filename
        "candidate_snapshot": "Sridhar Reddy Gadila is an experienced product manager with over 23 years of expertise in product strategy, agile delivery, and SaaS solutions. His background includes roles at Genpact and Mother Dairy, with skills in cloud platforms, stakeholder engagement, and finance systems. He holds certifications in Scrum and Lean Six Sigma, aligning with the technical and operational demands of the role.",
        "career_details": {
            "current_last_job_title": "Business Systems Analyst / Technical Lead",
            "total_years_of_experience": 23.16,
            "companies": ["Stic Soft E-Solutions Pvt. Ltd.", "Truetech Solutions Pvt. Ltd.", "Nath Agro Products", "Genpact India Ltd.", "Polaris Software Labs Ltd.", "GE Capital – IPointsoft Technologies", "Mother Dairy India Ltd."],
            "job_titles": ["Product Manager", "Product Manager – Agile Delivery", "Founder | Strategy Consultant – AgriTech", "Product Manager / Program Manager / Lead Consultant – IT Products", "Business Systems Analyst / Technical Lead", "Business Analyst (Consultant Role)", "Assistant Manager – Finance Systems (Functional Analyst)"],
            "duration_per_role": ["0.25 years", "0.58 years", "5 years", "11 years", "1 year", "0.33 years", "5 years"]
        },
        "role_fit": "The candidate's extensive experience as a Senior Product Manager exceeds the Associate level requirement, which may require adjustment in role expectations or seniority alignment.",
        "skill_match": "Strong overlap in core skills like product strategy, agile delivery, stakeholder engagement, and SaaS expertise. Missing some good-to-have tools (Figma, Mixpanel, Amplitude) but compensates with finance domain experience.",
        "measurable_impact": "Improved sprint velocity via process optimization, managed KPIs and product dashboards, delivered feasibility analysis, and optimized financial workflows.",
        "domain": "Finance systems and AgriTech experience align with the finance data orchestration focus of the role.",
        "education_match": "Satisfied",
        "locality": "Ambiguous - Needs Clarification",
        "red_flags": ["Extensive experience (23+ years) may not align with Associate-level expectations.", "Frequent role changes (7 roles in 23 years) could indicate instability.", "No explicit mention of relocation willingness to Hyderabad."],
        "matched_skills": ["Product Strategy & Roadmaps", "Agile Product Ownership", "Stakeholder Engagement", "Backlog Prioritization", "Cloud & SaaS Products", "Business Analysis", "Agile Delivery"],
        "missing_skills": ["Figma", "Mixpanel", "Amplitude"],
        "evaluation": {"experience_match": 100, "skills_match": 95, "measurable_impact": 80, "domain_industry_relevance": 90, "total_score": 94},
        "rating": "✅✅Best Fit"
    }
}

if __name__ == "__main__":
    for filename, eval_data in manual_results.items():
        update_candidate_evaluation(filename, eval_data)
    print("Done inserting manual records.")