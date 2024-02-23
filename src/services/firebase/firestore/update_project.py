from configs.firebase import MINI_PROJECTS_COLLECTION
from configs.logger import print_info_log, catch_error
from constants.log_tags import LogTag
from services.firebase.init_firebase import get_firestore


def update_project_status_and_translated_link_by_id(
    project_id: str,
    status: str,
    translated_file_link: str,
    show_logs: bool = False
):
    log_tag = LogTag.UPDATE_PROJECT

    project_fields_to_update = {
        "id": project_id,
        "status": status,
        "translatedFileLink": translated_file_link
    }

    if show_logs:
        print_info_log(
            tag=log_tag,
            message=f"Project fields to update: {project_fields_to_update}"
        )

    firestore = get_firestore()
    project_ref = firestore.collection(MINI_PROJECTS_COLLECTION).document(project_id)
    project_snap = project_ref.get()

    if not project_snap.exists:
        catch_error(
            tag=log_tag,
            error=Exception(f"Mini project with id {project_id} does not exist.")
        )

    project_ref.update({
        "id": project_id,
        "status": status,
        "translatedFileLink": translated_file_link
    })

    if show_logs:
        print_info_log(
            tag=log_tag,
            message=f"Mini project was updated with fields: {project_fields_to_update}"
        )
