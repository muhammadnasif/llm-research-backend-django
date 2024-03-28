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
from operator import itemgetter


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
             "Extract the relevant information, if not explicitly provided do not guess. Extract partial info. Answer from the {context}' and take user information from the '{chat_history}'"),
            ("human", "{question}")
        ])

        prompt = ChatPromptTemplate.from_messages([ 
            # MessagesPlaceholder(variable_name="chat_history"),
            prompt_model,
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        chain = RunnableMap({
            "context": lambda x: vectorstore.similarity_search(x["question"], k=2),
            "agent_scratchpad": lambda x: x["agent_scratchpad"],
            "chat_history": lambda x: x["chat_history"],
            "question": lambda x: x["question"]
        }) | prompt | model | OpenAIFunctionsAgentOutputParser()

        
        # memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True,output_key='chat_history')

        # memory = ConversationBufferMemory(
        #     return_messages=True, memory_key="chat_history")

        # user_memory_dict = {}
        if session_id not in global_session:
            global_session[session_id] = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

        memory = global_session[session_id]

        agent_chain = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_functions(x["intermediate_steps"]),
                chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("chat_history")
        ) | chain

        agent_executor = AgentExecutor(
            agent=agent_chain, tools=tools, verbose=True, return_intermediate_steps=True)

        llm_response = agent_executor.invoke({"question": question})

        inputs = {"question": question}
        global_session[session_id].save_context(inputs, {"output": llm_response['output']})

        print(memory.load_memory_variables({}))
        if len(llm_response['intermediate_steps'] ) > 0:
            function_infos = {
                "function-name" : json.loads(llm_response['intermediate_steps'][0][0].json())['tool'],
                "parameters" : json.loads(llm_response['intermediate_steps'][0][0].json())['tool_input']
            }
        else:
            function_infos = None
        

        print(global_session)


        response_data = {
            "success": True,
            "message": "Response received successfully",
            "function-call-status" : 1 if function_infos else 0,
            "data": {
                "query": question,
                "answer": None if function_infos else llm_response['output'],
            },
            "function" : function_infos
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
