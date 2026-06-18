// const textBox = document.getElementById("input-box"); // this is the text box where the user puts prompts for the llm's
let cachedModels = null; // used to store and compare previously models available for use (downloaded on the server/backend)
// let emptyChat = true; // NO LONGER USED!
let currentModel = 'qwen2.5:14b-instruct';
let currentChatName = 'newchat';
let context = [];
const contextSize = 40; // limit number of total messages to 40 (one msg is a user input or an llm output) -- total 20 user inputs + 20 llm outputs

// when AI Assistant page loads, perform the following
document.addEventListener("DOMContentLoaded", async () => {

    // ensure the selected model (icon) matches that of the one present in the code
    selectModel(currentModel);

    // document.cookie returns a string of all the cookies in key value pairs separated by semicolons
    // e.g. "cookie1=value; cookie2=value; ..."
    const cookies = document.cookie.split("; "); // split all cookies --> cookies = list of strings, each element = one cookie

    for (const cookie of cookies) {
        const key = cookie.split("=");

        if (key[0] === "login-status") {
            // for the login-status cookie, its value is bool indicating whether the user is logged in
            if (key[1]) {
                // when the user is logged in:
                // hide the login button, show the logout button
                document.getElementById('login-button').style.display = 'none';
                document.getElementById('login-button-link').style.display = 'none';

                document.getElementById('logout-button').style.display = 'block';
                document.getElementById('logout-button-link').style.display = 'block';

            } 
            // if user is not logged in, show login button, hide logout button
            else {
                document.getElementById('login-button').style.display = 'block';
                document.getElementById('login-button-link').style.display = 'block';
                
                document.getElementById('logout-button').style.display = 'none';
                document.getElementById('logout-button-link').style.display = 'none';
            }
            break;
        }


    }

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


// posts user input to backend (using another function) and updates the UI
async function uploadText() {

    // THIS FUNCTION NEEDS TO: (some of the orders were changed in the code to make more logical sense)
    // disable uploadText button (here) until previous upload fully completes
        // update the upload button icon to be a square to indicate 'STOP' (current does nothing -- implement stop for streaming later)
    // this function first needs to empty the user input inside the input text area
    // then it needs to update the UI:
        // hide welcome greeting (if this is a new chat)
        // append user input to the children of current-chat-container
    // send post request with user input prompt and extract LLM response from the route response
        // in backend, save user input prompt into chat database (create new history file this is a new chat)
        // wait for LLM response then append response to children of current-chat-container
    // enable uploadText button (here) so next prompt can be made
        // restore upload text button icon to an up arrow to indicate completion


    const uploadTextButton = document.getElementById('upload-text-btn');
    uploadTextButton.onclick = null; // remove attached onclick function
    // updateSubmitButtonIcon('disable'); // implement this later to update the icon

    const textBox = document.getElementById("input-box");
    const userInput = textBox.value; // read and save textbox value
    // const userInput = textBox.value.trim(); // read and save textbox value
    textBox.value = ""; // clear textbox
    resizeTextBox(); // update textbox UI


    // create element to container user input
    const userTextElement = document.createElement('p');
    userTextElement.className = 'chat-text-style user-chat-margins'; // here, set the second class name (the one that sets the margins) based on whether it is a user or ai block of text
    userTextElement.textContent = userInput; // set the text as the literal user input

    // get container to hold all of the chat text (by user and LLM)
    const currentChatContainer = document.getElementById('current-chat-container');

    // hide initial greeting and show container holding all the chat text
        // although this only needs to be done if the chat is a newchat, lets do it always to be more robust
    // if (document.getElementById('loaded-chat-name').textContent == "newchat") {
        document.getElementById('initial-greeting').style.display = 'none';
        currentChatContainer.style.display = 'flex';
    // } 
    
    // add the user input element to the chat box
    currentChatContainer.appendChild(userTextElement);
    // const chatName = document.getElementById('loaded-chat-name').textContent;
    // currentChatName = chatName;

    // define post request body
    const body = JSON.stringify({
        message: userInput,
        model: currentModel,
        chatname: currentChatName,
        context: context
    });

    // generate post request with user input over the given route
    const response = await sendJsonPostRequest("/api/user/chat/inputs/", body);
    const data = await response.json();

    // append user input to the context field after the context has been sent (prevent duplaction of user input)
    context.push({role: "user", content: userInput});

    // if the current chat is a new chat, get the generated chat name
    if (currentChatName == "newchat" || currentChatName == null) {
        currentChatName = data.chatname;
    }
    // currentChatName = data.chatName;
    console.log(data.status);
    if (data.status.includes("success")) {
    
        // create element to contain LLM response
        const llmTextElement = document.createElement('div');
        llmTextElement.className = 'chat-text-style ai-chat-margins';
        const llm_response = data.chatbot_response;
        // populate the element the HTML code that was generated from the LLM output
        // llmTextElement.innerHTML = llm_response; // get the LLM response (response has been translated to HTML)
        llmTextElement.innerText = llm_response; // get the LLM response (response has been translated to HTML)

        context.push({role: "user", content: llm_response}); // store the llm output into the context

        // if the number of tokens read and evaluated is > 6000, remove the oldest prompt and response
        if (context.length > contextSize) {
            context.shift()
            context.shift()
        }

        currentChatContainer.appendChild(llmTextElement);
    }
    
    resizeTextBox(); // update textbox UI again after LLM response is displayed

    // updateSubmitButtonIcon('enable'); // implement this later to update the icon
    uploadTextButton.onclick = () => {uploadText()}; // re-attack onclick method for upload text button

}

// opens/triggers the file selection browser upon upload file button press
function triggerFilePicker() {
    document.getElementById("upload-file-input").click();
}

// uploads the literal file (incomplete, this should later post the file to the backend)
function uploadFile(inputElement) {    
    
    if (inputElement.files && inputElement.files[0]) {
        const file = inputElement.files[0];

        console.log("File was input. File name = ", file.name);


        // place code for file upload to backend here


        inputElement.value = '';
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
    }



    
}


// updates the UI to bring the new chat menu (clears chat content and hides the chat text container and shows the initial greeting)
function openNewChat() {
    // for a new chat, empty the current-chat-container except keep the loaded-chat-name element (set the textconteont of the loaded chat to be 'newchat')
    const currentChatContainer = document.getElementById('current-chat-container');
    currentChatName = 'newchat';
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


// THIS WAS USED BY uploadText() BEFORE IT WAS REFACTORED -- NO LONGER USED!
// triggers a post request with user input data (sent as a json {"message": data} )
// returns the json response.status element of the post request (should be == 'sent' for success)
// async function sendChatData(data) {

//     const dataUrlPath = "/api/user/chat/inputs/";
//     // console.log(data)
//     const response = await fetch(dataUrlPath, {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json'
//         },
//         body: JSON.stringify({ 
//             message: data, 
//             model: currentModel 
//         })
//     });

//     // the response.json contains 2 elements, status and chatbot_response, return this directly so the parent function can update the UI using LLM response
//     const result = await response.json();

//     return result;
// }

// THIS IS A SAVE OF THE OLD FUNCTION BEFORE REFACTORING -- NO LONGER USED!
// // posts user input to backend (using another function) and updates the UI
// async function uploadText() {

//     const data = textBox.value.trim(); // read the data

//     // if data is not empty, send post request (with the data) over the given path above (also logs to console and updates UI)
//     if (data !== "") {
//         // send post request with data:
//         const result = await sendChatData(data);
//         if (result.status === "sent") {
//             // console.log("Submitted Text:", data);
//             textBox.value = "";

//             const llm_response = result.chatbot_response; // the response has been translated to HTML from markdown

//             resizeTextBox();

//             // make the welcome greeting invisible (if the chat was previously empty, i.e. no chat history)
//             if (emptyChat) {
//                 emptyChat = false; // set chat as no longer being empty (there is now a history--first prompt)

//                 // remove welcome greeting
//                 const greetingHeader = document.getElementById("initial-greeting");
//                 greetingHeader.style.display = 'none';
                
//                 // enable visibility of current chat container (wrapper for user and llm texts and responses)
//                 const currentChatContainer = document.getElementById("current-chat-container");
//                 currentChatContainer.style.display = 'block';

//                 // create element to container user input
//                 const text = document.createElement('p');
//                 text.className = 'chat-text-style user-chat-margins'; // here, set the second class name (the one that sets the margins) based on whether it is a user or ai block of text
//                 text.textContent = data; // set the text as the literal user input

//                 // add the user input element to the chat box
//                 currentChatContainer.appendChild(text);

//                 // create element to contain llm response
//                 const llm_text = document.createElement('p');
//                 llm_text.className = 'chat-text-style ai-chat-margins';
//                 llm_text.innerHTML = llm_response;
//                 // translate markdown and latex into html so the effects are visible
//                 // import {marked} from 'marked';
//                 // llm_text.textContent = markdownToHtml(llm_response);
//                 // convertMarkdownToHtml(llm_response, llm_text);

//                 currentChatContainer.appendChild(llm_text);

//             }
//             else {
//                 // the chat box should already be visible here
//                 const currentChatContainer = document.getElementById("current-chat-container");

//                 // create element to container user input
//                 const text = document.createElement('p');
//                 text.className = 'chat-text-style user-chat-margins'; // here, set the second class name (the one that sets the margins) based on whether it is a user or ai block of text
//                 text.textContent = data; // set the text as the literal user input

//                 // add the user input (element) to the chat box
//                 currentChatContainer.appendChild(text);

//                 // create element to contain llm response
//                 const llm_text = document.createElement('p');
//                 llm_text.className = 'chat-text-style ai-chat-margins';
//                 llm_text.innerHTML = llm_response;
//                 // llm_text.textContent = llm_response;

//                 // convertMarkdownToHtml(llm_response, llm_text);
//                 currentChatContainer.appendChild(llm_text);

//             }
//         }
//     }
// }