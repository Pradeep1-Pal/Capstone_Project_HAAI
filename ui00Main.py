import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(
    page_title="resumeRanking",
    page_icon="🛸",
    layout="wide"
)

@st.dialog("~JOIN BETA")
def modal():
    st.write("Fill out this form to join our beta program!")
    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    
    if st.button("Submit", key="joinbeta"):
        if name and email and phone:
            data = {'Name': [name], 'Email': [email], 'Phone Number': [phone]}
            beta_df = pd.DataFrame(data)
            
            # Check if file exists to determine if we need headers
            try:
                existing_df = pd.read_csv('beta.csv')
                beta_df.to_csv('beta.csv', mode='a', index=False, header=False)
            except FileNotFoundError:
                beta_df.to_csv('beta.csv', mode='w', index=False, header=True)
            
            st.success("Thank you for joining the beta!")
            st.rerun()
        else:
            st.error("Please fill out all fields")

def home_page():
    # Hero Section
    st.image("demo.png", use_container_width=True)
    
    # Main Title with styling
    st.markdown("""
        <h1 style='text-align: left; color: red; font-size: 3.5em; margin-bottom: 0;'>
            ResumeRanking
        </h1>
        <p style='text-align: left; font-size: 1.3em; color: #666; margin-top: 0;'>
            AI-Powered Resume Analysis & Candidate Ranking
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Introduction Card
    st.info("**Smart Hiring Made Simple** - Leverage advanced AI to analyze candidate resumes against job descriptions and identify the perfect match for your team.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # How It Works Section
    st.markdown("## How It Works")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style='background-color: #f0f8ff; padding: 20px; border-radius: 10px; border-left: 4px solid #1E88E5;'>
                <h3 style='color: #1E88E5;'>📤 Step 1: Upload</h3>
                <p>Upload your job descriptions and candidate resumes to get started.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='background-color: #f0fff4; padding: 20px; border-radius: 10px; border-left: 4px solid #4CAF50;'>
                <h3 style='color: #4CAF50;'>🔍 Step 2: Analyze</h3>
                <p>Select the job and resumes from the dashboard and let AI work its magic.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='background-color: #fff8f0; padding: 20px; border-radius: 10px; border-left: 4px solid #FF9800;'>
                <h3 style='color: #FF9800;'>🏆 Step 3: Review</h3>
                <p>View ranked candidates with detailed relevance scores on the leaderboard.</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Analysis Factors Section
    st.markdown("## Analysis Factors")
    st.markdown("Our AI evaluates candidates across multiple dimensions to ensure comprehensive assessment:")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create two columns for analysis factors
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style='background-color: #fafafa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <h4>🎯 Skills & Relevance</h4>
                <p style='color: #666;'>Assesses the relevance of skills mentioned in the resume to those required in the job description.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style='background-color: #fafafa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <h4>💼 Experience</h4>
                <p style='color: #666;'>Analyzes the candidate's work experience and how it aligns with the job requirements.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style='background-color: #fafafa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <h4>🎓 Education</h4>
                <p style='color: #666;'>Considers the candidate's educational background and its relevance to the job.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='background-color: #fafafa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <h4>🚀 Projects</h4>
                <p style='color: #666;'>Evaluates the projects listed in the resume and their relevance to the job.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style='background-color: #fafafa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <h4>📜 Certifications</h4>
                <p style='color: #666;'>Reviews any certifications mentioned in the resume and their relevance to the job.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div style='background-color: #fafafa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <h4>🔗 Portfolio Links</h4>
                <p style='color: #666;'>Checks for any links provided in the resume and their relevance.</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Results Section
    st.success("✨ **The Result**: Each candidate receives a comprehensive relevance score, making it easy to identify your top talent at a glance!")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Call to Action
    st.markdown("---")
    
    st.markdown("<h3 style='text-align: left;'>Ready to Get Started?</h3>", unsafe_allow_html=True)
    if st.button("Join Beta", type="primary"):
        modal()

# Define navigation
pg = st.navigation([
    st.Page(home_page, title="Home", icon=":material/home:"),
    st.Page("pages/ui04UploadJD.py", title="Upload Job Description", icon=":material/domain:"),
    st.Page("pages/ui03UploadResume.py", title="Upload Resume", icon=":material/upload_file:"),
    st.Page("pages/ui02Dashboard.py", title="Dashboard", icon=":material/dashboard:"),
    st.Page("pages/ui05Leaderboard.py", title="Leaderboard", icon=":material/leaderboard:"),
    st.Page("pages/ui06Setting.py", title="Settings", icon=":material/settings:"),
])

pg.run()