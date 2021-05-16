from gobiko.apns import APNsClient
from gobiko.apns.exceptions import BadDeviceToken

from pushjack import APNSClient


from botmarket.settings import TEAM_ID, BUNDLE_ID, APNS_KEY_ID, APNS_AUTH_KEY



CLIENT_ISO_PUSH = APNsClient(
    team_id=TEAM_ID,
    bundle_id=BUNDLE_ID,
    auth_key_id=APNS_KEY_ID,
    auth_key_filepath=APNS_AUTH_KEY
)


# CLIENT_ISO_PUSH = APNSClient(
#     certificate=APNS_AUTH_KEY,
#     default_error_timeout=10,
#     default_expiration_offset=2592000,
#     default_batch_size=100,
#     default_retries=5)


text = {"en": "You are the owner of the bot: ", "ru": "Вам добавлены права на бота: "}


def get_text_change_user(language):
    try:
        message = text.get(language)
        if message is None:
            return text.get("en")
        return message
    except Exception:
        return text.get("en")


def send_push_on_all_device(user_tg, title):
    for user in user_tg.user_phone.filter(registration_id__isnull=False):

        send_push(user.registration_id, get_text_change_user(user.language), title)


def send_push(registration_id, message, title):
    try:
        # bulk
        CLIENT_ISO_PUSH.send_message(registration_id, {
            'title': title,
            'body': message
        })
    except BadDeviceToken:
        pass
    except Exception:
        # stange token
        pass
