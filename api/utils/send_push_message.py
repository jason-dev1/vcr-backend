from requests.exceptions import ConnectionError, HTTPError
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)


def send_push_message(token, title, message, extra=None):
    """Function for calling Expo's notification service to send notification using token"""
    try:
        response = PushClient().publish(
            PushMessage(to=token,
                        title=title,
                        body=message,
                        data=extra))
    except PushServerError:
        print('Notification formatting/validation error')
        raise
    except (ConnectionError, HTTPError):
        print('Could not send notification to client due to connection problem')
        raise

    try:
        response.validate_response()
    except DeviceNotRegisteredError:
        print('Notification push token is inactive')
    except PushTicketError:
        print('Notification error')
        raise
