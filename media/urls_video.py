from rest_framework.routers import DefaultRouter

from .views import VideoMetadataViewSet

app_name = "video_media"

router = DefaultRouter()
router.register("videos", VideoMetadataViewSet, basename="video-metadata")

urlpatterns = router.urls
