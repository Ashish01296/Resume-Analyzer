import os
import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import csv
from googleapiclient.discovery import build
import requests
# Load environment variables
load_dotenv()

# Configure the Google Generative AI API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_text):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input_text)
    return response.text

def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

def check_resume_format(text):
    sections = ["Work Experience", "Education", "Skills", "Certifications", "Projects"]
    missing_sections = [section for section in sections if section.lower() not in text.lower()]
    
    feedback = ""
    if missing_sections:
        feedback += "Your resume is missing the following sections:\n"
        for section in missing_sections:
            feedback += f"- {section}\n"
    else:
        feedback += "Your resume contains all the standard sections.\n"
    
    return feedback

def save_feedback_to_file(section, rating, feedback):
    file_path = "feedback.csv"
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([section, rating, feedback])


input_prompt1 = """
Act as an experienced ATS (Applicant Tracking System) specialist with a strong understanding 
of various technical fields, such as software engineering, data science, and big data engineering.
Your job is to evaluate the resume based on the provided job description. 

1. Identify any missing keywords that are crucial for the role.
2. Recommend new skills that would improve the resume in relation to the job description.

Here are the inputs:

Resume:
{text}

Job Description:
{jd}

Please return the response as a JSON string with the following structure:
{{
    "MissingKeywords": [list of missing keywords],
    "RecommendedSkills": [list of new recommended skills]
}}
"""



def search_youtube_playlists(skill, api_key):

    api_key = os.getenv("API_KEY")
    youtube = build('youtube', 'v3', developerKey=api_key)
    query = f"{skill} full course playlist"
    try:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="playlist",
            maxResults=1
        )
        response = request.execute()
        playlist_url = ""
        thumbnail_url = ""
        if response['items']:
            playlist_id = response['items'][0]['id']['playlistId']
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            thumbnail_url = response['items'][0]['snippet']['thumbnails']['default']['url']
        return playlist_url, thumbnail_url
    except Exception as e:
        st.error(f"An error occurred while searching for playlists: {e}")
        return "", ""

def search_hr_interview_playlists(api_key):
    api_key = os.getenv("API_KEY")
    youtube = build('youtube', 'v3', developerKey=api_key)
    query = "HR interview questions playlist"
    try:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="playlist",
            maxResults=1
        )
        response = request.execute()
        playlist_url = ""
        thumbnail_url = ""
        if response['items']:
            playlist_id = response['items'][0]['id']['playlistId']
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            thumbnail_url = response['items'][0]['snippet']['thumbnails']['default']['url']
        return playlist_url, thumbnail_url
    except Exception as e:
        st.error(f"An error occurred while searching for HR interview playlists: {e}")
        return "", ""



# New input prompt for job role suggestions
job_role_prompt = """
Analyze the skills, experience, and education in the resume below and suggest alternate job roles or career paths that align with the candidate's qualifications. Provide at least 3 potential job roles based on the resume content.

Resume: {text}

I want the response in this format:
{{
"SuggestedRoles": ["Role1", "Role2", "Role3"]
}}
"""
# Input prompt for resume evaluation
input_prompt = """
Hey, act like a skilled and very experienced ATS (Application Tracking System) 
with a deep understanding of the tech field, including software engineering, data science, 
data analysis, and big data engineering. Your task is to evaluate the resume based on the given job description.
The job market is very competitive, so provide the best assistance for improving the resumes. 

1. Assign a percentage match based on the job description (JD).
2. Identify and list the missing keywords that are essential for this role.
3. Recommend new skills that could improve the resume based on the job description.

Provide detailed feedback on the following sections:
- Work Experience
- Education
- Skills

Your response should be a single string formatted as follows:
{{
    "JD Match":"%",
    "MissingKeywords":["keyword1", "keyword2", ...],
    "Profile Summary":"", 
    "RecommendedSkills":["skill1", "skill2", ...],
    "Feedback": {{
        "Work Experience": "Detailed feedback on work experience.",
        "Education": "Detailed feedback on education.",
        "Skills": "Detailed feedback on skills."
    }}
}}

Make sure to provide examples where applicable to illustrate your feedback.
resume: {text}
description: {jd}
"""

def get_ai_response(prompt):
    # Placeholder response for format evaluation
    return {
        "Format Assessment": "Good",
        "Suggestions": ["Increase white space between sections.", "Use a consistent font size throughout."],
        "Common Mistakes": ["Avoid using multiple font types.", "Ensure all sections are clearly labeled."]
    }
