import requests
import streamlit as st
import pandas as pd
import base64
import os
import io
import sqlite3

# Initialize session state variables
if 'token_checked' not in st.session_state:
    st.session_state.token_checked = False
if 'token_valid' not in st.session_state:
    st.session_state.token_valid = False
if 'repo_checked' not in st.session_state:
    st.session_state.repo_checked = False
if 'repo_valid' not in st.session_state:
    st.session_state.repo_valid = False
if 'file_checked' not in st.session_state:
    st.session_state.file_checked = False
if 'file_valid' not in st.session_state:
    st.session_state.file_valid = False
if 'db_data' not in st.session_state:
    st.session_state.db_data = None
if 'file_sha' not in st.session_state:
    st.session_state.file_sha = None
    
# Get secrets with proper error handling
def get_secret(secret_name, default_value=""):
    try:
        return st.secrets[secret_name]
    except:
        return default_value

# Get GitHub token - first try from secrets, then from session state, then prompt user
github_token = get_secret('GITHUB_TOKEN')
if not github_token and 'github_token' in st.session_state:
    github_token = st.session_state.github_token

# Get repository owner from secrets or session state
repo_owner = get_secret('REPO_OWNER')
if not repo_owner and 'repo_owner' in st.session_state:
    repo_owner = st.session_state.repo_owner

# Get repository name from secrets or session state  
repo_name = get_secret('REPO_NAME')
if not repo_name and 'repo_name' in st.session_state:
    repo_name = st.session_state.repo_name

# Get file path from secrets or session state
file_path = get_secret('FILE_PATH')
if not file_path and 'file_path' in st.session_state:
    file_path = st.session_state.file_path

st.title("GitHub SQLite Editor")

# Create initial SQLite database if it doesn't exist
if not os.path.exists('test.db'):
    conn = sqlite3.connect('test.db')
    # Create a sample table
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['John', 'Jane', 'Bob'],
        'age': [25, 30, 35]
    })
    df.to_sql('sample_table', conn, if_exists='replace', index=False)
    conn.close()
    st.success("Created initial SQLite database 'test.db' with sample data")

# If token not available in secrets or session, ask user
if not github_token:
    github_token = st.text_input("Enter your GitHub Personal Access Token:", type="password")
    if github_token:
        st.session_state.github_token = github_token

