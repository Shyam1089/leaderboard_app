from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db.models import Max
from .models import User, Winner
from .serializers import UserSerializer, WinnerSerializer, UpdateScoreSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed, created, edited, or deleted.
    """
    queryset = User.objects.all().order_by('-points')
    serializer_class = UserSerializer

    @action(detail=True, methods=['patch'])
    def update_score(self, request, pk=None):
        """
        Update a user's score by adding or subtracting points.
        """
        user = self.get_object()
        # Explicitly validate input to be an integer using serializer 
        serializer = UpdateScoreSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "validation_errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        change = serializer.data.get('change')
        user.points += change
        user.save()
        return Response(UserSerializer(user).data)

    @action(detail=False, methods=['get'])
    def grouped_by_score(self, request):
        """
        Get users grouped by score with average age.
        """
        users = User.objects.all()
        score_groups = {}

        for user in users:
            score = user.points
            if score not in score_groups:
                score_groups[score] = {"names": [], "total_age": 0, "count": 0}
            
            score_groups[score]["names"].append(user.name)
            score_groups[score]["total_age"] += user.age
            score_groups[score]["count"] += 1

        # Calculate average age and sort by score (highest first)
        sorted_groups = {
            score: {
                "names": data["names"],
                "average_age": data["total_age"] // data["count"],
            }
            for score, data in sorted(score_groups.items(), reverse=True)
        }
        return Response(sorted_groups)


class WinnerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows winners to be viewed, created, edited, or deleted.
    """
    queryset = Winner.objects.all().order_by('-timestamp')
    serializer_class = WinnerSerializer

@api_view(['POST'])
def update_winners(request):
    """
    Endpoint can be called by any external Cloud Scheduler to update winner
    Have added a button on the UI to call this method to manually update winner
    """
    max_points = User.objects.aggregate(Max('points'))['points__max']
    top_users = User.objects.filter(points=max_points)
    if top_users.count() == 1:
        top_user = top_users.first()
        winner = Winner.objects.create(
            user=top_user,
            points_at_win=top_user.points
        )
        return Response({
            'status': 'success',
            'winner': WinnerSerializer(winner).data
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            'status': 'tie',
            'message': 'No winner declared due to a tie'
        }, status=status.HTTP_200_OK)
