import os
from typing import List, Optional
from sqlalchemy import create_engine, ForeignKey, String, Text, BLOB, Engine, text, event, Column, Integer, Table, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from pathlib import Path

class Base(DeclarativeBase):
    pass

engine = None


# these are for the sqlite-vec extension!!!
# virtual_metadata = MetaData()
# embeddings_table = Table(
#     "embeddings",
#     virtual_metadata,
#     Column("ID", Integer, primary_key=True),
#     Column("vector_embedding", Text, nullable=False),
#     Column("raw_text", Text, nullable=True),
#     Column("chat_ID", Integer),
#     Column("file_ID", Integer)
#     # prefixes=["VIRTUAL USING vec0"]  # Combines custom extensions without breaking the dialect validator
# )




# create table to hold users 
class User(Base):
    __tablename__ = "users"

    ID: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False) # currently unsure of hashed password sizes, allow dynamic size

    # make virtual shortcut to view all chats and files for this user 
    chats: Mapped[List["Chat"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # this establishes the link between users -> chats and chats -> files so we can shortcut from users -> files
    # files: AssociationProxy[List["File"]] = association_proxy("chats", "files")

# create table to hold chats
class Chat(Base):
    __tablename__ = "chats"

    ID: Mapped[int] = mapped_column(primary_key=True)

    # ForeignKey links this chat to the user who created it
    user_ID: Mapped[int] = mapped_column(ForeignKey("users.ID"), nullable=False)

    model: Mapped[str] = mapped_column(Text, nullable=True) # will hold the model the chat was made with
    chat_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)


    # make virtual shortcut to see all messsages, files in this chat
    user: Mapped["User"] = relationship(back_populates="chats") # shortcut to see user for this chat
    # messages: Mapped[List["Message"]] = relationship(back_populates="chats", cascade="all, delete-orphan", order_by="Message.ID")
    messages: Mapped[List["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    files: Mapped[List["File"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    
    # this is for the sqlite-vec extension
    # embeddings: Mapped[List["Embeddings"]] = relationship(
    #     primaryjoin="Chat.ID == foreign(Embeddings.chat_ID)",
    #     back_populates="chat", 
    #     cascade="all, delete-orphan", 
    #     order_by="Embeddings.ID"
    # )

# create table to hold chat messages
class Message(Base):
    __tablename__ = "messages"

    ID: Mapped[int] = mapped_column(primary_key=True)

    # ForeignKey links this message to the chat that created it
    chat_ID: Mapped[int] = mapped_column(ForeignKey("chats.ID"), nullable=False)

    role: Mapped[str] = mapped_column(String(32), nullable=False)
    contents: Mapped[str] = mapped_column(Text, nullable=True) # allow empty content for messages by user and LLM response

    # make virtual shortcut to see the parent/chat for this message
    chat: Mapped["Chat"] = relationship(back_populates="messages")

# create table to hold raw uploaded file content
class File(Base):
    __tablename__ = "files"

    ID: Mapped[int] = mapped_column(primary_key=True)

    # ForeignKey links this file to the chat and user that created it (chat where file was uploaded and user that uploaded the file)
    chat_ID: Mapped[int] = mapped_column(ForeignKey("chats.ID"), nullable=False)

    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_binary_data: Mapped[Optional[bytes]] = mapped_column(BLOB, nullable=True) # allow nullable content/data (i.e. empty raw binary)
    # timestamp: Mapped[str] = mapped_column(Text, nullable=False) # timestampt of file creation

    # Virtual Shortcuts
    chat: Mapped["Chat"] = relationship(back_populates="files")
    embeddings : Mapped[List["Embeddings"]] = relationship(back_populates="file", cascade="all, delete-orphan")

    # this is for the sqlite-vec extension
    # embeddings : Mapped[List["Embeddings"]] = relationship(
    #     primaryjoin="File.ID == foreign(Embeddings.file_ID)",
    #     back_populates="file",
    #     cascade="all, delete-orphan"
    # )

# this is for the sqlite-vec extension!!!!
# create table to hold RAG file upload text embeddings --> this is skipped by 
# the create_all(engine) function because it is defined as "virtual"
# - Must manually create this table
# class Embeddings(Base):
#     __table__ = embeddings_table
#     # __tablename__ = "embeddings"

#     # __table_args__ = {"prefixes": ["Virtual"], "sqlite_with": "vec0"}

#     # ID = Column(Integer, primary_key=True)
#     # vector_embedding = Column(Text, nullable=False)
#     # raw_text = Column(Text, nullable=True)
#     # chat_ID = Column(Integer)
#     # file_ID = Column(Integer)

#     # define shortcuts/relationships
#     chat = relationship("Chat", primaryjoin="Chat.ID == foreign(Embeddings.chat_ID)", back_populates="embeddings")
#     file = relationship("File", primaryjoin="File.ID == foreign(Embeddings.file_ID)", back_populates="embeddings")


#     # ID : Mapped[int] = mapped_column(primary_key=True)
#     # vector_embedding: Mapped[Text] = mapped_column(nullable=False)
#     # raw_text : Mapped[Text] = mapped_column(nullable=True) # if the embedding is for an IMAGE, then raw text = NULL

#     # # foreign key not suppored in virtual table --> ????
#     # chat_ID : Mapped[int] = mapped_column(nullable=False) # the associated CHAT ID for the given embedding
#     # file_ID : Mapped[int] = mapped_column(nullable=False) # the associated FILE ID for the given embedding


#     # chat : Mapped["Chat"] = relationship(primaryjoin="Chat.ID == foreign(Embeddings.chat_ID)", back_populates="embeddings")
#     # file : Mapped["File"] = relationship(primaryjoin="File.ID == foreign(Embeddings.file_ID)", back_populates="embeddings")


# this is for pure sqlite (no extension)
class Embeddings(Base):
    __tablename__ = "embeddings"

    # primary key
    ID: Mapped[int] = mapped_column(primary_key=True)
    # ForeignKey links this embedding to its parent file
    file_ID: Mapped[int] = mapped_column(ForeignKey("files.ID"), nullable=False)

    # contents (other columns)
    vector_embedding: Mapped[bytes] = mapped_column(nullable=False)
    raw_chunk: Mapped[str] = mapped_column(Text, nullable=True) # allow empty content for messages by user and LLM response

    # define bidirectional relationship with the files
    file : Mapped["File"] = relationship(back_populates="embeddings") # this points to the specific parent file of the embedding





databasePath = "user-data/myDatabase.db" # relative path to database, parent directory is 'webserver/website/'
def init_db() -> Engine:
    global engine

    # dropAll() # this is for testing only

    # get absolute path of this python file then route it to /user-data/myDatabase.db

    # database path is 'webserver/website/user-data/myDatabase.db'
    # this file is located at 'webserver/website/src/databaseTables.py
    DB_PATH = Path(__file__).parent.parent / "user-data" / "myDatabase.db" # go to /website/ dir then route to database
    # DB_PATH = os.path.join(os.path.dirname(__file__), databasePath) # OLD RELATIVE DIRECTORY
    
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False) # initiate the engine using sqlite (should suffice for low user count)

    # this is for the sqlite-vec extension!!!
    # once a connection is made on the engine, ensure the sqlite_vec extension is loaded
    # @event.listens_for(engine, "connect")
    # def load_sqlite_extensions(dbapi_connection, connection_record):
    #     if isinstance(dbapi_connection, sqlite3.Connection):
    #         dbapi_connection.enable_load_extension(True)
    #         sqlite_vec.load(dbapi_connection)
    #         dbapi_connection.enable_load_extension(False)



    Base.metadata.create_all(engine) # builds all the tables

    # this is for the sqlite-vec extension!!!!
    # create the virtual table (for the embeddings)
    # with engine.connect() as conn:
    #     # REPLACE FLOAT[4096] WITH THE DIMENSION MADE BY THE CHOSEN EMBEDDING MODEL!!!!!!!
    #     conn.execute(text(
    #         """
    #         CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(
    #             ID INTEGER PRIMARY KEY,
    #             vector_embedding FLOAT[768],
    #             raw_text TEXT,
    #             +chat_ID INTEGER,
    #             +file_ID INTEGER
    #         );
    #     """))
    #     conn.commit()

    return engine # return the instantiated engine


def dropAll():
    """Drops all tables associated with the Declarative Base metadata.

    Extracts the bind (engine) directly from the active session.
    """

    # 1. Get the engine bound to the session
    engine = get_engine()
    if engine:
        # 2. Drop all tables defined in your Base metadata
        Base.metadata.drop_all(bind=engine)


# helper function
def get_engine():
    global engine
    return engine