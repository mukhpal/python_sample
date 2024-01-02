#  Class Components with rest 
###################################
from rest_framework.response import Response
from administrator.elements.models import Element
from administrator.elements.serializers import EleSerializer
from rest_framework import status
from myapps.app.baseViewSet import aBaseViewset
from django.conf import settings

# Create your views here.
class ElementView(aBaseViewset):
    queryset = Element.objects
    serializer_class = EleSerializer
    http_method_names = ['post','get','put','delete']    
     
    #Rest Method   
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            self.queryset.create(
                name=data['name'],
                ref_user = request.user,
                file= request.FILES['file'],
                status = 1
            )
            return Response({
                "message":"Element created successfully",
                "status":True,
                "response":"success"
            },status=status.HTTP_200_OK)
        except Exception as error:
                return Response({
                        "message": str(error),
                        "status": False,
                        "response": "fail", }, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        try:
           
            search  =   request.GET.get('search')
            if int(request.GET.get('page')) > 1:
                    offset  =  settings.offset * limit
                    limit   = settings.limit
            else:   
                offset  =  settings.offset * limit
                limit   = settings.limit

            elements    = self.queryset.filter(name__icontains=search).order_by('-id')[offset:offset+limit]
            serialized  = self.serializer_class(elements,many=True).data
            
            return Response({
                'data':serialized,
                'count':elements.count(),
                "message":"Elements fetch successfully",
                "status":True,
                "response":"success"
            },status=status.HTTP_200_OK)
        except Exception as error:
                return Response({
                        "message": str(error),
                        "status": False,
                        "response": "fail", }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            data        = request.data
            element     = self.queryset.get(id= int(self.kwargs['pk']))
            try:
                file    = request.FILES['file']
            except:
                file    = None
            try:
                element.name    = data['name']
                # element.status = data['status']
                if file:
                    element.file = file
                element.save()
            except:
                pass
            
            serialized = self.serializer_class(element).data
            return Response({
                'data':serialized,
                "message":"Element updated successfully",
                "status":True,
                "response":"success"
            },status=status.HTTP_200_OK)
        except Exception as error:
                return Response({
                        "message": str(error),
                        "status": False,
                        "response": "fail", }, status=status.HTTP_400_BAD_REQUEST)
    

