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

class TaskGeneratePngFromGeoTiff(TaskView):
    def post(self, request, pk=None):
        task = self.get_and_check_task(request, pk)

        if task.orthophoto_extent is None:
            return Response({'error': 'No orthophoto is available.'})

        try:
            orthophoto = os.path.abspath(task.get_asset_download_path("orthophoto.tif"))
            dst_folder = os.path.dirname(orthophoto)

            context = grass.create_context({'auto_cleanup' : False})
            context.add_param('dst_folder', dst_folder)
            context.add_param('orthophoto', orthophoto)
            context.set_location(orthophoto)

            celery_task_id = execute_grass_script.delay(os.path.join(os.path.dirname(os.path.abspath(__file__)), "convert_to_png.grass"), context.serialize()).task_id

            return Response({'celery_task_id': celery_task_id}, status=status.HTTP_200_OK)
        except GrassEngineException as e:
            return Response({'error': str(e)}, status=status.HTTP_200_OK)

class TaskCheckCeleryTask(TaskView):
    def get(self, request, pk=None, celery_task_id=None):
        task = self.get_and_check_task(request, pk)

        res = celery.AsyncResult(celery_task_id)
        if not res.ready():
            return Response({'ready': False}, status=status.HTTP_200_OK)
        else:
            result = res.get()
            if result.get('error', None) is not None:
                cleanup_grass_context(result['context'])
                return Response({'ready': True, 'error': result['error']})

            file_path = result.get('output')
            if not file_path or not os.path.exists(file_path):
                cleanup_grass_context(result['context'])
                return Response({'ready': True, 'error': 'File could not be generated. This might be a bug.'})
            
            request.session['labels_' + celery_task_id] = file_path
            folder = os.path.relpath(os.path.dirname(os.path.abspath(task.get_asset_download_path("orthophoto.tif"))), settings.MEDIA_ROOT)
            file = os.path.basename(file_path)
            return Response({'ready': True, 'folder': folder, 'file': file})

class TaskUploadGeoJsonToLabelMe(TaskView):
    def post(self, request, pk=None):
        task = self.get_and_check_task(request, pk)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            orthophoto = os.path.abspath(task.get_asset_download_path("orthophoto.tif"))
            relative_path = os.path.relpath(os.path.dirname(orthophoto), settings.MEDIA_ROOT)
            labels_path = os.path.join(settings.ANNOTATIONS_ROOT, relative_path, "orthophoto.xml")
            geojson = request.data.get('geojson', '')
            script_path = os.path.join(current_dir, 'geojson_to_labels.py')
            context = grass.create_context({'auto_cleanup' : False})
            with open(os.path.join(context.get_cwd(), 'geojson.txt'), 'w+') as file:
                file.write(geojson)

            return run_python_script(script_path, '{} {} {}'.format(orthophoto, labels_path, 'geojson.txt'), orthophoto, labels_path, context)  
        except GrassEngineException as e:
            return Response({'error': str(e)}, status=status.HTTP_200_OK)

class TaskGenerateGeoJsonFromVerified(TaskView):
    def post(self, request, pk=None):
        task = self.get_and_check_task(request, pk)
        
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            orthophoto = os.path.abspath(task.get_asset_download_path('orthophoto.tif'))
            relative_path = os.path.relpath(os.path.dirname(orthophoto), settings.MEDIA_ROOT)
            labels_path = os.path.join(settings.ANNOTATIONS_ROOT, relative_path, 'orthophoto.xml')
            
            if not os.path.exists(labels_path):
                return Response({'error': 'Failed to find the labels file. Are you sure you added some labels?'}, status=status.HTTP_200_OK)
            
            script_path = os.path.join(current_dir, 'labels_to_geojson.py')
            return run_python_script(script_path, '{} {}'.format(orthophoto, labels_path), orthophoto, 'output.json') 
        except GrassEngineException as e:
            return Response({'error': str(e)}, status=status.HTTP_200_OK)      

class TaskDownloadVerified(TaskView):
    def get(self, request, pk=None, celery_task_id=None):
        file = request.session.get('labels_' + celery_task_id, None)
        return download_file(file)

def run_python_script(script_path, script_params, location, output_path, context = None):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if context is None:
        context = grass.create_context({'auto_cleanup' : False})

    context.add_param('script', script_path)
    context.add_param('params', '{}'.format(script_params))
    context.add_param('output', '{}'.format(output_path))
    context.set_location(location)

    celery_task_id = execute_grass_script.delay(os.path.join(current_dir, "run_python_script.grass"), context.serialize()).task_id
    return Response({'celery_task_id': celery_task_id}, status=status.HTTP_200_OK)

def download_file(file_path):
    if file_path is not None:
        filename = os.path.basename(file_path)
        filesize = os.stat(file_path).st_size

        f = open(file_path, "rb")

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
    else:
        return Response({'error': 'Invalid download id'})    
        