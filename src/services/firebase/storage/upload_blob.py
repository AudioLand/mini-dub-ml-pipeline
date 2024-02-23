from configs.firebase import bucket
from configs.logger import catch_error, print_info_log
from constants.log_tags import LogTag


def upload_blob(
    source_file_name: str,
    destination_blob_name: str,
    project_id: str,
    show_logs: bool = False
):
    try:
        if show_logs:
            print_info_log(
                tag=LogTag.UPLOAD_BLOB,
                message=f"Local file path: {source_file_name}"
            )

        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)

        if show_logs:
            print_info_log(
                tag=LogTag.UPLOAD_BLOB,
                message=f"File uploaded to bucket on path {destination_blob_name}"
            )

        blob.make_public()
        public_link = blob.public_url

        if show_logs:
            print_info_log(
                tag=LogTag.UPLOAD_BLOB,
                message=f"Public url for this file: {public_link}"
            )

        return public_link

    except Exception as e:
        catch_error(
            tag=LogTag.UPLOAD_BLOB,
            error=e,
            project_id=project_id
        )
