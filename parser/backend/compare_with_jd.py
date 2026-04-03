from parser.backend.db_functions import fetch_resumes

def resume_comparison_with_jd(resume,jd,present_date,input_from_user,comparison_chain):
  result=[]
  comparison_output = comparison_chain.invoke({"job_description": jd, "resume": resume,"present_date":present_date,
                   "min_experience":input_from_user[0],"must_have_skills":input_from_user[1],
                  "nice_to_have_skills":input_from_user[2],"role_expectations":input_from_user[3]})
  # Handle AIMessage object if StrOutputParser is not used
  print("comparison output:",comparison_output,"\n")
  comparison_output_json_string = comparison_output.content if hasattr(comparison_output, 'content') else comparison_output
  print(comparison_output_json_string)
  #final_analysis_for_one_resume = json.loads(comparison_output_json_string)
  #result.append(final_analysis_for_one_resume)
  result.append(comparison_output_json_string)
  return result

def resumes_sending_to_comparison(resumes,job_description,present_date,input_from_user,comparison_chain):
  all_results=[]
  for i in resumes:
    print(i)
    all_results.append(resume_comparison_with_jd(i,job_description,present_date,input_from_user,comparison_chain))
  return all_results