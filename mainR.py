import streamlit as st
import requests
import json

st.title("GitHub Token Tester with Streamlit Secrets")

# Try to access the GitHub token from secrets
try:
    # This will access the token from .streamlit/secrets.toml locally
    # or from the deployed app's secrets in Streamlit Cloud
    github_token = st.secrets["GITHUB_TOKEN"]
    token_source = "Successfully loaded token from Streamlit secrets!"
    token_display = "Token found (hidden for security)"
except Exception as e:
    github_token = None
    token_source = f"Failed to load token from secrets: {str(e)}"
    token_display = "No token found"

# Display token status (but not the actual token)
st.write("### Token Status")
st.write(token_source)
st.write(f"Token: {token_display}")

# Test the token if it exists
if github_token:
    if st.button("Test GitHub Token"):
        with st.spinner("Testing token..."):
            # Create headers with the token
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Make a request to GitHub API
            response = requests.get("https://api.github.com/user", headers=headers)
            
            # Display the result
            if response.status_code == 200:
                user_data = response.json()
                st.success(f"✅ Token is valid! Authenticated as: {user_data['login']}")
                
                # Display some user info
                st.write("### Your GitHub Info")
                st.json(json.dumps({
                    "username": user_data.get('login'),
                    "name": user_data.get('name'),
                    "followers": user_data.get('followers'),
                    "public_repos": user_data.get('public_repos')
                }))
            else:
                st.error(f"❌ Token authentication failed with status code: {response.status_code}")
                st.text(response.text)
else:
    st.warning("Please set up your GitHub token in Streamlit secrets to test it.")
    
# Add instructions for setting up secrets
with st.expander("How to set up Streamlit secrets"):
    st.write("""
    ### Local Development
    1. Create a `.streamlit/secrets.toml` file in your project root
    2. Add your GitHub token to the file:
    ```toml
    GITHUB_TOKEN = "your-github-token-here"
    ```
    3. Make sure `.streamlit/` is in your `.gitignore`
    
    ### Deployment
    1. In Streamlit Cloud, go to your app settings
    2. Find the "Secrets" section
    3. Add your secrets in TOML format:
    ```toml
    GITHUB_TOKEN = "your-github-token-here"
    ```
    4. Save the changes
    """)