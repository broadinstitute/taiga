from celery import Celery
from celery.result import AsyncResult

import flask
import gzip
import json
import logging
import shutil
import tempfile
import uuid

from requests.exceptions import HTTPError
from typing import IO, Optional
from urllib.parse import urlparse

import taiga2.conv as conversion
from taiga2.conv.util import Progress, make_temp_file_generator, get_file_hashes
from taiga2.controllers import models_controller
from taiga2.conv.imp import ImportResult
from taiga2.models import S3DataFile
from taiga2.third_party_clients.aws import aws
from taiga2.third_party_clients.gcs import upload_from_file
from taiga2.third_party_clients.figshare import (
    initiate_new_upload,
    upload_parts,
    complete_upload,
)
import humanize

celery = Celery("taiga2")
log = logging.getLogger()


@celery.task
def print_config():
    import flask

    print(flask.current_app.config)


def _compress_and_upload_to_s3(
    s3_object,
    download_dest,
    compressed_dest,
    compressed_s3_object,
    mime_type: str,
    encoding: Optional[str],
):
    # Create a new compressed object to upload
    download_dest.seek(0)
    with open(download_dest.name, "rb") as f:
        with gzip.open(compressed_dest.name, "wb") as f_compressed:
            shutil.copyfileobj(f, f_compressed)

    compressed_s3_object.upload_file(
        compressed_dest.name,
        ExtraArgs={
            "ContentEncoding": "gzip",
            "ContentType": "{}; charset={}".format(
                mime_type, encoding if encoding is not None else "ISO 8859-1"
            ),
        },
    )


def _from_s3_convert_to_s3(
    progress,
    upload_session_file_id,
    s3_object,
    download_dest,
    converted_dest,
    converted_s3_object,
    converter,
    compressed_dest,
    compressed_s3_object,
    mime_type,
    encoding: Optional[str],
):
    progress.progress("Downloading the file from S3")

    s3_object.download_fileobj(download_dest)
    download_dest.flush()

    import_result = converter(progress, download_dest.name, converted_dest.name)
    assert isinstance(import_result, ImportResult)

    # Create a new converted object to upload
    progress.progress("Uploading to S3")
    converted_dest.seek(0)
    converted_s3_object.upload_fileobj(converted_dest)

    _compress_and_upload_to_s3(
        s3_object,
        download_dest,
        compressed_dest,
        compressed_s3_object,
        mime_type,
        encoding,
    )

    return import_result