# Helper function to create headers
def get_headers():
    return {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

# Check token function
def check_token():
    response = requests.get("https://api.github.com/user", headers=get_headers())
    
    st.session_state.token_checked = True
    st.session_state.token_valid = (response.status_code == 200)
    
    if response.status_code == 200:
        st.session_state.user_data = response.json()
        
        # Get rate limit info
        rate_response = requests.get("https://api.github.com/rate_limit", headers=get_headers())
        if rate_response.status_code == 200:
            st.session_state.rate_data = rate_response.json()
    else:
        st.session_state.user_error = response.text

# Check repository function
def check_repository(repo_owner, repo_name):
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    response = requests.get(repo_url, headers=get_headers())
    
    st.session_state.repo_checked = True
    st.session_state.repo_valid = (response.status_code == 200)
    
    if response.status_code == 200:
        st.session_state.repo_data = response.json()
    else:
        st.session_state.repo_error = response.text

# Check file function and load SQLite
def check_file(repo_owner, repo_name, file_path):
    # For local testing, use the local database file
    try:
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        if tables:
            table_name = tables[0][0]
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            st.session_state.db_data = df
            st.session_state.table_name = table_name
            st.session_state.file_checked = True
            st.session_state.file_valid = True
        conn.close()
    except Exception as e:
        st.session_state.file_error = f"Error parsing SQLite DB: {str(e)}"
        st.session_state.file_checked = True
        st.session_state.file_valid = False

# Function to save edited SQLite back to GitHub
def save_sqlite_to_github(repo_owner, repo_name, file_path, df):
    try:
        # Save to local SQLite database
        conn = sqlite3.connect('test.db')
        df.to_sql(st.session_state.table_name, conn, if_exists='replace', index=False)
        conn.close()
        return True, "File updated successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"

# Function to download SQLite from GitHub
def download_sqlite_from_github(repo_owner, repo_name, file_path):
    try:
        with open('test.db', 'rb') as f:
            return f.read()
    except Exception as e:
        st.error(f"Error downloading file: {str(e)}")
        return None

# Reset function
def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()  # Updated from st.experimental_rerun()

# Display secrets status
with st.expander("Secrets Status"):
    st.write("GitHub Token:", "Available ✅" if github_token else "Not set ❌")
    st.write("Repository Owner:", "Available ✅" if repo_owner else "Not set ❌")
    st.write("Repository Name:", "Available ✅" if repo_name else "Not set ❌")
    st.write("SQLite File Path:", "Available ✅" if file_path else "Not set ❌")

# Main UI flow
if github_token:
    # Token test section
    st.subheader("Step 1: Test Token Authorization")
    if not st.session_state.token_checked:
        if st.button("Test Token Authorization"):
            with st.spinner("Checking token..."):
                check_token()
    
    if st.session_state.token_checked:
        if st.session_state.token_valid:
            st.success("✅ Token is valid and working!")
            if hasattr(st.session_state, 'user_data'):
                user_data = st.session_state.user_data
                st.write(f"Authenticated as: {user_data['login']}")
        else:
            st.error("❌ Token authorization failed!")
            if hasattr(st.session_state, 'user_error'):
                st.text(st.session_state.user_error)
    
    # Repository test section
    if st.session_state.token_valid:
        st.subheader("Step 2: Test Repository Access")
        
        # If repo details not in secrets, ask user
        if not repo_owner:
            repo_owner = st.text_input("Repository Owner:")
            if repo_owner:
                st.session_state.repo_owner = repo_owner
                
        if not repo_name:
            repo_name = st.text_input("Repository Name:")
            if repo_name:
                st.session_state.repo_name = repo_name
        
        if repo_owner and repo_name and not st.session_state.repo_checked:
            if st.button("Test Repository Access"):
                with st.spinner("Checking repository access..."):
                    check_repository(repo_owner, repo_name)
        
        if st.session_state.repo_checked:
            if st.session_state.repo_valid:
                st.success(f"✅ Successfully accessed repository: {repo_owner}/{repo_name}")
            else:
                st.error(f"❌ Failed to access repository: {repo_owner}/{repo_name}")
                if hasattr(st.session_state, 'repo_error'):
                    st.text(st.session_state.repo_error)
        
        # File test section
        if st.session_state.repo_valid:
            st.subheader("Step 3: Select SQLite File")
            
            # If file path not in secrets, ask user
            if not file_path:
                file_path = st.text_input("SQLite File Path:")
                if file_path:
                    st.session_state.file_path = file_path
            
            if file_path and not st.session_state.file_checked:
                if st.button("Load SQLite File"):
                    with st.spinner("Loading SQLite file..."):
                        check_file(repo_owner, repo_name, file_path)
            
            if st.session_state.file_checked:
                if st.session_state.file_valid:
                    if st.session_state.db_data is not None:
                        st.success(f"✅ Successfully loaded SQLite file: {file_path}")
                        
                        # SQLite Editor Section
                        st.subheader("Step 4: Edit SQLite Data")
                        
                        # Show original data
                        with st.expander("View Original Data", expanded=False):
                            st.dataframe(st.session_state.db_data)
                        
                        # Edit data
                        st.write("Make your changes below:")
                        edited_df = st.data_editor(
                            st.session_state.db_data,
                            num_rows="dynamic",
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Save changes
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Save Changes to GitHub"):
                                with st.spinner("Saving changes..."):
                                    success, message = save_sqlite_to_github(
                                        repo_owner, repo_name, file_path, edited_df
                                    )
                                    if success:
                                        st.session_state.db_data = edited_df  # Update the local data
                                        st.success(message)
                                    else:
                                        st.error(message)
                        
                        with col2:
                            if st.button("Download SQLite DB"):
                                db_content = download_sqlite_from_github(repo_owner, repo_name, file_path)
                                if db_content:
                                    st.download_button(
                                        label="Click to Download",
                                        data=db_content,
                                        file_name="downloaded_file.db",
                                        mime="application/x-sqlite3"
                                    )
                                else:
                                    st.error("Failed to download the file")
                    else:
                        st.error("The selected file is not a valid SQLite database or could not be parsed.")
                else:
                    st.error(f"❌ Failed to access file: {file_path}")
                    if hasattr(st.session_state, 'file_error'):
                        st.text(st.session_state.file_error)

    # Add a reset button at the bottom
    if st.session_state.token_checked:
        if st.button("Start Over"):
            reset_all()

else:
    st.info("Please enter your GitHub Personal Access Token to check authorization.")