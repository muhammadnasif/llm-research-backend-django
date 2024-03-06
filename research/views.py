from rest_framework.views import APIView
from rest_framework.response import Response

class DemoClass(APIView):

    def get(self, request):
        return Response("Get Response")

    def post(self, request):
        return Response("Post Response")

