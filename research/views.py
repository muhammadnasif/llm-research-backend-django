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

@csrf_exempt
def getResponse(request):

    question = request.GET.get('q')
    
    memory = ConversationBufferMemory(
        return_messages=True, memory_key="chat_history")

    agent_chain = RunnablePassthrough.assign(
        agent_scratchpad=lambda x: format_to_openai_functions(
            x["intermediate_steps"]),
    ) | cache.get("chain")


    agent_executor = AgentExecutor(
        agent=agent_chain, tools=tools, verbose=True, memory=memory)

    x = agent_executor.invoke({"question": question})   


    return JsonResponse(x, safe=False)
    # return Response("test response")




def llmResponse(request):
    question = request.POST['question']

    print(request.POST)

    return JsonResponse(question)

