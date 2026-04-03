import os
from django.shortcuts import render, redirect
from django.contrib import messages

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from httpcore import request
from pymongo import MongoClient
from .forms import JDForm
from parser.backend import (creating_df,structuring_process,save_data_to_mongo,fetch_resumes, resumes_sending_to_comparison,text_df,update_candidate_evaluation,get_cached_evaluation)
from parser.backend.pdf_extraction_new import pdf_extraction,extract_text_from_docx
from dotenv import load_dotenv
load_dotenv()
from parser.chain import structuring_chain,comparison_llm_initialisation
import json
import re
from json_repair import repair_json
import pandas as pd
from django.http import HttpResponse
import csv
from datetime import date
from django.core.cache import cache
cache.clear()

structuring_chain= structuring_chain()
comparison_chain= comparison_llm_initialisation()

# MongoDB connection setup
client = MongoClient(os.getenv("MONGO_URI"))
resume_db = client['resumeDB']
collection = resume_db['resume_parser']


def parse_nested_results(nested_res):
    """Parse LLM comparison results from nested_res into a list of dicts."""
    parsed = []
    for res in nested_res:
        if isinstance(res, list):
            res = res[0]
        match = re.search(r'\{.*\}', str(res), re.DOTALL)
        if match:
            try:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError:
                    data = repair_json(match.group(0), return_objects=True)
                if isinstance(data, str): data = json.loads(data)
                
                if "Resume_Screener" in data:
                    parsed.append(data["Resume_Screener"])
                else:
                    parsed.append(data)
            except json.JSONDecodeError:
                print("Failed to parse JSON:", str(res)[:200])
    return parsed


def home(request):
    request.session.flush()
    print("In home view")
    storage=messages.get_messages(request)
    storage.used=True
    form = JDForm()
    if request.method == 'POST':
        print("Form submitted")
        form = JDForm(request.POST, request.FILES)
        print(form.errors)
        if form.is_valid():
            print("Form is valid")
            # Process job description (text or file)
            jd_text = form.cleaned_data.get('jd_text')
            jd_file = form.cleaned_data.get('jd_file')
            resume_text = form.cleaned_data.get('resume_text')
            source_choice = form.cleaned_data.get('source_choice')
            min_experience=form.cleaned_data.get('min_experience')
            must_have_skills=form.cleaned_data.get('must_have_skills')
            nice_to_have_skills=form.cleaned_data.get('nice_to_have_skills')
            role_expectations=form.cleaned_data.get('role_expectations')


            if min_experience:request.session['min_experience']=min_experience
            else: request.session['min_experience']=None
            if must_have_skills:request.session['must_have_skills']=must_have_skills
            else: request.session['must_have_skills']=None
            if nice_to_have_skills:request.session['nice_to_have_skills']=nice_to_have_skills
            else: request.session['nice_to_have_skills']=None
            if role_expectations:request.session['role_expectations']=role_expectations
            else: request.session['role_expectations']=None

            # Extract job description text
            job_description = None
            if jd_text:
                job_description = jd_text
            elif jd_file:
                try:
                    # Handle different file types if necessary
                    if jd_file.name.endswith('.pdf'):
                        print("Processing PDF job description")
                        job_description = pdf_extraction(jd_file)
                
                    elif jd_file.name.endswith('.docx'):
                        print("Processing DOCX job description")
                        try: 
                            job_description = extract_text_from_docx(jd_file)
                        except Exception as e:
                            print(f"Error processing DOCX job description: {e}")
                            from docx import Document
                            document = Document(jd_file)
                            job_description = "\n".join([p.text for p in document.paragraphs])

                    elif jd_file.name.endswith('.txt'):
                        raw_data = jd_file.read()
                        try:
                            job_description = raw_data.decode("utf-8")
                        except UnicodeDecodeError:
                            job_description = raw_data.decode("latin-1", errors="ignore")

                    else:
                        messages.error(request, "Unsupported file format. Please upload .txt, .pdf, or .docx")
                        return render(request, 'updated_home_ui.html', {'form': form})
                    print("Extracted Job Description:", job_description)
                except Exception as e:
                    messages.error(request, f"Error processing job description file: {str(e)}")
                    return redirect('home')

            if not job_description:
                messages.error(request, "Please provide a job description")
                return redirect('home')

            # Store job description in session
            request.session['job_description'] = job_description
            
            if resume_text and (source_choice == 'database' or source_choice == 'upload'):
                messages.error(request, "Please provide either pasted resume text or upload/select resumes, not both.")
                return redirect('home')

            if resume_text:
                print("Resume text provided")
                request.session['resume_text'] = resume_text
                request.session['resume_source'] = 'text'
            # Process by source choice
            elif source_choice == 'upload':
                resume_files = form.cleaned_data.get('resume_files', [])
                if not resume_files:
                    messages.error(request, "Please upload at least one resume file")
                    return redirect('home')

                # Store uploaded files to temp directory
                if request.POST.get('insert_to_db') == 'on':
                    request.session['store_resumes'] = True
                else:
                    request.session['store_resumes'] = False
                temp_dir = os.path.join(os.getcwd(), 'temp_resumes')
                os.makedirs(temp_dir, exist_ok=True)

                file_paths = []
                for resume_file in resume_files:
                    print(resume_file)

                    # file_path = os.path.join(temp_dir, resume_file.name)
                    safe_filename = sanitize_filename(resume_file.name)  # Use the sanitize_filename function from previous answer
                    file_path = os.path.join(temp_dir, safe_filename)
                    with open(file_path, 'wb+') as destination:
                        for chunk in resume_file.chunks():
                            destination.write(chunk)
                    file_paths.append(file_path)

                # Store file paths in session
                request.session['resume_files'] = file_paths
                request.session['resume_source'] = 'resume_files'
                request.session['source_choice'] = 'upload'

            elif source_choice == 'database':
                request.session['source_choice'] = 'database'
                request.session['resume_source'] = 'resume_files'
            return redirect('results')
        else: form = JDForm()  # Reset form if invalid

    return render(request, 'updated_home_ui.html', {'form': form})


