let cachedModels = null; // used to store and compare previously models available for use (downloaded on the server/backend)
let currentModel = 'qwen2.5:14b-instruct';
let currentChatName = 'newchat';
let context = [];
let agentMode = false;
const contextSize = 40; // limit number of total messages to 40 (one msg is a user input or an llm output) -- total 20 user inputs + 20 llm outputs

// this will act as a 'queue' for the FormData object that is to be sent (when a user uploads files) with the next 
// user prompt (when the user presses 'enter' or submit text button, prompt CAN be empty)
let fileFormData = null;

const dropbox = document.getElementById("dropbox");

// dropbox.addEventListener("dragenter", dragenter);
dropbox.addEventListener("dragover", dragover);
dropbox.addEventListener("dragleave", dragleave);
dropbox.addEventListener("drop", drop);



// function dragenter(e) {
//     e.stopPropagation();
//     e.preventDefault();
// }


function dragover(e) {
    e.stopPropagation();
    e.preventDefault();

    // console.log(e);
    const dt = e.dataTransfer;

    // trigger UI changes if the dragged elements are actually files
    if (dt.types && dt.types.includes('Files')) {
        // dropbox.style.backgroundColor = "red";
        document.getElementById('overlay').style.display = "block";
    }

    // const dropbox = document.getElementById("dropbox");
    // dropbox.style.backgroundColor = "red";
}

function drop(e) {
    e.stopPropagation();
    e.preventDefault();

    const dt = e.dataTransfer;
    const files = dt.files;

    prepareUploadFile(files);

    dragleave(e); // also trigger UI updates in dragleave function
}

function dragleave(e) {
    e.stopPropagation();
    e.preventDefault();

    // dropbox.style.backgroundColor = "black"
    document.getElementById('overlay').style.display = "none";
}




// ping the backend periodically to check if the user is active
// pings every X seconds (the argument is in ms, so 60000 = 60 seconds)
setInterval(() => {
    sendHeartbeat();
}, 30000);


// when AI Assistant page loads, perform the following
document.addEventListener("DOMContentLoaded", async () => {
    sendHeartbeat();

    // ensure the selected model (icon) matches that of the one present in the code
    selectModel(currentModel);

    if (userIsLoggedIn()) {
        // when the user is logged in:
        // hide the login button, show the logout button
        document.getElementById('login-button').style.display = 'none';
        document.getElementById('login-button-link').style.display = 'none';

        document.getElementById('logout-button').style.display = 'block';
        document.getElementById('logout-button-link').style.display = 'block';
    }
    else {
        document.getElementById('login-button').style.display = 'block';
        document.getElementById('login-button-link').style.display = 'block';
                        
        document.getElementById('logout-button').style.display = 'none';
        document.getElementById('logout-button-link').style.display = 'none';
    }


});

document.addEventListener("keydown", function(event) {
    
    // skip the auto focus if the tab key is pressed or enter is pressed
    // if (event.key == 'Tab' || event.key == 'Enter') {
    //     return;
    // }
    
    const textBox = document.getElementById("input-box");

    // const isCharKey = /^[a-zA-Z0-9]$/.test(event.key);
    const excludedKeys = [
        'Control', 'Shift', 'Alt', 'Tab', 'CapsLock', 'Meta',
        'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
    ]

    // check to see if a control key is currently being held (like when doing ctrl-c)
    const isModifierKeyPressed = event.getModifierState('Control') ||
                                 event.getModifierState('Shift') ||
                                 event.getModifierState('Alt');

    // if the pressed key is not a character/symbol (i.e. a control key, such as 'Shift' or 'Control'), do nothing and exit
    if (excludedKeys.includes(event.key) || isModifierKeyPressed) {
        // console.log("Control key pressed!", event.key)
        return;
    }


    // focus the textbox and close the dropdown menu (if open)
    textBox.focus();
    const dropdown = document.getElementById("model-dropdown");
    if (dropdown && dropdown.classList.contains("show")) {
        dropdown.classList.remove("show");
    };
    // textBox.value += event.key;


});

