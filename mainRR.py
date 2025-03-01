# Get environment variables from .env during development or Streamlit secrets in production
def get_env_variable(var_name, default_value=""):
    # Try Streamlit secrets first (for production)
    try:
        return st.secrets[var_name]
    except (KeyError, AttributeError):
        # Fall back to environment variables (for local development)
        value = os.getenv(var_name)
        return value if value else default_value