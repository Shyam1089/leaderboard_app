from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import User, Winner
from .serializers import UserSerializer, WinnerSerializer
import json
from django.utils import timezone
from datetime import timedelta

class UserViewSetTests(TestCase):
    """Test cases for the UserViewSet"""
    
    def setUp(self):
        """Set up test data and client"""
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create(
            name="Test User 1",
            age=30,
            address="123 Test St",
            points=10
        )
        
        self.user2 = User.objects.create(
            name="Test User 2",
            age=25,
            address="456 Test Ave",
            points=15
        )
        
        self.user3 = User.objects.create(
            name="Test User 3",
            age=35,
            address="789 Test Blvd",
            points=5
        )
        
        # Valid user data for creation tests
        self.valid_user_data = {
            'name': 'New Test User',
            'age': 28,
            'address': '101 New St',
            'points': 0
        }
        
        # Invalid user data for negative tests
        self.invalid_user_data = {
            'name': '',
            'age': 'not-a-number',
            'address': '101 New St',
            'points': 0
        }
    
    def test_get_all_users(self):
        """Test retrieving all users"""
        response = self.client.get(reverse('api:user-list'))
        users = User.objects.all().order_by('-points')
        serializer = UserSerializer(users, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_create_valid_user(self):
        """Test creating a new user with valid data"""
        response = self.client.post(
            reverse('api:user-list'),
            data=json.dumps(self.valid_user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 4)
        self.assertEqual(response.data['name'], 'New Test User')
    
    def test_create_invalid_user(self):
        """Test creating a new user with invalid data"""
        response = self.client.post(
            reverse('api:user-list'),
            data=json.dumps(self.invalid_user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 3)  # No new user should be created
    
    def test_get_single_user(self):
        """Test retrieving a single user"""
        response = self.client.get(reverse('api:user-detail', kwargs={'pk': self.user1.pk}))
        serializer = UserSerializer(self.user1)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_update_user(self):
        """Test updating a user"""
        update_data = {
            'name': 'Updated User',
            'age': 31,
            'address': '123 Updated St',
            'points': 10
        }
        
        response = self.client.put(
            reverse('api:user-detail', kwargs={'pk': self.user1.pk}),
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.name, 'Updated User')
        self.assertEqual(self.user1.age, 31)
    
    def test_delete_user(self):
        """Test deleting a user"""
        response = self.client.delete(reverse('api:user-detail', kwargs={'pk': self.user3.pk}))
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 2)
    
    def test_update_score(self):
        """Test updating a user's score"""
        initial_points = self.user1.points
        change_data = {'change': 5}
        
        response = self.client.patch(
            reverse('api:user-update-score', kwargs={'pk': self.user1.pk}),
            data=json.dumps(change_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.points, initial_points + 5)
    
    def test_grouped_by_score(self):
        """Test getting users grouped by score"""
        # Create another user with the same score as user1 to test grouping
        User.objects.create(
            name="Test User 4",
            age=40,
            address="101 Test Lane",
            points=10  # Same as user1
        )
        
        response = self.client.get(reverse('api:user-grouped-by-score'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that scores are in descending order
        scores = list(response.data.keys())
        scores_int = [int(score) if isinstance(score, str) else score for score in scores]
        self.assertEqual(scores_int, sorted(scores_int, reverse=True))
        
        # Check the content for the highest score group (15 points)
        # The key could be either an integer or a string depending on the serialization
        highest_score_key = 15
        if highest_score_key not in response.data:
            highest_score_key = '15'  # Try string version
        
        self.assertIn(self.user2.name, response.data[highest_score_key]['names'])
        self.assertEqual(response.data[highest_score_key]['average_age'], self.user2.age)
        
        # Check the content for the middle score group (10 points)
        # This group should have 2 users now
        middle_score_key = 10
        if middle_score_key not in response.data:
            middle_score_key = '10'  # Try string version
            
        self.assertEqual(len(response.data[middle_score_key]['names']), 2)
        self.assertIn(self.user1.name, response.data[middle_score_key]['names'])
        self.assertIn("Test User 4", response.data[middle_score_key]['names'])
        
        # Check that the average age is calculated correctly for the group
        # (30 + 40) / 2 = 35
        self.assertEqual(response.data[middle_score_key]['average_age'], 35)
        
        # Check the content for the lowest score group (5 points)
        lowest_score_key = 5
        if lowest_score_key not in response.data:
            lowest_score_key = '5'  # Try string version
            
        self.assertIn(self.user3.name, response.data[lowest_score_key]['names'])
        self.assertEqual(response.data[lowest_score_key]['average_age'], self.user3.age)

    def test_grouped_by_score_no_users(self):
        """Test getting users grouped by score when there are no users"""
        # Delete all users
        User.objects.all().delete()
        
        response = self.client.get(reverse('api:user-grouped-by-score'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})

    def test_grouped_by_score_single_user(self):
        """Test getting users grouped by score when there's only one user"""
        # Delete all users except one
        User.objects.exclude(pk=self.user1.pk).delete()
        
        response = self.client.get(reverse('api:user-grouped-by-score'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that there's only one score group
        self.assertEqual(len(response.data), 1)
        
        # The key could be either an integer or a string
        score_key = 10  # user1's score
        if score_key not in response.data:
            score_key = '10'  # Try string version
            
        # Check the content of the score group
        self.assertIn(self.user1.name, response.data[score_key]['names'])
        self.assertEqual(response.data[score_key]['average_age'], self.user1.age)

    def test_grouped_by_score_sorting(self):
        """Test that scores are properly sorted in descending order"""
        # Delete existing users and create new ones with specific scores
        User.objects.all().delete()
        
        # Create users with scores in random order
        User.objects.create(name="User A", age=30, address="Address A", points=5)
        User.objects.create(name="User B", age=25, address="Address B", points=20)
        User.objects.create(name="User C", age=35, address="Address C", points=10)
        User.objects.create(name="User D", age=40, address="Address D", points=15)
        
        response = self.client.get(reverse('api:user-grouped-by-score'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Extract the scores and convert to integers if they're strings
        scores = list(response.data.keys())
        scores_int = [int(score) if isinstance(score, str) else score for score in scores]
        
        # Expected order: 20, 15, 10, 5
        expected_order = [20, 15, 10, 5]
        
        # Check that the scores are in the expected order
        self.assertEqual(scores_int, expected_order)

    def test_grouped_by_score_same_age(self):
        """Test average age calculation when users have the same age"""
        # Delete existing users and create new ones with the same age but different scores
        User.objects.all().delete()
        
        # Create users with the same age (30) but different scores
        User.objects.create(name="User Same Age 1", age=30, address="Address 1", points=10)
        User.objects.create(name="User Same Age 2", age=30, address="Address 2", points=10)
        User.objects.create(name="User Same Age 3", age=30, address="Address 3", points=10)
        
        response = self.client.get(reverse('api:user-grouped-by-score'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # The key could be either an integer or a string
        score_key = 10
        if score_key not in response.data:
            score_key = '10'  # Try string version
            
        # Check that there are 3 users in this score group
        self.assertEqual(len(response.data[score_key]['names']), 3)
        
        # Check that the average age is 30
        self.assertEqual(response.data[score_key]['average_age'], 30)

    def test_grouped_by_score_multiple_groups(self):
        """Test multiple score groups with multiple users in each group"""
        # Delete existing users and create new ones with specific scores
        User.objects.all().delete()
        
        # Create users with two different score groups
        # Score group 10
        User.objects.create(name="Group A User 1", age=20, address="Address A1", points=10)
        User.objects.create(name="Group A User 2", age=30, address="Address A2", points=10)
        
        # Score group 5
        User.objects.create(name="Group B User 1", age=25, address="Address B1", points=5)
        User.objects.create(name="Group B User 2", age=35, address="Address B2", points=5)
        
        response = self.client.get(reverse('api:user-grouped-by-score'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that there are 2 score groups
        self.assertEqual(len(response.data), 2)
        
        # The keys could be either integers or strings
        score_key_a = 10
        if score_key_a not in response.data:
            score_key_a = '10'  # Try string version
            
        score_key_b = 5
        if score_key_b not in response.data:
            score_key_b = '5'  # Try string version
        
        # Check group A (score 10)
        self.assertEqual(len(response.data[score_key_a]['names']), 2)
        self.assertIn("Group A User 1", response.data[score_key_a]['names'])
        self.assertIn("Group A User 2", response.data[score_key_a]['names'])
        self.assertEqual(response.data[score_key_a]['average_age'], 25)  # (20+30)/2 = 25
        
        # Check group B (score 5)
        self.assertEqual(len(response.data[score_key_b]['names']), 2)
        self.assertIn("Group B User 1", response.data[score_key_b]['names'])
        self.assertIn("Group B User 2", response.data[score_key_b]['names'])
        self.assertEqual(response.data[score_key_b]['average_age'], 30)  # (25+35)/2 = 30


class WinnerViewSetTests(TestCase):
    """Test cases for the WinnerViewSet"""
    
    def setUp(self):
        """Set up test data and client"""
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create(
            name="Winner Test User 1",
            age=30,
            address="123 Winner St",
            points=20
        )
        
        self.user2 = User.objects.create(
            name="Winner Test User 2",
            age=25,
            address="456 Winner Ave",
            points=15
        )
        
        # Create test winners
        self.winner1 = Winner.objects.create(
            user=self.user1,
            points_at_win=20,
            timestamp=timezone.now() - timedelta(minutes=30)
        )
        
        self.winner2 = Winner.objects.create(
            user=self.user2,
            points_at_win=15,
            timestamp=timezone.now() - timedelta(hours=1)
        )
    
    def test_get_all_winners(self):
        """Test retrieving all winners"""
        response = self.client.get(reverse('api:winner-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Get the IDs of the winners in the response
        winner_ids = [winner['id'] for winner in response.data['results']]
        
        # Check that both winners are in the response
        self.assertIn(self.winner1.id, winner_ids)
        self.assertIn(self.winner2.id, winner_ids)
        
        # Verify the order of winners in the response
        # Get the timestamps from the response
        timestamps = [winner['timestamp'] for winner in response.data['results']]
        
        # Check that timestamps are in descending order (most recent first)
        self.assertTrue(timestamps[0] > timestamps[1], 
                       f"First timestamp {timestamps[0]} should be more recent than second timestamp {timestamps[1]}")
    
    def test_get_single_winner(self):
        """Test retrieving a single winner"""
        response = self.client.get(reverse('api:winner-detail', kwargs={'pk': self.winner1.pk}))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['name'], self.user1.name)
        self.assertEqual(response.data['points_at_win'], 20)


class UpdateWinnersTests(TestCase):
    """Test cases for the update_winners endpoint"""
    
    def setUp(self):
        """Set up test data and client"""
        self.client = APIClient()
        
        # Create test users with same points (for tie scenario)
        self.user1 = User.objects.create(
            name="Update Winner User 1",
            age=30,
            address="123 Update St",
            points=10
        )
        
        self.user2 = User.objects.create(
            name="Update Winner User 2",
            age=25,
            address="456 Update Ave",
            points=10
        )
    
    def test_update_winners_tie(self):
        """Test update_winners with a tie scenario"""
        response = self.client.post(reverse('api:update-winners'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'tie')
        self.assertEqual(Winner.objects.count(), 0)  # No winner should be created
    
    def test_update_winners_success(self):
        """Test update_winners with a clear winner"""
        # Update one user to have higher points
        self.user1.points = 15
        self.user1.save()
        
        response = self.client.post(reverse('api:update-winners'))
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(Winner.objects.count(), 1)
        
        # Check the winner details
        winner = Winner.objects.first()
        self.assertEqual(winner.user, self.user1)
        self.assertEqual(winner.points_at_win, 15) 