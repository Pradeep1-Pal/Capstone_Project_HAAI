import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime
import plotly.graph_objs as go
from streamlit_option_menu import option_menu

def main():
    
    st.title("~/Leaderboard")
    
    csv_path = "resume_database.csv"
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Evaluations", len(df), border=True)
        
        with col2:
            passed = len(df[df['status'] == 'pass'])
            st.metric("Passed", passed, border=True)
        
        with col3:
            failed = len(df[df['status'] == 'fail'])
            st.metric("Failed", failed, border=True)
        
        with col4:
            avg_score = df['total_score'].mean()
            st.metric("Avg Score", f"{avg_score:.1f}", border=True)
        
        st.divider()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect("Status", ['pass', 'fail'], default=['pass', 'fail'])
        with col2:
            min_score = st.slider("Minimum Score", 0, 100, 0)
        with col3:
            search = st.text_input("🔍 Search by name/email")
        
        # Apply filters
        filtered_df = df[df['status'].isin(status_filter)]
        filtered_df = filtered_df[filtered_df['total_score'] >= min_score]
        if search:
            filtered_df = filtered_df[
                filtered_df['name'].str.contains(search, case=False, na=False) |
                filtered_df['email'].str.contains(search, case=False, na=False)
            ]
        
        st.markdown(f"#### Showing {len(filtered_df)} of {len(df)} records")
        
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "total_score": st.column_config.ProgressColumn(
                    "Total Score",
                    format="%d",
                    min_value=0,
                    max_value=100,
                ),
            }
        )
        
        
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            ":material/download:  Download Filtered Results",
            csv,
            "resume_results.csv",
            "text/csv",
        )

    else:
        st.info("📭 No evaluations yet. Start evaluating resumes to build your database!")


if __name__ == "__main__":
    main()