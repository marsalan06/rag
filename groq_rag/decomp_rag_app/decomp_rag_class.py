import os
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# Configure logging for better debugging and traceability
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class DecompositionRAG:
    def __init__(self, openai_api_key, langchain_api_key, pinecone_api_key, pinecone_index_name, load=True):
        os.environ['OPENAI_API_KEY'] = openai_api_key
        os.environ['LANGCHAIN_TRACING_V2'] = 'true'
        os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
        os.environ['LANGCHAIN_API_KEY'] = langchain_api_key
        os.environ['PINECONE_API_KEY'] = pinecone_api_key
        # os.environ['PINECONE_INDEX_NAME'] = pinecone_index_name

        self.embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
        self.pinecone_index_name = pinecone_index_name
        self.vectorstore = self._load_or_create_vectorstore(load)

    def _load_or_create_vectorstore(self, load):
        # persist_directory = "chroma_db_llamaparse"

        if load:
            logging.info("Attempting to load existing vector database.")
            try:
                vs = PineconeVectorStore(
                    index_name=self.pinecone_index_name, embedding=self.embed_model)
                # vs = Chroma(persist_directory=persist_directory,
                #             embedding_function=self.embed_model)
                logging.info("Vector database loaded successfully.")
                return vs
            except FileNotFoundError:
                logging.warning(
                    "No existing vector database found. A new one will be created.")

        # logging.info(
        #     "Loading and processing PDF documents from the 'data' directory.")
        # documents = self._load_documents_from_directory("data")
        # docs = self._split_documents(documents)
        # vs = Chroma.from_documents(
        #     docs, self.embed_model, persist_directory=persist_directory)
        # vs.persist()
        # logging.info("Vector database created and persisted successfully.")
        # return vs

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
            | ChatOpenAI(model_name='gpt-4o-mini', temperature=0.0)
            | StrOutputParser()
            | (lambda x: x.strip().split("\n\n"))
        )

    def generate_subquestions(self, question, generate_queries_chain):
        return generate_queries_chain.invoke({"question": question})

    def retrieve_and_format_qa_pairs(self, questions, retriever, decomposition_prompt):
        q_a_pairs = []
        print("----questions-=-----", questions,
              type(questions), questions[:1])
        for q in questions:
            print("--------question-----", q)
            logging.info(f"Retrieving documents for sub-question: {q}")
            docs = retriever.similarity_search(q, namespace='class_IX', k=1)
            print("-----docs------")
            logging.info(f"Docs retrived: {docs}")
            context = "\n".join(doc.page_content for doc in docs)
            print("-----context-------")
            logging.info(f"Context for {q}: {context}")

            prompt_input = {
                "context": context,
                "question": q,
                "q_a_pairs": "\n\n".join(q_a_pairs)
            }
            print("-----prompt input-----")
            logging.info(f"Prompt input: {prompt_input}")

            rag_chain = (
                decomposition_prompt
                | ChatOpenAI(model_name='gpt-4o-mini', temperature=0.0)
                | StrOutputParser()
            )
            answer = rag_chain.invoke(prompt_input)
            q_a_pairs.append(self.format_qa_pair(q, answer))
        return "\n\n---\n\n".join(q_a_pairs)

    @staticmethod
    def format_qa_pair(question, answer):
        return f"Question: {question}\n\nAnswer: {answer.strip()}"

    def generate_response(self, question, q_a_pairs, final_prompt_template):
        final_rag_chain = (
            final_prompt_template
            | ChatOpenAI(model_name='gpt-4o-mini', temperature=0.0)
            | StrOutputParser()
        )
        return final_rag_chain.invoke({"context": q_a_pairs, "question": question})
