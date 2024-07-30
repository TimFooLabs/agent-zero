import streamlit as st
import main
from agent import Agent, AgentConfig
import models
from python.helpers import files
import os
import json
from datetime import datetime

# Set the working directory
os.chdir(files.get_abs_path("./work_dir"))

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

def save_conversation(chat_history, total_tokens, total_cost):
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    conversation_data = {
        'timestamp': timestamp,
        'chat_history': chat_history,
        'total_tokens': total_tokens,
        'total_cost': total_cost
    }
    file_name = f"conversation_{timestamp}.json"
    with open(os.path.join(conversations_dir, file_name), "w") as f:
        json.dump(conversation_data, f)

def load_conversations():
    conversations = []
    for file_name in os.listdir(conversations_dir):
        if file_name.endswith('.json'):
            with open(os.path.join(conversations_dir, file_name), "r") as f:
                try:
                    conversation_data = json.load(f)
                    if 'timestamp' not in conversation_data:
                        print(f"Warning: 'timestamp' key not found in {file_name}")
                        print(f"File contents: {conversation_data}")
                        continue
                    conversations.append(conversation_data)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {file_name}")
    if not conversations:
        print("No valid conversations found.")
        return []
    return sorted(conversations, key=lambda x: x['timestamp'], reverse=True)

def show_settings():
    st.sidebar.header("Settings")
    
    with st.sidebar.expander("Model Settings"):
        st.text(f"Chat Model: {st.session_state.agent.config.chat_model.__class__.__name__}")
        st.text(f"Utility Model: {st.session_state.agent.config.utility_model.__class__.__name__}")
        st.text(f"Embeddings Model: {st.session_state.agent.config.embeddings_model.__class__.__name__}")
    
    with st.sidebar.expander("Memory Settings"):
        st.session_state.agent.config.auto_memory_count = st.number_input(
            "Number of automatic memory retrievals",
            value=st.session_state.agent.config.auto_memory_count,
            min_value=0,
            help="Number of automatic memory retrievals. 0 means no automatic retrieval."
        )
        
        st.session_state.agent.config.auto_memory_skip = st.number_input(
            "Interactions to skip before next retrieval",
            value=st.session_state.agent.config.auto_memory_skip,
            min_value=0,
            help="Number of interactions to skip before next automatic memory retrieval."
        )
    
    with st.sidebar.expander("Response Settings"):
        st.session_state.agent.config.response_timeout_seconds = st.number_input(
            "Maximum response time (seconds)",
            value=st.session_state.agent.config.response_timeout_seconds,
            min_value=1,
            help="Maximum time allowed for the agent to generate a response before timing out."
        )
    
    with st.sidebar.expander("Code Execution Settings"):
        st.text(f"Docker Enabled: {st.session_state.agent.config.code_exec_docker_enabled}")
        st.text(f"SSH Enabled: {st.session_state.agent.config.code_exec_ssh_enabled}")
    
    with st.sidebar.expander("Rate Limiting"):
        st.text(f"Requests per {st.session_state.agent.config.rate_limit_seconds} seconds: {st.session_state.agent.config.rate_limit_requests}")
        st.text(f"Input Tokens: {st.session_state.agent.config.rate_limit_input_tokens}")
        st.text(f"Output Tokens: {st.session_state.agent.config.rate_limit_output_tokens}")

def main():
    st.title("Agent Zero Streamlit Interface")

    # Initialize session state
    if 'agent' not in st.session_state:
        st.session_state.agent = initialize_agent()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'total_tokens' not in st.session_state:
        st.session_state.total_tokens = 0
    if 'total_cost' not in st.session_state:
        st.session_state.total_cost = 0.0
    if 'current_chat' not in st.session_state:
        st.session_state.current_chat = "New Chat"

    # Sidebar for settings and chats
    with st.sidebar:
        st.title("Agent Zero Streamlit UI")
        
        # Settings button
        if st.button("Settings"):
            st.session_state.show_settings = not st.session_state.get('show_settings', False)
        
        # Show settings if the button was clicked
        if st.session_state.get('show_settings', False):
            show_settings()
        
        st.sidebar.markdown("---")
        
        # Chats section
        st.sidebar.subheader("Chats")
        
        # New chat button
        if st.sidebar.button("New Chat"):
            st.session_state.chat_history = []
            st.session_state.total_tokens = 0
            st.session_state.total_cost = 0.0
            st.session_state.current_chat = "New Chat"
        
        # List of past chats
        chats = load_conversations()
        for chat in chats:
            if st.sidebar.button(f"Chat {chat['timestamp']}"):
                st.session_state.chat_history = chat['chat_history']
                st.session_state.total_tokens = chat['total_tokens']
                st.session_state.total_cost = chat['total_cost']
                st.session_state.current_chat = f"Chat {chat['timestamp']}"

    # Display current chat name
    st.subheader(st.session_state.current_chat)

    # Display chat history
    for message in st.session_state.chat_history:
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
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                response, tokens, cost = st.session_state.agent.message_loop(user_input)
                st.write(response)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "tokens": tokens,
                    "cost": cost,
                    "model": st.session_state.agent.config.chat_model.__class__.__name__
                })
                st.caption(f"Model: {st.session_state.agent.config.chat_model.__class__.__name__} | Tokens: {tokens} | Cost: ${cost:.4f}")
                
                # Update session totals
                st.session_state.total_tokens += tokens
                st.session_state.total_cost += cost
                
                # Save the conversation
                save_conversation(st.session_state.chat_history, st.session_state.total_tokens, st.session_state.total_cost)

    # Add a button to export all conversations
    if st.sidebar.button("Export All Conversations"):
        conversations = load_conversations()
        st.sidebar.download_button(
            label="Download Conversations",
            data=json.dumps(conversations, indent=2),
            file_name="all_conversations.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()
