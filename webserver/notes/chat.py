from ollama import chat, ChatResponse
import subprocess, os, ollama

# starts ollama (ready to run any model)
def openOllama():

    try: 
        a = ollama.list()
        print("Ollama is running :)")
        
        # time.sleep(2)

    except:

        print("Ollama is not running. Starting Ollama...")

        # starts ollama by listing available (downloaded) llms
        subprocess.run(["ollama", "ls"], shell=True)
        
        print("Ollama Started!")

def startChat(model):
    # response : ChatResponse = chat(model=model)

    # print(response)

    # NOTE: This instruction helped deepseek-r1 model correctly answer 'how many r's are in strawberry?'
    context = [{
        "role": "system", 
        "content": "Be concise and analyze in detail before jumping to conclusions."
    }]

    string = ''
    while(string != "quit"):
        string = input("\nInput a prompt (or 'quit' to exit):\n").strip()

        if (string == "quit"):
            break

        # print("\n")
        # string = input("Input a prompt!\n")
        messages = {
            "role":  "user", "content": string
        }

        context.append(messages) # context now holds all previous prompts and responses + current prompt

        # print(context)

        response = ''
        thinking = ''
        for piece in getChatResponse(context, model):
            response, thinking = piece

        context.append({"role": "assistant", "content": response}) # add the llm response to the context window

        
# clears the prompt history file
def clearHistory():
    user_profile = os.environ.get("USERPROFILE", "")
    historyFilePath = os.path.join(user_profile, ".ollama", "history")

    # get size of the history file (holds all previous user prompts)
    size : int = os.path.getsize(historyFilePath)
    size_updated = size
    count : int = 0

    while (size_updated > 1024):
        size_updated = size_updated / 1024
        count = count + 1
        if count == 3:
            break

    # array for printing
    type = ["B", "KB", "MB", "GB"]

    size_updated = round(size_updated, 2) # round the file size
    print(f"Size of history file = {size_updated} {type.pop(count)}")

    # print()
    string = input("Clear history? (y/n): ").strip()

    # ask user whether to clear the history file
    if (string == "y" or string == "Y"):
        print("Clearing history...")
        with open(historyFilePath, "wb") as file:
            pass

# terminates the running ollama model, ollama.exe, and "ollama app.exe"
def stopOllama(model):

    string = input("Close Ollama? (y/n): ").strip()

    if (string == "y" or string == "Y"):
        subprocess.run(["ollama", "stop", model])
        subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"])
        subprocess.run(["taskkill", "/F", "/IM", "ollama app.exe"])


def getModelNames() -> list[str]:
    list = ollama.list()
    models = []
    for modelInfo in list.get('models', []):
        models.append(modelInfo.get('model', []))
    return models


def getChatResponse(messages, model):
    responseStream = ollama.chat(
        model=model,
        messages=messages,
        stream=True,
    )

    in_thinking = False
    thinking = ''
    content = ''
    usageTokens = 0
    promptTokens = 0

    for chunk in responseStream:
        # if the current generated chunk of tokens contains thinking
        if chunk.message.thinking:
            if not in_thinking:
                in_thinking = True
                print("Thinking:\n", end='', flush=True)
            print(chunk.message.thinking, end='', flush=True)

            thinking += chunk.message.thinking
            yield content, thinking
        # otherwise if the current generated chunk of tokens contains actual content (final response)
        elif chunk.message.content:
            if in_thinking:
                in_thinking = False
                print("\n\nAnswer:\n", end='', flush=True)
            print(chunk.message.content, end='', flush=True)

            content += chunk.message.content
            yield content, thinking
        # the last chunk in the llm response contains the usage metrics/statistics (e.g. token count)
        if chunk.get('done'):
            usageTokens = chunk.eval_count
            promptTokens = chunk.prompt_eval_count


    print("\nUsage Tokens = ", usageTokens)
    print("Prompt Tokens = ", promptTokens)
    yield content, thinking


# Call Functions Here:
model = "nemotron-3-super:cloud"

openOllama()
# models = getModelNames()
# print(models)
startChat(model)
stopOllama(model)



# clearHistory()