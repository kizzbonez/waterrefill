import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
import json
from django.conf import settings
def send_firebase_notification(title, body, token):
    """
    Sends a push notification to a single Firebase token.
    :param title: Notification title
    :param body: Notification body
    :param token: Device FCM token
    :return: Firebase response
    """
    # cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
    # firebase_admin.initialize_app(cred)
    if not firebase_admin._apps:
        print("Firebase app not initialized")
        return {"error": "Firebase app not initialized"}

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=token,
        )

        response = messaging.send(message)
        print(" Firebase Notification Sent:", response)
        return response

    except messaging.UnregisteredError:
        print(" Error: Token is not registered or expired.")
        return {"error": "Token is not registered or expired"}

    except messaging.InvalidArgumentError as e:
        print(f" Invalid Firebase Request: {e}")
        return {"error": f"Invalid Firebase Request: {e}"}

    except firebase_admin.exceptions.FirebaseError as e:
        print(f" Firebase API Error: {e}")
        return {"error": f"Firebase API Error: {e}"}

    except Exception as e:
        print(f" Unexpected Error: {e}")
        return {"error": f"Unexpected Error: {e}"}