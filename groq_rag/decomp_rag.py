import os
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class DecompositionRAG:
    def __init__(self, openai_api_key, langchain_api_key, load=True):
        os.environ['OPENAI_API_KEY'] = openai_api_key
        os.environ['LANGCHAIN_TRACING_V2'] = 'true'
        os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
        os.environ['LANGCHAIN_API_KEY'] = langchain_api_key

        self.embed_model = OpenAIEmbeddings()
        self.vectorstore = self._load_or_create_vectorstore(load)

    def _load_or_create_vectorstore(self, load):
        persist_directory = "chroma_db_llamaparse"

        if load:
            logging.info("Loading existing vector database.")
            try:
                vs = Chroma(persist_directory=persist_directory,
                            embedding_function=self.embed_model)
                logging.info("Vector DB loaded successfully!")
                return vs
            except FileNotFoundError:
                logging.warning(
                    "No existing vector DB found, building a new one.")

        logging.info("Loading PDF documents from the 'data' directory.")
        documents = self._load_documents_from_directory("data")
        docs = self._split_documents(documents)

        vs = Chroma.from_documents(
            docs, self.embed_model, persist_directory=persist_directory)
        vs.persist()
        logging.info("Vector DB created and persisted successfully!")
        return vs

    @staticmethod
    def _load_documents_from_directory(directory):
        documents = []
        for file_name in os.listdir(directory):
            if file_name.endswith(".pdf"):
                logging.info(f"Loading file: {file_name}")
                pdf_loader = PyPDFLoader(os.path.join(directory, file_name))
                documents.extend(pdf_loader.load())
        return documents

    @staticmethod
    def _split_documents(documents):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700, chunk_overlap=100)
        return text_splitter.split_documents(documents)

    @staticmethod
    def create_prompt_template(template):
        return ChatPromptTemplate.from_template(template)

    def generate_queries_chain(self, prompt_template):
        return (
            prompt_template
            | ChatOpenAI(temperature=0.0)
            | StrOutputParser()
            | (lambda x: x.split("\n\n"))
        )

    def generate_subquestions(self, question, generate_queries_chain):
        return generate_queries_chain.invoke({"question": question})

    def retrieve_and_format_qa_pairs(self, questions, retriever, decomposition_prompt):
        q_a_pairs = ""
        for q in questions:
            logging.info(f"Retrieving documents for sub-question: {q}")
            docs = retriever.similarity_search(q)
            context = [doc.page_content for doc in docs]
            logging.debug(f"Context for {q}: {context}")

            prompt_input = {
                "context": "\n".join(context),
                "question": q,
                "q_a_pairs": q_a_pairs
            }

            rag_chain = (
                decomposition_prompt
                | ChatOpenAI(temperature=0.0)
                | StrOutputParser()
            )
            answer = rag_chain.invoke(prompt_input)
            q_a_pair = self.format_qa_pair(q, answer)
            q_a_pairs = q_a_pairs + "\n\n---\n\n" + q_a_pair
        return q_a_pairs

    @staticmethod
    def format_qa_pair(question, answer):
        return f"Question: {question}\n\nAnswer: {answer}\n\n"

    def generate_response(self, question, q_a_pairs, final_prompt_template):
        llm = ChatOpenAI(temperature=0)
        final_rag_chain = (
            final_prompt_template
            | llm
            | StrOutputParser()
        )
        return final_rag_chain.invoke({"context": q_a_pairs, "question": question})
