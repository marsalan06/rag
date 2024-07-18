import os
from langchain.chains.api.base import APIChain
from langchain_openai import OpenAI
from langchain.chains.api import news_docs

os.environ['OPENAI_API_KEY'] = "sk-proj-------"
os.environ['NEWS_API_KEY'] = '------'
news_api_key = os.getenv('NEWS_API_KEY')


def main(question: str):
    llm = OpenAI(temperature=0.5)
    chain = APIChain.from_llm_and_api_docs(llm=llm, api_docs=news_docs.NEWS_DOCS,
                                           verbose=True, headers={'x-api-key': news_api_key},
                                           limit_to_domains=['https://newsapi.org'])

    result = chain.invoke(question)

    return result


if __name__ == "__main__":
    question = "What is the update about Donald Trump?"
    res = main(question)

    print(res)
