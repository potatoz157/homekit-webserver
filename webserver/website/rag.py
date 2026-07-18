from langchain_core.embeddings import Embeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from werkzeug.datastructures.file_storage import FileStorage
from databaseTables import databasePath, Embeddings
from sqlalchemy import text, func
from sqlalchemy.orm import Session 
import ollama, struct

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
python_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.PYTHON, chunk_size=1500, chunk_overlap=0)
html_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.HTML, chunk_size=1500, chunk_overlap=0)


# This function takes in a FileStoage object and returns all of the chunks for the given FileStorage object.
# Makes use of langchain text splitting libraries.
def chunkifyDoc(file : FileStorage) -> list[str]:
    """
    This function checks the type of the file (i.e. the file extension from its name) and uses the appropriate language from langchain's text splitter's library.
    The literal file storage object should be passed in as the argument, which should contain both the file name and the file contents.
    """

    chunks = []
    fileName = file.name
    
    # if the file does not have a name, exit
    if not fileName:
        print("Error: Input file does not have a name!")
        return chunks

    # extension = getFileNameExtension(fileName=fileName)

    file.seek(0)
    contents = file.read().decode('utf-8') # decode converts to string
    file.seek(0)

    # for now, just perform generic text chunking through character limit:
    # print("FILE CONTENTS:", contents)
    chunks = text_splitter.split_text(contents)
    return chunks



# returns the extension from a given file name string. If any errors occur, the return value is NULL/None
def getFileNameExtension(fileName: str) -> str | None:
    """
    Parses the input file name string and returns everything after the last '.'
    If the input is blank or the string does not contain a '.' the return value is None (i.e. NULL)
    """
    if not fileName:
        return None
    
    # if no '.' is inside of the file name, then splits is a list with a single element that is equal to the file name
    splits = fileName.split('.') # split the string using '.'

    # if the split succeeded, 
    if splits[0] != fileName: 
        return splits.pop()
    
    return None


# define custom embedding class using the 'Embedding' interface from the langchain library 
# INCOMPLETE --> NEEDS INTEGRATION OF LOCAL EMBEDDING MODEL FROM OLLAMA
class CustomEmbedder(Embeddings):
    model = "nomic-embed-text"
    databasePath = None
    embedding_size = 768 # this size is based on the embedding model that is used, the current model outputs vectors of length 768

    # this is like the constructor for the class. When instantiating an object of this class, the arguments 
    # needed for the __init__ function are the arguments needed to create the new class object
    def __init__(self, databasePath : str = "user-data/myDatabase.db") -> None:
        """
        The databasePath defaults to "user-data/myDatabase.db", which is the relative path to database with a parent directory of 'webserver/website/'.
        """
        # super().__init__()
        self.databasePath = databasePath

    # helper function to convert the list[float] structure to bytes so that they can be stored in the sqlite-vec database
    # def list_to_bytes(self, vector: list[float]) -> bytes:
    #     """Converts a list of floats to a raw binary blob for sqlite-vec."""
    #     return struct.pack(f"{len(vector)}f", *vector)


    # embeds a list of strings to a list of embeddings (and embedding is a list of floats)
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embeds (generates embedding vector) for a list of input strings. Returns a list of embeddings where each embedding is a list of floats, i.e. list[list[float]]."""
        embeddings = []
        for text in texts:
            embedding = ollama.embed(model=self.model, input=text)
            embeddings.append(list(*embedding.embeddings))
        return embeddings
    
    # embeds a single string to a single embedding (a list of floats)
    def embed_query(self, text: str) -> list[float]:
        """Embeds (generates embedding vector) for a single input string. The embedding is returned as a list of floats."""
        embedding = ollama.embed(model=self.model, input=text)
        return list(*embedding.embeddings)



    # def query_similar_chunks_orm(self, db_session: Session, query_text: str, chat_id: int, limit: int = 5):
    #     """Queries sqlite-vec using your existing exact table setup via the ORM layer."""
        
    #     # 1. Generate the query vector bytes (assumes 768 dimensions for nomic)
    #     query_vector = self.embed_query(query_text)
    #     binary_query = self.list_to_bytes(query_vector)
        
    #     # 2. Safely grab the columns from the underlying __table__ structure
    #     # This completely bypasses any class attribute resolution errors
    #     vector_col = Embeddings.__table__.c.vector_embedding
    #     chat_id_col = Embeddings.__table__.c.chat_ID
        
    #     # 3. Build the distance expression using sqlite-vec's custom function
    #     distance_expr = func.vec_distance_cosine(vector_col, binary_query).label("distance")
        
    #     # 4. Query the database
    #     results = (
    #         db_session.query(Embeddings, distance_expr)
    #         .filter(chat_id_col == chat_id)
    #         .order_by(distance_expr.asc())
    #         .limit(limit)
    #         .all()
    #     )
        
    #     # 5. Package your chunks safely
    #     matched_chunks = []
    #     for embedding_obj, distance in results:
    #         # Access properties exactly as they are defined in your original Table
    #         matched_chunks.append({
    #             "text": embedding_obj.raw_text,
    #             "file_id": embedding_obj.file_ID,
    #             "distance": distance
    #         })
            
    #     return matched_chunks


    # # this takes in a list of embeddings/vectors and stores each one into the database for the given chat
    # def save_embeddings(self, db_session: Session, embeddings: list[list[float]], raw_texts: list[str], chat_id: int, file_id: int):
    #     """Saves a batch of text chunks and their embeddings into sqlite-vec."""
    #     with db_session.begin_nested(): # Safe transaction wrapper
    #         for embedding, text_content in zip(embeddings, raw_texts):
    #             # Serialize floats to bytes blob
    #             binary_vector = self.list_to_bytes(embedding)
                
    #             new_embedding = Embeddings(
    #                 vector_embedding=binary_vector,
    #                 raw_text=text_content,
    #                 chat_ID=chat_id,
    #                 file_ID=file_id
    #             )
    #             db_session.add(new_embedding)
    #         db_session.commit()


    









# testFile = 'C:/Users/ME/Downloads/github-webserver/homekit-webserver/webserver/website/globals.py'
# with open(testFile) as pythonFile:
#     contents = pythonFile.read()

# # for code files, load them as 'document' objects then use the correct language splitter by doing .split_documents(document_object)
# # for now, we will use .split_text directly for simpler implementation
# split_code = python_splitter.split_text(contents)
# # index = 0
# # for line in split_code:
# #     print(f"Line {index}:\n{line}\n")
# #     index = index + 1

# user_input = 'clean up the active users'

# embedder = CustomEmbedder(databasePath=databasePath)
# doc_embeddings = embedder.embed_documents(split_code)
# user_embedding = embedder.embed_query(user_input)



