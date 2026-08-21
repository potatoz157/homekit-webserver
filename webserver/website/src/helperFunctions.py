import importlib, inspect
from collections.abc import Generator
from mistune.plugins.math import math
from ollama import chat
from datetime import datetime
from flask import jsonify, session
from databaseFunctions import getAllUserChatNames, getUserChat
from databaseTables import get_engine
from sqlalchemy.orm import Session
from globals import getActiveUsers, getDictLock
# from main import tool_definitions
import toolDefinitions as toolDefinitions # we dynamically call the function based on the tool call of the LLM (using getattr(tools, func_name)) 
from toolDefinitions import ToolDefinitions

# starts ollama process (ollama needs to be open to fetch available model names)
def openOllama():
    import ollama, subprocess
    try: 
        a = ollama.list()
        print("Ollama is running :)")
        # time.sleep(2)
    except:
        print("Ollama is not running. Starting Ollama...")
        # starts ollama by listing available (downloaded) llms
        subprocess.run(["ollama", "ls"], shell=True)
        print("Ollama Started!")

    global tool_definitions
    tool_definitions = ToolDefinitions() # create tool definition object (holds all the tools used by ollama)

def getModelNames() -> list[str]:
    import ollama

    # to disable all models except qwen2.5:14b-instruct, set this to true
    disableList = False


    openOllama() # ensure ollama process is running

    # if the full list is disabled, return the single, hardcoded model
    if (disableList):
        models = ['qwen2.5:14b-instruct']
        return models
    
    # otherwise, dynamically fetch all available models
    list = ollama.list()
    models = []

    for modelInfo in list.get('models', []):
        modelName = modelInfo.get('model', [])
        if 'cloud' not in modelName and 'embed' not in modelName: # do not provide cloud or embed models (implementation does not allow for cloud model use so for -- fix later maybe)
            models.append(modelName)
    return models



