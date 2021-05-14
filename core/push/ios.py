from gobiko.apns import APNsClient
from gobiko.apns.exceptions import BadDeviceToken

from botmarket.settings import TEAM_ID, BUNDLE_ID, APNS_KEY_ID, APNS_AUTH_KEY

CLIENT_ISO_PUSH = APNsClient(
    team_id=TEAM_ID,
    bundle_id=BUNDLE_ID,
    auth_key_id=APNS_KEY_ID,
    auth_key_filepath=APNS_AUTH_KEY
)

# CLIENT_ISO_PUSH.send_message('f0c328b3a8dc8cc8e9c5a4b023d5ccd361f151217f420aaf3f92fc44fcf63a4d', 'скучаю')
