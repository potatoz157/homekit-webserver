import json, os, cv2
from cv2_enumerate_cameras import enumerate_cameras
from ollama import chat

# appends the data to the end of the chatHistory.json. The input argument should be in the format of a json!
def storeChatData(data, user):
    # the first argument, the input data, should be in the form of a json: {"message": data}
    from flask import jsonify

    chat_count = 0
    filePath = 'user-data/guest/chatHistory.json'

    # check for actual user (not guest--guest account has user=None)
    if (user is not None):
        filePath = 'user-data/' + user + '/chatHistory' + str(chat_count) + ".json"
    
    # check if the folder for the data exists
    folder = os.path.dirname(filePath)
    if not os.path.exists(folder):
        os.mkdir(folder)

    try:
        # if the file exits, read and save its contents
        if os.path.exists(filePath):
            f = open(filePath, "r")
            # when the contents are read, the result should be of type list
            # when the file does not exist, we create an empty list and fill it with json objects, so the json should ALWAYS hold a list of json objects
            try: 
                existingContents = json.load(f) 
                # if not isinstance(existingContents, list):
                #     existingContents = []
            except Exception as e:
                print("Error reading stored chat history: " + str(e))
                existingContents = []
            f.close()
        else: # otherwise, say its contents are empty
            existingContents = [] # if the file does not exist, we will populate it with a list (of json objects--the message data)

        # append new data to the end of the existing data
        # existingContents = [existingContents, data]
        existingContents.append(data)

        f = open(filePath, "w")
        json.dump(existingContents, f, indent=4)
        f.close()
        return jsonify({
            "status": "sent",
        }), 200
    
    except Exception as e:
        print("Failed to save chat history to JSON")
        print(str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    

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

    openOllama() # ensure ollama process is running

    list = ollama.list()
    models = []

    
    for modelInfo in list.get('models', []):
        models.append(modelInfo.get('model', []))
    return models


def generateLLMResponse(user_input : str, model : str):
    # user_input = value of a json object (equal to a string)
    # model = value of a json object = string

    # to keep chat history context, you must fetch all of the previous prompts and resend them
    # to the llm as part of your message.
    # NOTE: The message sent to the llm is in the form of a json array (or dict in python)
    # Ollama uses the 'role' parameter to tell the model who is speaking 
    # (i.e. user or assistant = llm)
    # a 'system' role also exists which is useful for hard-coding an important instruction
    # the system role is not meant to be used dynamically (i.e. user should not be sending
    # messages as with the role of system)

    # reconstruct a json object to hold all previous chat context
    messages = [{
        "role":  "system", "content": "Be concise." # optional, (hard-coded) high-priority instruction
    }]


    # fetch previous chat history and append it to the messages




    # add current user prompt/input (should be added LAST so the model sees it 
    # as the question and not chat history)
    messages.append({"role": "user", "content": user_input})
    chatResponse = chat(model=model, messages=messages, options={'num_ctx': 8192})

    reasoning = chatResponse.message.thinking
    final_answer = chatResponse.message.content

    # chatResponse = generate(model, messages)
    # chat_thinking = chatResponse.thinking
    # print("LLM THINKING: ", chatResponse.thinking)
    # print("LLM RESPONSE: ", chatResponse.response)


    # return chatResponse.response, chatResponse.thinking

    return final_answer, reasoning




def getUserChatHistory(user):
    print("triggered get user data for: ", user)


    # go to directory for user data:
    # /user-data/USERNAME/*.json --> all json files here are different chat histories

    # for every json file inside of the directory, get the filename, and file contents


    # the history should have the format of a json:
    # basically, one json object holding keys, chat0, chat1, chat2, ...(lets call it chat_i)
    # the value of each chat_i object is a json array that holds the user message/prompt, llm thoughts, llm response and model name 
    
    # {
    #     "chat0": [
    #         {
    #             "message": "message contents",
    #             "response": "llm response",
    #             "model_thinking": "llm thinking response",
    #             "model": "model name"
    #         },
    #                     {
    #             "message": "message contents",
    #             "response": "llm response",
    #             "model_thinking": "llm thinking response",
    #             "model": "model name"
    #         }
    #     ],
    #     "chat1": [
    #         # repeat same pattern for all chats
    #     ]
    # }






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