// removes the dropdown menu if the user clicks anywhere outside the dropdown menu
window.addEventListener("click", function() {
    const dropdown = document.getElementById("model-dropdown");
    if (dropdown && dropdown.classList.contains("show")) {
        dropdown.classList.remove("show");
    };
});

// runs the upload text function (posts user input to backend) upon 'enter' keypress in the textarea input box
document.getElementById("input-box").addEventListener("keydown", (event) => {
    if (event.key == "Enter") { // if keydown is enter

        // default behavior is to add a newline in a textarea
        if (!event.shiftKey) { // if shift is not being held
            event.preventDefault(); // prevent newline from being added
            uploadText();
        }
    }
});

// upon user input into textarea, update the size of the input box
document.getElementById("input-box").addEventListener("input", function() {
    resizeTextBox();
});


// enable/disable tool calling using the slider -- LATER, implement the enable/disable feature in the backend so it actual disables the tools!
document.getElementById("agentic-mode-toggle-checkbox").addEventListener('change', (event) => {
    // event.stopPropagation();

    const checkbox = document.getElementById("agentic-mode-toggle-checkbox");
    const button = document.getElementById("agentic-mode-button");

    // checkbox.checked = !checkbox.checked;
    // Action when checked -- enable agentic mode (allow tool use)
    if (event.target.checked) {
        agentMode = true;
        checkbox.style.marginRight = '0';
        checkbox.style.marginLeft = 'auto';
        button.style.backgroundColor = "rgb(94, 221, 94)";
        // console.log("Active")
    }
    // Action when unchecked -- disable agentic mode (disable tool use, acts as chatbot only)
    else {
        agentMode = false;
        checkbox.style.marginRight = 'auto';
        checkbox.style.marginLeft = '0';
        button.style.backgroundColor = "lightgray";
        // console.log("Inactive")
    }
});

// this function is triggered when the user presses the slider button for toggling agentic mode.
function updateSlider() {
    const checkbox = document.getElementById("agentic-mode-toggle-checkbox");
    checkbox.checked = !checkbox.checked; // toggle slider
    // trigger checkbox event listener
    const event = new Event('change');
    checkbox.dispatchEvent(event);
}

