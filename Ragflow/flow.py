import os
import logging
from flask import Flask, request, jsonify, render_template, session
from langchain.chains import LLMChain
from flask_session import Session
from langchain.chains.base import Chain
from langchain_core.callbacks.manager import CallbackManagerForChainRun
from langchain_chroma import Chroma
from langchain_openai import OpenAI
from langchain.output_parsers import YamlOutputParser
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.base_language import BaseLanguageModel
from langchain_core.callbacks import Callbacks
from typing import Any, Optional, Dict
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings


# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Load environment variables
load_dotenv()

# Set your OpenAI API key
oai_api_key = os.environ.get("OPENAI_API_KEY")

# Initialize the OpenAI embedding function
embeddings = OpenAIEmbeddings(api_key=oai_api_key)

# Load the vector store from disk with the embedding function
vectorstore = Chroma(
    persist_directory="C:/Users/user/Downloads/OPEN AI CHATBOT/chroma_db",
    embedding_function=embeddings
)

# Initialize the OpenAI LLM
llm = OpenAI(api_key=oai_api_key)

@app.route('/')
def home():
    return render_template('base.html')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define a custom prompt template for the RAG chain
rag_prompt_template = """You are June, an AI assistant for CloudJune , a cloud service provider comapny. Use the following pieces of context to answer the question at the end. If the question is not related to CloudJune company or it's products or services or if you don't know the answer, politely explain that you can only provide information about CloudJune..

Context: {context}

Question: {question}
Answer:"""
RAG_PROMPT = PromptTemplate(
    template=rag_prompt_template,
    input_variables=["context", "question"]
)

# Create the LLM chain
llm_chain = LLMChain(llm=llm, prompt=RAG_PROMPT)

logger.debug("Initializing rag_chain")
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs={
        "prompt": RAG_PROMPT,
    }
)
logger.debug("rag_chain initialized successfully")

# Define the prompts (using the COSTAR framework as per your example)
REPHRASING_PROMPT_TEMPLATE = """
# Context #
# Objective #
Evaluate the given user question and determine if it requires reshaping according to chat history to provide necessary context and information for answering, or if it can be processed as it is.

#########

# Style #
The response should be clear, concise, and in the form of a straightforward decision - either "Reshape required" or "No reshaping required".

#########

# Tone #
Professional and analytical.

#########

# Audience #
The audience is the internal system components that will act on the decision.

#########

# Response #
If the question should be rephrased return response in YAML file format:
```
    result: true
```
otherwise return in YAML file format:
```
    result: false
```

##################

# Chat History #
{chat_history}

#########

# User question #
{question}

#########

# Your Decision in YAML format # 
"""
REPHRASING_PROMPT = PromptTemplate(
    template=REPHRASING_PROMPT_TEMPLATE,
    input_variables=["chat_history", "question"]
)

STANDALONE_PROMPT_TEMPLATE = """

# Context #
This is part of a conversational AI system that determines whether to use a retrieval-augmented generator (RAG) or a chat model to answer user questions. 

#########

# Objective #
Take the original user question and chat history, and generate a new standalone question that can be understood and answered without relying on additional external information.

#########

# Style #
The reshaped standalone question should be clear, concise, and self-contained, while maintaining the intent and meaning of the original query.

#########

# Tone #
Neutral and focused on accurately capturing the essence of the original question.

#########

# Audience #
The audience is the internal system components that will act on the decision.

#########

# Response #
If the original question requires reshaping, provide a new reshaped standalone question that includes all necessary context and information to be self-contained.
If no reshaping is required, simply output the original question as is.

##################

# Chat History #
{chat_history}

#########

# User original question #
{question}

#########

# The new Standalone question #
"""
STANDALONE_PROMPT = PromptTemplate(
    template=STANDALONE_PROMPT_TEMPLATE,
    input_variables=["chat_history", "question"]
)

ROUTER_DECISION_PROMPT_TEMPLATE = """
# Context #
This is part of a conversational AI system that determines whether to use a retrieval-augmented generator (RAG) or a chat model to answer user questions. 

#########

# Objective #
Evaluate the given question and decide whether the RAG application is required to provide a comprehensive answer by retrieving relevant information from a knowledge base, or if the chat model's inherent knowledge is sufficient to generate an appropriate response.

#########

# Style #
The response should be a clear and direct decision, stated concisely.

#########

# Tone #
Analytical and objective.

#########

# Audience #
The audience is the internal system components that will act on the decision.

#########

# Response #
If the question should be rephrased return response in YAML file format:
```
    result: true
```
otherwise return in YAML file format:
```
    result: false
```

##################

# Chat History #
{chat_history}

#########

# User question #
{question}

#########

# Your Decision in YAML format #
"""
ROUTER_DECISION_PROMPT = PromptTemplate(
    template=ROUTER_DECISION_PROMPT_TEMPLATE,
    input_variables=["chat_history", "question"]
)

