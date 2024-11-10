import streamlit as st
import requests

# FastAPI server URL
FASTAPI_URL = "http://localhost:8000"  # Make sure FastAPI is running on this URL

# Store session ID for the current chat session
if "session_id" not in st.session_state:
    st.session_state.session_id = "user_session_1"  # Unique session ID


# Function to interact with the FastAPI backend
def search_papers(topic):
    response = requests.post(f"{FASTAPI_URL}/search_papers/", json={"topic": topic})
    if response.status_code == 200:
        return response.json()
    return []


def summarize(text):
    response = requests.post(f"{FASTAPI_URL}/summarize/", json={"text": text})
    if response.status_code == 200:
        return response.json().get("summary")
    return "Error summarizing."


def answer_question(question, context):
    response = requests.post(f"{FASTAPI_URL}/answer_question/", json={"question": question, "context": context})
    if response.status_code == 200:
        return response.json().get("answer")
    return "Error answering question."


def get_context():
    response = requests.get(f"{FASTAPI_URL}/get_context/", params={"session_id": st.session_state.session_id})
    if response.status_code == 200:
        return response.json().get("context", [])
    return []


def update_context(user_input, bot_response):
    requests.post(f"{FASTAPI_URL}/update_context/", json={
        "session_id": st.session_state.session_id,
        "user_input": user_input,
        "bot_response": bot_response
    })


# Streamlit UI
st.title("Academic Research Assistant")

# Search Research Papers
topic = st.text_input("Enter Research Topic")
if topic:
    papers = search_papers(topic)
    if papers:
        st.write(f"Found {len(papers)} papers related to '{topic}':")
        selected_papers = st.multiselect("Select Papers", [paper['title'] for paper in papers])

        # Display selected papers and summarize
        if selected_papers:
            selected_papers_details = [paper for paper in papers if paper['title'] in selected_papers]
            for paper in selected_papers_details:
                st.write(f"### {paper['title']}")
                st.write(f"Authors: {', '.join(paper['authors'])}")
                st.write(f"Summary: {paper['summary']}")
                st.write(f"[Read more on Arxiv]({paper['link']})")

                # Summarize Paper
                if st.button(f"Summarize {paper['title']}"):
                    summary = summarize(paper['summary'])
                    st.write(f"Summary: {summary}")

                # Ask Question
                question = st.text_input("Ask a question about the selected papers:")
                if question:
                    context = paper["summary"]
                    answer = answer_question(question, context)
                    st.write(f"Answer: {answer}")
                    update_context(question, answer)

    else:
        st.write("No papers found related to this topic.")

# Show previous chat history (Context)
context = get_context()
if context:
    st.write("### Previous Chat History")
    for entry in context:
        st.write(f"**User**: {entry['user']}")
        st.write(f"**Bot**: {entry['bot']}")
