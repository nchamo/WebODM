import mimetypes
import os

from django.http import FileResponse
from django.http import HttpResponse
from wsgiref.util import FileWrapper
from rest_framework import status
from rest_framework.response import Response
from app.plugins.views import TaskView
from worker.tasks import execute_grass_script
from app.plugins.grass_engine import grass, GrassEngineException, cleanup_grass_context
from worker.celery import app as celery
from webodm import settings

class TaskLabelPathGenerate(TaskView):
    def post(self, request, pk=None):
        task = self.get_and_check_task(request, pk)

        if task.orthophoto_extent is None:
            return Response({'error': 'No orthophoto is available.'})

        try:
            orthophoto = os.path.abspath(task.get_asset_download_path("orthophoto.tif"))
            dst_folder = task.assets_path()

            context = grass.create_context({'auto_cleanup' : False})

            context.add_param('dst_folder', dst_folder)
            context.add_param('orthophoto', orthophoto)
            context.set_location(orthophoto)

            celery_task_id = execute_grass_script.delay(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "convert_to_png.grass"
            ), context.serialize()).task_id

            return Response({'celery_task_id': celery_task_id}, status=status.HTTP_200_OK)
        except GrassEngineException as e:
            return Response({'error': str(e)}, status=status.HTTP_200_OK)

class TaskLabelPathCheck(TaskView):
    def get(self, request, pk=None, celery_task_id=None):
        task = self.get_and_check_task(request, pk)
        assets_path = task.assets_path()

        res = celery.AsyncResult(celery_task_id)
        if not res.ready():
            return Response({'ready': False}, status=status.HTTP_200_OK)
        else:
            result = res.get()
            if result.get('error', None) is not None:
                cleanup_grass_context(result['context'])
                return Response({'ready': True, 'error': result['error']})

            image_file = result.get('output')
            if not image_file or not os.path.exists(os.path.join(assets_path, image_file)):
                cleanup_grass_context(result['context'])
                return Response({'ready': True, 'error': 'Image file could not be generated. This might be a bug.'})

            return Response({'ready': True, 'folder': os.path.relpath(assets_path, settings.MEDIA_ROOT), 'image': image_file})

class TaskConvertLabelsToGeoJson(TaskView):
    def get(self, request, pk=None):
        task = self.get_and_check_task(request, pk)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        orthophoto_path = os.path.abspath(task.get_asset_download_path("orthophoto.tif"))
        relative_path = os.path.relpath(task.assets_path(), settings.MEDIA_ROOT)
        labels_path = os.path.join(settings.ANNOTATIONS_ROOT, relative_path, "orthophoto.xml")
        
        if not os.path.exists(labels_path):
            return Response({'error': 'Failed to find the labels file. Are you sure you added some labels?'}, status=status.HTTP_400_BAD_REQUEST)
        
        python_script_path = os.path.join(current_dir, "labels_to_geojson.py")
        
        context = grass.create_context({'auto_cleanup' : False})

        context.add_param('params', '{} {}'.format(orthophoto_path, labels_path))
        context.add_param('script', python_script_path)
        context.set_location(orthophoto_path)

        execution = execute_grass_script.delay(os.path.join(current_dir, "run_python_script.grass"), context.serialize())
        result = execution.get(timeout=None, propagate=True, interval=0.5)
        
        if result.get('error', None) is not None:
            # cleanup_grass_context(result['context'])
            return Response({'error': result['error']})

        output_file = result.get('output')
        if not output_file or not os.path.exists(output_file):
            # cleanup_grass_context(result['context'])
            return Response({'error': 'Output file could not be generated. This might be a bug.'})

        filename = os.path.basename(output_file)
        filesize = os.stat(output_file).st_size

        f = open(output_file, "rb")

        # More than 100mb, normal http response, otherwise stream
        # Django docs say to avoid streaming when possible
        stream = filesize > 1e8
        if stream:
            response = FileResponse(f)
        else:
            response = HttpResponse(FileWrapper(f),
                                    content_type=(mimetypes.guess_type(filename)[0] or "application/zip"))

        response['Content-Type'] = mimetypes.guess_type(filename)[0] or "application/zip"
        response['Content-Disposition'] = "attachment; filename={}".format(filename)
        response['Content-Length'] = filesize

        return response   
        