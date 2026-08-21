from flask import Blueprint, request, session, jsonify, Response
from helperFunctions import getModelNames, generateLLMResponse, getUserChatHeaders, getChatContents, generateChatName
from databaseFunctions import getUser, getUserChat, addUserChat, addFileToChat, addAllFileEmbeddings
from databaseTables import get_engine, Message, Chat
from sqlalchemy.orm import Session
from chatbot import generateUserId
from globals import getActiveUsers, getDictLock, addUserToGlobals
import json, time
from rag import CustomEmbedder, chunkifyDoc

# all URLS inside of chat_bp will automatically have their route start with /api/ because of the 3rd argument
# api_bp = Blueprint('api', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api/')


# this variable will hold each users' ID (as the key) and a json object as the value
# the JSON object value will contain various global variables
    # for now, the json object will only have a flag to indicate whether or not to interrupt the chat response stream
# Example:
# users = {
#     'user1_uuid4': {
#         interruptStream: False,
#         ...
#     },
#     'user2_uuid4': {
#         interruptStream: False,
#         ...
#     },
#     ...
# }



@api_bp.post('/user/chat/inputs/')
def handleUserInputPrompt():
    # data should have the form of a json where:
    # {
    #     "message": "user input/prompt message",
    #     "model": "model name",
    #     "chatname": 'chat name here"
    # }

    data = request.get_json()
    user_message = data.get('message')
    context = data.get('context')   # context needs to be in the format of a json array!
    chatName = data.get('chatname')
    model = data.get('model')
    allowAgent = data.get('allow_agent') # if this is true, then tools will be fed into the model, otherwise, the model will not have access to tools

    chat_id = None # track the chat ID across different sessions

    # logged in chat response behavior
    if 'username' in session:
        if chatName == "newchat":
            chatName = generateChatName(chatName=chatName, model=model)


        # chat = None
        username = session.get('username')
        assert username
        with Session(get_engine()) as sesh:
            chat = getUserChat(session=sesh, username=username, chatName=chatName)
            sesh.commit()

        # if the chat was found, append the user input to the chat
        if chat:
            status_msg = "success:existing-chat"
            with Session(get_engine()) as sesh:
                sesh.add(chat)
                chat.messages.append(Message(role="user", contents=user_message))
                sesh.commit()
                chat_id = chat.ID
            
        # if no chat was found, create a new chat and append the user input to the chat
        else:
            with Session(get_engine()) as sesh:
                # chatName = generateChatName(chatName=chatName, model=model)
                chat_added, new_chat = addUserChat(session=sesh, username=username, chatName=chatName, model=model)
                if (chat_added and new_chat): # if a new chat was successfully made, save the user input prompt to the chat's messages
                    new_chat.messages.append(Message(role="user", contents=user_message))
                    chat_id = new_chat.ID
                    status_msg = "success:new-chat-created"
                else:
                    # print("Error: failed to create and add a new chat to the database...")
                    status_msg = "success:failed-to-save-to-chat"
                sesh.commit()

                
        # ai_response, ai_thinking, _ = generateLLMResponse(user_input=user_message, model=model, context=context)
        # if chat: # if we made or located a chat previously, add the LLM output to the chat's messages
        #     chat.messages.append(Message(role="assistant", contents=ai_response))
    else:
        status_msg = "success:guest"


    def stream_response(user_id):
        generator = generateLLMResponse(user_input=user_message, model=model, context=context, user_id=user_id, agent_mode=allowAgent)

        final_response = ""
        final_thinking = ""
        tool_content = ""

        # send the initial response back to frontend so that the frontend has the new chat name and status before waiting for LLM stream
        init_payload = {
            "status": status_msg,
            "chatname": chatName,
            "is_initial": True,
            "done": False
        }

        yield f"data: {json.dumps(init_payload)}\n\n"

        lastChunk = None
        for data_chunk in generator:
            # Format and stream the current chunk directly to the frontend
            lastChunk = data_chunk.copy() # save a copy so that we can access the LAST chunk outputs

            # only send the data back to the frontend if the chunk does not contain a tool call -- later see if we can disable 
            # streaming to frontend entirely (for trip 1) when a tool call is made rather than relying on a random intermediate chunk
            if not allowAgent or not data_chunk.get('tool_calls'): # if tool calls are not allowed or the current chunk does not have any tool calls, send the current LLM response chunk to the user 
                format_data_chunk = {
                    'ai_response': data_chunk.get('ai_response'),
                    'ai_thinking': data_chunk.get('ai_thinking'),
                    'in_thinking': data_chunk.get('in_thinking'),
                    'done': data_chunk.get('done')
                }
                yield f"data: {json.dumps(format_data_chunk)}\n\n"


            # Capture the aggregate results for database storage
            if not data_chunk.get('done'):
                if data_chunk.get('ai_response'):
                    assert isinstance(data_chunk['ai_response'], str)
                    final_response += data_chunk['ai_response']
                if data_chunk.get('ai_thinking'):
                    assert isinstance(data_chunk['ai_thinking'], str)
                    final_thinking += data_chunk['ai_thinking']



        # append the user input to the context history prior to appending the LLM tool call decision
        context.append({"role": "user", "content": user_message})
        
        # if the last chunk's tool_calls attribute contains anything, assemble the tool_call message and generate another LLM response using the tool outputs
        assert lastChunk
        if allowAgent and lastChunk.get('tool_calls'):
            # append LLM decision to call the tool to context
            context.append({
                'role': 'assistant',
                'thinking': final_thinking,
                'content': final_response,
                'tool_calls': lastChunk['tool_calls']
            })
            # append tool call results to context
            context.extend(lastChunk.get('tool_outputs'))

            # later, save the LLM tool call decision and tool outputs to the database HERE!!!

            # reset the LLM outputs
            final_response = ""
            final_thinking = ""

            # generate a new LLM response by feeding it the new context that has the tool calls and outputs -- the response to the tool outputs is what streams to the user
            # the context at this point = [old history, {user input}, {tool call decision}]
            trip2_generator = generateLLMResponse(user_input="", model=model, context=context, user_id=user_id, agent_mode=allowAgent)

            for chunk in trip2_generator:
                format_data_chunk = {
                    'ai_response': chunk.get('ai_response'),
                    'ai_thinking': chunk.get('ai_thinking'),
                    'in_thinking': chunk.get('in_thinking'),
                    'done': chunk.get('done')
                }
                yield f"data: {json.dumps(format_data_chunk)}\n\n"

                # Capture the aggregate results for database storage
                if not chunk.get('done'):
                    if chunk.get('ai_response'):
                        assert isinstance(chunk['ai_response'], str)
                        final_response += chunk['ai_response']
                    if chunk.get('ai_thinking'):
                        assert isinstance(chunk['ai_thinking'], str)
                        final_thinking += chunk['ai_thinking']

        # save the final answer (LLM response to the tool outputs) to the database
        if chat_id:
            with Session(get_engine()) as sesh:
                db_chat = sesh.query(Chat).get(chat_id)
                if db_chat:
                    db_chat.messages.append(Message(role="assistant", contents=final_response))
                    sesh.commit()
        

    # ai_response, ai_thinking, context_tokens = generateLLMResponse(user_input=user_message, model=model, context=context)
    # if chat: # if we made or located a chat previously, add the LLM output to the chat's messages
    #     with Session(get_engine()) as sesh:
    #         sesh.add(chat)
    #         chat.messages.append(Message(role="assistant", contents=ai_response))
    #         sesh.commit()

    # return jsonify({
    #     "status": status_msg,
    #     "chatbot_response": ai_response,
    #     "chatbot_thinking": ai_thinking,
    #     "context_tokens": context_tokens,
    #     "chatname": chatName
    # }), 200
    user_id = session['user-id']


    return Response(stream_response(user_id=user_id), mimetype='text/event-stream')
    


