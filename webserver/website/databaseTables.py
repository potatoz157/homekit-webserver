import os
from typing import List, Optional
from sqlalchemy import create_engine, ForeignKey, String, Text, BLOB, Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

class Base(DeclarativeBase):
    pass

# create table to hold users 
class User(Base):
    __tablename__ = "users"

    ID: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False) # currently unsure of hashed password sizes, allow dynamic size

    # make virtual shortcut to view all chats and files for this user 
    chats: Mapped[List["Chat"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # this establishes the link between users -> chats and chats -> files so we can shortcut from users -> files
    files: AssociationProxy[List["FileUpload"]] = association_proxy("chats", "files")

# create table to hold chats
class Chat(Base):
    __tablename__ = "chats"

    ID: Mapped[int] = mapped_column(primary_key=True)

    # ForeignKey links this chat to the user who created it
    user_ID: Mapped[int] = mapped_column(ForeignKey("users.ID"), nullable=False)

    chat_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)


    # make virtual shortcut to see all messsages, files in this chat
    messages: Mapped[List["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    files: Mapped[List["FileUpload"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    user: Mapped["User"] = relationship(back_populates="chats") # shortcut to see user for this chat

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
class FileUpload(Base):
    __tablename__ = "files"

    ID: Mapped[int] = mapped_column(primary_key=True)

    # ForeignKey links this file to the chat and user that created it (chat where file was uploaded and user that uploaded the file)
    chat_ID: Mapped[int] = mapped_column(ForeignKey("chats.ID"), nullable=False)

    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_data: Mapped[Optional[bytes]] = mapped_column(BLOB, nullable=True) # allow nullable content/data (i.e. empty raw binary)

    # Virtual Shortcuts
    chat: Mapped["Chat"] = relationship(back_populates="files")

# # create table to hold RAG file upload text embeddings
# class Embeddings(Base):
#     __tablename__ = "embeddings"

#     ID: Mapped[int] = mapped_column(primary_key=True)

#     # finish the table definition ........

engine = None

def init_db() -> Engine:
    global engine

    # get absolute path of this python file then route it to /user-data/myDatabase.db
    DB_PATH = os.path.join(os.path.dirname(__file__), "user-data/myDatabase.db") 
    
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False) # initiate the engine using sqlite (should suffice for low user count)

    Base.metadata.create_all(engine) # builds all the tables

    return engine # return the instantiated engine

# helper function
def get_engine():
    global engine
    return engine