@celery.task(bind=True)
def background_process_new_upload_session_file(
    self,
    upload_session_file_id,
    initial_s3_key,
    file_type,
    bucket_name,
    converted_s3_key,
    compressed_s3_key,
    encoding,
):
    s3 = aws.s3
    progress = Progress(self)

    # If we receive a raw file, we don't need to do anything
    from taiga2 import models

    column_types = None

    # TODO: Instead of comparing two strings, we could also use DataFileType(file_type) and compare the result, or catch the exception
    if file_type == models.InitialFileType.Raw.value:
        progress.progress("Received {}".format(initial_s3_key))

        # Create a new converted object to upload
        progress.progress(
            "Uploading the {} to S3".format(S3DataFile.DataFileFormat(file_type))
        )

        # We copy the file to 'convert/'
        copy_source = {"Bucket": bucket_name, "Key": initial_s3_key}
        b = s3.Bucket(bucket_name)
        existing_obj = b.Object(initial_s3_key)
        b.copy(copy_source, converted_s3_key)
        compressed_s3_object = s3.Object(bucket_name, compressed_s3_key)
        with tempfile.NamedTemporaryFile("w+b") as download_dest:
            with tempfile.NamedTemporaryFile("w+b") as compressed_dest:
                existing_obj.download_fileobj(download_dest)
                download_dest.flush()
                sha256, md5 = get_file_hashes(download_dest.name)

                _compress_and_upload_to_s3(
                    existing_obj,
                    download_dest,
                    compressed_dest,
                    compressed_s3_object,
                    "text/plain",
                    encoding,
                )

        import_result = ImportResult(
            sha256=sha256,
            md5=md5,
            long_summary=None,
            short_summary=humanize.naturalsize(existing_obj.content_length),
        )
    else:
        if file_type == models.InitialFileType.NumericMatrixCSV.value:
            converter = conversion.csv_to_hdf5
        elif file_type == models.InitialFileType.TableCSV.value:
            converter = conversion.csv_to_columnar
        elif file_type in {"NumericMatrixTSV", "TableTSV"}:
            raise Exception(
                "TSV files are no longer supported. Please use CSV format instead."
            )
        else:
            raise Exception("unimplemented: {}".format(file_type))

        s3_object = s3.Object(bucket_name, initial_s3_key)
        converted_s3_object = s3.Object(bucket_name, converted_s3_key)
        compressed_s3_object = s3.Object(bucket_name, compressed_s3_key)

        with tempfile.NamedTemporaryFile("w+b") as download_dest:
            with tempfile.NamedTemporaryFile("w+b") as converted_dest:
                with tempfile.NamedTemporaryFile("w+b") as compressed_dest:
                    if (
                        file_type == models.InitialFileType.NumericMatrixCSV.value
                        or file_type == models.InitialFileType.TableCSV.value
                    ):
                        mime_type = "text/csv"
                    else:
                        mime_type = "text/tab-separated-values"

                    import_result = _from_s3_convert_to_s3(
                        progress,
                        upload_session_file_id,
                        s3_object,
                        download_dest,
                        converted_dest,
                        converted_s3_object,
                        converter,
                        compressed_dest,
                        compressed_s3_object,
                        mime_type,
                        encoding,
                    )

    models_controller.update_upload_session_file_summaries(
        upload_session_file_id,
        import_result.short_summary,
        import_result.long_summary,
        column_types,
        import_result.sha256,
        import_result.md5,
    )


# TODO: This is only for background_process_new_upload_session_file, how to get it generic for any Celery tasks?
def taskstatus(task_id):
    print("In task status of task_id {}".format(task_id))
    task = AsyncResult(task_id, app=celery)
    print("Task {}".format(task))
    print("The task is in state: {}".format(task.state))
    print("Task info is {}".format(task.info))
    if task.state == "PENDING":
        # job did not start yet
        response = {
            "id": task.id,
            "state": task.state,
            "message": "Waiting in the task queue",
            "current": 0,
            "total": 1,
            "s3Key": "TODO",
        }
    elif task.state == "SUCCESS":
        response = {
            "id": task.id,
            "state": task.state,
            "message": "Task has successfully terminated",
            "current": 1,
            "total": 1,
            "s3Key": "TODO",
        }
    elif task.state != "FAILURE":
        task_info = task.info
        if task_info is not None:
            message = task_info.get("message", "No message")
            current = int(task_info.get("current", 0))
            total = int(task_info.get("total", 1))
            s3key = task_info.get("s3Key", "TODO")
        else:
            message = "Failure :/"
            current = 0
            total = 1
            s3key = "TODO"

        response = {
            "id": task.id,
            "state": task.state,
            "message": message,
            "current": current,
            "total": total,
            "s3Key": s3key,
        }

        if task_info is not None and "result" in task.info:
            response["result"] = task.info["result"]
    else:
        response = {
            "id": task.id,
            "state": task.state,
            "message": str(task.info),
            "current": 1,
            "total": -1,
            "s3Key": "TODO" if task.info else task.info.get("s3Key", "TODO"),
        }

    print("response", repr(response))

    return response


