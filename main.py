import difflib
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
#from google.colab import userdata
from transformers import BartTokenizer, BartForConditionalGeneration
import PyPDF2
import google.generativeai as genai
import numpy as np
import pandas as pd
import sqlite3
import ast
import json

data = pd.read_csv('JEE_Resources.csv')
jee_data = data['Topic']+''+data['Resource Link']
tfidf = TfidfVectorizer()
JEE_data = tfidf.fit_transform(jee_data)
similarity = cosine_similarity(JEE_data)

genai.configure(api_key='AIzaSyD4BFFD4ZN0IsBofjusZT3627GMAg_J-Gk')


def generate_and_store_study_plan(topic, duration):

    model = genai.GenerativeModel("models/gemini-1.5-pro")

    # Generate the study plan using the Generative AI model
    prompt = f"Generate a JEE specific roadmap for the topic of {topic} over a duration of {duration}. Generate it in the format [[subtopic1,short description with no comma written in text(content should remain between these commas. no other comma should be there bwtween these commas),time to be given],[subtopic2, ...]...]. dont make a week wise plan .stick to the format provided earlier strictly.provideed answer should only be in the given format no other text or word to be written."
    response = model.generate_content(prompt)
    generated_plan = response.text
    print(generated_plan)

    # Parse the generated plan and store it in the table
    plan_items = []
    for item in generated_plan.strip('[]').split('],'):
        subtopicdict = {}
        subtopic_time = [part.strip() for part in item.split(',')]
        subtopicdict["subtopic"] = subtopic_time[0].strip('"')
        subtopicdict["description"] = subtopic_time[1].strip('"')
        subtopicdict["time_to_be_given"] = subtopic_time[2].strip('"')

        print(subtopicdict)

        plan_items.append(subtopicdict)
    return plan_items


def suggest_resource(topic):
    list_of_all_topics = data['Topic'].tolist()
    find_close_match = difflib.get_close_matches(topic, list_of_all_topics, n=1)

    if find_close_match:
        close_match = find_close_match[0]
    else:
        print("No close topic found. Please check your input.")
        exit()

# Filter resources for the matched topic
    filtered_data = data[data['Topic'] == close_match].reset_index()

    if filtered_data.empty:
        print("No resources found for the given topic.")
        exit()

    similarity_score = list(enumerate(similarity[filtered_data.index[0]]))

# Sort and keep only those belonging to the close_match topic
    sorted_similar_resources = sorted(
        similarity_score, key=lambda x: x[1], reverse=True)

    print(f"Resources recommended for {close_match}:")
    i = 1
    resource_types = set()  # Track different resource categories
    resource_list=[]
    for resource in sorted_similar_resources:
        index = resource[0]
        resource={}

    # Ensure the resource belongs to the matched topic
        if data.loc[index, 'Topic'] != close_match:
            continue

        topic_from_index = data.loc[index, 'Topic']
        resource_name = data.loc[index, 'Resource Name']
        resource_link = data.loc[index, 'Resource Link']


    # Categorize resources to ensure diversity
        resource_category = "Book" if "HC Verma" in resource_name else "Notes" if "Notes" in resource_name else "Other"

        if resource_category not in resource_types:
            resource['topic']=topic_from_index
            resource['resource']= resource_name
            resource['resource_link']=resource_link

            i += 1

        if i > 5:  # Limit to 5 diverse recommendations
            break
    resource_list.append(resource_list)


    if i == 1:
        print("No relevant resources found for the given topic.")
    return resource_list




def generate_summary(pdf_path):
    tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
    model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"

    inputs = tokenizer.encode('summarize: ' + text, return_tensors="pt",
                              max_length=1024, truncation=True)  # Reduced max_length to 1024
    summary_ids = model.generate(inputs, max_length=1000, min_length=50,
                                 length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# Function to get the answer


def Ask_Summary(summary_text, question):
    qa_pipeline = pipeline("question-answering",
                           model="deepset/roberta-base-squad2")
    # Ensure keyword arguments
    results = qa_pipeline(question=question, context=summary_text)
    return results


'''
# Print the generated table
print("\nGenerated Study Plan Table:")
topic_name = topic.replace(" ", "_")
cursor.execute(f"SELECT * FROM {topic_name}")
rows = cursor.fetchall()
for row in rows:
    print(f"Subtopic: {row[0]}, description: {row[1]}, material: {row[2]}, time_to_be_given: {row[3]} Proficiency: {row[4]}")
'''
if __name__ == "__main__":
    # Ensure all poarguments are passed

    topic = 'Gravitation'
    duration = '2 weeks'

    # Generate quiz
    roadmap=generate_and_store_study_plan(topic, duration)
    resource= suggest_resource(topic)

    file_path = ""
    summary=generate_summary(file_path)

    question=""
    answer_dict= Ask_Summary(summary, question)
    answer= answer_dict["answer"]




