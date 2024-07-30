import streamlit as st
import main
from agent import Agent, AgentConfig
import models
from python.helpers import files
import os

# Set the working directory
os.chdir(files.get_abs_path("./work_dir"))

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
    st.session_state.chat_history = []

def initialize_agent():
    config = AgentConfig(
        chat_model=models.get_openai_chat(temperature=0),
        utility_model=models.get_openai_chat(temperature=0),
        embeddings_model=models.get_embedding_openai(),
        code_exec_docker_enabled=True,
        code_exec_ssh_enabled=True,
    )
    st.session_state.agent = Agent(number=0, config=config)

def main():
    st.title("Agent Zero Streamlit Interface")

    # Initialize agent if not already done
    if st.session_state.agent is None:
        initialize_agent()

    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        st.session_state.agent.config.auto_memory_count = st.number_input("Auto Memory Count", value=st.session_state.agent.config.auto_memory_count, min_value=0)
        st.session_state.agent.config.auto_memory_skip = st.number_input("Auto Memory Skip", value=st.session_state.agent.config.auto_memory_skip, min_value=0)
        st.session_state.agent.config.response_timeout_seconds = st.number_input("Response Timeout (seconds)", value=st.session_state.agent.config.response_timeout_seconds, min_value=1)

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    user_input = st.chat_input("Type your message here...")
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                response = st.session_state.agent.message_loop(user_input)
                st.write(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
