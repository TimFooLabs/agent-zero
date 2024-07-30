import streamlit as st
import main
from agent import Agent, AgentConfig
import models
from python.helpers import files
import os
import uuid
import json
from datetime import datetime

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
if 'conversations' not in st.session_state:
    st.session_state.conversations = []

# Create conversations directory if it doesn't exist
conversations_dir = files.get_abs_path("conversations")
os.makedirs(conversations_dir, exist_ok=True)

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
    
    # Add new conversation to the list
    new_conversation = {
        'id': session_id,
        'name': f"Conversation {len(st.session_state.conversations) + 1}",
        'timestamp': datetime.now().isoformat()
    }
    st.session_state.conversations.append(new_conversation)
    save_conversations()

def save_conversations():
    conversations_file = os.path.join(conversations_dir, "conversations.json")
    with open(conversations_file, "w") as f:
        json.dump(st.session_state.conversations, f)

def load_conversations():
    conversations_file = os.path.join(conversations_dir, "conversations.json")
    if os.path.exists(conversations_file):
        with open(conversations_file, "r") as f:
            st.session_state.conversations = json.load(f)
    else:
        st.session_state.conversations = []

def save_current_session():
    if st.session_state.current_session_id:
        session = st.session_state.sessions[st.session_state.current_session_id]
        session_data = {
            'id': st.session_state.current_session_id,
            'chat_history': session['chat_history'],
            'total_tokens': st.session_state.total_tokens,
            'total_cost': st.session_state.total_cost
        }
        file_name = f"conversation_{st.session_state.current_session_id}.json"
        with open(os.path.join(conversations_dir, file_name), "w") as f:
            json.dump(session_data, f)

def load_session(session_id):
    file_name = f"conversation_{session_id}.json"
    file_path = os.path.join(conversations_dir, file_name)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            session_data = json.load(f)
        st.session_state.sessions[session_id] = {
            'agent': initialize_agent(),
            'chat_history': session_data['chat_history']
        }
        st.session_state.current_session_id = session_id
        st.session_state.total_tokens = session_data['total_tokens']
        st.session_state.total_cost = session_data['total_cost']
    else:
        st.error(f"Session file not found: {file_name}")

def main():
    st.title("Agent Zero Streamlit Interface")

    # Load existing conversations
    load_conversations()

    # Create a new session if there are no sessions
    if not st.session_state.sessions:
        create_new_session()

    # Session management in the sidebar
    with st.sidebar:
        st.header("Conversation Management")
        
        # Button to create a new conversation
        if st.button("New Conversation"):
            create_new_session()
        
        # Dropdown to select existing conversations
        conversation_options = [conv['name'] for conv in st.session_state.conversations]
        selected_conversation = st.selectbox(
            "Select a conversation",
            conversation_options,
            index=conversation_options.index(next(conv['name'] for conv in st.session_state.conversations if conv['id'] == st.session_state.current_session_id)) if st.session_state.current_session_id else 0
        )
        
        selected_session_id = next(conv['id'] for conv in st.session_state.conversations if conv['name'] == selected_conversation)
        
        if selected_session_id != st.session_state.current_session_id:
            save_current_session()
            load_session(selected_session_id)
            st.experimental_rerun()
        
        # Button to rename the current conversation
        new_name = st.text_input("Rename conversation")
        if st.button("Rename"):
            for conv in st.session_state.conversations:
                if conv['id'] == st.session_state.current_session_id:
                    conv['name'] = new_name
                    save_conversations()
                    st.experimental_rerun()

    # Get the current session
    current_session = st.session_state.sessions[st.session_state.current_session_id]
    agent = current_session['agent']
    chat_history = current_session['chat_history']

    # Sidebar for settings and configurations
    with st.sidebar:
        st.header("Settings and Configurations")
        
        with st.expander("Model Settings"):
            st.text(f"Chat Model: {agent.config.chat_model.__class__.__name__}")
            st.text(f"Utility Model: {agent.config.utility_model.__class__.__name__}")
            st.text(f"Embeddings Model: {agent.config.embeddings_model.__class__.__name__}")
        
        with st.expander("Memory Settings"):
            agent.config.auto_memory_count = st.number_input(
                "Number of automatic memory retrievals",
                value=agent.config.auto_memory_count,
                min_value=0,
                help="Number of automatic memory retrievals. 0 means no automatic retrieval."
            )
            
            agent.config.auto_memory_skip = st.number_input(
                "Interactions to skip before next retrieval",
                value=agent.config.auto_memory_skip,
                min_value=0,
                help="Number of interactions to skip before next automatic memory retrieval."
            )
        
        with st.expander("Response Settings"):
            agent.config.response_timeout_seconds = st.number_input(
                "Maximum response time (seconds)",
                value=agent.config.response_timeout_seconds,
                min_value=1,
                help="Maximum time allowed for the agent to generate a response before timing out."
            )
        
        with st.expander("Code Execution Settings"):
            st.text(f"Docker Enabled: {agent.config.code_exec_docker_enabled}")
            st.text(f"SSH Enabled: {agent.config.code_exec_ssh_enabled}")
        
        with st.expander("Rate Limiting"):
            st.text(f"Requests per {agent.config.rate_limit_seconds} seconds: {agent.config.rate_limit_requests}")
            st.text(f"Input Tokens: {agent.config.rate_limit_input_tokens}")
            st.text(f"Output Tokens: {agent.config.rate_limit_output_tokens}")

    # Display chat history
    for message in chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "tokens" in message and "cost" in message:
                if "model" in message:
                    st.caption(f"Model: {message['model']} | Tokens: {message['tokens']} | Cost: ${message['cost']:.4f}")
                else:
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
                    "cost": cost,
                    "model": agent.config.chat_model.__class__.__name__
                })
                st.caption(f"Model: {agent.config.chat_model.__class__.__name__} | Tokens: {tokens} | Cost: ${cost:.4f}")
                
                # Update session totals
                st.session_state.total_tokens += tokens
                st.session_state.total_cost += cost
                
                # Save the current session
                save_current_session()
                
                # Force a rerun to update the sidebar statistics
                st.rerun()

if __name__ == "__main__":
    main()
