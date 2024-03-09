from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse, FileResponse



def getResponse(request):
    question = request.GET.get('q', '')
    return JsonResponse(question, safe=False)
    # return Response("test response")

class DemoClass(APIView):

    def get(self, request):
        return Response("Get Response")

    def post(self, request):
        return Response("Post Response")