// posts user input to backend (using another function) and updates the UI
async function uploadText() {

    
    const textBox = document.getElementById("input-box");
    const userInput = textBox.value; // read and save textbox value

    // if there are files to upload, upload them then deal with the user prompt, later maybe send both in the same post request
    if (fileFormData !== null) {
            uploadQueuedFiles(); // automatically clears the queued fileFormData variable
        }
    
    // if the text box was empty then do nothing
    if (userInput.length == 0) {
        return;
    }
    
    const uploadTextButton = document.getElementById('upload-text-btn');
    // uploadTextButton.onclick = null; // remove attached onclick function

    // make the upload button trigger the stop chat stream function -- interrupts the LLM response stream
    uploadTextButton.onclick = () => {stopLLMResponse()};
    // change uploadTextButton icon to be a stop button
    uploadTextButton.innerText = '⏹';

    // after user input is displayed, scroll to bottom of page
    scrollToBottomOfChat();

    textBox.value = ""; // clear textbox
    resizeTextBox(); // update textbox UI


    // create element to container user input
    const userTextElement = document.createElement('p');
    userTextElement.className = 'chat-text-style user-chat-margins'; 
    userTextElement.textContent = userInput; // set the text as the literal user input

    // get container to hold all of the chat text (by user and LLM)
    const currentChatContainer = document.getElementById('current-chat-container');

    document.getElementById('initial-greeting').style.display = 'none';
    currentChatContainer.style.display = 'flex';
    
    // add the user input element to the chat box
    currentChatContainer.appendChild(userTextElement);

    // define post request body
    const body = JSON.stringify({
        message: userInput,
        model: currentModel,
        chatname: currentChatName,
        context: context,
        allow_agent: agentMode
    });

    // append user input to the context field after the context has been sent (prevent duplication of user input)
    context.push({role: "user", content: userInput});

    // Generate post request. We assume sendJsonPostRequest returns the raw Response object.
    const response = await sendJsonPostRequest("/api/user/chat/inputs/", body);
    
    // --- START OF STREAMING LOGIC ---
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    // Create elements to hold incoming response and thinking text
    const llmTextElement = document.createElement('div');
    llmTextElement.className = 'chat-text-style ai-chat-margins';
    currentChatContainer.appendChild(llmTextElement);

    let full_ai_response = "";
    let full_ai_thinking = "";
    let buffer = ""; // Buffer to catch incomplete stream lines

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        // Decode binary data to string and add to our buffer
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        
        // Save the last potentially incomplete line back to the buffer
        buffer = lines.pop();

        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith("data: ")) continue;

            try {
                // Strip the "data: " prefix and parse the JSON payload
                const data = JSON.parse(trimmed.slice(6));

                // 1. Check for the initial structural packet containing metadata
                if (data.is_initial) {
                    if (currentChatName == "newchat" || currentChatName == null) {
                        currentChatName = data.chatname;
                    }
                    // console.log(data.status);
                    continue;
                }

                // 2. Accumulate response or thinking streams
                if (!data.done) {
                    if (data.ai_response) {
                        full_ai_response += data.ai_response;
                        scrollToBottomOfChat();
                    }
                    if (data.ai_thinking) {
                        full_ai_thinking += data.ai_thinking;
                        scrollToBottomOfChat();
                    }
                }
                // 3. Update the UI continuously with the latest accumulated response text
                // Adjust this if you want to visually display thinking blocks differently
                llmTextElement.innerText = full_ai_response;
                
            } catch (err) {
                console.error("Error parsing stream chunk:", err);
            }
        }
        scrollToBottomOfChat();
    }
    // --- END OF STREAMING LOGIC ---

    // Store the complete accumulated output into the context now that streaming is complete
    context.push({role: "assistant", content: full_ai_response}); 

    // Keep context history managed within your context limits
    if (context.length > contextSize) {
        context.shift();
        context.shift();
    }
    
    resizeTextBox(); // update textbox UI again after LLM response is fully displayed
    
    // add slight delay to make feel more natural
    setTimeout(() => {
        uploadTextButton.innerText = '↑';
        uploadTextButton.onclick = () => {uploadText()}; // re-attach onclick method for upload text button
    }, 50);

}

// opens/triggers the file selection browser upon upload file button press
function triggerFilePicker() {
    document.getElementById("upload-file-input").click();
}

// uploads the literal file and triggers UI changes
async function prepareUploadFile(inputElement) {

    
    if (!userIsLoggedIn()) {
        uploadFileUiUpdate("failed:not-logged-in");
        return;
    }


    let fileList = null;

    // when the user uploads files using the upload button, the inputElement has a .files property (the inputElement is the literal html <input> element that calls this function)
    if (inputElement.files && inputElement.files.length > 0) {
        fileList = inputElement.files;
        inputElement.value = '';
    }
    // when the user uploads files by drag and drop, the input element is a FileList object
    else if (inputElement instanceof FileList){
        fileList = inputElement;
    }
    else {
        console.log("Error: prepareUploadFile() failed due to unknown inputElement argument type: ", inputElement);
    }

    const dataToSend = new FormData();
    // dataToSend.append('fileList', fileList);
    const fileIconContainer = document.getElementById("file-upload-icons-container");
    const clearIconBtn = document.getElementById("file-icon-clear-button");
    // for every file, append it to the FormData.files object and generate a file upload icon
    for (file of fileList) {
        dataToSend.append('files', file);
        const extension = getFileNameExtension(file.name);
        if (extension) {
            const fileIcon = document.createElement('p'); // create new p tag for file icon
            fileIcon.className = 'file-icon'; // apply file icon CSS using the class name
            fileIcon.innerText = extension.toUpperCase();; // set the icon string
            fileIconContainer.appendChild(fileIcon); // add the new icon to the icon container
            fileIconContainer.moveBefore(fileIcon, clearIconBtn); // append the new node right before the clear button
        }
    }
    clearIconBtn.style.display = "block"; // show the clear icons/uploads button
    
    // WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    // THE CHATNAME IS NOT UPDATED CORRECTLY. CURRENTLY, THE CHATNAME IS ONLY UPDATED AFTER THE USER INPUTS A PROMPT!
    // TO ENSURE THE 'currentChatName' VARIABLE IS NOT 'newchat', MAKE SURE A CHAT NAME IS MADE FOR ALL NEW CHATS THE MOMENT THEY
    // ARE OPENED!!!!!!!!!!!!!!!!!!!!!!!!!!
    // Later, make it so that the actual upload is only triggered when the user presses submit (i.e. the prompt submit button) or the 'enter' key.
    // Right now, the file is immediately uploaded to the backend without user intervention required.
    dataToSend.append('chatname', currentChatName); // send the chatname so the files are attached to the right place

    fileFormData = dataToSend; // save the data to the 'queue' so it can be sent when the user triggers uploadText()
    

}


