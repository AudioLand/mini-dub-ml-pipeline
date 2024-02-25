import logging

import sentry_sdk

from configs.env import IS_DEV_ENVIRONMENT
from constants.log_tags import LogTag
from models.project import ProjectStatus
from services.sentry.init_sentry import init_sentry

init_sentry()

MESSAGE_FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=MESSAGE_FORMAT
)


def catch_error(
    tag: LogTag,
    error: Exception,
    project_id: str | None = None,
):
    logging.error(msg=f"({tag.value}) {str(error)}")

    if not IS_DEV_ENVIRONMENT:
        # Send error to Sentry
        sentry_sdk.capture_exception(error)

        # DO NOT MOVE THIS IMPORT unless error :)
        # TODO: write what error raises if import not here but in top of this file
        from services.firebase.firestore.update_project import update_project_status_and_translated_link_by_id

        # Update project status to 'translationError'
        if project_id is not None:
            update_project_status_and_translated_link_by_id(
                project_id=project_id,
                status=ProjectStatus.TRANSLATION_ERROR.value,
                translated_file_link=""
            )
    raise error


def print_info_log(tag: LogTag, message: str):
    logging.info(msg=f"({tag}) {message}")


if __name__ == "__main__":
    # Test error log
    test_error_tag = LogTag.TEST_ERROR
    print(test_error_tag)
    test_exception = Exception("some error long message")
    catch_error(
        tag=test_error_tag,
        error=test_exception,
    )

    # Test info log (need comment test error log)
    test_info_tag = LogTag.TEST_INFO
    test_message = "test info message"
    print_info_log(
        tag=test_info_tag,
        message=test_message,
    )
