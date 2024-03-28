from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from .methods import tools
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
import json


from .methods import tools

from tqdm.auto import tqdm

global_session = {}

index_name = 'llama-2-rag'


@csrf_exempt
def chatbot_engine(request):
    try:
        data = json.loads(request.body)
        question = data.get("query")
        session_id = data.get("session_id")

        OPENAI_API_KEY = data.get("openai_api_key")
        PINECONE_API_KEY = data.get("pinecone_api_key")
        COHERE_API_KEY = data.get("cohere_api_key")

        # if not OPENAI_API_KEY or not PINECONE_API_KEY or not COHERE_API_KEY:
        # throw exception
        if not OPENAI_API_KEY or OPENAI_API_KEY == "":
            return JsonResponse({"status": "error", "message": "Provide OPENAI API KEY"}, status=400)
        if not PINECONE_API_KEY or PINECONE_API_KEY == "":
            return JsonResponse({"status": "error", "message": "Provide PINECONE API KEY"}, status=400)
        if not COHERE_API_KEY or COHERE_API_KEY == "":
            return JsonResponse({"status": "error", "message": "Provide COHERE API KEY"}, status=400)

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
                "Extract the relevant information, if not explicitly provided do not guess. Extract partial info. Always return the output you get from the function as it is. Also answer from the {context} "),
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
            global_session[session_id] = ConversationBufferMemory(
                return_messages=True, memory_key="chat_history")

        memory = global_session[session_id]

        print(memory)

        agent_chain = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_functions(
                x["intermediate_steps"]),
        ) | chain

        agent_executor = AgentExecutor(
            agent=agent_chain, tools=tools, verbose=True, memory=memory)

        llm_response = agent_executor.invoke({"question": question})


        if 'function-name' in llm_response['output']:
            function_info = json.loads(llm_response['output'])
            answer = None
        else:
            function_info = None
            answer = llm_response['output']


        response_data = {
            "success": True,
            "message": "Response received successfully",
            "function-call-status" : True if 'function-name' in llm_response['output'] else False,
            "data": {
                "query": question,
                "answer": answer
            },
            "function" : function_info
        }
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
