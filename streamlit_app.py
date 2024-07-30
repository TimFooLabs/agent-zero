import streamlit as st
import main
from agent import Agent, AgentConfig
import models
from python.helpers import files
import os
import uuid
import json

# Set the working directory
os.chdir(files.get_abs_path("./work_dir"))

# Initialize session state
if 'sessions' not in st.session_state:
    st.session_state.sessions = {}
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'total_tokens' not in st.session_state:
    st.session_state.total_tokens = 0
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0

def initialize_agent():
    config = AgentConfig(
        chat_model=models.get_openai_chat(temperature=0),
        utility_model=models.get_openai_chat(temperature=0),
        embeddings_model=models.get_embedding_openai(),
        code_exec_docker_enabled=True,
        code_exec_ssh_enabled=True,
    )
    return Agent(number=0, config=config)

def create_new_session():
    session_id = str(uuid.uuid4())
    st.session_state.sessions[session_id] = {
        'agent': initialize_agent(),
        'chat_history': []
    }
    st.session_state.current_session_id = session_id
    st.session_state.total_tokens = 0
    st.session_state.total_cost = 0.0

def main():
    st.title("Agent Zero Streamlit Interface")

    # Create a new session if there are no sessions
    if not st.session_state.sessions:
        create_new_session()

    # Session management in the sidebar
    with st.sidebar:
        st.header("Session Management")
        
        # Button to create a new session
        if st.button("New Session"):
            create_new_session()
        
        # Dropdown to select existing sessions
        session_options = list(st.session_state.sessions.keys())
        selected_session = st.selectbox(
            "Select a session",
            session_options,
            index=session_options.index(st.session_state.current_session_id) if st.session_state.current_session_id else 0
        )
        
        if selected_session != st.session_state.current_session_id:
            st.session_state.current_session_id = selected_session
            st.experimental_rerun()

    # Get the current session
    current_session = st.session_state.sessions[st.session_state.current_session_id]
    agent = current_session['agent']
    chat_history = current_session['chat_history']

    # Sidebar for settings and configurations
    with st.sidebar:
        st.header("Settings and Configurations")
        
        st.subheader("Model Settings")
        st.text(f"Chat Model: {agent.config.chat_model.__class__.__name__}")
        st.text(f"Utility Model: {agent.config.utility_model.__class__.__name__}")
        st.text(f"Embeddings Model: {agent.config.embeddings_model.__class__.__name__}")
        
        st.subheader("Memory Settings")
        agent.config.auto_memory_count = st.number_input(
            "Number of automatic memory retrievals (0 or greater)",
            value=agent.config.auto_memory_count,
            min_value=0,
            help="Determines the number of automatic memory retrievals the agent performs. If set to 0, no automatic memory retrieval occurs."
        )
        
        agent.config.auto_memory_skip = st.number_input(
            "Interactions to skip before next memory retrieval",
            value=agent.config.auto_memory_skip,
            min_value=0,
            help="Determines how many interactions to skip before performing another automatic memory retrieval."
        )
        
        st.subheader("Response Settings")
        agent.config.response_timeout_seconds = st.number_input(
            "Maximum response time (seconds)",
            value=agent.config.response_timeout_seconds,
            min_value=1,
            help="Sets the maximum time allowed for the agent to generate a response before timing out."
        )
        
        st.subheader("Code Execution Settings")
        st.text(f"Docker Enabled: {agent.config.code_exec_docker_enabled}")
        st.text(f"SSH Enabled: {agent.config.code_exec_ssh_enabled}")
        
        st.subheader("Rate Limiting")
        st.text(f"Requests per {agent.config.rate_limit_seconds} seconds: {agent.config.rate_limit_requests}")
        st.text(f"Input Tokens: {agent.config.rate_limit_input_tokens}")
        st.text(f"Output Tokens: {agent.config.rate_limit_output_tokens}")

    # Display chat history
    for message in chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "tokens" in message and "cost" in message:
                st.caption(f"Tokens: {message['tokens']} | Cost: ${message['cost']:.4f}")

    # Display total token usage and cost for the session
    st.sidebar.markdown("---")
    st.sidebar.subheader("Session Statistics")
    st.sidebar.text(f"Total Tokens: {st.session_state.total_tokens}")
    st.sidebar.text(f"Total Cost: ${st.session_state.total_cost:.4f}")

    # Chat input
    user_input = st.chat_input("Type your message here...")
    if user_input:
        # Add user message to chat history
        chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                response, tokens, cost = agent.message_loop(user_input)
                st.write(response)
                chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "tokens": tokens,
                    "cost": cost
                })
                st.caption(f"Tokens: {tokens} | Cost: ${cost:.4f}")
                
                # Update session totals
                st.session_state.total_tokens += tokens
                st.session_state.total_cost += cost
                
                # Force a rerun to update the sidebar statistics
                st.rerun()

if __name__ == "__main__":
    main()
