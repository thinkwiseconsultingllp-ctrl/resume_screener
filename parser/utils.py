import os
import tempfile
from parser.backend import resume_structuring, db_functions, compare_with_jd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.chains import LLMChain
from pymongo import MongoClient
import json
from django.conf import settings
import re


client = MongoClient(os.getenv("MONGO_URI"))
db = client['resumeDB']
collection=db['resume_parser']

with open(os.path.join(settings.BASE_DIR, "parser/prompts/structuring_prompt.txt"),encoding="utf8") as f:
    resume_structuring_prompt = f.read()

with open(os.path.join(settings.BASE_DIR, "parser/prompts/comparison_prompt.txt"),encoding="utf8") as f:
    Resume_screening_prompt = f.read()

def handle_uploaded_resumes(files):
    temp_dir = tempfile.mkdtemp()
    file_paths = []
    for file in files:
        path = os.path.join(temp_dir, file.name)
        with open(path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        file_paths.append(path)
    chain = structuring_chain()
    df = resume_structuring.creating_df(files)
    structured = resume_structuring.structuring_process(df, chain)
    db_functions.save_data_to_mongo(structured)
    filenames = [entry['filename'] for entry in structured]
    return filenames

def structuring_chain():
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
    prompt = PromptTemplate.from_template(resume_structuring_prompt)
    chain = prompt | llm | StrOutputParser()
    return chain

def extract_and_structure(files,jd):
    # Extract and structure resumes
    file_paths=handle_uploaded_resumes(files)
    chain = structuring_chain()
    df = resume_structuring.creating_df(files)
    structured = resume_structuring.structuring_process(df,chain)
    db_functions.save_data_to_mongo(structured)
    filenames = [entry['filename'] for entry in structured]
    return filenames

def fetch_relevant_from_db(jd_text, collection):
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    extract_prompt = PromptTemplate.from_template("""
    Extract job domain, primary skills, and title from this job description:
    {job_description}
    Return in json with keys 'domain', 'primary_skills', 'title'.
    """)
    fetching_llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
    extractor_chain = extract_prompt | fetching_llm | StrOutputParser()

    info_json = extractor_chain.invoke({"job_description": jd_text})
    info = json.loads(info_json)
    domain = info.get("domain", "")
    skills = info.get("primary_skills", [])
    title = info.get("title", "")

    query = {"$or": [
        {"Domain": {"$regex": domain, "$options": "i"}},
        {"Skills": {"$in": skills}},
        {"Experience.Position": {"$regex": title, "$options": "i"}}
    ]}
    return list(collection.find(query, {"_id": 0}))


def comparison_llm_initialisation():
    comparison_prompt = PromptTemplate(input_variables=["job_description", "resume"], template=Resume_screening_prompt)
    comparison_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GEMINI_API_KEY"),
                                             convert_system_message_to_human=True)
    comparison_chain = comparison_prompt | comparison_llm | StrOutputParser()
    return comparison_chain

comparing_chain = comparison_llm_initialisation()

def compare_resumes(resumes, jd):
    results = []
    for resume in resumes:
        if isinstance(resume, str):  # If filename, fetch from DB
            resume_data = collection.find_one({"filename": resume}, {"_id": False})
        else:
            resume_data = resume
        if resume_data:
            output = compare_with_jd.resume_comparison_with_jd(resume_data, jd,comparing_chain)
            try:
                parsed = json.loads(output[0])
                resume_data.update(parsed)
                results.append(resume_data)
            except:
                continue
    return results


def normalize_candidate_data(results):
    """
    Normalizes candidate data to handle inconsistent keys and formats
    """
    normalized_results = []

    for candidate in results:
        # Handle cases where data might be nested under 'Resume_Screener'
        if 'Resume_Screener' in candidate:
            candidate = candidate['Resume_Screener']

        normalized = {}

        # Normalize Candidate Snapshot keys
        if 'Candidate Snapshot' in candidate:
            normalized['Candidate_Snapshot'] = candidate['Candidate Snapshot']
        elif 'Candidate_Snapshot' in candidate:
            normalized['Candidate_Snapshot'] = candidate['Candidate_Snapshot']

        # Normalize Career Details keys
        if 'Career Details' in candidate:
            career_details = candidate['Career Details']
            normalized_career = {}

            # Normalize Career Detail subkeys
            if 'Current/Last Job Title' in career_details:
                normalized_career['Current_Job_Title'] = career_details['Current/Last Job Title']
            elif 'Current_Last_Job_Title' in career_details:
                normalized_career['Current_Job_Title'] = career_details['Current_Last_Job_Title']
            elif 'Current_Job_Title' in career_details:
                normalized_career['Current_Job_Title'] = career_details['Current_Job_Title']

            if 'Total Years of Experience' in career_details:
                normalized_career['Total_Years_of_Experience'] = career_details['Total Years of Experience']
            elif 'Total_Years_of_Experience' in career_details:
                normalized_career['Total_Years_of_Experience'] = career_details['Total_Years_of_Experience']

            normalized['Career_Details'] = normalized_career
        elif 'Career_Details' in candidate:
            normalized['Career_Details'] = candidate['Career_Details']

        # Normalize Role Fit keys
        if 'Role Fit' in candidate:
            normalized['Role_Fit'] = candidate['Role Fit']
        elif 'Role_Fit' in candidate:
            normalized['Role_Fit'] = candidate['Role_Fit']

        # Normalize Skill Match keys
        if 'Skill Match' in candidate:
            normalized['Skill_Match'] = candidate['Skill Match']
        elif 'Skill_Match' in candidate:
            normalized['Skill_Match'] = candidate['Skill_Match']

        # Normalize Tool/Tech Match keys
        if 'Tool/Tech Match' in candidate:
            normalized['Tool_Tech_Match'] = candidate['Tool/Tech Match']
        elif 'Tool_Tech_Match' in candidate:
            normalized['Tool_Tech_Match'] = candidate['Tool_Tech_Match']

        # Normalize Domain/Industry Match keys
        if 'Domain/Industry Match' in candidate:
            normalized['Domain_Industry_Match'] = candidate['Domain/Industry Match']
        elif 'Domain_Industry_Match' in candidate:
            normalized['Domain_Industry_Match'] = candidate['Domain_Industry_Match']

        # Normalize Red Flags keys
        if 'RED FLAGS' in candidate:
            normalized['RED_FLAGS'] = candidate['RED FLAGS']
        elif 'RED_FLAGS' in candidate:
            normalized['RED_FLAGS'] = candidate['RED_FLAGS']

        # Normalize Scoring/Evaluation keys
        if 'Scoring' in candidate:
            normalized['Evaluation'] = candidate['Scoring']
        elif 'Evaluation' in candidate:
            normalized['Evaluation'] = candidate['Evaluation']

        # Extract candidate name from snapshot if possible
        if 'Candidate_Snapshot' in normalized:
            snapshot = normalized['Candidate_Snapshot']
            name_match = re.search(r'^([A-Za-z\s]+)\s+is\s+a', snapshot)
            if name_match:
                normalized['Name'] = name_match.group(1).strip()

        normalized_results.append(normalized)

    return normalized_results