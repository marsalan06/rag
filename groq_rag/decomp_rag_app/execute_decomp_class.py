import os
import logging
from decomp_rag_class import DecompositionRAG
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    load_dotenv()
    # Initialize the DecompositionRAG class
    decomposition_rag = DecompositionRAG(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        langchain_api_key=os.getenv("LANGCHAIN_API_KEY"),
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
        pinecone_index_name=os.getenv("PINECONE_INDEX_NAME"),
        load=True
    )

    # Define the prompt for generating sub-questions
    sub_question_prompt = """
    You are a helpful study assistant who communicates in a friendly tone, when given with an input query determine whether it is a
    pleasantry or a genuine question. If the input is a pleasantry (e.g., "How are you?" or "Good morning!"), respond with a friendly and relevant reply.
    If the input is a genuine question generate 3 sub-questions strictly related to an input question.
    The goal is to break down the input into a set of sub-problems / sub-questions that can be answered in isolation.
    This output should just be a un-numbered list of sub-questions and nothing else. This is the user input: {question}"""

    sub_question_template = decomposition_rag.create_prompt_template(
        sub_question_prompt)

    # Generate sub-questions
    generate_queries_chain = decomposition_rag.generate_queries_chain(
        sub_question_template)
    question = "Explain partial diffrential equations rule?"
    subquestions = decomposition_rag.generate_subquestions(
        question, generate_queries_chain)
    print("----sub questions list=====", subquestions, type(subquestions))
    sub_ques_list = [
        q.strip() for q in subquestions[0].split('\n') if q.strip()]
    print("----sub questions----", sub_ques_list)
    # Define the prompt for decomposition
    decomposition_prompt = """
    Here is the question you need to answer:
    {question}
    Here is any available question + answer pairs:
    {q_a_pairs}
    Here is additional context relevant to the question:
    {context}
    Use only the above context and the question + answer pairs to answer the question: {question}"""

    decomposition_template = decomposition_rag.create_prompt_template(
        decomposition_prompt)

    # Retrieve and format QA pairs
    q_a_pairs = decomposition_rag.retrieve_and_format_qa_pairs(
        sub_ques_list, decomposition_rag.vectorstore, decomposition_template
    )

    # Define the final prompt template for generating a concise answer
    final_prompt = """
    You are a helpful assistant that generates a concise answer to an input question using the given context.
    Here is the question you need to answer:
    {question}
    Here is the context relevant to the question:
    {context}
    Use ONLY the above context to provide a precise and concise answer to the question: {question}.
    If the context does not contain enough information to answer the question, respond with: "couldn't find information, rephrase the question".
    Do not break character."""

    final_template = decomposition_rag.create_prompt_template(final_prompt)

    # Generate the final response
    final_response = decomposition_rag.generate_response(
        question, q_a_pairs, final_template)
    logging.info(f"Final response: {final_response}")


if __name__ == "__main__":
    main()