# def generateLLMResponse(user_input : str, model : str, context: list) -> tuple[str, str, int]:
def generateLLMResponse(user_input : str, model : str, context: list, user_id : int, agent_mode : bool) -> Generator[dict[str, str | bool | list]]:
    """
    Combines the user input prompt and context then feeds it to the defined model using ollama's python library.

    Parameters
    -----------
        user_input: str
            should be a string with the literal value of the user prompt.
        model: str
            should be a string that exactly matches the available/installed ollama model.
        context: list
            should be a json array that holds all of the past prompts and responses excluding the system prompt.
    
    Returns
    -------
        Returns a json object containing the llm reponse and thinking

        result: dict
            - result.ai_response: str

                the literal response of the LLM
            - result.ai_thinking: str

                the literal thinking of the LLM

    """

    # Define system prompt:
    # For adding skills, add the skill name here, the LLM will use a tool to fetch the associate skill markdown file
    # Add a small descriptor telling the LLM when to use the skill.
    # Inside the markdown file, there should be a list of instructions to tell the LLM how to behave, example:
    # .md file:
        # ---
        # name: short-kebab-case-name
        # description: This skill should be used when ...
        # ---

        # # Workflow
        # Step-by-step instructions for the AI.

        # # Decision Rules
        # What the AI should do in edge cases.

        # # Guardrails
        # Things the AI must avoid at all costs.

        # # Output Requirements
        # Formatting specifics (e.g., Markdown, JSON, specific coding standards).

        # # Verification
        # How to test or double-check the final result.
    # The literal headers can be customized, but be consistend across every skill markdown file.
    # LATER, Automate the system prompt generation by iteratively reading all the available skill files, parsing the yaml frontmatter (delimited by '---') to 
    # fetch the skill names and descriptions so that the system prompt does not need to manually be defined.
    system_prompt = """
        You are an AI assistant with access to specialized skills.

        Available Skills:
        - resume-tailoring: Use this when the user wants to modify or create a resume.
        
        STRICT INSTRUCTION FOLLOW-THROUGH RULES:
        1. MANDATORY TOOL EXECUTION: Whenever a user asks for information, instructions, or details regarding a skill, you MUST execute the `get_skill_details` tool first. Do NOT guess content, tell the user if the tool is not accessible.
        2. RAW OUTPUT: Prioritize raw outputs for inconsistent data. Do NOT summarize, redact, paraphrase, or apologize for any apparent mismatch between the file content and the skill name.
        3. NO EAGER CORRECTION: Do NOT attempt to self correct. Tell the user if tool access is not available or information is missing!
        """ 


    messages = [{
        "role":  "system", "content": system_prompt
    }]


    if context:
        messages.extend(context) # combine the previous chat history with messages


    # append the user prompt to the messages
    if user_input and user_input!="":
        messages.append({
            "role": "user", "content": user_input
        })


    # Later when implementing tool access, pass in the tools as a list of function names. For example:
    # NOTE: Ollama knows how to use the function based on the function description. So you MUST include text that states when to use the function
    # and how to use the function (i.e. what the arguments and the return value(s) are). Enforce argument and return types as well.
    # def get_time():
    #     return current_time()
    # To make this function a tool the LLM can use, you must pass it into the 'tools=' argument for the ollama chat() object:
    # response = chat(
        # ...,
        # tools=[get_time], # 
        # ...
    # )
    
    llm_tools_dict = {}
    if agent_mode:
        llm_tools_dict = tool_definitions.tools
        # llm_tools = list(tool_definitions.tools.values())
        # tools_script = importlib.import_module('tools') # import dynamically
        
        # # for every member in the tools script that is a function:
        # for name, func in inspect.getmembers(tools_script, inspect.isfunction):
        #     # Check if the function was written inside tools.py (and not imported into it)
        #     is_defined_in_tools = func.__module__ == tools_script.__name__

        #     if is_defined_in_tools: # append to the list of llm tools
        #         llm_tools.append(func)
        # # manual/hardcoded tool definitions
        # # llm_tools = [get_time, get_date, add, getDailyMsg, read_pdf, read_url]

    chatResponse = chat(
        model=model,
        messages=messages,
        tools=list(llm_tools_dict.values()),  # llm_tools_dict holds the name-function handle pairs of the available tools.
        options={
            'num_ctx':8192
        },
        stream=True
    )

    ai_response = ""
    ai_thinking = ""
    in_thinking = False

    tool_calls = []

    for chunk in chatResponse:

        # if the interruptChat flag is set to true, break out of the loop and return the full response made up to now
        with getDictLock():
            # user_id = session['user-id'] # this causes an error -- cannot access session inside a generator?
            active_users = getActiveUsers()
            user_data = active_users.get(user_id)
            # if the user data was deleted (by the cleanup thread) or the interruptChat flag is set, break
            if not user_data:
                break
            elif user_data.get('interruptChat'):
                user_data['interruptChat'] = False # reset the flag if the user data exists
                break


        if chunk.message.thinking: # if the current response chunk has thinking
            if not in_thinking:
                in_thinking = True
            ai_thinking += chunk.message.thinking
            yield {
                'ai_response': '',
                'ai_thinking': chunk.message.thinking,
                'in_thinking': in_thinking,
                'done': False
            }
        elif chunk.message.content: # otherwise if the current response chunk has actual response
            if in_thinking:
                in_thinking = False
            ai_response += chunk.message.content
            yield {
                'ai_response': chunk.message.content,
                'ai_thinking': '',
                'in_thinking': in_thinking,
                'done': False
            }
        # check if the chunk contains tool call(s) and add them to the list of tool calls
        if chunk.message.tool_calls:
            tool_calls.extend(chunk.message.tool_calls)

        # the last chunk in the llm response contains the usage metrics/statistics (e.g. token count)
        # if chunk.get('done'):
        #     usageTokens = chunk.eval_count
        #     promptTokens = chunk.prompt_eval_count

    # handle the literal function/tool calls here -- to add more tools, fetch and format the results HERE
    tool_outputs = []
    if tool_calls:
        for call in tool_calls:
            # if call.function.name == 'get_time':
            #     result = get_time(**call.function.arguments)
            # elif call.function.name == 'get_date':
            #     result = get_date(**call.function.arguments)
            # elif call.function.name == 'add':
            #     result = add(**call.function.arguments)
            # elif call.function.name == 'getDailyMsg':
            #     result = getDailyMsg(**call.function.arguments)
            # elif call.function.name == 'read_pdf':
            #     result = read_pdf(**call.function.arguments)
            # elif call.function.name == 'read_url':
            #     result = read_url(**call.function.arguments)
            # else:
            #     result = 'unknown tool'

            # func = getattr(toolDefinitions, call.function.name, None) # this fetches the function handle using its name: tools.function_name, where tools is a python file (tools.py)
            
            # llm_tools holds the function handle. Use llm_tools to get the matching function handle
            func = llm_tools_dict.get(call.function.name, None)
            if func:
                result = func(**call.function.arguments)
            else:
                print(f"ERROR: Tool '{call.function.name}'")
                result = 'unknown tool'

            tool_outputs.append({
                'role': 'tool',
                'tool_name': call.function.name,
                'content': result
            })



    yield {
        'ai_response': ai_response,
        'ai_thinking': ai_thinking,
        'in_thinking': False,
        'tool_calls': tool_calls,
        'tool_outputs': tool_outputs,
        'done': True
    }


# this function should only be called with a valid user (and not a guest account)
def getUserChatHeaders(user):
    """
    For the given user, fetches and lists all of the chat names from the database.

    user: str
        user is the string value of the username
    """


    # go to directory for user data:
    # /user-data/USERNAME/*.json --> all json files here are different chat histories

    # NOTE: if you start the path with a slash, it is treated as an absolute path! Remove the starting slash for relative path!!!!
    # historyPath = 'user-data/' + user
    # existingFiles = os.listdir(historyPath)


    with Session(get_engine()) as sesh:
        return getAllUserChatNames(session=sesh, username=user)


    # chatList = []

    # # for every file inside of the directory, get the filename if the file is not empty
    # for file in existingFiles:
    #     filePath = os.path.join(historyPath, file)
        
    #     # if the current file (name) is actually a file (and not a folder/dir), and its not empty, append it to the list of chats
    #     if os.path.isfile(filePath):
    #         if os.path.getsize(filePath) > 0:
    #             chats.append(file.split(".")[0])

    # return chatList