def evaluate_resume_format(resume_text):
    # Input prompt for resume format evaluation
    input_prompt = f"""
    Act as an experienced resume reviewer with expertise in evaluating resume formats for various job applications in tech, engineering, and data science fields. 
    Your task is to assess the provided resume format based on best practices for layout, organization, and visual appeal.
    
    Consider the following aspects:
    1. Overall Layout: Clean and professional? Enough white space?
    2. Font and Typography: Appropriate fonts, consistent sizes, and styles?
    3. Section Headings: Clear, distinct, and logically ordered?
    4. Bullet Points: Effective use of bullet points and lists?
    5. Alignment and Margins: Proper alignment and professional margins?
    6. Length and Conciseness: Appropriate length and relevance?

    Respond with:
    {{
        "Format Assessment": "Excellent/Good/Needs Improvement",
        "Suggestions": [],
        "Common Mistakes": []
    }}

    resume: {resume_text}
    """
 # Get the response from Google Gemini model
    gemini_response = get_gemini_response(input_prompt)
    
    try:
        # Parse the response from the model (assuming the response is in JSON format)
        format_feedback = eval(gemini_response)
        return format_feedback
    except:
        # Return an error if the response is not parseable
        return {
            "Format Assessment": "Needs Improvement",
            "Suggestions": ["Error in parsing response from the model."],
            "Common Mistakes": []
        }

# Function to get job role suggestions
def get_job_role_suggestions(text):
    input_text = job_role_prompt.format(text=text)
    response = get_gemini_response(input_text)
    response_json = json.loads(response)
    return response_json.get("SuggestedRoles", [])


# Sample resumes and templates library
def display_sample_resumes():
    st.title("Sample Resumes and Templates")
    st.markdown(
        """
        Explore our library of sample resumes and templates tailored to various job roles and industries. 
        Click on the links below to download or preview the samples.
        """
    )
    
    samples = {
        "Software Engineer": "https://www.overleaf.com/latex/templates/resume-professional-template-software-engineer/ttwtyxskrcsz",
        "Data Scientist": "https://www.overleaf.com/articles/peter-rasmussens-resume-data-scientist/bphkfprrcnwv",
        "Product Manager": "https://www.overleaf.com/latex/templates/faangpath-simple-template/npsfpdqnxmbc",
        "Full Stack Developer": "https://www.overleaf.com/articles/jatin-varlyanis-resume/yxzpgvxnnssr",
        "Machine Learning Engineer": "https://www.overleaf.com/latex/templates/ats-friendly-technical-resume/yrhtcnjyzgsf"
    }
    
    for role, link in samples.items():
        st.markdown(f"{role}: [Download Sample]({link}) ")

# Streamlit app
st.set_page_config(page_title="Smart Resume Analyzer", page_icon=":memo:", layout="wide")

# Sidebar for navigation
st.sidebar.title("Smart Resume Analyzer Navigation")
st.sidebar.markdown("### Welcome!")
st.sidebar.markdown("Use the tabs below to navigate through the app.")

