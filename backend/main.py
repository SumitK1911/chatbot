from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import nltk
import re
import numpy as np
from nltk.stem import LancasterStemmer
from nltk.tokenize import word_tokenize
from collections import Counter
from math import sqrt, log

nltk.download("punkt")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cred = credentials.Certificate("credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

API_KEY = os.getenv("API_KEY")
genai.configure(api_key=API_KEY)

stemmer = LancasterStemmer()

class FAQ(BaseModel):
    question: str
    answer: str

def initializefaqs():
    faqs = [
        {"question": "What is the purpose of this website?", "answer": "This website is for FAQ-based chatbot interactions."},
        {"question": "How do I sign up?", "answer": "You can sign up by clicking on the 'Sign Up' button on the homepage."},
        {"question": "How do I log in?", "answer": "Click the 'Login' button and enter your credentials."},
        {"question": "Can I change my email?", "answer": "Yes, you can update your email from the settings page."},
        {"question": "How can I reset my password?", "answer": "Click on 'Forgot Password' and follow the instructions."},
        {"question": "How do I view my tuition fee bill?", "answer": "Log in to your student portal, navigate to the Billing/Payments section, and click View Current Bill to see your fee details."},
        {"question": "How do I download my payment receipt?", "answer": "After payment, go to the Payment History tab in the billing section and click Download Receipt."},
        {"question": "How do I access my semester marksheet?", "answer": "Go to the Academic Records section in your portal and click Download Marksheet under the relevant semester."},
        {"question": "Can I get a physical copy of my marksheet?", "answer": 'Request it via the "Document Requests" section. Collect it from the examination office or opt for postal delivery.'}
    ]

    faq_ref = db.collection("faqs")

    for faq in faqs:
        docs = faq_ref.where("question", "==", faq["question"]).stream()
        if not any([doc.id for doc in docs]):
            faq_ref.add(faq)

initializefaqs() 

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Chatbot API"}

def textPreprocess(text):
    text = text.lower()
    text = re.sub(r'\bsignup\b', 'sign up', text)
    text = re.sub(r'\blogin\b', 'log in', text)
    words = word_tokenize(text)
    stemmed_words = [stemmer.stem(word) for word in words] 
    return " ".join(stemmed_words)

def termFrequency(text):
    words = text.split()
    word_count = len(words)
    word_freq = Counter(words)
    return {word: freq / word_count for word, freq in word_freq.items()}

def inverseDocfre(texts):
    num_docs = len(texts)
    idf_dict = {}
    all_words = set(word for doc in texts for word in doc.split())

    for word in all_words:
        containing_docs = sum(1 for doc in texts if word in doc)
        idf_dict[word] = log((num_docs + 1) / (containing_docs + 1)) + 1  # Smoothing

    return idf_dict

def tfidf(texts):
    idf_values = inverseDocfre(texts)
    tfidf_vectors = []

    for doc in texts:
        tf_values = termFrequency(doc)
        tfidf_vectors.append({word: tf_values.get(word, 0) * idf_values[word] for word in idf_values})

    return tfidf_vectors

def cosineSimilarity(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum(vec1[word] * vec2[word] for word in intersection)

    sum1 = sum(val ** 2 for val in vec1.values())
    sum2 = sum(val ** 2 for val in vec2.values())

    denominator = sqrt(sum1) * sqrt(sum2)
    return numerator / denominator if denominator else 0.0

def matchMaking(user_query, faqs):
    questions = [faq["question"] for faq in faqs]
    processed_questions = [textPreprocess(q) for q in questions]
    
    tfidf_vectors = tfidf(processed_questions)
    user_query_vector = tfidf([textPreprocess(user_query)])[0]

    similarities = [cosineSimilarity(user_query_vector, tfidf_vec) for tfidf_vec in tfidf_vectors]

    best_match_idx = np.argmax(similarities)
    best_match_score = similarities[best_match_idx]

    if best_match_score > 0.6:  
        return faqs[best_match_idx]["answer"]
    return None

@app.get("/ask")
async def ask_question(query: str):
    query = textPreprocess(query) 
    faq_ref = db.collection("faqs")
    docs = faq_ref.stream()
    
    faqs = [{"question": textPreprocess(doc.to_dict()["question"]), "answer": doc.to_dict()["answer"]} for doc in docs]

    answer = matchMaking(query, faqs)
    
    if answer:
        db.collection("chat_history").add({"question": query, "answer": answer, "role": "FAQ"})
        return JSONResponse(content={"answer": answer, "source": "FAQ"})
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    instruction = """You are a chatbot for a college management system.
                     Only answer questions related to student fees, billing, payments, school, and college related.
                     """

    prompt = f"{instruction}\nUser Query: {query}"

    response = model.generate_content(prompt)
    answer = response.text

    db.collection("chat_history").add({"question": query, "answer": answer, "role": "AI"})
    return JSONResponse(content={"answer": answer, "source": "AI"})

@app.post("/add_faq")
async def add_faq(faq: FAQ): 
    faq_ref = db.collection("faqs")
    questionNormalize = textPreprocess(faq.question)
    existing_faqs = faq_ref.where("question", "==", questionNormalize).stream()
    if any([doc.id for doc in existing_faqs]):
        raise HTTPException(status_code=400, detail="FAQ already exists")

    faq_ref.add({"question": questionNormalize, "answer": faq.answer})
    
    return JSONResponse(content={"message": "FAQ added successfully"})