def results(request):
    print("In results view")
    if request.session.get('results_ready'):
        resumes = request.session.get('resumes')
        candidates = request.session.get('candidates')
        return render(request, 'new_results.html', {'results': zip(candidates, resumes)})
    print("Processing results")
    job_description = request.session.get('job_description')
    resume_source = request.session.get('resume_source')
    source_choice = request.session.get('source_choice')
    store_resumes = request.session.get('store_resumes')
    min_experience = request.session.get('min_experience')
    must_have_skills = request.session.get('must_have_skills')
    nice_to_have_skills = request.session.get('nice_to_have_skills')
    role_expectations = request.session.get('role_expectations')
    input_from_user=[min_experience,must_have_skills,nice_to_have_skills,role_expectations]
    present_date = request.session.get('present_date') or date.today().isoformat()

    if not job_description or not(resume_source or source_choice):
        print("job_description or resume_text or source_choice not set")
        messages.error(request, "Missing job description or source selection")
        return redirect('home')
    results = []

    try:
        if resume_source == 'text':
            print("Processing pasted resume text")
            resume_text = request.session.get('resume_text')
            if not resume_text:
                messages.error(request, "No resume text found")
                return redirect('home')
            df = text_df(resume_text)   
            print(df)
            structured = structuring_process(df, structuring_chain)
            resumes = structured if structured else []

            nested_res = resumes_sending_to_comparison(resumes, job_description, present_date, input_from_user, comparison_chain)
            print("Comparison results for pasted text:", nested_res, "\n")
            results = parse_nested_results(nested_res)

        elif source_choice == 'upload':
            resume_files = request.session.get('resume_files', [])
            if not resume_files:
                print("No resume files found in session")
                messages.error(request, "No resume files found in session")
                return redirect('home')
            # Process uploaded resumes
            structured_data = []
            results_dict = {}
            resumes_to_evaluate = []

            for file_path in resume_files:
                filename = os.path.basename(file_path)
                existing = collection.find_one({"filename": filename}, {"_id": False})

                # Check for cached evaluation
                cached_eval = get_cached_evaluation(filename)
                if cached_eval:
                    print(f"Found cached evaluation for {filename}")
                    structured_data.append(existing if existing else {"filename": filename})
                    if "Resume_Screener" in cached_eval:
                        results_dict[filename] = cached_eval["Resume_Screener"]
                    else:
                        results_dict[filename] = cached_eval
                    continue

                if existing:
                    structured_data.append(existing)
                    print(structured_data)
                    resumes_to_evaluate.append(existing)
                else:
                    # Process and structure new resumes only
                    df = creating_df(file_path)
                    structured = structuring_process(df, structuring_chain)
                    if structured:
                        structured_doc = structured[0]
                        structured_doc['filename'] = filename
                        print(structured)
                        if store_resumes:
                            print("storing in db")
                            save_data_to_mongo(structured)
                        structured_data.append(structured_doc)
                        resumes_to_evaluate.append(structured_doc)

            resumes = structured_data

            if resumes_to_evaluate:
                print("resume came to evaluation",resumes_to_evaluate)
                nested_res = resumes_sending_to_comparison(resumes_to_evaluate, job_description, present_date, input_from_user, comparison_chain)
                print("resumes evaluation:",nested_res)
                new_results = parse_nested_results(nested_res)
                print("new results after parsing:",new_results)
                for i, parsed_eval in enumerate(new_results):
                    filename = resumes_to_evaluate[i].get("filename")
                    if filename:
                        results_dict[filename] = parsed_eval
                        update_candidate_evaluation(filename, parsed_eval)

            # Reconstruct the results list in the exact order of structured_data 
            results = []
            for res_data in structured_data:
                fname = res_data.get("filename")
                results.append(results_dict.get(fname, {}))

            print("final results:",results)

            for file_path in resume_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Cleanup warning: Could not remove temp file {file_path}: {e}")

        elif source_choice == 'database':
            resumes = fetch_resumes(collection)
            nested_res = resumes_sending_to_comparison(resumes, job_description, present_date, input_from_user, comparison_chain)
            results = parse_nested_results(nested_res)

    except Exception as e:
        messages.error(request, f"Error processing resumes: {str(e)}")
        return redirect('home')

    # Clear session data
    # request.session.pop('job_description', None)
    # request.session.pop('resume_files', None)
    # request.session.pop('source_choice', None)
    candidates = results
    print("\nResumes:\n",resumes)

    def deep_lowercase_keys(obj):
        if isinstance(obj, dict):
            return {k.lower(): deep_lowercase_keys(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [deep_lowercase_keys(i) for i in obj]
        return obj

    candidates = deep_lowercase_keys(candidates)
    print("\nCandidates:\n", candidates)
    request.session['resumes'] = resumes
    request.session['candidates'] = candidates
    request.session['results_ready'] = True
    
    return render(request, 'new_results.html', {'results': zip(candidates,resumes)})

def clear_session_and_home(request):
    temp_dir = os.path.join(os.getcwd(), 'temp_resumes')
    if os.path.exists(temp_dir):
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
    request.session.flush()   # clears all session data
    return redirect('home')

def download_results_file(request,file_type):
    candidates = request.session['candidates']
    resumes = request.session['resumes']
    results = zip(candidates, resumes)
    if not results:
        return HttpResponse("No results available", status=400)

    if file_type == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="comparison_results.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "Name", "Email", "Candidate Snapshot", "Current Job Title",
            "Total Experience", "Skills Match", "Domain Match",
            "Measurable Impact", "Matching Skills", "Missing Skills",
            "Score", "Rating"
        ])
        for result, resume in results:
            job_title = result.get("career_details").get("Current_Last_Job_Title") or \
                        result.get("career_details").get("Current_Job_Title") or "Not available"

            writer.writerow([
                resume.get("Name", ""),
                resume.get("Email", ""),
                result.get("candidate_snapshot", ""),
            job_title,
            result.get("career_details").get("Total_Years_of_Experience", ""),
            result.get("evaluation").get("Skills_Match", ""),
            result.get("evaluation").get("Domain_Industry_Relevance", ""),
            result.get("evaluation").get("Measurable_Impact", ""),
            ", ".join(result.get("matched_skills", [])),
            ", ".join(result.get("missing_skills", [])),
            result["evaluation"].get("Total_score", ""),
            result.get("rating", "")
            ])
        return response

    data_for_file = []

    for result, resume in results:
        job_title = result.get("career_details").get("Current_Last_Job_Title") or \
                    result.get("career_details").get("Current_Job_Title") or "Not available"
        rating=re.sub(r'[^a-zA-Z\s]', '', result.get("rating"))
        data_for_file.append({
            "Name": resume.get("Name", ""),
            "Email": resume.get("Email", ""),
            "Candidate Snapshot": result.get("candidate_snapshot", ""),
            "Current Job Title": job_title,
            "Total Experience": result.get("career_details").get("Total_Years_of_Experience", ""),
            "Skills Match": result.get("evaluation").get("Skills_Match", ""),
            "Domain Match": result.get("evaluation").get("Domain_Industry_Relevance", ""),
            "Measurable Impact": result.get("evaluation").get("Measurable_Impact", ""),
            "Matching Skills": ", ".join(result.get("matched_skills", [])),
            "Missing Skills": ", ".join(result.get("missing_skills", [])),
            "Score": result.get("evaluation").get("Total_score", ""),
            "Rating": rating
        })

    if file_type == "json":
        response = HttpResponse(json.dumps(data_for_file, indent=2), content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="comparison_results.json"'
        return response

    elif file_type == "excel":
        df = pd.DataFrame(data_for_file)
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="comparison_results.xlsx"'
        df.to_excel(response, index=False)
        return response

    # request.session.pop('resumes', None)
    # request.session.pop('candidates', None)
    return HttpResponse("Invalid file type", status=400)


def sanitize_filename(filename):
    # Remove forbidden Windows characters: \ / : * ? " < > |
    return re.sub(r'[\\/:*?"<>|\[\]]', '_', filename)

@csrf_exempt
def api_screen_resumes(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    print("Received API data:", data)

    job_description = data.get("job_description")
    resume_paths = data.get("resume_data", [])
    input_from_user = data.get("input_from_user", [None, None, None, None])  # Default to list of Nones if not provided

    structured_data = []
    results_dict = {}
    resumes_to_evaluate = []

    for file_path in resume_paths:
        filename = os.path.basename(file_path)
        existing_doc = collection.find_one({"filename": filename}, {"_id": False})

        # Check ai_evaluations for cached evaluation
        cached_eval = get_cached_evaluation(filename)
        if cached_eval:
            print(f"Found cached evaluation for {filename}")
            structured_data.append(existing_doc if existing_doc else {"filename": filename})
            if "Resume_Screener" in cached_eval:
                results_dict[filename] = cached_eval["Resume_Screener"]
            else:
                results_dict[filename] = cached_eval
            continue

        if existing_doc:
            structured_doc = existing_doc
        else:
            df = creating_df(file_path)
            print(f"DataFrame for {file_path}:", df)
            structured = structuring_process(df, structuring_chain)
            save_data_to_mongo(structured)
            structured_doc = structured[0] if structured else {"filename": filename}

        structured_data.append(structured_doc)
        resumes_to_evaluate.append(structured_doc)

    print("Structured data for API:", structured_data)
    present_date = date.today().isoformat()

    if resumes_to_evaluate:
        nested_res = resumes_sending_to_comparison(
            resumes_to_evaluate, job_description, present_date, input_from_user, comparison_chain)
        print("Comparison results for API:", nested_res)
        for i, res in enumerate(nested_res):
            if isinstance(res, list):
                res = res[0]
            match = re.search(r'\{.*\}', str(res), re.DOTALL)
            if match:
                try:
                    try:
                        parsed_eval = json.loads(match.group(0))
                    except json.JSONDecodeError:
                        parsed_eval = repair_json(match.group(0), return_objects=True)
                    if isinstance(parsed_eval, str): parsed_eval = json.loads(parsed_eval)
                    
                    if "Resume_Screener" in parsed_eval:
                        clean_eval = parsed_eval["Resume_Screener"]
                    else:
                        clean_eval = parsed_eval

                    filename = resumes_to_evaluate[i].get("filename")
                    if filename:
                        results_dict[filename] = clean_eval
                        update_candidate_evaluation(filename, parsed_eval)

                except json.JSONDecodeError:
                    print("Failed to parse JSON for API:", res)

    candidates = []
    for res_data in structured_data:
        fname = res_data.get("filename")
        candidates.append(results_dict.get(fname, {}))

    def lowercase_keys(data):
        return [{k.lower(): v for k, v in d.items()} for d in data if isinstance(d, dict)]

    candidates = lowercase_keys(candidates)
    print("\nCandidates:\n", candidates)

    # Return JSON response instead of rendered HTML
    response_data = {
        "candidates": candidates,
        "resumes": structured_data
    }
    return JsonResponse(response_data, safe=False)