import streamlit as st
import os

# Define models for each provider
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro"
]

OLLAMA_MODELS = [
    # Llama Models
    "llama3.2:latest",
    "llama3.2:1b",
    "llama3.2:3b",
    "llama2:7b",
    "llama2:13b",
    "llama2:70b",
    
    # Gemma Models
    "gemma3:latest",
    "gemma3:12b",
    "gemma2:9b",
    
    # Mistral Models
    "mistral:7b",
    
    # Phi Models
    "phi3:latest",
    "phi3:14b",
    "phi4:latest",
    
    # DeepSeek Models
    "deepseek-r1:7b",
    "deepseek-r1:latest",
    "deepseek-v3.1:latest",
    
    # Qwen Models
    "qwen3:latest",
    "qwen3:4b",
    "qwen3:14b",
    "qwen3:235b",
    "qwen2.5:latest",
    
    # GPT Models
    "gpt-oss:latest"
]

# Default models
DEFAULT_MODELS = {
    "gemini": "gemini-2.5-pro",
    "ollama": "llama2:7b"
}

def write_config_file(provider, model, passing_score):
    """Write configuration to modelconfig.py file"""
    config_content = f"""# modelconfig.py file

PROVIDER = '{provider}'
MODEL = '{model}'
PASSING_SCORE = {passing_score}
"""
    
    with open('modelconfig.py', 'w') as f:
        f.write(config_content)
    
    return config_content

def main():
    # st.set_page_config(page_title="Model Configuration", page_icon="⚙️", layout="centered")
    
    st.title("~/Model Configuration Manager")
    st.markdown("Configure your AI model settings")
    
    st.divider()
    
    # Provider Selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Provider")
        provider = st.selectbox(
            "Select Provider",
            options=["gemini", "ollama"],
            index=0,
            help="Choose the AI provider"
        )
    
    with col2:
        st.subheader("Model")
        # Get models based on selected provider
        if provider == "gemini":
            available_models = GEMINI_MODELS
            default_model = DEFAULT_MODELS["gemini"]
        else:
            available_models = OLLAMA_MODELS
            default_model = DEFAULT_MODELS["ollama"]
        
        # Find default index
        default_index = available_models.index(default_model) if default_model in available_models else 0
        
        model = st.selectbox(
            "Select Model",
            options=available_models,
            index=default_index,
            help=f"Choose a model from {provider}"
        )
    
    st.divider()
    
    # Passing Score
    st.subheader("Passing Threshold")
    passing_score = st.slider(
        "Set Passing Score",
        min_value=0,
        max_value=100,
        value=70,
        step=1,
        help="Set the minimum passing score threshold"
    )
    
    st.divider()
    
    
    

    if st.button("💾 Generate Config File", type="primary"):
        try:
            config_content = write_config_file(provider, model, passing_score)
            st.success("✅ Configuration Updated successfully!")
            
            # # Show file location
            # current_dir = os.getcwd()
            # st.info(f"📂 File saved at: `{current_dir}/modelconfig.py`")
            
        except Exception as e:
            st.error(f"❌ Error creating config file: {str(e)}")


if __name__ == "__main__":
    main()