# Define the pydantic model for YAML output parsing
class ResultYAML(BaseModel):
    result: bool

class ConversationalRagChain(Chain):
    """Chain that encapsulates RAG application enabling natural conversations."""
    rag_chain: Chain
    rephrasing_chain: LLMChain
    standalone_question_chain: LLMChain
    router_decision_chain: LLMChain
    yaml_output_parser: YamlOutputParser
    
    # input/output parameters
    input_key: str = "query"  
    chat_history_key: str = "chat_history" 
    output_key: str = "result"

    @property
    def input_keys(self) -> list[str]:
        """Input keys."""
        return [self.input_key, self.chat_history_key]

    @property
    def output_keys(self) -> list[str]:
        """Output keys."""
        return [self.output_key]

    @property
    def _chain_type(self) -> str:
        """Return the chain type."""
        return "ConversationalRagChain"

    @classmethod
    def from_llm(
        cls,
        rag_chain: Chain,
        llm: BaseLanguageModel,
        callbacks: Optional[Callbacks] = None,
        **kwargs: Any,
    ) -> "ConversationalRagChain":
        """Initialize from LLM."""
        
        # Create the rephrasing chain
        rephrasing_chain = LLMChain(llm=llm, prompt=REPHRASING_PROMPT, callbacks=callbacks)
        
        # Create the standalone question chain
        standalone_question_chain = LLMChain(llm=llm, prompt=STANDALONE_PROMPT, callbacks=callbacks)
        
        # Create the router decision chain
        router_decision_chain = LLMChain(llm=llm, prompt=ROUTER_DECISION_PROMPT, callbacks=callbacks)
        
        # Return the instantiated ConversationalRagChain
        return cls(
            rag_chain=rag_chain,
            rephrasing_chain=rephrasing_chain,
            standalone_question_chain=standalone_question_chain,
            router_decision_chain=router_decision_chain,
            yaml_output_parser=YamlOutputParser(pydantic_object=ResultYAML),
            callbacks=callbacks,
            **kwargs,
        )

    def _call(self, inputs: Dict[str, Any], run_manager: Optional[CallbackManagerForChainRun] = None) -> Dict[str, Any]:
        """Call the chain."""
        chat_history = inputs[self.chat_history_key]
        question = inputs[self.input_key]
        answer = None

        logger.debug(f"ConversationalRagChain received question: {question}")

        try:
            if not chat_history:
                # If chat history is empty, directly use the RAG chain.
                answer = self.rag_chain.invoke({"query": question})['result'].strip()
            else:
                # Evaluate if rephrasing is needed.
                rephrasing_response = self.rephrasing_chain.invoke({"chat_history": chat_history, "question": question})['text'].strip()
                rephrasing_decision = self.yaml_output_parser.parse(rephrasing_response)

                if rephrasing_decision.result:
                    # Generate a standalone question if needed.
                    standalone_question = self.standalone_question_chain.invoke({"chat_history": chat_history, "question": question})['text'].strip()
                    question = standalone_question  # Update the question to standalone.

                # Check if there are relevant documents.
                docs = self.rag_chain._get_docs(question, run_manager=run_manager)
                if docs:
                    # Use the RAG model if documents are found.
                    answer = self.rag_chain.invoke({"query": question})['result'].strip()
                else:
                    # Make a routing decision based on internal logic.
                    routing_response = self.router_decision_chain.invoke({"chat_history": chat_history, "question": question})['text'].strip()
                    routing_decision = self.yaml_output_parser.parse(routing_response)

                    if routing_decision.result:
                        # Use the chat model.
                        answer = self.llm.invoke(chat_history + [{"role": "user", "content": question}],).content
                    else:
                        # Fallback to RAG if routing suggests so.
                        answer = self.rag_chain.invoke({"query": question})['result'].strip()
        except Exception as e:
            logger.error(f"Error in ConversationalRagChain: {str(e)}", exc_info=True)
            answer = f"An error occurred while processing your request: {str(e)}"

        logger.debug(f"ConversationalRagChain produced answer: {answer}")
        return {self.output_key: answer}



@app.route('/query', methods=['POST'])
def query():
    logger.debug("Received a query request")
    data = request.json
    chat_history = data.get('chat_history', [])
    question = data.get('question', '')

    logger.debug(f"Question: {question}")
    logger.debug(f"Chat history: {chat_history}")

    try:
        logger.debug("Initializing ConversationalRagChain")
        conversational_chain = ConversationalRagChain.from_llm(
            rag_chain=rag_chain,
            llm=llm
        )

        logger.debug("Calling conversational_chain")
        result = conversational_chain({"query": question, "chat_history": chat_history})
        logger.debug(f"Result: {result}")

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
