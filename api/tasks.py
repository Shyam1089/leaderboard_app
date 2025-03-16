import logging
from celery import shared_task
from .views import update_winners
from django.http import HttpRequest
from rest_framework.request import Request

logger = logging.getLogger(__name__)

@shared_task
def update_winners_task():
    """
    Celery task to identify the user with the highest points.
    This task is scheduled to run every 5 minutes.
    """
    try:
        dummy_request = HttpRequest()
        dummy_request.method = 'POST'
        request = Request(dummy_request)
        response = update_winners(request)
        # Log the result
        if response.status_code == 201:  # Created
            data = response.data
            winner_data = data.get('winner', {})
            user_data = winner_data.get('user', {})
            logger.info(f"Winner declared: {user_data.get('name')} with {winner_data.get('points_at_win')} points")
            return {'status': 'success', 'winner': user_data.get('name'), 'points': winner_data.get('points_at_win')}
        else:
            logger.info(f"No winner declared: {response.data.get('message')}")
            return {'status': 'tie', 'message': response.data.get('message')}
    except Exception as e:
        logger.error(f"Error updating winners: {str(e)}")
        return {'status': 'error', 'message': str(e)} 