# django-aws-doc-manager

Methods inside ``django_aws_doc_manager/main/views/view.py``
1. ``document(request):``
* Provides option for user to download or preview the file by specifying in the get request.

2. ``upload(request):``
* Supported drag and drop multiple files for uploading.
* Allowed users to rename the file before uploading.

3. ``pull_file_metadata(request):``
* Pulled and parsed file metadata to provide fraud analysis
* Users are able to pull information like creator, file creation date, producer, file modification date, etc.
