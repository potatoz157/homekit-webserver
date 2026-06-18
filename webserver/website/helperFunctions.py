import json, os, cv2, mistune, re
from mistune.plugins.math import math
from cv2_enumerate_cameras import enumerate_cameras
from ollama import chat
from datetime import datetime
from flask import jsonify
from databaseFunctions import getAllUserChatNames, getUserChat
from databaseTables import get_engine
from sqlalchemy.orm import Session

# # appends the data to the end of the chatHistory.json. The input argument should be in the format of a json!
# def storeChatData(data, user, chatName):
#     # the first argument, the input data, should be in the form of a json: {"message": data}

#     if not user:
#         user = 'guest'

#     existingContents = getChatContents(user, chatName) # fetch existing chat history (creates the file if needed)
#     existingContents.append(data) # append user input/prompt to chat history (data is already a json object)

#     filePath = 'user-data/' + user + '/' + chatName + '.json'
#     # print("File path to save to is: ", filePath)
#     try: 
#         # open the chat file and write the updated contents to it (replaces everything already inside)
#         f = open(filePath, "w")
#         json.dump(existingContents, f, indent=4)
#         f.close()
#         return jsonify({
#             "status": "sent",
#         }), 200
    
#     except Exception as e:
#         print("Failed to save chat history to JSON: " + str(e))
#         return jsonify({
#             "status": "error",
#             "message": str(e)
#         }), 400
    

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


def getModelNames() -> list[str]:
    import ollama

    # openOllama() # ensure ollama process is running

    list = ollama.list()
    models = []

    
    for modelInfo in list.get('models', []):
        models.append(modelInfo.get('model', []))
    return models

def generateLLMResponse(user_input : str, model : str, context: list) -> tuple[str, str, int]:
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
        Returns a tuple containing the llm reponse and thinking.

        ai_response: str
            the literal response of the LLM
        ai_thinking: str
            the literal thinking of the LLM
    """


    messages = [{
        "role":  "system", "content": "Be concise. Respond in english only unless prompted." # optional, (hard-coded) high-priority instruction
    }]

    if context:
        messages.extend(context) # combine the previous chat history with messages

    # append the user prompt to the messages
    messages.append({
        "role": "user", "content": user_input
    })

    chatResponse = chat(
        model=model,
        messages=messages,
        options={
            'num_ctx':8192
        },
        stream=False
    )


    ai_response = chatResponse.message.content
    ai_thinking = chatResponse.message.thinking
    context_tokens = chatResponse.prompt_eval_count # number of tokens read and evaluated by LLM

    # ensure return value is always a string, even if its empty
    if not ai_thinking:
        ai_thinking = ""

    if not ai_response:
        ai_response = ""

    if not context_tokens:
        context_tokens = -1


    return ai_response, ai_thinking, context_tokens



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


def markdownToHtml(markdownText):
    if not markdownText:
        return ""
    
# 1. Fix Block Math: Convert [ ... ] to $$ ... $$
    # This now allows for any spaces/tabs before the opening bracket and clears them out
    fixed_text = re.sub(r'(?m)^[ \t]*\[\s*([\s\S]*?)\s*\]', r'$$\n\1\n$$', markdownText)
    
    # 2. Fix Inline Math: Convert ( ... ) to $ ... $
    fixed_text = re.sub(r'\(\s*([\s\S]*?)\s*\)', r'$\1$', fixed_text)
    
    # 3. Parse the Markdown safely to HTML
    mardownParser = mistune.create_markdown(plugins=[math])

    # print(fixed_text)
    html_output = mardownParser(fixed_text)

    return html_output




# to keep chat history context, you must fetch all of the previous prompts and resend them
# to the llm as part of your message.
# NOTE: The message sent to the llm is in the form of a json array (or dict in python)
# Ollama uses the 'role' parameter to tell the model who is speaking 
# (i.e. user or assistant = llm)
# a 'system' role also exists which is useful for hard-coding an important instruction
# the system role is not meant to be used dynamically (i.e. user should not be sending
# messages as with the role of system)
# def generateLLMResponse(user : str, user_input : str, model : str, chatName : str):
#     # user_input = value of a json object (equal to a string)
#     # model = value of a json object = string

#     # reconstruct a json object to hold all previous chat context
#     messages = [{
#         "role":  "system", "content": "Be concise. Respond in english only unless prompted." # optional, (hard-coded) high-priority instruction
#     }]

#     # fetch previous chat history and append it to the messages
#     if user:
#         prevContents = getChatContents(user, chatName)
#         if prevContents:
#             for prompt in prevContents:
#                 messages.append({"role": "user", "content": prompt.get('message')})
#                 messages.append({"role": "assistant", "content": prompt.get('response')})
#         # if prevContents:
#         #     messages.extend(prevContents) # this expands the list of messages using the previous chat contents (i.e. [{}, {}] + [{}, {}] = [{}, {}, {}, {}])

#     # add current user prompt/input (should be added LAST so the model sees it 
#     # as the question and not chat history)
#     messages.append({"role": "user", "content": user_input})
#     chatResponse = chat(model=model, messages=messages, options={'num_ctx': 8192})

#     reasoning = chatResponse.message.thinking
#     final_answer = chatResponse.message.content

#     return final_answer, reasoning






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