# Create navigation tabs
tab = st.sidebar.radio("Choose a Section:", ["Home", "Resume Evaluation", "Resume Format Checker", "Resume Comparison","Feedback", "Sample Resumes and Templates","Job Role Suggestions"])
if tab == "Home":
    st.markdown("<h1 style='text-align: center;'>Welcome to Smart Resume Analyzer 🤖</h1>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style='text-align: center;'>
            <p>This tool helps you optimize your resume for Applicant Tracking Systems (ATS) 
            by evaluating its compatibility with a given job description. Use the "Resume Evaluation" tab 
            to get started with your resume analysis.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Use st.image to properly load the image
    st.image("Resume Analyzer.jpg", use_column_width=True)
    st.markdown("<h3 style='text-align: center;'>Features</h3>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style='text-align: center;'>
        <ul style='list-style-type: none; padding: 0;'>
            <li style='padding-bottom: 10px;'>✅ Evaluate resume compatibility with job descriptions</li>
            <li style='padding-bottom: 10px;'>✅ Identify missing keywords</li>
            <li style='padding-bottom: 10px;'>✅ Recommend new skills to improve your resume</li>
            <li style='padding-bottom: 10px;'>✅ Provide detailed feedback on work experience, education, and skills</li>
            <li style='padding-bottom: 10px;'>✅ Assist with HR interview preparation</li>
        </ul>
    </div>
        """,
        unsafe_allow_html=True
    )

elif tab == "Resume Format Checker":
    st.title("Resume Format Checker")

    # File uploader to allow users to upload their resume (PDF only)
    uploaded_file = st.file_uploader("Upload Your Resume (PDF only)", type="pdf")

    if uploaded_file is not None:
        # Extract text from the uploaded PDF
        resume_text = input_pdf_text(uploaded_file)
        
        # Get feedback from the Gemini model
        format_feedback = evaluate_resume_format(resume_text)

        # Display the format feedback
        st.subheader("Resume Format Feedback")
        st.write(f"**Format Assessment**: {format_feedback['Format Assessment']}")

        st.write("**Suggestions for Improvement**:")
        for suggestion in format_feedback['Suggestions']:
            st.markdown(f"- {suggestion}")

        st.write("**Common Mistakes**:")
        for mistake in format_feedback['Common Mistakes']:
            st.markdown(f"- {mistake}") 

elif tab == "Resume Comparison":
    st.title("Resume Comparison")
    
    st.markdown("### Step 1: Paste the Job Description")
    jd = st.text_area("Paste the Job Description", help="Copy and paste the job description you want to match your resumes with.")

    st.markdown("### Step 2: Upload Two Resume Versions")
    uploaded_file1 = st.file_uploader("Upload First Resume (PDF only)", type="pdf", help="Upload the first resume in PDF format for comparison.")
    uploaded_file2 = st.file_uploader("Upload Second Resume (PDF only)", type="pdf", help="Upload the second resume in PDF format for comparison.")
    
    st.markdown("### Step 3: Submit for Comparison")
    submit_comparison = st.button("Compare Resumes")

    if submit_comparison:
        if uploaded_file1 is not None and uploaded_file2 is not None and jd:
            with st.spinner('Comparing resumes...'):
                try:
                    text1 = input_pdf_text(uploaded_file1)
                    text2 = input_pdf_text(uploaded_file2)
                    
                    input_text1 = input_prompt.format(text=text1, jd=jd)
                    response1 = get_gemini_response(input_text1)
                    response_json1 = json.loads(response1)
                    
                    input_text2 = input_prompt.format(text=text2, jd=jd)
                    response2 = get_gemini_response(input_text2)
                    response_json2 = json.loads(response2)
                    
                    st.success("Resume comparison complete!")
                    st.subheader("Comparison Results")

                    st.markdown("### First Resume")
                    st.markdown(f"*Job Description Match:* {response_json1['JD Match']}")
                    st.markdown("*Missing Keywords:*")
                    for keyword in response_json1['MissingKeywords']:
                        st.markdown(f"<span class='badge'>{keyword}</span>", unsafe_allow_html=True)
                    st.markdown("*Profile Summary:*")
                    st.write(response_json1['Profile Summary'])
                    st.markdown("*Recommended Skills:*")
                    for skill in response_json1['RecommendedSkills']:
                        st.markdown(f"<span class='badge badge-skill'>{skill}</span>", unsafe_allow_html=True)
                    st.markdown("*Work Experience:*")
                    st.write(response_json1['Feedback']['Work Experience'])
                    st.markdown("*Education:*")
                    st.write(response_json1['Feedback']['Education'])
                    st.markdown("*Skills:*")
                    st.write(response_json1['Feedback']['Skills'])

                    st.markdown("### Second Resume")
                    st.markdown(f"*Job Description Match:* {response_json2['JD Match']}")
                    st.markdown("*Missing Keywords:*")
                    for keyword in response_json2['MissingKeywords']:
                        st.markdown(f"<span class='badge'>{keyword}</span>", unsafe_allow_html=True)
                    st.markdown("*Profile Summary:*")
                    st.write(response_json2['Profile Summary'])
                    st.markdown("*Recommended Skills:*")
                    for skill in response_json2['RecommendedSkills']:
                        st.markdown(f"<span class='badge badge-skill'>{skill}</span>", unsafe_allow_html=True)
                    st.markdown("*Work Experience:*")
                    st.write(response_json2['Feedback']['Work Experience'])
                    st.markdown("*Education:*")
                    st.write(response_json2['Feedback']['Education'])
                    st.markdown("*Skills:*")
                    st.write(response_json2['Feedback']['Skills'])

                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")
        else:
            st.error("Please provide the job description and both resume versions.")
    
    st.markdown(
        """
        *Tips for Resume Comparison:*
        - Compare how each resume matches the job description.
        - Look for missing keywords and recommend improvements.
        - Analyze which resume is better tailored for the job description.
        """
    )

elif tab == "Feedback":
    st.title("Submit Feedback")

    section = st.selectbox("Select Section", ["Resume Evaluation", "Resume Formate Checker" , "Resume Comparison" , "Job Role Suggestion" , "Sample Resume and Templates"])
    rating = st.slider("Rate this Section", min_value=0, max_value=10, step=1)
    feedback = st.text_area("Your Feedback", placeholder="Please provide your detailed feedback here...")

    submit_feedback = st.button("Submit Feedback")

    if submit_feedback:
        save_feedback_to_file(section, rating, feedback)
        st.success("Thank you for your feedback!")

elif tab == "Sample Resumes and Templates":
    display_sample_resumes()

elif tab == "Job Role Suggestions":
    st.title("Job Role Suggestions")

    st.markdown("### Step 1: Upload Your Resume")
    uploaded_file = st.file_uploader("Upload Your Resume (PDF only)", type="pdf", help="Upload your resume in PDF format for job role suggestions.")

    if uploaded_file is not None:
        text = input_pdf_text(uploaded_file)
        st.markdown("### Job Role Suggestions")
        with st.spinner('Fetching job role suggestions...'):
            try:
                job_roles = get_job_role_suggestions(text)
                for role in job_roles:
                    st.markdown(f"- {role}")
            except Exception as e:
                st.error(f"Error: {e}")





elif tab == "Resume Evaluation":
    st.title("Resume Evaluation And Youtube Playlist Recommendation")
    
    st.markdown("### Step 1: Paste the Job Description")
    jd = st.text_area("Paste the Job Description", help="Copy and paste the job description you want to match your resume with.")

    st.markdown("### Step 2: Upload Your Resume")
    uploaded_file = st.file_uploader("Upload Your Resume (PDF only)", type="pdf", help="Upload your resume in PDF format for evaluation.")

    st.markdown("### Step 3: Submit for Evaluation")
    submit = st.button("Submit")

    if submit:
        if uploaded_file is not None and jd:
            with st.spinner('Processing...'):
                try:
                    text = input_pdf_text(uploaded_file)
                    input_text = input_prompt.format(text=text, jd=jd)
                    response = get_gemini_response(input_text)
                    response_json = json.loads(response)

                    st.success("Resume evaluation complete!")
                    st.subheader("Evaluation Results")

                    st.markdown(f"*Job Description Match:* {response_json['JD Match']}")

                    st.markdown("*Missing Keywords:*")
                    for keyword in response_json['MissingKeywords']:
                        st.markdown(f"<span class='badge'>{keyword}</span>", unsafe_allow_html=True)

                    st.markdown("*Profile Summary:*")
                    st.write(response_json['Profile Summary'])

                    st.markdown("*Recommended Skills:*")
                    for skill in response_json['RecommendedSkills']:
                        st.markdown(f"<span class='badge badge-skill'>{skill}</span>", unsafe_allow_html=True)

                    st.markdown("### Free YouTube Course Playlists")
                    cols = st.columns(2)
                    api_key = "AIzaSyBOfYAqPggpYg9PaVy13Thlk1y5hhQnpRE"
                    for i, skill in enumerate(response_json['RecommendedSkills']):
                        playlist_url, thumbnail_url = search_youtube_playlists(skill, api_key)
                        with cols[i % 2]:
                            if playlist_url:
                                st.markdown(f"#### {skill}")
                                st.markdown(f"[![{skill}]({thumbnail_url})]({playlist_url})")
                            else:
                                st.markdown(f"#### {skill} - No playlist found")

                    st.markdown("### HR Interview Preparation Playlists")
                    hr_playlist_url, hr_thumbnail_url = search_hr_interview_playlists(api_key)
                    if hr_playlist_url:
                        st.markdown(f"#### HR Interview Preparation")
                        st.markdown(f"[![HR Interview Preparation]({hr_thumbnail_url})]({hr_playlist_url})")
                    else:
                        st.markdown(f"#### HR Interview Preparation - No playlist found")

                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")
        else:
            st.error("Please provide both a job description and a resume.")
    
    st.markdown(
        """
        *Tips for Improving Your Resume:*
        - Ensure your resume includes keywords mentioned in the job description.
        - Highlight relevant experience and skills.
        - Keep the formatting clean and ATS-friendly.
        """
    )

# CSS to style the badges and layout
st.markdown(
    """
    <style>
    .badge {
        display: inline-block;
        padding: 0.25em 0.4em;
        margin: 0.1em;
        font-size: 75%;
        font-weight: 700;
        line-height: 1;
        color: #fff;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.25rem;
        background-color: #007bff;
    }
    .badge-skill {
        background-color: #28a745;
    }
    .streamlit-expanderHeader {
        font-size: 1.5em;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)

