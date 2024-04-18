from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response.pprint_utils import pprint_response
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
import os
from dotenv import load_dotenv
load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
PERSISTENT_DIR = "vector_store"

# check if storage doesnt exists create it, else get index from it
if not os.path.exists(PERSISTENT_DIR):
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents, show_progress=True)
    index.storage_context.persist(persist_dir=PERSISTENT_DIR)
else:
    storage_context = StorageContext.from_defaults(persist_dir=PERSISTENT_DIR)
    index = load_index_from_storage(storage_context)

# documents = SimpleDirectoryReader("data").load_data()

# print(documents)

# index = VectorStoreIndex.from_documents(documents, show_progress=True)

# print(index)

######## simple reteriver with less control ####
# # query_engine = index.as_query_engine()  # retriver

# # response = query_engine.query("What is the position of umpires")


# print("-------response----")
# pprint_response(response, show_source=True)
# print(response)

# vector index retriver with top result and index control
retriever = VectorIndexRetriever(index=index, similarity_top_k=4)
# optional postprocessor to set min similarity context
postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)
# new query engine, node_postprocessor is optional
query_engine = RetrieverQueryEngine(
    retriever=retriever, node_postprocessors=[postprocessor])
# query response
response = query_engine.query("what is a chemical process?")

pprint_response(response, show_source=True)