def get_converter(src_format, dst_format):
    from taiga2.models import DataFile

    is_hdf5 = src_format == str(S3DataFile.DataFileFormat.HDF5)
    is_columnar = src_format == str(S3DataFile.DataFileFormat.Columnar)

    if is_hdf5:
        if dst_format == conversion.CSV_FORMAT:
            return conversion.hdf5_to_csv
        elif dst_format == conversion.RDS_FORMAT:
            return conversion.hdf5_to_rds
        elif dst_format == conversion.TSV_FORMAT:
            return conversion.hdf5_to_tsv
        elif dst_format == conversion.GCT_FORMAT:
            return conversion.hdf5_to_gct
    elif is_columnar:
        if dst_format == conversion.CSV_FORMAT:
            return conversion.columnar_to_csv
        elif dst_format == conversion.TSV_FORMAT:
            return conversion.columnar_to_tsv
        elif dst_format == conversion.RDS_FORMAT:
            return conversion.columnar_to_rds

    raise Exception("No conversion for {} to {}".format(src_format, dst_format))


def _start_conversion_task(
    self, progress, bucket, key, src_format, dst_format, cache_entry_id
):
    from taiga2.controllers import models_controller

    dest_bucket = flask.current_app.config["S3_BUCKET"]

    s3 = aws.s3
    with tempfile.NamedTemporaryFile() as raw_t:
        with make_temp_file_generator() as temp_file_generator:
            models_controller.update_conversion_cache_entry(
                cache_entry_id, "Downloading from S3"
            )
            s3.Object(bucket, key).download_fileobj(raw_t)
            raw_t.flush()

            models_controller.update_conversion_cache_entry(
                cache_entry_id, "Running conversion"
            )

            converter = get_converter(src_format, dst_format)
            converted_files = converter(progress, raw_t.name, temp_file_generator)
            assert isinstance(converted_files, list)

            urls = []
            for converted_file in converted_files:
                dest_key = models_controller.EnumS3FolderPath.Export.value + str(
                    uuid.uuid4().hex
                )
                urls.append("s3://{}/{}".format(dest_bucket, dest_key))

                models_controller.update_conversion_cache_entry(
                    cache_entry_id, "Uploading converted file to S3"
                )
                with open(converted_file, "rb") as converted_file_fd:
                    s3.Object(dest_bucket, dest_key).upload_fileobj(converted_file_fd)

        models_controller.update_conversion_cache_entry(
            cache_entry_id, "Completed successfully", urls=urls
        )


@celery.task(bind=True)
def start_conversion_task(self, bucket, key, src_format, dst_format, cache_entry_id):
    log.info("Starting a Conversion task")
    try:
        return _start_conversion_task(
            self, Progress(self), bucket, key, src_format, dst_format, cache_entry_id
        )
    except:
        models_controller.mark_conversion_cache_entry_as_failed(cache_entry_id)
        log.exception(
            "Error running conversion on %s/%s src_format=%s dst_format=%s cache_entry_id=%s",
            bucket,
            key,
            src_format,
            dst_format,
            cache_entry_id,
        )
        raise


def _get_s3_key_from_conversion_cache_url(cache_entry_id: str) -> str:
    conversion_cache_entry = models_controller.get_conversion_cache_entry_by_id(
        cache_entry_id
    )
    s3_path = json.loads(conversion_cache_entry.urls_as_json)[0]
    p = urlparse(s3_path)
    s3_key = p.path.lstrip("/")
    return s3_key


def _download_and_compress_s3_backfill(datafile_id: str, s3_key: str, mime_type: str):
    # TODO: Add progress?
    s3 = aws.s3
    datafile = models_controller.get_datafile(datafile_id)
    compressed_s3_key = models_controller.generate_compressed_key() + "-backfilled"

    bucket_name = flask.current_app.config["S3_BUCKET"]

    s3_object = s3.Object(bucket_name, s3_key)
    compressed_s3_object = s3.Object(bucket_name, compressed_s3_key)

    with tempfile.NamedTemporaryFile() as download_dest:
        with tempfile.NamedTemporaryFile() as compressed_dest:
            s3_object.download_fileobj(download_dest)
            _compress_and_upload_to_s3(
                s3_object,
                download_dest,
                compressed_dest,
                compressed_s3_object,
                mime_type,
                None,
            )

    models_controller.update_datafile_compressed_key_and_column_types(
        datafile_id, compressed_s3_key, None
    )


