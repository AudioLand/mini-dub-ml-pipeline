import logging

import sentry_sdk

from configs.env import IS_DEV_ENVIRONMENT
from constants.log_tags import LogTag
from models.project import ProjectStatus
from services.sentry.init_sentry import init_sentry

init_sentry()

ERROR_MESSAGE_FORMAT = "[%(asctime)s] ERROR - %(levelname)s: %(message)s"
INFO_MESSAGE_FORMAT = "[%(asctime)s] INFO - %(message)s"


def catch_error(
    tag: LogTag,
    error: Exception,
    project_id: str | None = None,
    user_email: str | None = None
):
    # DO NOT MOVE THIS IMPORT unless error :)
    # TODO: write what error raises if import not here but in top of this file
    from services.firebase.firestore.update_project import update_project_status_and_translated_link_by_id

    logging.basicConfig(
        level=logging.ERROR,
        format=ERROR_MESSAGE_FORMAT
    )
    logging.error(msg=f"({tag.value}) {str(error)}")

    if IS_DEV_ENVIRONMENT:
        return

    # Send error to Sentry
    sentry_sdk.capture_exception(error)

    # Update project status to 'translationError'
    if project_id is not None:
        update_project_status_and_translated_link_by_id(
            project_id=project_id,
            status=ProjectStatus.TRANSLATION_ERROR.value,
            translated_file_link=""
        )
        # # Send email to user about project error
        # if user_email is not None:
        #     send_email_with_api(
        #         user_email=user_email,
        #         email_template=EmailTemplate.ProjectError
        #     )

    raise error


def print_info_log(tag: LogTag, message: str):
    logging.basicConfig(
        level=logging.INFO,
        format=INFO_MESSAGE_FORMAT,
    )
    logging.info(msg=f"({tag.value}) {message}")


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
