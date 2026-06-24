from flask import Blueprint, request, session, jsonify, Response
from helperFunctions import getModelNames, generateLLMResponse, getUserChatHeaders, getChatContents, markdownToHtml, generateChatName
from databaseFunctions import getUser, getUserChat, addUserChat
from databaseTables import get_engine, Message, Chat
from sqlalchemy.orm import Session
from chatbot import generateUserId
from globals import getActiveUsers, getDictLock
import json, time

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
def saveChatData():
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

    chat_id = None # track the chat ID across different sessions

    # logged in chat response behavior
    if 'username' in session:
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
                chatName = generateChatName(chatName=chatName, model=model)
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
        generator = generateLLMResponse(user_input=user_message, model=model, context=context, user_id=user_id)

        final_response = ""
        final_thinking = ""

        # send the initial response back to frontend so that the frontend has the new chat name and status before waiting for LLM stream
        init_payload = {
            "status": status_msg,
            "chatname": chatName,
            "is_initial": True,
            "done": False
        }

        yield f"data: {json.dumps(init_payload)}\n\n"

        for data_chunk in generator:
            # Format and stream the current chunk directly to the frontend
            yield f"data: {json.dumps(data_chunk)}\n\n"
            
            # Capture the aggregate results for database storage
            if data_chunk.get('ai_response'):
                assert isinstance(data_chunk['ai_response'], str)
                final_response += data_chunk['ai_response']
            if data_chunk.get('ai_thinking'):
                assert isinstance(data_chunk['ai_thinking'], str)
                final_thinking += data_chunk['ai_thinking']


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
def cancelResponseStream():

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
def loadPreviousChats():
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
def loadChatContents():
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
def getHeartbeat():

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