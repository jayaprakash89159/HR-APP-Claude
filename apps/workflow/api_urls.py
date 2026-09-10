from django.urls import path
from apps.workflow.views import SwipeRequestAPIView, SwipeRequestDecisionAPIView

urlpatterns = [
    path('swipe-requests/', SwipeRequestAPIView.as_view(), name='swipe_requests'),
    path('swipe-requests/<uuid:pk>/decision/', SwipeRequestDecisionAPIView.as_view(), name='swipe_request_decision'),
]
