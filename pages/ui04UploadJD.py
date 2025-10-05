import streamlit as st
import pandas as pd
import os
from datetime import datetime

def generate_job_description():

    st.title("~/New Job Description")

    with st.container(border=True):

        organization = st.text_input("Organization")
        job_role = st.text_input("Job Role")
        last_date = st.date_input("Last Date of Application")
        num_positions = st.number_input("Number of Positions", min_value=1, step=1)

        job_text = st.text_area("Enter job description", height=200)

        if st.button("Submit", type="primary"):
            if organization.strip() == "":
                st.warning("Please enter the organization.")
            elif job_role.strip() == "":
                st.warning("Please enter the job role.")
            elif last_date is None:
                st.warning("Please select the last date of application.")
            elif num_positions < 1:
                st.warning("Please enter a valid number of positions.")
            elif job_text.strip() == "":
                st.warning("Please enter a job description.")
            else:
                # Create jds folder if it doesn't exist
                os.makedirs("jds", exist_ok=True)
                
                # Save to CSV
                csv_file = "job_descriptions.csv"
                if not os.path.exists(csv_file):
                    df = pd.DataFrame(columns=["id", "organization", "job_role", "last_date", "num_positions", "job_details"])
                    df.to_csv(csv_file, index=False)

                df = pd.read_csv(csv_file)
                last_id = df["id"].max() if not df.empty else 0

                with open(csv_file, "a") as f:
                    f.write(f"{last_id + 1},\"{organization}\",\"{job_role}\",\"{last_date}\",{num_positions},\"{job_text}\"\n")

                # Create markdown file
                current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"{job_role.replace(' ', '_')}_at_{organization.replace(' ', '_')}_job_creted_at_{current_datetime}.txt"
                filepath = os.path.join("jds", filename)
                
                # Create markdown content
                markdown_content = f"""# job role : {job_role}

**Organization:** {organization}  
**Last Date of Application:** {last_date}  
**Number of Positions:** {num_positions}  
**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Job Description

{job_text}

"""
                
                # Write to markdown file
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                st.success(f"Job created successfully! Saved as: {filename}")

if __name__ == "__main__":
    generate_job_description()