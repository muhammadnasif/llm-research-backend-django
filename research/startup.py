# in startup.py
import pandas as pd
import pinecone
import time
from langchain.embeddings.openai import OpenAIEmbeddings
import json
import os
from langchain.vectorstores import Pinecone
from langchain.tools import tool
import requests
from pydantic import BaseModel, Field, constr
import datetime
from datetime import date
from langchain.tools.render import format_tool_to_openai_function
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import MessagesPlaceholder
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.schema.runnable import RunnableMap
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from django.core.cache import cache


from .methods import tools

from tqdm.auto import tqdm

OPENAI_API_KEY = "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"
PINECONE_API_KEY = "d021beff-2603-4cfd-835c-f38c2c4ac075"
COHERE_API_KEY = "UsShXF5e8ag3p1eJbFc7XZT7t496lUbJen519VlO"

index_name = 'llama-2-rag'

def my_startup_code():
    # Your startup code here

    data = []

    # Open the JSONL file and read each line
    with open('research/testDataset.jsonl', 'r') as file:
        for line in file:
            try:
                # Parse each line as JSON
                json_data = json.loads(line)
                # Append the JSON data to the list
                data.append(json_data)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON on line {file.readline()}: {e}")

    # Create a DataFrame from the list of JSON data
    df = pd.DataFrame(data)

    pinecone.init(
        api_key=PINECONE_API_KEY,
        environment="gcp-starter"
    )

    if index_name not in pinecone.list_indexes():
        pinecone.create_index(
            index_name,
            dimension=1536,
            metric='cosine'
        )
        # wait for index to finish initialization
        while not pinecone.describe_index(index_name).status['ready']:
            time.sleep(1)

    index = pinecone.Index(index_name)

    embed_model = OpenAIEmbeddings(
        model="text-embedding-ada-002", openai_api_key=OPENAI_API_KEY)

    data = pd.DataFrame(data)  # new
    # data = dataset.to_pandas()  # this makes it easier to iterate over the dataset

    batch_size = 100

    for i in tqdm(range(0, len(data), batch_size)):
        i_end = min(len(data), i + batch_size)  # 13 100
        # get batch of data
        batch = data.iloc[i:i_end]
        # generate unique ids for each chunk
        ids = [f"{x['chunk-id']}" for i, x in batch.iterrows()]
        # get text to embed
        texts = [x['chunk'] for _, x in batch.iterrows()]
        # embed text
        embeds = embed_model.embed_documents(texts)
        # get metadata to store in Pinecone
        metadata = [
            {'text': x['chunk'],
             'title': x['title']} for i, x in batch.iterrows()
        ]
        # add to Pinecone
        print(ids, embeds, metadata)
        try:
            index.upsert(vectors=zip(ids, embeds, metadata))
            print("Inserted")
        except Exception as e:
            print("got exception" + str(e))

    print(index)

    text_field = "text"  # the metadata field that contains our text

    # initialize the vector store object
    vectorstore = Pinecone(
        index, embed_model.embed_query, text_field
    )

    retreiver = vectorstore.as_retriever()
    retreiver.get_relevant_documents(
        "what is the capital of Bangladesh ? ", k=2)

    functions = [format_tool_to_openai_function(f) for f in tools]
    model = ChatOpenAI(openai_api_key=OPENAI_API_KEY).bind(functions=functions)

    prompt_model = ChatPromptTemplate.from_messages([
        ("system",
         "Extract the relevant information, if not explicitly provided do not guess. Extract partial info. If function not executed then answer from the {context} "),
        ("human", "{question}")
    ])

    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        prompt_model,
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    chain = RunnableMap({
        "context": lambda x: vectorstore.similarity_search(x["question"], k=2),
        "agent_scratchpad": lambda x: x["agent_scratchpad"],
        "chat_history": lambda x: x["chat_history"],
        "question": lambda x: x["question"]
    }) | prompt | model | OpenAIFunctionsAgentOutputParser()
    

    print("----------------------------------------------------------------------")
    print("----------------------------------------------------------------------")
    print("----------------------------------------------------------------------")
    print("----------------------------------------------------------------------")
    print("----------------------------------------------------------------------")

    # memory = ConversationBufferMemory(
    #     return_messages=True, memory_key="chat_history")

    # agent_chain = RunnablePassthrough.assign(
    #     agent_scratchpad=lambda x: format_to_openai_functions(
    #         x["intermediate_steps"]),
    # ) | chain


    # agent_executor = AgentExecutor(
    #     agent=agent_chain, tools=tools, verbose=True, memory=memory)

    # x = agent_executor.invoke({"question": "My room is messed up. Send someone to clean it"})   

    # print(x)