@api_bp.post('/user/chat/inputs/cancel-response-stream/')
def cancelLLMResponseStream():

    with getDictLock():
        if 'user-id' in session:
            user_id = session['user-id']
            active_users = getActiveUsers()
            active_users[user_id]['interruptChat'] = True # set the interrupt chat flag to true (will be reset to false in the LLM response stream function that checks the flag)

        else:
            print("Error: User does not have an attached ID!")
            return jsonify({
                "status": "failed"
            }), 401

    
    return jsonify({
        "status": "success"
    }), 200


# reads user chat history and sends it to the client side
@api_bp.get('/user/chat/history/')
def getListOfPreviousChats():
    if 'username' in session:
        user = session['username']
        history = getUserChatHeaders(user)
    else:
        history = []

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


    return jsonify({
        "status": "success",
        "chatList": history
    }), 200


@api_bp.get('/user/chat/history/contents')
def getChatMessages():
    # sends the entire chat contents back to the user
    # the selected chat is defined in the cookies sent by the user
    chat_name = request.cookies.get('chat-name')
    # print(chat_name)
    user = session.get('username')
    if not user:
        response = jsonify({
            "status": "failed:no-user",
            "message": ""
        })
        response.delete_cookie('chat-name', path="api/user/chat/history/contents") # remove the temporary cookie

        return response, 402
    
    if not chat_name:
        response = jsonify({
            "status": "failed:no-chat-name",
            "message": ""
        })
        response.delete_cookie('chat-name', path="api/user/chat/history/contents") # remove the temporary cookie
        return response, 403

    chat_contents, model = getChatContents(user, chat_name)

    print("Last used model: ", model)

    response = jsonify({
        "status": "success",
        "message": chat_contents,
        "model": model
    })

    response.delete_cookie('chat-name', path="api/user/chat/history/contents") # remove the temporary cookie
    return response, 200


