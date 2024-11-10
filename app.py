from fastapi import FastAPI
from pydantic import BaseModel
import requests
from transformers import pipeline
from typing import List

# Initialize the FastAPI app and the NLP pipelines
app = FastAPI()
summarizer = pipeline("summarization")
qa_model = pipeline("question-answering")

# Store chat context for each session
chat_context = {}


# Function to search papers on Arxiv
def search_arxiv_papers(topic: str):
    url = f'http://export.arxiv.org/api/query?search_query=all:{topic}&start=0&max_results=10'
    response = requests.get(url)
    if response.status_code == 200:
        return parse_arxiv_results(response.text)
    else:
        return []


# Function to parse Arxiv results
def parse_arxiv_results(xml_text):
    import xml.etree.ElementTree as ET
    tree = ET.ElementTree(ET.fromstring(xml_text))
    root = tree.getroot()

    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        summary = entry.find('{http://www.w3.org/2005/Atom}summary').text
        link = entry.find('{http://www.w3.org/2005/Atom}id').text
        authors = [author.text for author in entry.findall('{http://www.w3.org/2005/Atom}author')]

        papers.append({
            'title': title,
            'summary': summary,
            'link': link,
            'authors': authors
        })
    return papers


# Pydantic models for request data validation
class PaperRequest(BaseModel):
    topic: str


class QARequest(BaseModel):
    question: str
    context: str


class SummarizeRequest(BaseModel):
    text: str


# FastAPI endpoints
@app.post("/search_papers/")
async def search_papers(request: PaperRequest):
    papers = search_arxiv_papers(request.topic)
    return papers


@app.post("/summarize/")
async def summarize(request: SummarizeRequest):
    summary = summarizer(request.text, max_length=200, min_length=50, do_sample=False)[0]['summary_text']
    return {"summary": summary}


@app.post("/answer_question/")
async def answer_question(request: QARequest):
    answer = qa_model(question=request.question, context=request.context)
    return {"answer": answer['answer']}


@app.get("/get_context/")
async def get_context(session_id: str):
    return {"context": chat_context.get(session_id, [])}


@app.post("/update_context/")
async def update_context(session_id: str, user_input: str, bot_response: str):
    if session_id not in chat_context:
        chat_context[session_id] = []
    chat_context[session_id].append({"user": user_input, "bot": bot_response})
    return {"message": "Context updated"}
