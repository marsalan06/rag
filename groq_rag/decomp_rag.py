import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain.load import dumps, loads
from operator import itemgetter


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
            print("---load---")
            try:
                vs = Chroma(persist_directory=persist_directory,
                            embedding_function=self.embed_model)
                print("Vector DB loaded successfully!")
                print("----loaded----")
                return vs
            except FileNotFoundError:
                print("No existing vector DB found, building a new one.")

        # Load PDF documents from the "data" directory
        documents = []
        for file_name in os.listdir("data"):
            if file_name.endswith(".pdf"):
                print("=====file name----", file_name)
                pdf_loader = PyPDFLoader(os.path.join("data", file_name))
                documents.extend(pdf_loader.load())
            print("----documents----", documents)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        print("----docs----", docs)

        # Create and persist a new Chroma vector database from the chunked documents
        vs = Chroma.from_documents(
            docs, self.embed_model, persist_directory=persist_directory)
        vs.persist()
        print("00000vs-0---", vs)
        print('Vector DB created and persisted successfully!')
        return vs

    def create_prompt_template(self, template):
        return ChatPromptTemplate.from_template(template)

    def generate_queries(self, prompt_template):
        return (
            prompt_template
            | ChatOpenAI(temperature=0.0)
            | StrOutputParser()
            | (lambda x: x.split("\n\n"))
        )

    def generate_subquestions(self, question, generate_queries_decomposition):
        return generate_queries_decomposition.invoke({"question": question})

    def retrieve_and_format_qa_pairs(self, questions, retriever, decomposition_prompt):
        q_a_pairs = ""
        for q in questions:
            print("-----q-----", q)
            # Retrieve documents for the sub-question
            docs = retriever.similarity_search(q)
            # try this
            #  retriever.as_retriever(search_type=search_type, search_kwargs={"k": 3})
            print("---docs----", docs)
            context = [doc.page_content for doc in docs]
            print("----context----", context)
            # Format the context for the decomposition prompt
            prompt_input = {
                "context": "\n".join(context),
                "question": q,
                "q_a_pairs": q_a_pairs
            }
            print("-----prompt_input----", prompt_input)

            rag_chain = (
                decomposition_prompt
                | ChatOpenAI(temperature=0.0)
                | StrOutputParser()
            )
            answer = rag_chain.invoke(prompt_input)
            q_a_pair = self.format_qa_pair(q, answer)
            print("-----q/a pairs text---", q_a_pairs)
            q_a_pairs = q_a_pairs + "\n\n---\n\n" + q_a_pair

        return q_a_pairs

    @staticmethod
    def format_qa_pair(question, answer):
        return f"Question: {question}\n\nAnswer: {answer}\n\n"

    def generate_response(self, question, q_a_pairs, final_prompt_template):
        prompt = ChatPromptTemplate.from_template(final_prompt_template)
        llm = ChatOpenAI(temperature=0)
        final_rag_chain = (
            prompt
            | llm
            | StrOutputParser()
        )
        return final_rag_chain.invoke({"context": q_a_pairs, "question": question})
