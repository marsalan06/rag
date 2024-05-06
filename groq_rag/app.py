# base package
import os
import joblib
import nest_asyncio
import markdown
import time
import re

# requirements package
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader, UnstructuredMarkdownLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.chains.retrieval import create_retrieval_chain
from llama_parse import LlamaParse


load_dotenv()
nest_asyncio.apply()

os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
groq_api_key = os.getenv('GROQ_API_KEY')
llamaparse_api_key = os.getenv('LLAMA_CLOUD_API_KEY')


def load_or_parse_data(file_paths=None, parsing_instructions=None, api_key=llamaparse_api_key):
    parsed_results = {}
    for i, file_path in enumerate(file_paths):
        data_file = f"./data/parsed_data_{os.path.basename(file_path)}.pkl"

        if os.path.exists(data_file):
            # Load the parsed data from the file
            print(f"Loading parsed data from {data_file}...")
            parsed_data = joblib.load(data_file)
        else:
            # Perform the parsing step and store the result
            if i < len(parsing_instructions):
                current_instruction = parsing_instructions[i]
            else:
                raise ValueError("Insufficient parsing instructions provided.")

            print(
                f"Parsing document: {file_path} with instruction: {current_instruction}")
            parser = LlamaParse(api_key=api_key,
                                result_type="markdown",
                                parsing_instruction=current_instruction,
                                max_timeout=5000)
            parsed_data = parser.load_data(file_path)

            # Save the parsed data to a file
            print(f"Saving the parse results of {file_path} in .pkl format...")
            joblib.dump(parsed_data, data_file)

        # Store parsed data in dictionary with the file name as key
        parsed_results[os.path.basename(file_path)] = parsed_data
    # print(parsed_results)
    return parsed_results


def create_vector_database(file_paths=None, parsing_instructions=None, load=False):
    """
    Creates or loads a vector database using document loaders and embeddings.

    Args:
    file_paths (list): List of file paths to process.
    parsing_instructions (list): Instructions for how documents should be parsed.
    load (bool): Whether to load the database if available, otherwise build.

    Returns:
    Tuple containing the Chroma vector database object and embedding model.
    """
    # Initialize embedding model
    embed_model = OpenAIEmbeddings()

    # Determine the directory for persisting/loading the database
    persist_directory = "chroma_db_llamaparse"

    if load:
        print("--34-43-43-4-34-")
        # Try to load the database from disk
        try:
            vs = Chroma(persist_directory=persist_directory,
                        embedding_function=embed_model)
            print("Vector DB loaded successfully!")
            return vs, embed_model
        except FileNotFoundError:
            print("No existing vector DB found, building a new one.")

    # Call the function to either load or parse the data
    parsed_docs = load_or_parse_data(file_paths, parsing_instructions)
    print("----parsed_docs-----", parsed_docs)
    all_docs = []

    for file_name, documents in parsed_docs.items():
        output_path = f'data/output_{file_name}.md'
        print("====output_path---", output_path)
        with open(output_path, 'w') as f:
            for doc in documents:
                f.write(doc.text + '\n')

        loader = UnstructuredMarkdownLoader(output_path)
        loaded_docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=100)
        docs = text_splitter.split_documents(loaded_docs)
        print("----docs----")
        all_docs.extend(docs)  # Append all chunks to the all_docs list
        print(
            f"Document {file_name} loaded and split into {len(docs)} chunks.")

    # Create and persist a new Chroma vector database from the chunked documents
    vs = Chroma.from_documents(
        all_docs,
        embed_model,
        persist_directory=persist_directory,
    )
    vs.persist()

    print('Vector DB created and persisted successfully !')
    return vs, embed_model


def create_chat_model(model_name, groq_api_key=groq_api_key, temperature=0, **kwargs):
    """
    Instantiates and returns a ChatGroq model object with specified parameters.

    Args:
    groq_api_key (str): The API key for model authentication.
    model_name (str): The name of the model to use.
    temperature (float, optional): Controls the randomness of the output, default is 0.
    **kwargs: Additional keyword arguments for other model parameters.

    Returns:
    ChatGroq: An instantiated ChatGroq model object.
    """
    # Assuming the ChatGroq class has been defined elsewhere in your code
    model_instance = ChatGroq(
        groq_api_key=groq_api_key, model_name=model_name, temperature=temperature, **kwargs)
    return model_instance


# prompt = ChatPromptTemplate.from_template(
#     """
#     Please evaluate the student's response based on the provided context and the question.
#     Provide feedback on accuracy, relevance, and any missing key points.

#     Context:
#     {context}

#     Question:
#     {input}

#     Student's Answer:
#     {input}

#     Based on the context and the question, how accurate and relevant is the student's response? What key points, if any, are missing or inaccurately addressed?
#     """)

prompt_static_template = """
    Please evaluate the context and question to generate 3 pairs of questions and answers, if there are multiple questions in the provided Question generate indivual responses,
    The responses should be based on the provided context and the question.
    The question and answers generated should be unique and the answers should be relevent based on the provided information, 
    as these are for we question papers

    Context:
    {context}

    Question:
    {input}

    Do well as it would be reported as your performance rating
    """


def chaining(input_question=None, input_answer=None, context=None):

    llm = create_chat_model("Llama3-8b-8192", temperature=0.7)
    document_chain = create_stuff_documents_chain(llm, prompt)
    vs, embed_model = create_vector_database(load=True)
    retriever = vs.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    start = time.process_time()
    response = retrieval_chain.invoke({"input": input_question})
    print("Response time : ", time.process_time()-start)
    print("Response Dict: ", response)
    print("Ans: ", response['answer'])
    print("Context: ", response['context'])


def parse_llm_response(content):
    """
    Parses the LLM response content to extract question and answer pairs.

    Args:
    content (str): The string content containing multiple pairs of questions and answers.

    Returns:
    list of dict: A list where each dictionary contains 'question' and 'answer' as keys.
    """
    # Regex to find all question-answer pairs
    qa_pattern = re.compile(
        r"\*\*Pair \d+\*\*\nQuestion: (.+?)\nAnswer: (.+?)(?=\n\n|\Z)", re.DOTALL)
    matches = qa_pattern.findall(content)

    # Create a list of dictionaries from the matches
    qa_list = [{'question': match[0], 'answer': match[1]} for match in matches]

    return qa_list


def query(query_text):
    vs, embed_model = create_vector_database(load=True)
    results = vs.similarity_search_with_score(query_text, k=3)
    print("-----result----")
    context_text = "\n\n---\n\n".join(
        [doc.page_content for doc, _score in results])
    print(context_text)
    prompt_template = ChatPromptTemplate.from_template(prompt_static_template)
    prompt = prompt_template.format(context=context_text, input=query_text)
    llm = create_chat_model("Llama3-8b-8192", temperature=0.5)
    # llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
    print("-----prompt sent----")
    print(prompt)
    response_text = llm.invoke(prompt)
    print("-----response from llm------")
    sources = [doc.metadata.get("id", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}"
    sources = f"Source: {sources}"
    print(response_text.content)
    print(sources)
    return response_text
