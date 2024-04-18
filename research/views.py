from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from .methods import tools,ROOM_NUMBER
import pinecone
import time
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.tools.render import format_tool_to_openai_function
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import MessagesPlaceholder
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.schema.runnable import RunnableMap
from langchain_core.messages import HumanMessage
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_community.tools import MoveFileTool
import json


from .methods import tools

from tqdm.auto import tqdm

global_session = {}
global_agent_chain = None

index_name = 'llama-2-rag'


def llm_startup():
    OPENAI_API_KEY = ""
    PINECONE_API_KEY = ""

    # throw exception
    if not OPENAI_API_KEY or OPENAI_API_KEY == "":
        return JsonResponse({"status": "error", "message": "Provide OPENAI API KEY"}, status=400)
    if not PINECONE_API_KEY or PINECONE_API_KEY == "":
        return JsonResponse({"status": "error", "message": "Provide PINECONE API KEY"}, status=400)
    
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
   
    model = ChatOpenAI(openai_api_key=OPENAI_API_KEY).bind(
        functions=functions)
    

    prompt_model = ChatPromptTemplate.from_messages([
        ("system",
            "only call the function(s) if all the parameters are procided from the users request, else start follow-up questions to clarify missing parameters. Never guess any parameters. "),
        ("human", "{question}")
    ])

    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        prompt_model,
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    chain = RunnableMap({
        "agent_scratchpad": lambda x: x["agent_scratchpad"],
        "chat_history": lambda x: x["chat_history"],
        "question": lambda x: x["question"]
    }) | prompt | model | OpenAIFunctionsAgentOutputParser()

    agent_chain = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_functions(
                x["intermediate_steps"]),
    ) | chain
    
    global global_agent_chain 
    global_agent_chain = agent_chain

    # tools1 = [MoveFileTool()]
    # functions1= [convert_to_openai_function(t) for t in tools]

    # model1 = ChatOpenAI(model="gpt-3.5-turbo",openai_api_key=OPENAI_API_KEY)
   
    # message=model.invoke([HumanMessage(content="move file foo to bar")], functions=functions1)
    # print(message)


@csrf_exempt
def chatbot_engine(request):
    try:
        data = json.loads(request.body)
        question = data.get("query")
        session_id = data.get("session_id")
        room_number = data.get("room")
        
        # memory = ConversationBufferMemory(
        #     return_messages=True, memory_key="chat_history")

        # user_memory_dict = {}
        if session_id not in global_session:
            global_session[session_id] = ConversationBufferMemory(
                return_messages=True, memory_key="chat_history")

        
        memory = global_session[session_id]

        agent_executor = AgentExecutor(
            agent=global_agent_chain, tools=tools, verbose=True, memory=memory)

        llm_response = agent_executor.invoke({"question": question})

        print(llm_response)

        if 'function-name' in llm_response['output']:
            function_info = json.loads(llm_response['output'])
            answer = None
        else:
            function_info = None
            answer = llm_response['output']

        response_data = {
            "success": True,
            "message": "Response received successfully",
            "function-call-status": True if 'function-name' in llm_response['output'] else False,
            "data": {
                "query": question,
                "answer": answer
            },
            "function": function_info
        }
        global_session[session_id].chat_memory.messages = memory.chat_memory.messages[-14:]
        # print("=========================")
        # print(global_session)
        # print("=========================")
        # print(len(memory.chat_memory.messages))
        # print("===========================")
        # print(global_session[session_id])


        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse(
            {"success": False,
             "error": {
                 "message": str(e),
                 "type": type(e).__name__ if hasattr(e, "__name__") else "Internal Server Error"
             }
             },
            status=e.http_status if hasattr(e, "http_status") else 500)


@csrf_exempt
def llmResponse(request):
    try:
        data = json.loads(request.body)
        question = data.get("question")
        session_id = data.get("session_id")

        response_data = {
            "status": "success",
            "message": "Response received successfully",
            "data": {
                "query": question,
                "session_id": session_id,
            }
        }
        return JsonResponse(response_data)
    except json.JSONDecodeError:
        # Handle JSON decoding error
        return JsonResponse({"status": "error", "message": "Invalid JSON data"}, status=400)
