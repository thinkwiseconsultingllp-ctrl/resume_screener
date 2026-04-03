import os
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
# from langchain_core.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser
from pymongo import MongoClient
import json
from django.conf import settings

from langchain_openai import ChatOpenAI
OPENROUTER_MODEL_ID = "nvidia/nemotron-nano-9b-v2:free"
# OPENROUTER_MODEL_ID = "nvidia/nemotron-3-nano-30b-a3b:free"
# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
 
SITE_URL = os.getenv("SITE_URL", "http://localhost")
SITE_NAME = os.getenv("SITE_NAME", "My Local App")

llm = ChatOpenAI(
                model=GROQ_MODEL,
                openai_api_key=GROQ_API_KEY,
                openai_api_base="https://api.groq.com/openai/v1",
                temperature=0.2,
                max_tokens=8000,
                max_retries=2,
            )

with open(os.path.join(settings.BASE_DIR, "parser/prompts/structuring_prompt.txt"),encoding="utf8") as f:
    resume_structuring_prompt = f.read()

with open(os.path.join(settings.BASE_DIR, "parser/prompts/resume_analyser.txt"),encoding="utf8") as f:
    Resume_screening_prompt = f.read()

# def structuring_chain():
#     llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
#     prompt = PromptTemplate.from_template(resume_structuring_prompt)
#     chain = LLMChain(llm=llm, prompt=prompt, verbose=False)
#     return chain

# def comparison_llm_initialisation():
#     comparison_prompt = PromptTemplate(input_variables=["job_description", "resume","present_date","min_experience","must_have_skills","nice_to_have_skills","role_expectations",""], template=Resume_screening_prompt)
#     comparison_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"), temperature=0.0,
#                                              convert_system_message_to_human=True)
#     comparison_chain = LLMChain(llm=comparison_llm, prompt=comparison_prompt,verbose=False)  # Set verbose=True for debugging
#     return comparison_chain

def structuring_chain():
    prompt = PromptTemplate.from_template(resume_structuring_prompt)
    # chain = LLMChain(llm=llm, prompt=prompt, verbose=False)
    chain = prompt | llm #| StrOutputParser()
    return chain

def comparison_llm_initialisation():
    comparison_prompt = PromptTemplate(input_variables=["job_description", "resume","present_date","min_experience","must_have_skills","nice_to_have_skills","role_expectations",""], template=Resume_screening_prompt)
    # comparison_chain = LLMChain(llm=llm, prompt=comparison_prompt, verbose=False)
    comparison_chain = comparison_prompt | llm #| StrOutputParser()
    return comparison_chain
