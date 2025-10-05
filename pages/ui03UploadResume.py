import streamlit as st
import os

def bulk_file_uploader():
    st.title("Bulk Resume Uploader")

    st.write("Upload one or more files:")
    uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True)

    if uploaded_files:
        if not os.path.exists("cvs"):
            os.makedirs("cvs")
            # st.info("Created 'db' folder.")

        # Function to save uploaded files into the 'db' folder
        def save_uploaded_files(files):
            for file in files:
                with open(os.path.join("cvs", file.name), "wb") as f:
                    f.write(file.getbuffer())
            st.success(f"Done uploading resume in database")

        save_uploaded_files(uploaded_files)

if __name__ == "__main__":
    bulk_file_uploader()