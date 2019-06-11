from app.plugins import PluginBase
from app.plugins import MountPoint
from .api import TaskGeneratePngFromGeoTiff
from .api import TaskCheckCeleryTask
from .api import TaskGenerateGeoJsonFromVerified
from .api import TaskUploadGeoJsonToLabelMe
from .api import TaskDownloadVerified



class Plugin(PluginBase):
    def include_js_files(self):
        return ['main.js']
        
    def build_jsx_components(self):
        return ['Labels.jsx']

    def api_mount_points(self):
        return [
            MountPoint('task/(?P<pk>[^/.]+)/labels/generatepng', TaskGeneratePngFromGeoTiff.as_view()),
            MountPoint('task/(?P<pk>[^/.]+)/labels/check/(?P<celery_task_id>.+)', TaskCheckCeleryTask.as_view()),
            MountPoint('task/(?P<pk>[^/.]+)/labels/generateverified', TaskGenerateGeoJsonFromVerified.as_view()),
            MountPoint('task/(?P<pk>[^/.]+)/labels/downloadverified/(?P<celery_task_id>.+)', TaskDownloadVerified.as_view()),
            MountPoint('task/(?P<pk>[^/.]+)/labels/upload', TaskUploadGeoJsonToLabelMe.as_view()),
        ]