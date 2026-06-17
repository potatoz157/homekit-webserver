from flask import Blueprint, request, session, jsonify
from helperFunctions import storeChatData, getModelNames, generateLLMResponse, getUserChatHeaders, getChatContents, markdownToHtml, generateChatName
from databaseTables import engine

# all URLS inside of chat_bp will automatically have their route start with /api/ because of the 3rd argument
# api_bp = Blueprint('api', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api/')


# this saves the user chat-text (as a json) on the server side over the given path/route
@api_bp.post('/user/chat/inputs/')
def saveChatData(): 

    # data should have the form of a json where:
    # {
    #     "message": "user input/prompt message",
    #     "model": "model name",
    #     "chatname": 'chat name here"
    # }

    data = request.get_json()
    chatName = data.get('chatname')
    print("Chat name before generating: ", chatName)

    user_message = data.get('message')
    model = data.get('model')
    

    # if this is a new chat, generate a new name for the chat
    if chatName == 'newchat' or not chatName:
        chatName = generateChatName(chatName, model)
        print("Chat name after generating: " , chatName)

    
    # message_text = data.get("message")
    user = ''
    if 'username' in session:
        user = session['username']
        # print(f"'{user}' sent a message: {message_text}")
        # storeChatData(data, user)
    # else:
        # print(f"Guest user sent a message: {message_text}")
        # storeChatData(data, None)


    ai_response, ai_thinking = generateLLMResponse(user, user_message, model, chatName)
    # ai_thinking = ''
    # ai_response = ''

    # ai_response = markdownToHtml(ai_response)
    # ai_thinking = markdownToHtml(ai_thinking)

    newData = {
        "message": user_message,
        "response": ai_response,
        "model_thinking": ai_thinking,
        "model": model
    }

    storeChatData(newData, user, chatName)

    # print(ai_response)

    return jsonify({
        "status": "sent",
        "chatbot_response": ai_response,
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
        "message": history
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

    chat_contents = getChatContents(user, chat_name)
    model = chat_contents[-1].get('model')

    print("Last used model: ", model)

    response = jsonify({
        "status": "success",
        "message": chat_contents,
        "model": model
    })

    response.delete_cookie('chat-name', path="api/user/chat/history/contents") # remove the temporary cookie
    return response, 200



# @app.get('/api/usable-models/')
@api_bp.get('/usable-models/') # the full route is /api/usable-models/
def getAvailableModels():

    models = getModelNames() # models = [list of model names]
    return models, 200