// Sends a post request with the queued file FormData object (variable is fileFormData). This variable should be null if no files were given by the user or
// if the given files were already uploaded. Otherwise, (if not null) there are files pending to be uploaded.
// This function sends those files and clears (sets to null) the fileFormData variable.
async function uploadQueuedFiles() {
    const fileIconContainer = document.getElementById("file-upload-icons-container");
    const clearBtn = document.getElementById("file-icon-clear-button");

    const childrenBackup = [...fileIconContainer.children]; // save array of children nodes in case the upload fails (to restore icons)

    // clear file icons
    fileIconContainer.replaceChildren(clearBtn); // clear all the icons
    clearBtn.style.display = "none"; // make clear button invisible again

    if (fileFormData == null) {
        console.error("File Form Data was null");
        return;
    }
    
    const dataUrlPath = "/api/user/file/upload/"
    const response = await fetch(dataUrlPath, {
        method: 'POST',
        body: fileFormData
    });

    if (response.ok) {
        const data = await response.json();
        uploadFileUiUpdate(data.status); // updates the UI based on the status that is returned

        // clear queued file form data object once the response fully completes
        fileFormData = null; 

    }
    // if the response is not ok, restore the icons
    else {
        fileIconContainer.replaceChildren(...childrenBackup);
        clearBtn.style.display = "block"; // make clear uploads button invisible again
    }

}



// updates the model selection dropdown menu -- this triggers a get request of available models (i.e. those downloaded on the backend server)
// get request is sent only if the number of models has changed since last viewing (since last time the dropdown was seen)
async function toggleSelectModelDropdown(event) {
    // Prevent the window click listener from immediately closing it down
    event.stopPropagation(); 

    const dropdownContainer = document.getElementById("model-dropdown");

    // if the dropdown menu is visible, do not fetch model list, simply hide the dropdown menu and exit
    if (dropdownContainer.classList.contains("show")) {
        dropdownContainer.classList.remove("show"); // activate/deactivate dropdown menu
        return;
    }

    // get request for all the available models
    const dataUrlPath = "/api/usable-models"; // path were usable models list is sent
    const response = await fetch(dataUrlPath, {
        method: 'GET'
    });

    const models = await response.json(); // get the json from response (models now equals a list)

    // if cachedModels is not initialized, or if the cachedModels and fetched models lists are different in length, update cachedModels
    if (cachedModels==null || cachedModels.length !== models.length) {
        cachedModels = models;
        console.log("Updated cached models") // log when the cache is updated
    }
    else {
        console.log("Used old/cached models") // log when the cache is used (cache not updated)
    }
    
    // if the number of elements in the dropdown screen (child div elements) matches the number of cachedModels, skip the step to add more div elements
    // note that 'cachedModels' is iterated over and not 'models' for creation of div elements
    if (dropdownContainer.childElementCount == cachedModels.length) {
        dropdownContainer.classList.toggle("show"); // activate/deactivate dropdown menu
        return;
    }

    // for each model in cachedModels, create a div element with the following parameters:
    // <div class="model-dropdown-item" onclick="selectModel('deepseek-r1:14b')">deepseek-r1:14b</div>
    for (let i = 0; i < cachedModels.length; i++) {
        const model = cachedModels[i];

        // for each model, create an element that sits in the dropdown menu
        const div = document.createElement("div");
        // define the element class, text content and operation upon clicking
        div.className = "model-dropdown-item";
        div.textContent = model;
        div.onclick = function() {
            selectModel(model);
        }

        // add the new element as a child of the dropdown menu container
        dropdownContainer.appendChild(div);
    }

    dropdownContainer.classList.toggle("show"); // activate/deactivate dropdown menu
}

