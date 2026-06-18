from pathlib import Path
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from databaseTables import User, Chat, Message, FileUpload

# creates a new user object, returns True on success and False on failure (i.e. if username already exists)
def addUser(session: Session, username: str, password: str) -> tuple[bool, Optional[User]]:
    # first check if username already exists
    username_exists = session.scalars(select(User.ID).where(User.username == username)).first()

    if username_exists:
        print("Error: failed to add user, the following username already exists: ", username)
        return False, None

    hashedPassword = password # APPLY HASHING FUNCTION HERE

    new_user = User(username=username, password=hashedPassword)
    session.add(new_user)
    session.commit()
    return True, new_user

# creates a new chat object for the given user
def addUserChat(session: Session, username: str, chatName: str, model='qwen2.5:14b-instruct') -> tuple[bool, Optional[Chat]]:
    # get user from database then append chat to user.chats
    stmt = select(User).where(User.username == username) # build the query

    # run the query
    # by default, select returns tuples, i.e. (username, password, ...), but .scalars() strips 
    # away the tuple and converts it into the Python object directly i.e. Users()
    user = session.scalars(stmt).first()
    new_chat = None
    if (user):
        new_chat = Chat(chat_name=chatName, model=model)
        user.chats.append(new_chat)
        session.commit()
        return True, new_chat
    
    print("Failed to locate user, chat not added...")
    return False, new_chat

# creates a new message object for the given chat for the given user
def addChatMsg(session: Session, username: str, chatName: str, role: str, contents: str) -> tuple[bool, Optional[Message]]:
    # get the specific chat for the specific user and append a new message
    chat = getUserChat(session=session, username=username, chatName=chatName)
    new_msg = None
    if chat:
        new_msg= Message(role=role, contents=contents)
        chat.messages.append(new_msg)
        session.commit()
        return True, new_msg

    print("Error: Failed to locate chat, message was not added...")
    return False, new_msg

# creates a new fileupload object for the given chat for the given user
def addFileToChat(session: Session, username: str, chatName: str, filePath) -> bool:
    # uploaded files will temporarily be stored on the physical drive of the backend (change path so it uses the HDD)
    # once the file is uploaded to the database, it will be DELETED from the backend drive (the HDD)
    # for now assume the file can be read

    # read file (if contents > 0) as raw binary
    chat = getUserChat(session=session, username=username, chatName=chatName)
    if not chat:
        print("Error: Failed to locate chat, file was not added...")
        return False
    
    try:
        path_obj = Path(filePath)
        file_name = path_obj.name

        with open(filePath, 'rb') as file:
            raw_binary_data = file.read()

        new_file = FileUpload(file_name=file_name, file_data=raw_binary_data)
        chat.files.append(new_file)

        session.commit()
        return True
    
    except FileNotFoundError:
        print(f"Error: The file at path '{filePath}' could not be found.")
        return False
    except Exception as e:
        print(f"Error: An unexpected error occurred while reading the file: {e}")
        return False

# fetches the user based on the given username, full_load determines if user.chats and user.files are also fully loaded
def getUser(session: Session, username: str, full_load: bool) -> Optional[User]:
    """
    Fetches a user based on their username. 
    If full_load is True, it eagerly loads all of their chats and files.
    """
    # Build the base statement
    stmt = select(User).where(User.username == username)
    
    # If full_load is requested, add optimization strategies to the query
    if full_load:
        stmt = stmt.options(
            # Eagerly load chats, and eagerly load the files attached to those chats
            selectinload(User.chats).selectinload(Chat.files)
        )
        
    # Execute the query and return the User object (or None if not found)
    user = session.scalars(stmt).first()
    if not user:
        print("Error: failed to find user...")

    return user

# fetches a specific chat of a given user
def getUserChat(session: Session, username: str, chatName: str) -> Optional[Chat]:
    stmt = (
        select(Chat)
        .join(Chat.user)
        .where(User.username == username, Chat.chat_name == chatName)
        .options(selectinload(Chat.messages),
                 selectinload(Chat.files)
        )
    )

    chat = session.scalars(stmt).first()
    if not chat:
        print("Error: failed to locate chat for given user...")
    return chat

# fetches all messages of a given chat
def getChatMsgs(session: Session, username: str, chatName: str) -> List[Message]:
    chat = getUserChat(session=session, username=username, chatName=chatName)
    if chat:
        return chat.messages
    print("Error: chat not found, returning empty list of messages...")
    return []

# fetches all the files attached to the given chat for the given user
def getUserChatFiles(session: Session, username: str, chatName: str) -> List[FileUpload]:
    chat = getUserChat(session=session, username=username, chatName=chatName)
    if chat:
        return chat.files
    print("Error: failed to locate chat, returning empty list of files for given chat...")
    return []

# fetches all files attached to the given user
def getAllUserFiles(session: Session, username: str) -> List[FileUpload]:
    user = getUser(session=session, username=username, full_load=True)
    if user:
        return user.files
    print("Error: user not found, returning empty list of files for user...")
    return []

def getAllUserChatNames(session: Session, username: str) -> List[str]:

    chat_names = session.scalars(
        select(Chat.chat_name)
        .join(User.chats)
        .where(User.username == username)
    ).all()

    return list(chat_names)