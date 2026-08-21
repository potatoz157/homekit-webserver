from werkzeug.datastructures.file_storage import FileStorage
from databaseTables import User, Chat, Message, File, Embeddings
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from typing import List, Optional
from rag import CustomEmbedder
import struct

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

# creates a new file object and saves it in the given chat for the given user
def addFileToChat(session: Session, username: str, chatName: str, flask_file : FileStorage) -> File | None:
    # uploaded files will temporarily be stored on the physical drive of the backend (change path so it uses the HDD)
    # once the file is uploaded to the database, it will be DELETED from the backend drive (the HDD)
    # for now assume the file can be read

    # read file (if contents > 0) as raw binary
    chat = getUserChat(session=session, username=username, chatName=chatName)
    if not chat:
        print("Error: Failed to locate chat, file was not added...")
        return None
    
    try:

        # path_obj = Path(filePath)
        # file_name = path_obj.name

        # with open(filePath, 'rb') as file:
        #     raw_binary_data = file.read()
        file_name = flask_file.filename
        raw_binary_data = flask_file.read()

        # the File() object being created here is the custom row object for the File database table
        new_file = File(file_name=file_name, file_binary_data=raw_binary_data)
        chat.files.append(new_file)

        session.commit()
        return new_file
    
    # except FileNotFoundError:
    #     print(f"Error: The file at path '{filePath}' could not be found.")
    #     return False
    except Exception as e:
        print(f"Error: An unexpected error occurred while reading the file: {e}")
        return None

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
def getUserChatFiles(session: Session, username: str, chatName: str) -> List[File]:
    chat = getUserChat(session=session, username=username, chatName=chatName)
    if chat:
        return chat.files
    print("Error: failed to locate chat, returning empty list of files for given chat...")
    return []

# fetches all files attached to the given user
def getAllUserFiles(session: Session, username: str) -> List[File]:
    user = getUser(session=session, username=username, full_load=True)
    if user:
        files = []
        for chat in user.chats:
            files.append(*chat.files)
        return files
    print("Error: user not found, returning empty list of files for user...")
    return []

def getAllUserChats(session: Session, username: str) -> List[Chat]:

    chats = session.scalars(
        select(Chat)
        .join(User.chats)
        .where(User.username == username)
    ).all()

    return list(chats)

def getAllUserChatNames(session: Session, username: str) -> List[str]:

    chat_names = session.scalars(
        select(Chat.chat_name)
        .join(User.chats)
        .where(User.username == username)
    ).all()

    return list(chat_names)




# def addFileEmbedding(session: Session, file_obj : File, text_chunk : str) -> Embeddings:
#     """This function generates a vector embedding for the given text chunk, creates a new row object for the embeddings table, 
#     and sets the parent file of the new row object to the given file object (i.e. new_embedding.file). The new embedding row is returned.
#     """

#     # generate the vector embedding
#     embedder = CustomEmbedder()
#     vector = embedder.embed_query(text=text_chunk)

#     # serialize the vector into a sequence of bytes (so that it can be stored in the database)
#     serialized_data = serialize_vector(vector=vector)

#     # create new row object with the embedding, raw text, and parent file
#     new_embedding = Embeddings(vector_embedding=serialized_data, raw_chunk=text_chunk)
#     new_embedding.file = file_obj

#     session.add(new_embedding)
#     session.commit()

#     return new_embedding

# def addAllEmbeddingsForFile(session: Session, file_obj : File, text_chunks : list[str]) -> list[Embeddings]:
#     """This function takes in a list of text chunks, generates embeddings for each one, creates a new embedding row for each text chunk and stores them all.
#     The parent file (new_embedding.file) is also set here using the given file object. A list of all the created embedding rows is returned"""

#     new_embeddings = []
#     embedder = CustomEmbedder()

#     for chunk in text_chunks:
#         # generate embedding, convert to sequential bytes, create new Embedding row object and add it to the database
#         serialized_data = serialize_vector(vector=embedder.embed_query(chunk))
#         new_embedding = Embeddings(
#             vector_embedding=serialized_data,
#             raw_chunk=chunk
#         )
#         new_embedding.file=file_obj
#         session.add(new_embedding)
#         new_embeddings.append(new_embedding) # save into return value

#     session.commit()

#     return new_embeddings

def addFileEmbedding(session: Session, file_obj : File, embedding : list[float], raw_text : str) -> Embeddings:
    """This function takes in a single embedding vector and stores it in the database. The parent file for the embedding is also set based on the given file.
    The new embedding row is returned."""

    embedding_bytes = serialize_vector(vector=embedding)
    new_embedding = Embeddings(vector_embedding=embedding_bytes, raw_chunk=raw_text)
    new_embedding.file = file_obj
    session.add(new_embedding)
    session.commit()

    return new_embedding

