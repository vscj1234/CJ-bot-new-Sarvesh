import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

load_dotenv()

# Document class
class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

# Custom TextLoader to handle encoding issues
class CustomTextLoader(TextLoader):
    def load(self):
        try:
            with open(self.file_path, encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(self.file_path, encoding='utf-8', errors='ignore') as f:
                text = f.read()
        return [Document(page_content=text, metadata={"source": self.file_path})]

def prepare_embeddings(directory):
    try:
        # Set your OpenAI API key
        oai_api_key = os.environ.get("OPENAI_API_KEY")
        if not oai_api_key:
            raise ValueError("OpenAI API key not found in environment variables.")

        # Load documents manually for .txt files
        documents = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if filename.endswith(".txt"):
                loader = CustomTextLoader(file_path)
                loaded_docs = loader.load()
                documents.extend(loaded_docs)

        if not documents:
            raise ValueError("No documents loaded from the specified directory.")

        print(f"Loaded documents: {len(documents)}")

        # Split documents into chunks
        text_splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=60)
        texts = text_splitter.split_documents(documents)

        if not texts:
            raise ValueError("Text splitting failed or resulted in empty chunks.")

        print(f"Number of text chunks: {len(texts)}")

        # Create embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=oai_api_key)
        if not embeddings:
            raise ValueError("Embeddings creation failed.")

        # Create and persist the vector store
        print("Creating Chroma vector store...")
        vectorstore = Chroma.from_documents(texts, embeddings, persist_directory="./chromabq_db")
        print("Chroma vector store created successfully.")

        print("Persisting Chroma vector store...")
        vectorstore.persist()
        print("Chroma vector store persisted successfully.")

        # Create retrievers
        vectorstore_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        keyword_retriever = BM25Retriever.from_documents(texts)
        keyword_retriever.k = 3

        # Ensemble retriever
        ensemble_retriever = EnsembleRetriever(retrievers=[vectorstore_retriever, keyword_retriever], weights=[0.3, 0.7])

        print("Embeddings created and saved successfully.")
        return ensemble_retriever

    except Exception as e:
        print(f"An error occurred during embedding preparation: {e}")
        return None
