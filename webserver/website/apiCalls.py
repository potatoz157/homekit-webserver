from flask import Blueprint, request, session, jsonify
from helperFunctions import getModelNames, generateLLMResponse, getUserChatHeaders, getChatContents, markdownToHtml, generateChatName
from databaseFunctions import getUser, getUserChat, addUserChat
from databaseTables import get_engine, Message
from sqlalchemy.orm import Session

# all URLS inside of chat_bp will automatically have their route start with /api/ because of the 3rd argument
# api_bp = Blueprint('api', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api/')


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
    # context needs to be in the format of a json array!
    context = data.get('context') # THIS IS NEW, UPDATE THE JS TO ALSO SEND THE CONTEXT i.e. CHAT HISTORY!!!!!!!
    chatName = data.get('chatname')
    model = data.get('model')




    # logged in chat response behavior
    chat = None # this variable holds the fetched or created chat if the user was logged in
    if 'username' in session:
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
            
        # if no chat was found, create a new chat and append the user input to the chat
        else:
            with Session(get_engine()) as sesh:
                chatName = generateChatName(chatName=chatName, model=model)
                chat_added, new_chat = addUserChat(session=sesh, username=username, chatName=chatName, model=model)
                if (chat_added and new_chat): # if a new chat was successfully made, save the user input prompt to the chat's messages
                    new_chat.messages.append(Message(role="user", contents=user_message))
                    status_msg = "success:new-chat-created"
                else:
                    print("Error: failed to create and add a new chat to the database...")
                    status_msg = "success:failed-to-save-to-chat"
                chat = new_chat
                sesh.commit()
        # ai_response, ai_thinking, _ = generateLLMResponse(user_input=user_message, model=model, context=context)
        # if chat: # if we made or located a chat previously, add the LLM output to the chat's messages
        #     chat.messages.append(Message(role="assistant", contents=ai_response))
    else:
        status_msg = "success:guest"

    ai_response, ai_thinking, context_tokens = generateLLMResponse(user_input=user_message, model=model, context=context)
    if chat: # if we made or located a chat previously, add the LLM output to the chat's messages
        with Session(get_engine()) as sesh:
            sesh.add(chat)
            chat.messages.append(Message(role="assistant", contents=ai_response))
            sesh.commit()

    return jsonify({
        "status": status_msg,
        "chatbot_response": ai_response,
        "chatbot_thinking": ai_thinking,
        "context_tokens": context_tokens,
        "chatname": chatName
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