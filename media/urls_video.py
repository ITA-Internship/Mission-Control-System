"""URL routing for video artifacts."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import VideoMetadataBrowserView, VideoMetadataViewSet

app_name = "video_media"

router = DefaultRouter()
router.register("videos", VideoMetadataViewSet, basename="video-metadata")

urlpatterns = [
    path("videos/browser/", VideoMetadataBrowserView.as_view(), name="video-browser"),
] + router.urls
