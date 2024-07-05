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

question = "King Bruce was from where and what did he do?"
subquestions = decomposition_rag.generate_subquestions(
    question, generate_queries_decomposition)
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

# Add the final prompt template for generating the concise answer
final_prompt_template = """You are a helpful assistant that generates a concise answer to an input question using the given context.
Here is the question you need to answer:
{question}
Here is the context relevant to the question:
{context}
Use ONLY the above context to provide a precise and concise answer to the question: {question}.
If the context does not contain enough information to answer the question, respond with: "couldn't find information, rephrase the question".
Do not break character."""

# Modify the script to call generate_response with the new template
final_response = decomposition_rag.generate_response(
    question, q_a_pairs, final_prompt_template)
print("-----final response-----", final_response)