@api_bp.get('/usable-models/') # the full route is /api/usable-models/
def getAvailableModels():
    models = getModelNames() # models = [list of model names]
    return models, 200


@api_bp.post('/user/heartbeat/')
def handleHeartbeat():

    current_time = time.time()

    # if the user has a user-id (should always be true but check anyway)
    with getDictLock():
        active_users = getActiveUsers()
        if 'user-id' in session:
            user_id = session['user-id']
            if user_id in active_users:
                active_users[user_id]['last-seen'] = current_time # this treats the value of 'user-id' as a json object with a key called 'last-seen' inside it
            else:
                active_users[user_id] = {
                    'interruptChat': False,
                    'last-seen': current_time
                }


        else:
            print("User did not have a user-id in session, creating new id...")
            user_id = generateUserId()
            session['user-id'] = user_id # add it to the session

            active_users[user_id] = {
                'interruptChat': False,
                'last-seen': current_time
            }


    return jsonify({
        "status": "success"
    })


@api_bp.post('/user/file/upload/')
def saveFileUpload():
    """
    Handles POST requests from user that holds the uploaded files
    """
    max_instantaneous_uploads = 4

    # allow text files, pdfs, markdown, python scripts, matlab scripts, ...
    acceptableFileTypes = ['.txt', '.pdf', '.md', '.py', '.m']
    
    # the request contains a FileList object from the client side, parse through each file and verify if it actually contains files
    fileList = request.files.getlist('files')

    # do not allow more than 4 files to be uploaded at once
    if (len(fileList) > max_instantaneous_uploads):
        return jsonify({
            "status": "failed:too-many-files",
        }), 401

    # first, check if user is logged in (username is in session)
    if 'username' in session and request.files:
        # check if username is valid:
        with Session(get_engine()) as sesh:
            username = session['username']
            validUser = getUser(session=sesh, username=username, full_load=False)
            # next check if the username is actually valid
            if validUser:

                chatName = request.form.get('chatname') # extract the chatname from the form data

                # check if the chatName is valid (exists in the database)
                assert chatName # assume chatname is valid
                validChat = getUserChat(session=sesh, username=username, chatName=chatName)
                if not validChat: # create the chat if not valid -- for now just cause an error <============================ FIX THIS LATER ======================================
                    print(f"\nERROR: CHAT '{chatName}' DOES NOT EXIST!\nFailed to upload files: \n{fileList}")
                    return jsonify({
                        "status": "failed:invalid-chatname",
                        "chatname": chatName
                    }), 400

                # check if every file is valid -- fails immediately (without saving any files) if any file is invalid
                for file in fileList:
                    fileName = file.filename
                    assert fileName
                    extension = "." + fileName.split('.').pop() # grab just the extension of the file
                    
                    # if a single file type is invalid, exit and do not save any of the given files (maybe change this later so only the unsupported file is rejected)
                    if extension not in acceptableFileTypes:
                        print("Error: Invalid file type uploaded: ", extension)
                        return jsonify({
                            "status": "failed:invalid-file-type",
                            "filetype": extension
                        }), 400
                    
                    # if all files are supported, save them to the database for the given user
                    # validUser.chats

                # at this point, all of the files are supported and can now be stored into the database. Later, sanitize the file names before storing them for enhanced security.
                # Later, combine the file saving loop with the supported file checking loop
                with Session(get_engine()) as sesh:
                    embedder = CustomEmbedder()
                    # assert validChat
                    existingFiles = validChat.files
                    failedFiles = []

                    for fileItem in fileList:
                        assert chatName
                        fileAdded = None # boolean indicating if the file was successfully added to the chat
                        if fileItem not in existingFiles:
                            fileAdded = addFileToChat(session=sesh, username=username, chatName=chatName, flask_file=fileItem)
                            if not fileAdded: # if storing the file into database fails, skip chunking for that file
                                failedFiles.append(chatName)
                                continue

                            # here, we will start a thread that takes the current file object, splits it into chunks gets their embeddings and stores it in the database
                            # ================================= LATER, MAKE THIS PART ASYNCHRONOUS SO IT DOES NOT BLOCK THE MAIN THREAD!!!! =================================
                            text_chunks = chunkifyDoc(fileItem)
                            embeddings = embedder.embed_documents(text_chunks)
                            # print(f"Chunk count: {len(text_chunks)}\nEmbedding Count: {len(embeddings)}")
                            addAllFileEmbeddings(session=sesh, file_obj=fileAdded, embeddings=embeddings, raw_text=text_chunks)
                            # ===============================================================================================================================================



                    if (failedFiles and len(failedFiles) == len(fileList)):
                        return jsonify({
                            "status": "failed:no-saved-files"
                        }), 400
                    elif (failedFiles and len(failedFiles) > 0):
                        return jsonify({
                            "status": "failed:partially-saved-files",
                            "failed-files": failedFiles
                        }), 400

                return jsonify({
                    "status": "success"
                }), 200
    # otherwise, do nothing and return
    # else:
    return jsonify({
        "status": "failed:not-logged-in"
    }), 400

