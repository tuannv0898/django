from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import UhfRfModuleModel
from .uhf import UhfRfModuleSerializer
from .manager import modules_manager


class ManagerApi(APIView):

    def get(self, req):
        cmd = self.request.query_params.get('cmd', None)

        if cmd is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if cmd == 'get-all-uhfs':
            modules = modules_manager.get_all_modules()
            serializer = [UhfRfModuleSerializer(module).data for module in modules]

            return Response(data=serializer, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
