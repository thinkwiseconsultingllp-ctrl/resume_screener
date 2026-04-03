from glob import glob
from parser.backend.pdf_extraction_new import pdf_extraction,extract_text_from_docx
import os
import pandas as pd
from tqdm import tqdm
import json
import re
from json_repair import repair_json

def processing_resumes(resume_folder):
  all_resumes=glob(resume_folder,recursive=True)
  return all_resumes

def storing_in_df(files):
  extracted_text=[]
  for i in files:
    try:
        if os.path.splitext(i)[1].lower()==".docx": text=extract_text_from_docx(i)
        else: text=pdf_extraction(i)

        extracted_text.append({"filename":os.path.basename(i), "text":text})
    except Exception as e: print(f"Error with {i}:{e}")

  df=pd.DataFrame(extracted_text)
  return df

# def creating_df(resume_folder):
#   all_resumes=processing_resumes(resume_folder)
#   df=storing_in_df(all_resumes)
#   return df

def creating_df(input_source):
    if isinstance(input_source, str):
            all_resumes = processing_resumes(input_source)  # treat as folder
    elif isinstance(input_source, list):
        all_resumes = input_source  # treat as file list
    else:
        raise ValueError("Invalid input: must be folder path or list of file paths")

    df = storing_in_df(all_resumes)
    return df

def text_df(text):
  data={"filename":"pasted_resume","text":text}
  df=pd.DataFrame([data])
  return df

def structuring_process(df,chain):
  struc_data=[]
  for _, row in tqdm(df.iterrows(), total=len(df)):
        resume_text = row['text']
        file_name = row['filename']
        try:
            result = chain.invoke({"resume_text":resume_text})
            # Handle AIMessage object if StrOutputParser is not used
            result_text = result.content if hasattr(result, 'content') else result
            match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                try:
                    python_dictionary = json.loads(json_str)
                except json.JSONDecodeError:
                    # Fallback to json-repair if LLM output has formatting mistakes
                    python_dictionary = repair_json(json_str, return_objects=True)
            parsed_json = python_dictionary
            parsed_json["filename"] = file_name
            struc_data.append(parsed_json)
        except Exception as e: 
            print(f" Failed to process {file_name}: {e}")
            if 'json_str' in locals():
                print("--- FAILED JSON STRING ---")
                print(json_str)
                print("--------------------------")
  return struc_data
