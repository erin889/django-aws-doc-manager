from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.http import HttpResponseBadRequest
from decouple import config
from boto.exception import S3ResponseError

import logging
import boto3
import math
import json
import urllib
import os
import PyPDF2 as pyPdf

logger = logging.getLogger('')

ALLOWED_FILE_MIME_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'video/mpeg', 'video/mp4', 'video/quicktime', 'application/*']

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def detail(request):
    bucket_name = prefix = suffix = ""
    filemap = get_file_map(bucket_name, suffix, prefix)

    return render(request, 'viewdocs.html',
                  {'request': request,
                   'private_filemap' : filemap })

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def get_file_map(bucket_name, suffix, prefix):
    s3 = boto3.resource('s3', aws_access_key_id=config("AWS_ACCESS_KEY_ID"), aws_secret_access_key=config("AWS_SECRET_ACCESS_KEY"))
    bucket = s3.Bucket(bucket_name)
    filemap = []

    for object_summary in bucket.objects.filter(Prefix=prefix):
        metadata_lst = []
        if object_summary.key[-1] != '/': # Add to the file map only when it is a file, not folder
            filename = object_summary.key.rsplit(suffix+'/', 1)[-1]
            filetype = object_summary.key.rsplit('.', 1)[-1]
            size =  convert_size(float(object_summary.size))
            date = object_summary.last_modified
            encoded_filenmae = urllib.quote_plus(filename.encode('utf8'))
            try:
                if filetype == 'pdf':
                    mdata = FileMetadata.objects.using('default').filter(filename=filename).order_by('creation_date').last()
                    metadata_lst.append([['Producer', mdata.producer],['Creator', mdata.creator], ['File Creation Date', mdata.file_creation_date],
                        ['File Modified Date', mdata.file_mod_date], ['Title', mdata.title], ['Other Information', mdata.other_info]])
                else:
                    metadata_lst = 'Unavailable Metadata for Non-PDF Files'
            except:
                metadata_lst = None
            filemap.append([filename, metadata_lst, filetype, date, size, encoded_filenmae])

    filemap.sort(key = lambda x: x[3], reverse=True)
    return filemap


def pull_one_file_metadata(request, bucket_name, s3, filename, prefix):
    obj = s3.Object(bucket_name, prefix + "/" + filename)
    content = obj.get()['Body'].read().rpartition('EOF')[0] + 'EOF'
    keywords = ['producer', 'creator', 'creation', 'mod', 'title']
    info_list = [None] * 6

    try:
        with open('file.pdf', "w+b") as file:
            file.write(content)
            file.seek(0)
            pdfFile = pyPdf.PdfFileReader(file)
            if pdfFile.isEncrypted:
                try:
                    pdfFile.decrypt('')
                    logger.info('File Decrypted (PyPDF2): ' + prefix + "/" + filename)
                except:
                    command="cp file.pdf"+" temp.pdf; qpdf --password='' --decrypt temp.pdf file.pdf"
                    os.system(command)
                    logger.info('File Decrypted (qpdf): ' + prefix + "/" + filename)

            data = pdfFile.getDocumentInfo()
            for metadata in data:
                for kw in keywords:
                    if kw in metadata.lower():
                        index = keywords.index(kw)
                        break
                if any(substring in metadata.lower() for substring in keywords):
                    info_list[index] = data[metadata]
                elif info_list[5] is None:
                    info_list[5] = metadata[1:]+ ":" + str(data[metadata]) + ";"
                else:
                    info_list[5] += metadata[1:]+ ":" + str(data[metadata]) + ";"

    except Exception as e:
        logger.error('Unable to parse metadata for file: '+prefix+"/"+filename+". "+str(e))

    new_metadata = FileMetadata(producer=info_list[0], creator=info_list[1], file_creation_date=info_list[2],
                    file_mod_date=info_list[3], title=info_list[4], other_info=info_list[5], filename=filename,
                    creation_user=request.user, creation_date=timezone.now())

    new_metadata.save()
    os.remove('file.pdf')

def pull_file_metadata(request):
    bucket_name = ""
    suffix = ""
    prefix = ""

    s3 = boto3.resource('s3', aws_access_key_id=config("AWS_ACCESS_KEY_ID"), aws_secret_access_key=config("AWS_SECRET_ACCESS_KEY"))

    if request.GET.get('filename') == "allfilemetadata":
        for object_summary in s3.Bucket(bucket_name).objects.filter(Prefix=prefix):
            if object_summary.key[-1] != '/': # Pull file metadata only when it is a file, not folder
                filename = object_summary.key.rsplit(suffix+'/', 1)[-1]
                filetype = object_summary.key.rsplit('.', 1)[-1]
                if filetype == 'pdf':
                    pull_one_file_metadata(request, bucket_name, s3, filename, prefix)
    else:
        filename = urllib.unquote(request.GET.get('filename'))
        filetype = filename.rsplit('.', 1)[-1]
        if filetype == 'pdf':
            pull_one_file_metadata(request, bucket_name, s3, filename, prefix)

    return HttpResponseRedirect(request.path_info)


def document(request):
    is_download = json.loads(request.GET.get('download').lower())
    bucket_name = ""
    suffix = ""

    s3 = boto3.resource('s3', aws_access_key_id=config("AWS_ACCESS_KEY_ID"), aws_secret_access_key=config("AWS_SECRET_ACCESS_KEY"))
    filename = urllib.unquote(request.GET.get('filename'))
    prefix_filename = filename.encode('utf8')
    filetype = filename.rsplit('.', 1)[-1]
    logger.info('Viewing or Downloading the file: ' + prefix_filename.decode('utf8'))
    obj = s3.Object(bucket_name, prefix_filename)
    content = obj.get()['Body'].read()
    response = HttpResponse(content, content_type='application/'+filetype)

    if is_download:
        response['Content-Disposition'] = 'attachment; filename=' + '"' + filename + '"'
    else:
        response['Content-Disposition'] = 'inline; filename=' + '"' + filename + '"'
    return response


def get_settings(request):
    response = HttpResponse(json.dumps(
        {'ALLOWED_FILE_MIME_TYPES': ALLOWED_FILE_MIME_TYPES}))
    return response


def upload(request):
    bucket_name = ""
    suffix = ""

    if request.method == 'POST' and len(request.FILES) > 0:
        new_names = request.GET.get('names').split('>')

        for i in range(0, len(request.FILES)):
            file = request.FILES['file['+str(i)+']']
            filename = ""
            maintype = file.content_type.split('/')[0]
            if maintype == 'application' or file.content_type in ALLOWED_FILE_MIME_TYPES:
                for j in range(0, 5):
                    try:
                        if (j > 0):
                            logger.info('Retrying to uplaod documents to S3, attempt: ' + str(j))
                        s3 = boto3.resource('s3', aws_access_key_id=config("AWS_ACCESS_KEY_ID"), aws_secret_access_key=config("AWS_SECRET_ACCESS_KEY"))
                        logger.info('Uploading file ' + filename + ' to S3 bucket: ' + bucket_name)
                        obj = s3.Object(bucket_name, filename)
                        obj.put(Body=file.read())
                        response = HttpResponse()

                    except:
                        continue
                    break
            else:
                response = HttpResponseBadRequest('Sorry, valid file types are: ' + str(ALLOWED_FILE_MIME_TYPES))
    else:
        response = HttpResponseBadRequest('This view is only accessible via a POST request.')
    return response