// updates the actual selected model (for now, it updates just the text in the UI)
// incomplete -- later this should change an element that tells the backend which model to use when feeding user prompts into llm's
function selectModel(modelName) {
    currentModel = modelName;
    document.getElementById("current-model-text").innerText = modelName;

    const dropdown = document.getElementById("model-dropdown");
    if (dropdown.classList.contains("show")) {
        dropdown.classList.remove("show");
    }
}

// this updates the input text box area/background
function resizeTextBox() {
    const textBox = document.getElementById("input-box");
    textBox.style.height = "auto"; // Shrinks it instantly back to 56px
    textBox.style.height = (textBox.scrollHeight - 4) + "px";  // the (-4) accounts for the expansion upon (initial) interaction
}

// returns a list of chat history titles/headers (right now, it returns just the file names)
async function getChatHistory() {
    // generate get request to fetch list of chat history files
    const dataUrlPath = '/api/user/chat/history/';

    const response = await fetch(dataUrlPath, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    
    
    // check if the HTTP request actually succeeded (status 200-299)
    if (!response.ok) {
        console.error(`HTTP error! status: ${response.status}`);
        return null;
    }
    
    const data = await response.json(); // get the actual data as a json

    if (data.status == "success") {
        return data.chatList;
    }
    return null;

}


// generates get request to fetch the entire contents of the given chat, updating the UI with the results
async function openChat(chatName) {
    // console.log(chatName);

    // if the current chat container has its text 
    // const loadedChatName = await document.getElementById("loaded-chat-name");
    // if (loadedChatName.textContent == chatName) {
    if (currentChatName == chatName) {
        console.log('chat already loaded...');
        return;
    }

    // generate get request to get full chat data
    const dataUrlPath = '/api/user/chat/history/contents'; // setup api for reading full chat data

    // force the cookie to exist only on the same route as the get request
    document.cookie = "chat-name=" + encodeURIComponent(String(chatName)) + "; path=" + dataUrlPath; // this is used to determine which chat to load (send chat name into cookies)
    
    const response = await fetch(dataUrlPath, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    // check if the HTTP request actually succeeded (status 200-299)
    if (!response.ok) {
        console.error(`HTTP error! status: ${response.status}`);
        return null;
    }

    const data = await response.json();
    let contents = null;

    if (data.status == "success") {
        // get chat contents (actual implementation depends on how the API sends the data!!! --- also need to build the API!)
        contents = data.message;
        context = []; // clear the context
        // console.log(context);
    }
    else {
        console.error("Error accessing chat contents: ", data.status);
    }

    if (contents == null) {
        console.error("Error chat contents are NULL")
        return;
    }

    // update the currently open chat to match that of the requested chat
    currentChatName = chatName;
    
    // update the selected model to match the last used model in the opened chat
    currentModel = data.model;
    selectModel(currentModel)

    // upon successful retrieval of chat history, update the UI of the main-panel:

    // remove welcome greeting
    const greetingHeader = document.getElementById("initial-greeting");
    greetingHeader.style.display = 'none';
    
    // enable visibility of current chat container (wrapper for user and llm texts and responses)
    const currentChatContainer = document.getElementById("current-chat-container");
    currentChatContainer.style.display = 'block';

    currentChatContainer.replaceChildren();
    // currentChatContainer.replaceChildren(loadedChatName); // basically replace all children with nothing (clear all existing text content) except the loaded chat name


    // for every message in contents, get the user input and the LLM response (later get the thinking of the LLM too)
    for (const message of contents) {

        // create element to container user input
        const text = document.createElement('p');
        text.className = 'chat-text-style user-chat-margins'; // here, set the second class name (the one that sets the margins) based on whether it is a user or ai block of text
        text.textContent = message.message; // set the text as the literal user input

        // add the user input (element) to the chat box
        currentChatContainer.appendChild(text);

        // create element to contain llm response
        const llm_text = document.createElement('p');
        llm_text.className = 'chat-text-style ai-chat-margins';
        // llm_text.textContent = message.response;
        llm_text.innerHTML = message.response;  // the response was modified to be HTML and not raw text

        currentChatContainer.appendChild(llm_text);

        context.push({role: "user", content: message.message});
        context.push({role: "assistant", content: message.response});
    }


    scrollToBottomOfChat();
    
}


// updates the UI to bring the new chat menu (clears chat content and hides the chat text container and shows the initial greeting)
// also sets the currentChatName by sending a request to generate a chatname. For guest users, the chatname = 'guestchat'
async function openNewChat() {

    context = [];
    // for a new chat, empty the current-chat-container except keep the loaded-chat-name element (set the textconteont of the loaded chat to be 'newchat')
    const currentChatContainer = document.getElementById('current-chat-container');


    // currentChatName = 'newchat';
    // send post request for new chatname anytime a new chat is opened
    const dataUrlPath = "/api/user/chat/request-new-name/"
    const body = JSON.stringify({
        "chatName": currentChatName,
        "model": currentModel
    });
    const response = await sendJsonPostRequest(dataUrlPath, body); // send request to generate new chat name
    
    if (response.ok) {
        const data = await response.json();
        if (data.status == "success") {
            currentChatName = data.newChatName;
        }
        else {
            currentChatName = 'newchat';
        }
    }
    else {
        currentChatName = 'newchat';
    }



    // const loadedChat = document.getElementById('loaded-chat-name');
    // loadedChat.textContent = 'newchat';
    // currentChatContainer.replaceChildren(loadedChat);
    currentChatContainer.replaceChildren();

    // hide the current-chat-container and show the initial greeting
    currentChatContainer.style.display = 'none';
    const greetingHeader = document.getElementById("initial-greeting");
    greetingHeader.style.display = 'block';

    // clear and update the textbox UI as well
    const textBox = document.getElementById("input-box");
    textBox.value = "";
    resizeTextBox();


    // keep the same model as selected previously (if none, default to qwen2.5:14b-instruct)
    selectModel(currentModel);

    console.log("current chat name = ", currentChatName);
}

// toggle the display of the previous chats
async function listPreviousChats() {
    clearExcessCookies(); // clears the chat-name cookie (and everything else that is not login-status)

    // populate the chat-history-container with buttons, the buttons should have a class='previous-chat-button'
    // the textcontent of the buttons should be the chat name

    const chatHistoryContainer = document.getElementById('chat-history-container');
    // chatHistoryContainer.replaceChildren(); // clear it

    // if the previous chats are visible, hide them and exist
    if (chatHistoryContainer.style.display == "block") {
        chatHistoryContainer.style.display = "none";
        return;
    } 
    // otherwise, if the previous chats are not visible, fetch the list of previous chats and show them
    else {
        chatHistoryContainer.style.display = "block";
        chatHistoryContainer.replaceChildren(); // clear all previous children to prevent duplication
    }

    // fetch list of chat histories -- the user should be logged in
    const chatList = await getChatHistory();

    // for every element in the chatlist, append a button to the chat history container
    for (const chat of chatList) {
        // create new button with previous-chat-button style:
        const historyButton = document.createElement('button');
        historyButton.className = 'previous-chat-button'; // define class for styles
        historyButton.textContent = chat; // define the button text
        historyButton.onclick = function() {openChat(chat)}; // define on click behavior (opens the given chat)

        // add the button to the chat history container
        chatHistoryContainer.appendChild(historyButton);
    }
}

// clears all the existing cookies except the login-status cookie (does not do anything with flask 'sessions')
function clearExcessCookies() {
    const cookies = document.cookie.split("; ");

    for (const cookie of cookies) {
        const key = cookie.split("=");

        if (key[0] !== "login-status") {
            document.cookie = key[0] + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/api/user/chat/history/contents";
        }
    }

}


// periodically called (using setInterval) to ping the backend as a check to see if the user is still active
async function sendHeartbeat() {
    const dataUrlPath = '/api/user/heartbeat';
    sendJsonPostRequest(dataUrlPath, ""); // send empty post request to trigger heartbeat
}



// generic post request generator for json type content (currently used by the uploadText() function)
async function sendJsonPostRequest(dataUrlPath, body) {
    
    const response = await fetch(dataUrlPath, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: body
    });
    return response;
}

// sends a json post request to the route that terminates the LLM response stream
async function stopLLMResponse() {

    const dataUrlPath = '/api/user/chat/inputs/cancel-response-stream/';
    // the body does not really matter at the moment as the contents are not read in the backend...
    body = {
        "objective": "terminate-stream"
    }
    const response = await sendJsonPostRequest(dataUrlPath, body);

    if (response.ok) {
        if (response.status == "success") {
            console.log("successfully stopped LLM output stream")
        }
    }

}


// scrolls the window down based on the current-chat-container height
function scrollToBottomOfChat() {
    // force page to auto scroll to the bottom on initial load
    const currentChatContainer = document.getElementById("current-chat-container"); // already defined
    window.scrollTo(0, currentChatContainer.scrollHeight); // scroll based on the scroll size of the chat container (the div that holds all the text)
}


function userIsLoggedIn() {
    const cookies = document.cookie.split("; "); // split all cookies --> cookies = list of strings, each element = one cookie

    for (const cookie of cookies) {
        const key = cookie.split("=");
        if (key[0] == "login-status") {
            // for the login-status cookie, its value is bool indicating whether the user is logged in
            return key[1] == 'true';
        }
    }
}

// Updates the UI for the file upload based on the input status argument -- Later, refactor UI changes to be made here
function uploadFileUiUpdate(status) {
    // if the file upload is a success, display the filename and extension above the input text box
    // refer to the '/notes/file upload info.png' for more detail
    if (status == "success") {

    }
    // if the user is not logged in, show an error stating that the user must be logged in with a link to login
    // make it a popup menu in the middle of the screen. Make everything else dimmer (cover everything with 50% opacity solid black color).
    // ensure popup has a close button.
    else if (status == "failed:not-logged-in") {
    }
    // if the upload fails due to unsupported file, show an error indicator that states the attempted files are not acceptable
    // also list the acceptable file types
    else if (status == "failed:invalid-file-type") {
    }
    // display unknown error occurred + try again
    else {
        console.error("Unknown status: ", status);
    }
}

// this function clears the fileFormData variable and updates the UI to remove all uploaded files.
function clearFileUploads() {
    fileFormData = null;
    const clearBtn = document.getElementById("file-icon-clear-button");
    clearBtn.style.display = "none";
    document.getElementById("file-upload-icons-container").replaceChildren(clearBtn);
    
}

function getFileNameExtension(filename) {
    const dotIndex = filename.lastIndexOf('.');
    
    // Error check: No dot found, or dot is at the very end of the name
    if (dotIndex == -1 || dotIndex == filename.length - 1) {
        console.error(`Failed to locate file extension for: "${filename}"`);
        return '';
    }
    
    return filename.substring(dotIndex + 1);
}

// NO LONGER USED -- CONVERSION DONE IN PYTHON
// function convertMarkdownToHtml(markdownText, containerElement) {
//     // 1. Convert Markdown format to clean HTML
//     const htmlOutput = marked.parse(markdownText);
    
//     // 2. Inject the modified HTML into your target element
//     containerElement.innerHTML = htmlOutput;
    
//     // 3. Force MathJax to scan the new HTML and render the LaTeX math
//     if (window.MathJax) {
//         window.MathJax.typesetPromise([containerElement]);
//     }
// }
