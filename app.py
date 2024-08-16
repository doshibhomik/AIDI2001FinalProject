import streamlit as st
import openai
import PyPDF2 as pdf
import pandas as pd
import json
from dotenv import load_dotenv
import os

# Set up the page title and layout for Streamlit app
st.set_page_config(page_title="Resume Analysis & Job Search", layout="wide")

load_dotenv()  # Load environment variables from .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to get the response from OpenAI GPT model
def get_openai_response(input_prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Using the latest GPT-3.5 model
            messages=[{"role": "system", "content": input_prompt}],
            max_tokens=500,
            temperature=0.7,  # Adjusts creativity of the AI's response
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        st.error(f"Error with OpenAI API: {str(e)}")
        return None

# Function to extract text from uploaded PDF resume
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)  # Reading the PDF file
    text = ""
    for page_n in range(len(reader.pages)):
        page = reader.pages[page_n]
        text += str(page.extract_text())  # Extracting text from each page
    return text

# Function to create clickable links for job listings
def make_clickable(link):
    return f'<a href="{link}" target="_blank">{link}</a>'

# Load custom CSS for styling the UI
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load the CSS file to style the app
local_css("style.css")

# Streamlit UI setup
st.title("🎯 Resume Analysis and Job Search Tool")

# Sidebar setup with a logo and description
st.sidebar.image("logo.png", width=150)  # Display the logo in the sidebar
st.sidebar.markdown(
    "<p style='text-align: center;'>Enhance your career with personalized resume insights and relevant job searches.</p>",
    unsafe_allow_html=True)
st.sidebar.header("🔍 Explore Options")
st.sidebar.markdown("Select an action below to get started:")

# Option to select between Resume Analysis and Job Search
page = st.sidebar.radio("Choose an option", ["Analyze My Resume", "Find Matching Jobs"], label_visibility="collapsed")

if page == "Analyze My Resume":
    st.header("📄 Resume Analysis for Job Applications")
    st.write(
        "Upload your resume and the job description to get recommendations on certifications to obtain and keywords to include in your resume."
    )

    # File uploader for resume
    uploaded_resume = st.file_uploader("Upload your resume (PDF):", type=["pdf"])

    # Text area for job description input
    job_description = st.text_area("Paste the job description text here:")

    if st.button("Analyze"):
        if uploaded_resume is not None and job_description:
            # Extract text from the uploaded PDF resume
            resume_text = input_pdf_text(uploaded_resume)

            # Create a prompt to send to the GPT model
            input_prompt = f"""
            You are an advanced AI specialized in resume analysis for the Canadian job market. 
            Your task is to analyze the following resume based on the job description provided.
            Please recommend certifications and skills that are missing from the resume, and 
            suggest ways to optimize the resume for Applicant Tracking Systems (ATS).
            Also, calculate and provide the percentage match between the resume and the job description.

            Provide the response in a JSON format like this:
            {{
                "JD Match": "xx%",
                "Missing Keywords": ["keyword1", "keyword2", ...],
                "Missing Certifications": [
                    {{"name": "certification1", "description": "description1"}},
                    {{"name": "certification2", "description": "description2"}}
                ],
                "Profile Summary": "Your detailed profile summary here."
            }}

            Only include certifications that are highly valuable for the job position.
            Resume:
            {resume_text}

            Job Description:
            {job_description}
            """

            # Get the AI's response
            response = get_openai_response(input_prompt)

            if response:
                try:
                    # Parse the response as JSON
                    response_json = json.loads(response)

                    # Display Job Description Match Percentage
                    st.subheader("Job Description Match")
                    st.write(f"**Match Percentage:** {response_json['JD Match']}")

                    # Display Missing Keywords in a table
                    if response_json.get("Missing Keywords"):
                        st.subheader("Missing Keywords")
                        st.write("Add these keywords in your resume to increase chances:")
                        keywords_df = pd.DataFrame({"Keywords": response_json["Missing Keywords"]})
                        st.write(keywords_df.to_html(escape=False, index=False), unsafe_allow_html=True)

                    # Display Missing Certifications in a table
                    if response_json.get("Missing Certifications"):
                        st.subheader("Missing Certifications")
                        certs_df = pd.DataFrame(response_json["Missing Certifications"])
                        st.write(certs_df.to_html(escape=False, index=False), unsafe_allow_html=True)

                    # Display Profile Summary generated by AI
                    st.subheader("Profile Summary")
                    st.write(response_json["Profile Summary"])

                except json.JSONDecodeError as e:
                    st.error(f"Error parsing response: {e}")
                    st.text(response)  # Display the raw response for debugging

elif page == "Find Matching Jobs":
    st.header("🔍 Find Relevant Jobs Based on Your Resume")
    st.write("Upload your resume to find job listings on LinkedIn and Indeed.")

    # File uploader for resume
    uploaded_resume = st.file_uploader("Upload your resume (PDF):", type=["pdf"])

    if st.button("Search Jobs"):
        if uploaded_resume is not None:
            # Extract text from the uploaded PDF resume
            resume_text = input_pdf_text(uploaded_resume)

            # Create a prompt to send to the GPT model for job search
            input_prompt = f"""
            You are an advanced AI specialized in the Canadian job market. Based on the following resume,
            identify relevant job titles and provide direct search links to LinkedIn and Indeed job listings 
            that match the candidate's profile. The jobs should be related to their skills and experience.

            Provide the response in a JSON format like this:
            {{
                "Jobs": [
                    {{"title": "Job Title 1", "linkedin": "https://www.linkedin.com/jobs/search/?keywords=Job+Title+1", "indeed": "https://www.indeed.com/q-Job-Title-1-jobs.html"}},
                    {{"title": "Job Title 2", "linkedin": "https://www.linkedin.com/jobs/search/?keywords=Job+Title+2", "indeed": "https://www.indeed.com/q-Job-Title-2-jobs.html"}}
                ]
            }}

            Resume:
            {resume_text}
            """

            # Get the AI's response
            response = get_openai_response(input_prompt)

            if response:
                try:
                    # Parse the response as JSON
                    response_json = json.loads(response)

                    if "Jobs" in response_json:
                        # Prepare data for the table
                        jobs_data = {
                            "Job Title": [job["title"] for job in response_json["Jobs"]],
                            "LinkedIn": [make_clickable(job["linkedin"]) for job in response_json["Jobs"]],
                            "Indeed": [make_clickable(job["indeed"]) for job in response_json["Jobs"]],
                        }

                        # Create DataFrame and display as table
                        jobs_df = pd.DataFrame(jobs_data)
                        st.write(
                            jobs_df.to_html(escape=False, index=False), unsafe_allow_html=True
                        )
                    else:
                        st.error("No jobs found in the response.")

                except json.JSONDecodeError as e:
                    st.error(f"Error parsing response: {e}")
                    st.text(response)  # Display the raw response for debugging
                except KeyError as e:
                    st.error(f"KeyError: {str(e)} - Response might be incomplete or incorrectly formatted.")
                    st.text(response)  # Display the raw response for debugging
            else:
                st.error("No response from the API. Please try again.")
