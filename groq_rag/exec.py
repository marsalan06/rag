import os

from app import load_or_parse_data
from app import create_vector_database
# from app import create_chat_model
from app import query
files = []

pdf_folder_path = './data/'
for file in os.listdir(pdf_folder_path):
    if file.endswith('.pdf'):
        pdf_path = os.path.join(pdf_folder_path, file)
        files.append(pdf_path)
# files = ["./data/uber_10q_march_2022.pdf", "./data/lyft_10q_april_2022.pdf"]

print("Files: ", files)

instructions = [
    "Parse the grade 9th computer science book, it's for computer based queries, try to precise with it.",
    "Parse the arsalan's document it focuses on arsalan's education and experience.",
    "Parse the grade 9th chemistry book, it's for chemistry based queries, try to precise with it.",
    "Parse the cricket handbook, it has rules of cricket, consider it for cricket based queries."
]

# parsed_docs = load_or_parse_data(files, instructions)
# vs, embed_model = create_vector_database(files, instructions)
# print("-----vs---: ", vs)
# print("-----embed_model-----: ", embed_model)

# model_instance = create_chat_model("Llama3-8b-8192", temperature=0.7)
# print(model_instance)


# print(chaining("Ask about Arsalan and his qualifications, secondly what is lbw rule in cricket"))
query("Who is Arsalan and Special Purpose Computers")
