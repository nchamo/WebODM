from app.plugins import PluginBase
from app.plugins import MountPoint
from .api import TaskLabelPathGenerate
from .api import TaskLabelPathCheck
from .api import TaskConvertLabelsToGeoJson



class Plugin(PluginBase):
    def include_js_files(self):
        return ['main.js']
        
    def build_jsx_components(self):
        return ['Labels.jsx']

    def api_mount_points(self):
        return [
            MountPoint('task/(?P<pk>[^/.]+)/labels/generate', TaskLabelPathGenerate.as_view()),
            MountPoint('task/(?P<pk>[^/.]+)/labels/check/(?P<celery_task_id>.+)', TaskLabelPathCheck.as_view()),
            MountPoint('task/(?P<pk>[^/.]+)/labels/verified', TaskConvertLabelsToGeoJson.as_view()),
        ]