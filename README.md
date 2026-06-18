# homekit-webserver
Contains the software for a home webserver. Will feature options to access locally hosted LLMs', a security camera manager, and other TBD features.

Uses flask to host the local webserver and ollama to access installed models.

The webserver folder contains the main project folder, 'website', along with some testing code presented in 'testingAndLearning'

The chat.py file is a script that provides a command line interface for using a chatbot.

See requirements.txt for the list of ncessary python libraries.

## How to Setup and Run (Windows)

### 1. Clone and Enter the Project Folder
Clone the repository and navigate into the webserver directory:
```powershell
git clone https://github.com/potatoz157/homekit-webserver.git
cd homekit-webserver/webserver
```

### 2. Create the Virtual Environment
Create a clean Python environment inside the folder:
```powershell
python -m venv .venv
```

### 3. Enable Script Running (PowerShell Safety)
Windows blocks scripts by default. Choose an option below to allow the environment to turn on:

* **Option A: Temporary** - Only unlocks this single terminal window.
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
  ```
* **Option B: Permanent** - Unlocks scripts for your entire Windows account.
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

### 4. Activate and Install Dependencies
Activate your new environment and install the required project files:
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
