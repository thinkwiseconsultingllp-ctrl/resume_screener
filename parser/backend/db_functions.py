import pymongo
from pymongo import MongoClient, ASCENDING
from pymongo.errors import BulkWriteError
import os
from dotenv import load_dotenv
load_dotenv()
mongo_uri =os.getenv("MONGO_URI")

def fetch_resumes(collection):
    try:
        resumes = list(collection.find({}, {"_id": False}))
        print(f"Fetched {len(resumes)} resumes from collection Resume Parser Collection.")
        return resumes
    except:
        print("error fetching resumes from {collection}")

def save_data_to_mongo(data, db_name="resumeDB", collection_name="resume_parser"):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    collection.create_index([("Name", ASCENDING)], unique=True)
    collection.create_index([("Email", ASCENDING)], unique=True)
    collection.create_index([("Name", ASCENDING), ("Email", ASCENDING)], unique=True)
    if data:
        try:
            result = collection.insert_many(data, ordered=False)
            print(f"Successfully inserted {len(result.inserted_ids)} records.")
        except BulkWriteError as bwerror:
            duplicate_files = set()
            if bwerror.details and 'writeErrors' in bwerror.details:
                for error in bwerror.details['writeErrors']:
                    if error.get('code') == 11000:  # Duplicate key error code
                        offending_document = data[error['index']]
                        if 'filename' in offending_document:
                            duplicate_files.add(offending_document['filename'])

            inserted_count = len(bwerror.details.get('insertedIds', []))
            print(f"Inserted {inserted_count} records successfully (some duplicates were skipped) {duplicate_files}.")
    else:
        print("No data to insert.")

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


def get_cached_evaluation(filename, db_name="resumeDB", collection_name="ai_evaluations"):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    try:
        doc = collection.find_one({"filename": filename}, {"_id": False})
        if doc and "evaluation_result" in doc:
            return doc["evaluation_result"]
        return None
    except Exception as e:
        print(f"Error fetching cached evaluation for {filename}: {e}")
        return None