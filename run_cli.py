import asyncio
import sys
import threading, time, models, os
from ansio import application_keypad, mouse_input, raw_input
from ansio.input import InputEvent, get_input_event
from agent import AgentContext
from python.helpers.print_style import PrintStyle
from python.helpers.files import read_file
from python.helpers import files
import python.helpers.timed_input as timed_input
from initialize import initialize


context: AgentContext = None # type: ignore
input_lock = threading.Lock()
<<<<<<< HEAD:main.py
os.chdir(files.get_abs_path("./work_dir")) #change CWD to work_dir


def initialize():
    
    # main chat model used by agents (smarter, more accurate)
    chat_llm = models.get_openai_chat(temperature=0)

    # utility model used for helper functions (cheaper, faster)
    utility_llm = models.get_openai_chat(temperature=0)
    
    # embedding model used for memory
    embedding_llm = models.get_embedding_openai()

    # agent configuration
    config = AgentConfig(
        chat_model = chat_llm,
        utility_model = utility_llm,
        embeddings_model = embedding_llm,
        auto_memory_count = 0,
        code_exec_docker_enabled = True,
        code_exec_ssh_enabled = True,
    )
    
    # create the first agent
    agent0 = Agent(number=0, config=config)

    return agent0


# Main conversation loop
def chat(agent: Agent, user_input: str):
    # send message to agent
    assistant_response = agent.message_loop(user_input)
    
    return assistant_response

=======


# Main conversation loop
async def chat(context: AgentContext):
    
    # start the conversation loop  
    while True:
        # ask user for message
        with input_lock:
            timeout = context.agent0.get_data("timeout") # how long the agent is willing to wait
            if not timeout: # if agent wants to wait for user input forever
                PrintStyle(background_color="#6C3483", font_color="white", bold=True, padding=True).print(f"User message ('e' to leave):")        
                if sys.platform != "win32": import readline # this fixes arrow keys in terminal
                user_input = input("> ")
                PrintStyle(font_color="white", padding=False, log_only=True).print(f"> {user_input}") 
                
            else: # otherwise wait for user input with a timeout
                PrintStyle(background_color="#6C3483", font_color="white", bold=True, padding=True).print(f"User message ({timeout}s timeout, 'w' to wait, 'e' to leave):")        
                if sys.platform != "win32": import readline # this fixes arrow keys in terminal
                # user_input = timed_input("> ", timeout=timeout)
                user_input = timeout_input("> ", timeout=timeout)
                                    
                if not user_input:
                    user_input = context.agent0.read_prompt("fw.msg_timeout.md")
                    PrintStyle(font_color="white", padding=False).stream(f"{user_input}")        
                else:
                    user_input = user_input.strip()
                    if user_input.lower()=="w": # the user needs more time
                        user_input = input("> ").strip()
                    PrintStyle(font_color="white", padding=False, log_only=True).print(f"> {user_input}")        
                    
                    

        # exit the conversation when the user types 'exit'
        if user_input.lower() == 'e': break

        # send message to agent0, 
        assistant_response = await context.communicate(user_input).result()
        
        # print agent0 response
        PrintStyle(font_color="white",background_color="#1D8348", bold=True, padding=True).print(f"{context.agent0.agent_name}: reponse:")        
        PrintStyle(font_color="white").print(f"{assistant_response}")        
                        
>>>>>>> 2aedd5fd9d2290f857dfa23f2b5ed656b7e8fe13:run_cli.py

# User intervention during agent streaming
def intervention():
    if context.streaming_agent and not context.paused:
        context.paused = True # stop agent streaming
        PrintStyle(background_color="#6C3483", font_color="white", bold=True, padding=True).print(f"User intervention ('e' to leave, empty to continue):")        

        if sys.platform != "win32": import readline # this fixes arrow keys in terminal
        user_input = input("> ").strip()
        PrintStyle(font_color="white", padding=False, log_only=True).print(f"> {user_input}")        
        
        if user_input.lower() == 'e': os._exit(0) # exit the conversation when the user types 'exit'
<<<<<<< HEAD:main.py
        if user_input: Agent.streaming_agent.intervention_message = user_input # set intervention message if non-empty
        Agent.paused = False # continue agent streaming 


# Capture keyboard input to trigger user intervention
def capture_keys():
    global input_lock
    intervent = False            
    while True:
        if intervent: intervention()
        intervent = False
        time.sleep(0.1)
        
        if Agent.streaming_agent:
            with input_lock, raw_input, application_keypad:
                event: InputEvent | None = get_input_event(timeout=0.1)
                if event and (event.shortcut.isalpha() or event.shortcut.isspace()):
                    intervent = True
                    continue
=======
        if user_input: context.streaming_agent.intervention_message = user_input # set intervention message if non-empty
        context.paused = False # continue agent streaming 
    

# Capture keyboard input to trigger user intervention
def capture_keys():
        global input_lock
        intervent=False            
        while True:
            if intervent: intervention()
            intervent = False
            time.sleep(0.1)
            
            if context.streaming_agent:
                # with raw_input, application_keypad, mouse_input:
                with input_lock, raw_input, application_keypad:
                    event: InputEvent | None = get_input_event(timeout=0.1)
                    if event and (event.shortcut.isalpha() or event.shortcut.isspace()):
                        intervent=True
                        continue
>>>>>>> 2aedd5fd9d2290f857dfa23f2b5ed656b7e8fe13:run_cli.py

# User input with timeout
def timeout_input(prompt, timeout=10):
    return timed_input.timeout_input(prompt=prompt, timeout=timeout)

if __name__ == "__main__":
    print("Initializing framework...")

    # initialize context
    config = initialize()
    context = AgentContext(config)

    # Start the key capture thread for user intervention during agent streaming
    threading.Thread(target=capture_keys, daemon=True).start()

<<<<<<< HEAD
<<<<<<< HEAD:main.py
    # Initialize the agent
    agent = initialize()

    # Start the chat loop
    while True:
        user_input = input("User: ")
        if user_input.lower() == 'e':
            break
        response = chat(agent, user_input)
        print(f"Agent: {response}")
=======
    # initialize and start the chat
    config = initialize()
    context = AgentContext(config)
    asyncio.run(chat(context))
>>>>>>> 2aedd5fd9d2290f857dfa23f2b5ed656b7e8fe13:run_cli.py
=======
    #start the chat
    asyncio.run(chat(context))
>>>>>>> 4066a24c7fde89e211f547b81231b8a6d23919e1
