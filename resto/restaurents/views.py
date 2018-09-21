from django.contrib.auth.models import User
from django.views.generic import ListView
from django.http import Http404
from rest_framework import routers, serializers, viewsets, status, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from restaurents.models import Restaurant, Visit, Comment
from restaurents.serializers import (
    RestaurantSerializer, VisitSerializer, CommentSerializer, RestaurantVoteSerializer,
    UserSerializer
)

# HTML Views

class RestaurantListView(ListView):
    """
    Default landing page served by Django.
    It will render a basic html page as a landing page.
    """
    context_object_name = 'restaurant_list'
    queryset = Restaurant.objects.filter(active=True)[:50]
    template_name = "index.html"

# API Views

class CurrentUserView(APIView):
    """
    Return the current logged in user
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    API view that display/manage the list of Users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class RestaurantViewSet(viewsets.ModelViewSet):
    """
    API view that display/manage the list of Restaurants
    ---
    list:
        parameters:
            - name: search
              paramType: query
              description: terms to search in name and description fields
              required: false
            - name: ordering
              paramType: query
              description: fileds to order by. Allowed fields are id, name, vote, rating
              required: false
    """
    queryset = Restaurant.objects.filter(active=True)
    serializer_class = RestaurantSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name', 'description')
    ordering_fields = ('id', 'name', 'votes', 'rating')


class VisitViewSet(viewsets.ModelViewSet):
    """
    API view that display/manage the list of Visits of Restaurants
    """
    queryset = Visit.objects.filter(restaurant__active=True)
    serializer_class = VisitSerializer


class CommentViewSet(viewsets.ModelViewSet):
    """
    API view that display/manage the list of Comments for Restaurants
    """
    queryset = Comment.objects.filter(restaurant__active=True)
    serializer_class = CommentSerializer


class RestaurantVoteView(APIView):
    """
    Vote or get the vote count.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


    def get_object(self, pk):
        try:
            return Restaurant.objects.get(pk=pk)
        except Restaurant.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        restaurant = self.get_object(pk)
        return Response({'votes': restaurant.votes.count()})

    def put(self, request, pk, format=None):
        # Sanitize input
        restaurant = self.get_object(pk)
        serializer = RestaurantVoteSerializer(data=request.data)
        if serializer.is_valid():
            # if vote is True we Thumbs up, else Thumbs Down
            if serializer.data['vote']:
                # User can not vote more than once
                if not restaurant.votes.exists(request.user):
                    restaurant.votes.up(request.user)
            else:
                restaurant.votes.down(request.user)
            return Response({'votes': restaurant.votes.count()})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

