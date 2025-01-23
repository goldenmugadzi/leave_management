from django.urls import reverse
from it.users.models import UserProfile
from decouple import config
from it.users.views import email_notification
from datetime import datetime

def send_appraisal_notifications(user_object: UserProfile, notification_type: str, notification_id: int|str, url: str):
    try:
        domain_name = config('be_url')
        # url = reverse("url", kwargs={"pk": kra_obj_id})
        redirect_url = f"{domain_name}{url}"     
        
        hour = datetime.now().hour
        greetings = {(0, 4): "Good night!",(5, 11): "Good morning!",(12, 16): "Good afternoon!",(17, 20): "Good evening!",(21, 23): "Good night!"}
        subject = next((msg for (start, end), msg in greetings.items() if start <= hour <= end), "Hello!")
        message = "We kindly request that you review and take necessary action regarding this "
        
        print("=====================+>>>>>>> ", user_object)
        print()
        print()
        response = email_notification(subject=subject, user=user_object, message=message, redirect_url=redirect_url, url=url, notification_type=notification_type, notification_id=notification_id, cc_recipients=[])
        return response.status_code
    except Exception as e:
        raise Exception(f"send_appraisal_notifications handler failed with error: {e}")