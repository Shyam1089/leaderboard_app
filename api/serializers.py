from rest_framework import serializers
from .models import User, Winner

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class WinnerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Winner
        fields = '__all__'

class UpdateScoreSerializer(serializers.Serializer):
    change = serializers.IntegerField(required=True)