# fetches the full contents of a specific chat for the given user
def getChatContents(user : str, chatName : str) -> tuple[list, str]:
    
    with Session(get_engine()) as sesh:
        chat = getUserChat(session=sesh, username=user, chatName=chatName)

        if not chat:
            return [], ""
        
        db_messages = chat.messages
        model = chat.model
        chat_contents = []
        
        # for i = 0; i < len(db_message); i+=2
        num_msgs = len(db_messages)
        for i in range(0, num_msgs, 2):
            # the first msg is the user prompt
            user_msg = db_messages[i].contents

            # the second msg is the llm response
            llm_msg = None
            if i + 1 < num_msgs:
                llm_msg = db_messages[i+1].contents
            
            chat_contents.append({
                "message": user_msg,
                "response": llm_msg,
                # "model_thinking": None,
                # "model": model
            })
            
        return chat_contents, model


def generateChatName(chatName: str, model: str) -> str: 

    # the format of the resulting chat name will be:
    # 'modelname-YYYY-MM-DD-HH-MM-SS'
    # so model name followed by the date followed by the 

    model = model.replace(':', '-') # windows does not allow colons in file names
    model = model.replace('.', '-') # the file reading breaks if another period exists, so replace it with dashes

    # Generate current date and time in the format 'YYYY-MM-DD-HH-MM-SS' 
    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') 
    # Format the resulting chat name 
    chatName = f"{model}--{timestamp}" 
    return chatName 


# def markdownToHtml(markdownText):
#     if not markdownText:
#         return ""
    
# # 1. Fix Block Math: Convert [ ... ] to $$ ... $$
#     # This now allows for any spaces/tabs before the opening bracket and clears them out
#     fixed_text = re.sub(r'(?m)^[ \t]*\[\s*([\s\S]*?)\s*\]', r'$$\n\1\n$$', markdownText)
    
#     # 2. Fix Inline Math: Convert ( ... ) to $ ... $
#     fixed_text = re.sub(r'\(\s*([\s\S]*?)\s*\)', r'$\1$', fixed_text)
    
#     # 3. Parse the Markdown safely to HTML
#     mardownParser = mistune.create_markdown(plugins=[math])

#     # print(fixed_text)
#     html_output = mardownParser(fixed_text)

#     return html_output


# def generateLLMResponse(user_input : str, model : str, context: list) -> tuple[str, str, int]:
#     """
#     Combines the user input prompt and context then feeds it to the defined model using ollama's python library.

#     Parameters
#     -----------
#         user_input: str
#             should be a string with the literal value of the user prompt.
#         model: str
#             should be a string that exactly matches the available/installed ollama model.
#         context: list
#             should be a json array that holds all of the past prompts and responses excluding the system prompt.
    
#     Returns
#     -------
#         Returns a tuple containing the llm reponse and thinking.

#         ai_response: str
#             the literal response of the LLM
#         ai_thinking: str
#             the literal thinking of the LLM
#     """


#     messages = [{
#         "role":  "system", "content": "Be concise. Respond in english only unless prompted." # optional, (hard-coded) high-priority instruction
#     }]

#     if context:
#         messages.extend(context) # combine the previous chat history with messages

#     # append the user prompt to the messages
#     messages.append({
#         "role": "user", "content": user_input
#     })

#     chatResponse = chat(
#         model=model,
#         messages=messages,
#         options={
#             'num_ctx':8192
#         },
#         stream=False
#     )


#     ai_response = chatResponse.message.content
#     ai_thinking = chatResponse.message.thinking
#     context_tokens = chatResponse.prompt_eval_count # number of tokens read and evaluated by LLM

#     # ensure return value is always a string, even if its empty
#     if not ai_thinking:
#         ai_thinking = ""

#     if not ai_response:
#         ai_response = ""

#     if not context_tokens:
#         context_tokens = -1


#     return ai_response, ai_thinking, context_tokens




# def generateFrames(camera):

#     while camera.isOpened():
#         success, frame = camera.read()
#         if not success:
#             print('failed to read frame')
#             break
#         else:
#             ret, buffer = cv2.imencode('.jpg', frame)
#             frame_bytes = buffer.tobytes()

#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            

# def getCameraList():
#     cameraObjects = enumerate_cameras(cv2.CAP_DSHOW)

#     if (cameraObjects is None or len(cameraObjects) == 0):
#         print("Error, no connected cameras!")
#         return None
    
#     return cameraObjects


# def openCamera(index):
#     cameraObjects = getCameraList()

#     # this error is already displayed in the terminal from the previous function (getCameraList())
#     if (cameraObjects is None):
#         return

#     selectedCamera = cameraObjects[index]
#     cap = cv2.VideoCapture(selectedCamera.index, cv2.CAP_DSHOW)

#     if not cap.isOpened:
#         print("Camera failed to open!")
#         return None
        
#     return cap