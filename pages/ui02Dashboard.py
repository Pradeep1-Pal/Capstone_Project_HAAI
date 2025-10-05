import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime
import plotly.graph_objs as go

# Import your custom modules
from models.gemini.cvProcessingLLM_api_langchain import ResumeEvaluatorLangChain
from models.ollama.cvProcessingLLM_langchain import ResumeEvaluatorOllama
import modelconfig


def init_session_state():
    """Initialize session state variables"""
    if 'evaluation_results' not in st.session_state:
        st.session_state.evaluation_results = []
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = getattr(modelconfig, 'DEFAULT_MODEL', 'gemini-2.5-pro')
    if 'select_all_resumes' not in st.session_state:
        st.session_state.select_all_resumes = False


def get_available_resumes(folder_path="./cvs"):
    """Get list of available resumes from folder"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return []
    
    resume_files = [f for f in os.listdir(folder_path) 
                   if f.lower().endswith(('.pdf', '.docx', '.doc'))]
    return sorted(resume_files)


def get_available_jds(folder_path="./jds"):
    """Get list of available job descriptions from folder"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return []
    
    jd_files = [f for f in os.listdir(folder_path) 
               if f.lower().endswith(('.txt', '.pdf', '.docx'))]
    return sorted(jd_files)


def create_score_gauge(score, max_score, title, color_threshold=50):
    """Create a modern gauge chart for scores"""
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    color = 'green' if percentage >= color_threshold else 'orange' if percentage >= 30 else 'red'
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 14}},
        number={'suffix': f"/{max_score}", 'font': {'size': 20}},
        gauge={
            'axis': {'range': [None, max_score], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, max_score * 0.3], 'color': '#ffebee'},
                {'range': [max_score * 0.3, max_score * 0.7], 'color': '#fff9c4'},
                {'range': [max_score * 0.7, max_score], 'color': '#e8f5e9'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_score * 0.7
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_donut_chart(score, passing_score=70):
    """Create a modern donut chart for overall score"""
    color = 'green' if score >= passing_score else 'red'
    
    fig = go.Figure(data=[go.Pie(
        labels=['Score', 'Remaining'],
        values=[score, 100 - score],
        hole=0.7,
        marker=dict(colors=[color, '#f0f0f0']),
        textinfo='none',
        hoverinfo='label+value'
    )])
    
    fig.update_layout(
        showlegend=False,
        height=250,
        width=250,
        margin=dict(l=0, r=0, t=0, b=0),
        annotations=[dict(
            text=f'{score}%',
            x=0.5, y=0.5,
            font_size=40,
            showarrow=False,
            font=dict(color=color, weight='bold')
        )]
    )
    
    return fig


def display_candidate_header(result):
    """Display candidate information in a clean header"""
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 25px; border-radius: 10px; color: white; margin-bottom: 20px;'>
            <h2 style='margin: 0; color: white;'>👤 {result['name']}</h2>
            <p style='margin: 5px 0; font-size: 16px;'>
                📧 <a href='mailto:{result['email']}' style='color: white;'>{result['email']}</a> | 
                📱 {result['phone']}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    if result.get('profile'):
        with st.expander("Profile Summary", expanded=False):
            st.info(result['profile'])


def display_score_breakdown(result):
    """Display detailed score breakdown with modern UI"""
    st.markdown("### Score Breakdown")
    
    # Main score display
    col1, col2 = st.columns([1, 2])
    
    with col1:
        total_score = result.get('total_score', 0)
        passing_score = getattr(modelconfig, 'PASSING_SCORE', 70)
        fig = create_donut_chart(total_score, passing_score)
        st.plotly_chart(fig, use_container_width=True)
        
        status = "ELIGIBLE" if total_score >= passing_score else "NOT ELIGIBLE"
        status_color = "green" if total_score >= passing_score else "red"
        st.markdown(f"<h3 style='text-align: center; color: {status_color};'>{status}</h3>", 
                   unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Category Scores")
        
        # Define score mappings
        categories = [
            ('education', 'Education', 10),
            ('experience', 'Experience', 20),
            ('skills', 'Skills', 30),
            ('projects', 'Projects', 20),
            ('certifications', 'Certifications', 10),
            ('active_links', 'Active Links', 10)
        ]
        
        for key, label, max_score in categories:
            if key in result:
                score_data = result[key]
                score = score_data.get('score', 0)
                reason = score_data.get('reason', 'No reason provided')
                
                col_metric, col_reason = st.columns([1, 3])
                with col_metric:
                    percentage = (score / max_score * 100) if max_score > 0 else 0
                    color = "🟢" if percentage >= 70 else "🟡" if percentage >= 40 else "🔴"
                    st.metric(label=f"{color} {label}", value=f"{score}/{max_score}")
                
                with col_reason:
                    st.caption(f"**Reason:** {reason}")
                
                st.divider()


def display_detailed_analysis(result):
    """Display detailed analysis sections"""
    tab1, tab2, tab3, tab4 = st.tabs(["🎓 Education", "💼 Experience", "🛠️ Skills", "🚀 Projects"])
    
    with tab1:
        if 'education' in result:
            edu = result['education']
            col1, col2 = st.columns([1, 3])
            with col1:
                fig = create_score_gauge(edu['score'], 10, "Education Score")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("#### Analysis")
                st.write(edu.get('reason', 'N/A'))
    
    with tab2:
        if 'experience' in result:
            exp = result['experience']
            col1, col2 = st.columns([1, 3])
            with col1:
                fig = create_score_gauge(exp['score'], 20, "Experience Score")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("#### Analysis")
                st.write(exp.get('reason', 'N/A'))
    
    with tab3:
        if 'skills' in result:
            skills = result['skills']
            col1, col2 = st.columns([1, 3])
            with col1:
                fig = create_score_gauge(skills['score'], 30, "Skills Score")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("#### Skills Analysis")
                st.write(skills.get('reason', 'N/A'))
                
                col_possessed, col_required = st.columns(2)
                with col_possessed:
                    st.markdown("**✅ Skills Possessed:**")
                    possessed = skills.get('skills_possessed', [])
                    if possessed:
                        for skill in possessed:
                            st.markdown(f"- {skill}")
                    else:
                        st.write("None listed")
                
                with col_required:
                    st.markdown("**📋 Skills Required:**")
                    required = skills.get('skills_required', [])
                    if required:
                        for skill in required:
                            st.markdown(f"- {skill}")
                    else:
                        st.write("None listed")
    
    with tab4:
        if 'projects' in result:
            proj = result['projects']
            col1, col2 = st.columns([1, 3])
            with col1:
                fig = create_score_gauge(proj['score'], 20, "Projects Score")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("#### Projects Analysis")
                st.write(proj.get('reason', 'N/A'))
                
                st.markdown("**📁 Projects:**")
                projects = proj.get('projects', [])
                if projects:
                    for project in projects:
                        st.markdown(f"- {project}")
                else:
                    st.write("No projects listed")


def display_overall_assessment(result):
    """Display overall assessment"""
    if 'overall_assessment' in result:
        st.markdown("### 🎯 Overall Assessment")
        st.info(result['overall_assessment'])


def save_results_to_db(result, csv_path="resume_database.csv"):
    """Save results to CSV database"""
    try:
        passing_score = getattr(modelconfig, 'PASSING_SCORE', 70)
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'name': result.get('name', 'N/A'),
            'email': result.get('email', 'N/A'),
            'phone': result.get('phone', 'N/A'),
            'total_score': result.get('total_score', 0),
            'education_score': result.get('education', {}).get('score', 0),
            'experience_score': result.get('experience', {}).get('score', 0),
            'skills_score': result.get('skills', {}).get('score', 0),
            'projects_score': result.get('projects', {}).get('score', 0),
            'certifications_score': result.get('certifications', {}).get('score', 0),
            'links_score': result.get('active_links', {}).get('score', 0),
            'status': 'pass' if result.get('total_score', 0) >= passing_score else 'fail'
        }
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
            df.drop_duplicates(subset=['email'], keep='last', inplace=True)
        else:
            df = pd.DataFrame([data])
        
        df.to_csv(csv_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving to database: {e}")
        return False


def main():
    
    st.title("~/Resume Evaluation")

    st.markdown(f":violet-badge[:material/settings: {modelconfig.PROVIDER}] :orange-badge[:material/settings: {modelconfig.MODEL}]")
    
    # Job Description Selection
    with st.container(border=True):
        st.markdown("#### 📋 Select Job Description")
        
        jd_files = get_available_jds()
        
        if not jd_files:
            st.warning("⚠️ No job descriptions found in ./jds folder. Please add JD files.")
            selected_jd = None
        else:
            selected_jd = st.selectbox(
                "Choose a job description",
                jd_files,
                help="Select from available job descriptions in ./jds folder"
            )
            
            if selected_jd:
                st.success(f"✅ Selected: {selected_jd}")
                
                # Preview JD
                with st.expander("👁️ Preview Job Description"):
                    try:
                        jd_path = os.path.join("./jds", selected_jd)
                        with open(jd_path, 'r', encoding='utf-8') as f:
                            jd_content = f.read()
                        st.markdown(jd_content)
                    except Exception as e:
                        st.error(f"Error reading JD: {e}")
    
    # st.divider()
    
    # Resume Selection with Select All
    with st.container(border=True):
        st.markdown("#### 📁 Select Resumes")
        
        resume_files = get_available_resumes()
        
        if not resume_files:
            st.warning("⚠️ No resumes found . Please upload resume files.")
            selected_resumes = []
        else:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.caption(f"Found {len(resume_files)} resume(s)")
            
            with col2:
                select_all = st.checkbox("Select All", key="select_all_checkbox")
            
            if select_all:
                selected_resumes = st.multiselect(
                    "Choose resumes to evaluate",
                    resume_files,
                    default=resume_files,
                    help="Select one or more resumes from ./resume folder"
                )
            else:
                selected_resumes = st.multiselect(
                    "Choose resumes to evaluate",
                    resume_files,
                    help="Select one or more resumes from ./resume folder"
                )
            
            if selected_resumes:
                st.info(f"📊 {len(selected_resumes)} resume(s) selected for evaluation")
    
    st.divider()
    
    evaluate_btn = st.button(
        "Evaluate Resumes",
        type="primary",
        disabled=not (selected_jd and selected_resumes)
    )
    
    if evaluate_btn and selected_jd and selected_resumes:
        jd_path = os.path.join("./jds", selected_jd)
        
        st.markdown("---")
        st.markdown(f"### Evaluating {len(selected_resumes)} Resume(s)")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        
        for idx, resume_file in enumerate(selected_resumes):
            resume_path = os.path.join("./cvs", resume_file)
            
            status_text.text(f"Processing {idx + 1}/{len(selected_resumes)}: {resume_file}")
            progress_bar.progress((idx + 1) / len(selected_resumes))

            with st.container(border = True):
            
                try:

                    with st.spinner("⏳ Evaluating resume..."):

                        if modelconfig.PROVIDER == "gemini":
                            modelName = modelconfig.MODEL
                            start_time = time.time()
                            evaluator = ResumeEvaluatorLangChain(model_name=modelName)
                            result = evaluator.evaluate_resume(resume_path, jd_path)
                            elapsed_time = time.time() - start_time
                        if modelconfig.PROVIDER == "openai":
                            pass
                        if modelconfig.PROVIDER == "ollama":
                            modelName = modelconfig.MODEL
                            start_time = time.time()
                            evaluator = ResumeEvaluatorOllama(model_name=modelName)
                            result = evaluator.evaluate_resume(resume_path, jd_path)
                            elapsed_time = time.time() - start_time

                        
                    
                    # st.markdown("---")
                    st.success(f"✅ Completed: {resume_file} (in {elapsed_time:.2f}s)")
                    
                    # Display results
                    display_candidate_header(result)
                    display_score_breakdown(result)
                    display_detailed_analysis(result)
                    display_overall_assessment(result)
                    
                    # Auto-save to database
                    if save_results_to_db(result):
                        st.caption("💾 Results automatically saved to database")
                        
                except Exception as e:
                    st.error(f"❌ Error evaluating {resume_file}: {str(e)}")
        
        status_text.text("✅ All evaluations completed!")
        # st.balloons()/



    

if __name__ == "__main__":
    main()