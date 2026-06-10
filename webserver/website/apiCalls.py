from flask import Blueprint, request, session, jsonify
from helperFunctions import storeChatData, getModelNames, generateLLMResponse, getUserChatHistory

# all URLS inside of chat_bp will automatically have their route start with /api/ because of the 3rd argument
# api_bp = Blueprint('api', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api/')


# this saves the user chat-text (as a json) on the server side over the given path/route
# @app.post('/api/user/chats')
@api_bp.post('/user/chat/inputs/') # the full route is /api/user/chats/
def saveChatData(): 

    # data should have the form of a json where:
    # {
    #     "message": "user input/prompt message",
    #     "model": "model name"
    # }

    data = request.get_json()
    
    # message_text = data.get("message")
    user = None
    if 'username' in session:
        user = session['username']
        # print(f"'{user}' sent a message: {message_text}")
        # storeChatData(data, user)
    # else:
        # print(f"Guest user sent a message: {message_text}")
        # storeChatData(data, None)

    user_message = data.get('message')
    model = data.get('model')
    # ai_response, ai_thinking = generateLLMResponse(user_message, model)
    ai_thinking = ''
    ai_response = ''

    newData = {
        "message": user_message,
        "response": ai_response,
        "model_thinking": ai_thinking,
        "model": model
    }

    storeChatData(newData, user)

    print(ai_response)

    return jsonify({
        "status": "sent",
        "chatbot_response": ai_response
    }), 200


# reads user chat history and sends it to the client side
@api_bp.get('/user/chat/history/')
def loadChatHistory():
    if 'username' in session:
        user = session['username']
        history = getUserChatHistory(user)
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
        "history": history
    }), 200



# @app.get('/api/usable-models/')
@api_bp.get('/usable-models/') # the full route is /api/usable-models/
def getAvailableModels():

    models = getModelNames() # models = [list of model names]
    return models, 200