def addAllFileEmbeddings(session: Session, file_obj : File, embeddings : list[list[float]], raw_text : list[str]) -> list[Embeddings]:
    """This function takes in a list of embedding vectors and stores them in the database. The parent file for each embedding row is also set based on the given file.
    A list of all the generated/new embedding rows is returned."""

    saved = []
    index = 0
    for embedding in embeddings:
        current_text = raw_text[index]
        embedding_bytes = serialize_vector(vector=embedding)
        new_embedding = Embeddings(vector_embedding=embedding_bytes, raw_chunk=current_text)
        new_embedding.file = file_obj
        session.add(new_embedding)
        saved.append(new_embedding)
        index = index + 1
    session.commit()

    return saved

# for the given user and the given chat, fetches all of the files attached to the chat, then returns every embedding related to all of the files.
# For each file, a list of embeddings and saved. Over many files, the result is a list of a list of embeddings.
def getChatEmbeddings(session: Session, username : str, chatname : str) -> List[List[Embeddings]]:
    # the getUserChat force loads (instead of lazy load) all of the children of the Chat objects (i.e. the files and messages)
    currentChat = getUserChat(session=session, username=username, chatName=chatname)

    if not currentChat:
        return []
    
    files = currentChat.files

    embeddings = []
    for file in files:
        embeddings.append(file.embeddings)

    return embeddings


def serialize_vector(vector: List[float]) -> bytes:
    """Serializes a list of floats into a contiguous sequence of bytes with little endianness.

    Uses double-precision (8 bytes per float).
    """
    
    # 'd' represents a standard 8-byte C double (Python float)
    # Construct format string: e.g., '5d' for a list of 5 floats
    format = f"<{len(vector)}d"

    # Pack the list elements into bytes
    return struct.pack(format, *vector)

def deserialize_bytes(raw_bytes : bytes) -> List[float]:
    float_size = 8 # 8 bytes per float
    num_floats = CustomEmbedder.embedding_size # the embedding model outputs vectors of fixed length

    # if you are uncertain of the num_float value (it changes or are testing various models, uncomment the following):
    # num_floats = len(raw_bytes) // float_size # recall that '//' divides and rounds down (floor) to nearest int!

    if len(raw_bytes) % float_size != 0:
        raise ValueError(
            f"Byte length ({len(raw_bytes)}) must be a multiple of {float_size}."
        )
    
    # '<' = Little-Endian, 'd' = Double precision float (8 bytes)
    format = f"<{num_floats}d"
    return list(struct.unpack(format, raw_bytes))


# this is for the sqlite-vec extension!!!
# fetches all embeddings attached to a given user -- fully loads everything
# def getAllUserEmbeddings(session: Session, username: str) -> List[Embeddings]:

#     query = (
#         select(Embeddings)
#         .join(Embeddings.chat)
#         .join(Chat.user)
#         .where(User.username == username)
#         # FORCE EAGER LOADING: Pulls all parent chat and file info instantly in batch
#         .options(
#             selectinload(Embeddings.chat),
#             selectinload(Embeddings.file)
#         )
#     )
#     return list(session.scalars(query).all())

# this is for the sqlite-vec extension!!!
# fetches all embeddings associated to a given chat -- fully loads everything
# def getChatEmbeddings(session: Session, chatName: str) -> List[Embeddings]:
#     query = (
#         select(Embeddings)
#         .join(Embeddings.chat)
#         .where(Chat.chat_name == chatName)
#         .options(
#             selectinload(Embeddings.chat),
#             selectinload(Embeddings.file)
#         )
#     )
#     return list(session.scalars(query).all())




# The following functions are for debugging/development/testing (admin only!):

# returns a list of message objects that have the role of 'tool'. If a username is given, then the tool calls for that user are all listed.
# If a chatname is given, then the tool calls for that chat are given.
# def getToolCalls(session: Session, username : Optional[str], chatName : Optional[str]) -> List[Message]:
#     if username:
#         # if chatname is given, return simply the tool for the given chat
#         if chatName:
#             chat = getUserChat(session=session, username=username, chatName=chatName)
#             toolCalls = session.scalars(
#                 select(Message)
#                 .where(Message.role == "tool")
#                 .where(Message.chat == chat)
#             ).all()
#             return list(toolCalls)
#         # if chatname not given, return ALL messages tied to the user
#         else:
#             toolCalls = session.scalars(
#                 select(Message)
#                 .where(Message.role == "tool")
#             ).all()
#             return list(toolCalls)
#     # 
#     else: