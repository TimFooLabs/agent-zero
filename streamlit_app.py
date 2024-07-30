import streamlit as st
import main
from agent import Agent, AgentConfig
import models
from python.helpers import files
import os
import uuid
import json
from datetime import datetime
import re

# Set the working directory
os.chdir(files.get_abs_path("./work_dir"))

# Initialize session state
if 'current_conversation_id' not in st.session_state:
    st.session_state.current_conversation_id = None
if 'total_tokens' not in st.session_state:
    st.session_state.total_tokens = 0
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0
if 'conversations' not in st.session_state:
    st.session_state.conversations = []
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

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

def create_new_conversation():
    conversation_id = str(uuid.uuid4())
    st.session_state.current_conversation_id = conversation_id
    st.session_state.agent = initialize_agent()
    st.session_state.chat_history = []
    st.session_state.total_tokens = 0
    st.session_state.total_cost = 0.0
    
    # Generate a short name for the conversation
    short_name = generate_short_name()
    
    # Add new conversation to the list
    new_conversation = {
        'id': conversation_id,
        'name': short_name,
        'timestamp': datetime.now().isoformat()
    }
    st.session_state.conversations.append(new_conversation)
    save_conversations()

def generate_short_name():
    if st.session_state.conversations:
        return f"Conversation {len(st.session_state.conversations) + 1}"
    return "New Conversation"

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

def save_current_conversation():
    if st.session_state.current_conversation_id:
        conversation_data = {
            'id': st.session_state.current_conversation_id,
            'chat_history': st.session_state.chat_history,
            'total_tokens': st.session_state.total_tokens,
            'total_cost': st.session_state.total_cost
        }
        file_name = f"conversation_{st.session_state.current_conversation_id}.json"
        with open(os.path.join(conversations_dir, file_name), "w") as f:
            json.dump(conversation_data, f)

def load_conversation(conversation_id):
    file_name = f"conversation_{conversation_id}.json"
    file_path = os.path.join(conversations_dir, file_name)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            conversation_data = json.load(f)
        st.session_state.chat_history = conversation_data['chat_history']
        st.session_state.current_conversation_id = conversation_id
        st.session_state.total_tokens = conversation_data['total_tokens']
        st.session_state.total_cost = conversation_data['total_cost']
        st.session_state.agent = initialize_agent()
    else:
        st.error(f"Conversation file not found: {file_name}")

def main():
    st.title("Agent Zero Streamlit Interface")

    # Load existing conversations
    load_conversations()

    # Create a new conversation if there are no conversations
    if not st.session_state.conversations:
        create_new_conversation()

    # Conversation management in the sidebar
    with st.sidebar:
        st.header("Conversation Management")
        
        # Button to create a new conversation
        if st.button("New Conversation"):
            create_new_conversation()
        
        # Dropdown to select existing conversations
        conversation_options = [conv['name'] for conv in st.session_state.conversations]
        
        # Find the index of the current conversation, or default to 0
        current_index = 0
        if st.session_state.current_conversation_id:
            for i, conv in enumerate(st.session_state.conversations):
                if conv['id'] == st.session_state.current_conversation_id:
                    current_index = i
                    break
        
        selected_conversation = st.selectbox(
            "Select a conversation",
            conversation_options,
            index=current_index
        )
        
        selected_conversation_id = next(conv['id'] for conv in st.session_state.conversations if conv['name'] == selected_conversation)
        
        if selected_conversation_id != st.session_state.current_conversation_id:
            save_current_conversation()
            load_conversation(selected_conversation_id)
            st.experimental_rerun()
        
        # Button to rename the current conversation
        new_name = st.text_input("Rename conversation")
        if st.button("Rename"):
            for conv in st.session_state.conversations:
                if conv['id'] == st.session_state.current_conversation_id:
                    conv['name'] = new_name
                    save_conversations()
                    st.experimental_rerun()

    # Get the current conversation
    agent = st.session_state.agent
    chat_history = st.session_state.chat_history

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

        # Update conversation name if it's the first message
        if len(chat_history) == 1:
            update_conversation_name(user_input)

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

def update_conversation_name(user_input):
    # Generate a short name based on the first user message
    words = re.findall(r'\w+', user_input)
    short_name = ' '.join(words[:3]) + '...' if len(words) > 3 else user_input
    
    # Update the conversation name
    for conv in st.session_state.conversations:
        if conv['id'] == st.session_state.current_conversation_id:
            conv['name'] = short_name
            save_conversations()
            break

if __name__ == "__main__":
    main()