@api_bp.post('/user/chat/request-new-name/')
def createNewChatName():
    """
    If the user is logged in as a valid user, generates a new chat name and returns it.

    If the user is a guest, the chat name returned is 'guestchat'.

    If the user is logged in but is not a valid user, the request fails.
    """


    if 'username' in session:
        user = session['username']
        
        with Session(get_engine()) as sesh:
            if (getUser(session=sesh, username=user, full_load=False)): # check if the current username is a valid user
                data = request.get_json()
                chatname = data.get('chatName')
                newName = generateChatName(chatName=chatname, model=data.get('model')) # generate the chatname using the model and current chatname
                return jsonify({
                    "status": "success",
                    "newChatName": newName
                }), 200
            else:
                print("User is not valid!")
    else:
        return jsonify({
            "status": "success",
            "newChatName": 'guestchat'
        }), 200
    return jsonify({
        "status": "failed"
    }), 400


def queryChatFiles(usernmae : str, chatname : str, query : str) -> list[str]:
    """
    Based on the user input query, the top 'K' matching text chunks are fetched from the database and returned (fed to the LLM).
    This function merely fetches the K text chunks and returns them.
    """

    k_chunks = []




    return k_chunks



# # this saves the user chat-text (as a json) on the server side over the given path/route
# @api_bp.post('/user/chat/inputs/')
# def saveChatData(): 

#     # data should have the form of a json where:
#     # {
#     #     "message": "user input/prompt message",
#     #     "model": "model name",
#     #     "chatname": 'chat name here"
#     # }

#     data = request.get_json()
#     chatName = data.get('chatname')
#     print("Chat name before generating: ", chatName)

#     user_message = data.get('message')
#     model = data.get('model')
    

#     # if this is a new chat, generate a new name for the chat
#     if chatName == 'newchat' or not chatName:
#         chatName = generateChatName(chatName, model)
#         print("Chat name after generating: " , chatName)

#     ai_thinking = ''
#     ai_response = ''
    
#     # message_text = data.get("message")
#     # user = ''

#     # if the user is logged in, fetch the user chat and append the current message to the chat
#     if 'username' in session:
#         username = session['username']
#         if username:
#             ai_response, ai_thinking = generateLLMResponse(username, user_message, model, chatName)


#     # ai_response = markdownToHtml(ai_response)
#     # ai_thinking = markdownToHtml(ai_thinking)

#     newData = {
#         "message": user_message,
#         "response": ai_response,
#         "model_thinking": ai_thinking,
#         "model": model
#     }


#     # print(ai_response)

#     return jsonify({
#         "status": "sent",
#         "chatbot_response": ai_response,
#         "chatname": chatName
#     }), 200