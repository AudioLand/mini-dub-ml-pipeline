import sentry_sdk

from configs.env import SENTRY_DSN, ENVIRONMENT


def init_sentry():
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT
    )
