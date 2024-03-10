from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse, FileResponse
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import Settings
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from .methods import tools
from django.core.cache import cache
import pinecone
import time
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.tools import tool
from pydantic import BaseModel, Field, constr
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

global_session = {}

index_name = 'llama-2-rag'

@csrf_exempt
def getResponse(request):
    
    question = request.GET.get('q')
    session_id = request.GET.get('session_id')
    
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


    text_field = "text"  # the metadata field that contains our text

    # initialize the vector store object
    vectorstore = Pinecone(
        index, embed_model.embed_query, text_field
    )

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



    # memory = ConversationBufferMemory(
    #     return_messages=True, memory_key="chat_history")

    # user_memory_dict = {}
    if session_id not in global_session:
        global_session[session_id] = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

    memory = global_session[session_id]

    print(memory)

    agent_chain = RunnablePassthrough.assign(
        agent_scratchpad=lambda x: format_to_openai_functions(
            x["intermediate_steps"]),
    ) | chain


    agent_executor = AgentExecutor(
        agent=agent_chain, tools=tools, verbose=True, memory=memory)

    x = agent_executor.invoke({"question": question})   

#     print(f"""
#     CHAT HISTORY: 
#           ---------------------
#           {x['chat_history']}
#             ---------------------

# """)

    response_data = {
        "status": "success",
        "message": "Response received successfully",
        "data": {
            "query" : question,
            "answer": x['output'],
        }
    }

    return JsonResponse(response_data, safe=False)




@csrf_exempt
def llmResponse(request):

    if request.GET.get('q', '') not in global_session:
        global_session[request.GET.get('q', '')] = "True"
    
    global_session[request.GET.get('q', '')] = "True"

    print(global_session)

    response_data = {
        "status": "success",
        "message": "Response received successfully",
        "data": {
            "query": request.GET.get('q', '')

        }
    }
    return JsonResponse(response_data)

