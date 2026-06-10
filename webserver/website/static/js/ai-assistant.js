const textBox = document.getElementById("input-box"); // this is the text box where the user puts prompts for the llm's
let cachedModels = null; // used to store and compare previously models available for use (downloaded on the server/backend)
let emptyChat = true;
let currentModel = 'deepseek-r1:14b';

// when AI Assistant page loads, perform the following
document.addEventListener("DOMContentLoaded", () => {


    // document.cookie returns a string of all the cookies in key value pairs separated by semicolons
    // e.g. "cookie1=value; cookie2=value; ..."
    cookies = document.cookie.split("; "); // split all cookies --> cookies = list of strings, each element = one cookie

    for (const cookie of cookies) {
        key = cookie.split("=");

        if (key[0] === "login-status") {
            // for the login-status cookie, its value is bool indicating whether the user is logged in
            if (key[1]) {
                // when the user is logged in:
                // hide the login button, show the logout button
                document.getElementById('login-button').style.display = 'none';
                document.getElementById('login-button-link').style.display = 'none';

                document.getElementById('logout-button').style.display = 'block';
                document.getElementById('logout-button-link').style.display = 'block';


                // the user is logged in, so we must fetch existing chat history (if any)
                


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

// runs the upload text function (posts user input to backend)
textBox.addEventListener("keydown", (event) => {
    if (event.key == "Enter") { // if keydown is enter

        // default behavior is to add a newline in a textarea
        if (!event.shiftKey) { // if shift is not being held
            event.preventDefault(); // prevent newline from being added
            uploadText();
        }
    }
});

// upon user input into textarea, update the size of the input box
textBox.addEventListener("input", function() {
    resizeTextBox();
});


// posts user input to backend (using another function) and updates the UI
async function uploadText() {

    // disable more text upload requests (from the given user) until this one has been processed
    // ---- implement disabling here ----



    const data = textBox.value.trim(); // read the data

    // if data is not empty, send post request (with the data) over the given path above (also logs to console and updates UI)
    if (data !== "") {
        // send post request with data:
        result = await sendChatData(data);
        if (result.status === "sent") {
            console.log("Submitted Text:", data);
            textBox.value = "";

            const llm_response = result.chatbot_response;

            resizeTextBox();

            // make the welcome greeting invisible (if the chat was previously empty, i.e. no chat history)
            if (emptyChat) {
                emptyChat = false; // set chat as no longer being empty (there is now a history--first prompt)

                // remove welcome greeting
                const greetingHeader = document.getElementById("initial-greeting");
                greetingHeader.style.display = 'none';
                
                // enable visibility of current chat container (wrapper for user and llm texts and responses)
                const currentChatContainer = document.getElementById("current-chat-container");
                currentChatContainer.style.display = 'block';

                // create element to container user input
                const text = document.createElement('p');
                text.className = 'chat-text-style user-chat-margins'; // here, set the second class name (the one that sets the margins) based on whether it is a user or ai block of text
                text.textContent = data; // set the text as the literal user input

                // add the user input element to the chat box
                currentChatContainer.appendChild(text);

                // create element to contain llm response
                const llm_text = document.createElement('p');
                llm_text.className = 'chat-text-style ai-chat-margins';
                llm_text.textContent = llm_response;

                currentChatContainer.appendChild(llm_text);

            }
            else {
                // the chat box should arealy be visible here
                const currentChatContainer = document.getElementById("current-chat-container");

                // create element to container user input
                const text = document.createElement('p');
                text.className = 'chat-text-style user-chat-margins'; // here, set the second class name (the one that sets the margins) based on whether it is a user or ai block of text
                text.textContent = data; // set the text as the literal user input

                // add the user input (element) to the chat box
                currentChatContainer.appendChild(text);

                // create element to contain llm response
                const llm_text = document.createElement('p');
                llm_text.className = 'chat-text-style ai-chat-margins';
                llm_text.textContent = llm_response;

                currentChatContainer.appendChild(llm_text);

            }
        }
    }


    // re-enable text upload requests here
    // ---- implement code here ----


}

// opens/triggers the file selection browser upon upload file button press
function triggerFilePicker() {
    document.getElementById("upload-file-input").click();
}

// uploads the literal file (incomplete, this should later post the file to the backend)
function uploadFile(inputElement) {    
    
    if (inputElement.files && inputElement.files[0]) {
        file = inputElement.files[0];

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
    document.getElementById("model-dropdown").classList.remove("show");
}

// this updates the input text box area/background
function resizeTextBox() {
    textBox.style.height = "auto"; // Shrinks it instantly back to 56px
    textBox.style.height = (textBox.scrollHeight - 4) + "px";  // the (-4) accounts for the expansion upon (initial) interaction
}

// triggers a post request with user input data (sent as a json {"message": data} )
// returns the json response.status element of the post request (should be == 'sent' for success)
async function sendChatData(data) {

    

    const dataUrlPath = "/api/user/chat/inputs/";
    console.log(data)
    const response = await fetch(dataUrlPath, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            message: data, 
            model: currentModel 
        })
    });

    // the response.json contains 2 elements, status and chatbot_response, return this directly so the parent function can update the UI using LLM response
    const result = await response.json();

    return result;
}



// function openLoginPage() {
    
// }