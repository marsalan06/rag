# Usage
from decomp_rag import DecompositionRAG

decomposition_rag = DecompositionRAG(
    openai_api_key="=---=--", langchain_api_key="------", load=True)


print(f'decomposition_rag {decomposition_rag}')

template = """You are a helpful assistant that generates 3 sub-questions related to an input question. The goal is to break down the input into a set of sub-problems / sub-questions that can be answered in isolation. Generate multiple search queries related to: {question}"""
prompt_template = decomposition_rag.create_prompt_template(template)
print("---prompt_template----", prompt_template)
generate_queries_decomposition = decomposition_rag.generate_queries(
    prompt_template)

print(f'generated sub queries: {generate_queries_decomposition}')

subquestions = decomposition_rag.generate_subquestions(
    "Describe J.J Thompson's work", generate_queries_decomposition)
print("-----sub questions----", subquestions)

sub_ques_list = subquestions[0].split('\n')
print("---ques--list--", sub_ques_list)


decomposition_prompt_template = """Here is the question you need to answer:
{question}
Here is any available background question + answer pairs:
{q_a_pairs}
Here is additional context relevant to the question:
{context}
Use the above context and any background question + answer pairs to answer the question: {question}"""

decomposition_prompt = decomposition_rag.create_prompt_template(
    decomposition_prompt_template)

q_a_pairs = decomposition_rag.retrieve_and_format_qa_pairs(
    sub_ques_list, decomposition_rag.vectorstore, decomposition_prompt)

print("-----q_a_pairs-----", q_a_pairs)


# response_template = """Here is a set of Q+A pairs:
# {context}
# Use these to synthesize an answer to the question: {question}"""
# response = decomposition_rag.generate_response(
#     "What are the main components of an LLM-powered autonomous agent system?", q_a_pairs, response_template)
# print(response)
