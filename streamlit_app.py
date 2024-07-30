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
                conversation_data = json.load(f)
                conversations.append(conversation_data)
    return sorted(conversations, key=lambda x: x['timestamp'], reverse=True)

def main():
    st.title("Agent Zero Streamlit Interface")

    agent = initialize_agent()
    chat_history = []
    total_tokens = 0
    total_cost = 0.0

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
    st.sidebar.text(f"Total Tokens: {total_tokens}")
    st.sidebar.text(f"Total Cost: ${total_cost:.4f}")

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
                total_tokens += tokens
                total_cost += cost
                
                # Save the conversation
                save_conversation(chat_history, total_tokens, total_cost)
                
                # Force a rerun to update the sidebar statistics
                st.rerun()

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