@celery.task(bind=True)
def convert_and_backfill_compressed_file(self, datafile_id: str, cache_entry_id: str):
    """
    Convert a HDF5 or Columnar file to CSV, then compress, upload to S3, and update
    DataFile compressed_s3_key and column types
    
    Args:
        datafile_id (str): ID for the (S3) DataFile to update
        cache_entry_id (str): ID for the ConversionCache entry to update
    """
    datafile = models_controller.get_datafile(datafile_id)
    _start_conversion_task(
        self,
        Progress(self),
        datafile.s3_bucket,
        datafile.s3_key,
        str(datafile.format),
        "csv",
        cache_entry_id,
    )
    s3_key = _get_s3_key_from_conversion_cache_url(cache_entry_id)

    _download_and_compress_s3_backfill(datafile_id, s3_key, "text/csv")


@celery.task(bind=True)
def backfill_compressed_file(self, datafile_id: str, cache_entry_id: Optional[str]):
    """
    Get the S3 key from ConversionCache (if DataFile is not Raw) or s3_key field, then
    compress, upload to S3, and update DataFile compressed_s3_key and column types
    
    Args:
        datafile_id (str): ID for the (S3) DataFile to update
        cache_entry_id (Optional[str]): ID for the ConversionCache entry to use, or
            None if the DataFile is a Raw DataFile
    """
    if cache_entry_id is None:
        datafile = models_controller.get_datafile(datafile_id)
        s3_key = datafile.s3_key
        mime_type = "text/plain"
    else:
        s3_key = _get_s3_key_from_conversion_cache_url(cache_entry_id)
        mime_type = "text/csv"

    _download_and_compress_s3_backfill(datafile_id, s3_key, mime_type)


@celery.task(bind=True)
def copy_datafile_to_google_bucket(
    self, datafile_id: str, dest_bucket: str, dest_gcs_path: str
):
    s3 = aws.s3
    datafile = models_controller.get_datafile(datafile_id)
    compressed_s3_object = s3.Object(datafile.s3_bucket, datafile.compressed_s3_key)
    with tempfile.NamedTemporaryFile() as download_dest:
        compressed_s3_object.download_fileobj(download_dest)
        download_dest.seek(0)
        upload_from_file(
            download_dest,
            dest_bucket,
            dest_gcs_path,
            compressed_s3_object.content_type,
            compressed_s3_object.content_encoding,
        )


@celery.task(bind=True)
def upload_datafile_to_figshare(
    self,
    new_article_id: int,
    figshare_dataset_version_link_id: str,
    file_name: str,
    datafile_id: str,
    compressed_s3_key: str,
    original_file_md5: Optional[str],
    token: str,
) -> str:
    progress = Progress(self)
    with tempfile.NamedTemporaryFile("w+b") as download_dest:
        try:
            progress.progress("Downloading file from S3")
            file_info = initiate_new_upload(
                new_article_id,
                file_name,
                compressed_s3_key,
                original_file_md5,
                token,
                download_dest,
            )
        except HTTPError as error:
            progress.failed(str(error))
            raise error

        try:
            upload_parts(download_dest, file_info, progress, token)
        except HTTPError as error:
            progress.failed(str(error))
            raise error

        try:
            complete_upload(new_article_id, file_info["id"], token)
        except HTTPError as error:
            progress.failed(str(error))
            raise error

    figshare_datafile_link = models_controller.add_figshare_datafile_link(
        datafile_id, file_info["id"], figshare_dataset_version_link_id
    )
    return figshare_datafile_link.id
