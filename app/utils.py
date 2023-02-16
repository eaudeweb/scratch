import string

import requests

from django.conf import settings
from .models import Profile


class TenderSource:
    TED = 'TED'
    UNGM = 'UNGM'


def emails_to_notify():
    return Profile.objects.filter(
        notify=True).values_list("user__email", flat=True).distinct()


def log_tenders_update(tender_source: TenderSource):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            headers = {
                "accept": "application/json",
                "X-Cachet-Application": "Demo",
                "content-type": "application/json",
                "X-Cachet-Token": settings.APP_TOKEN
            }

            url = settings.APP_URL + "/api/v1/incidents"
            payload = {
                "visible": 1,
                "notify": False,
                "name": f"Importing new {tender_source} tenders...",
                "message": f"Importing new {tender_source} tenders...",
                "status": 3,
            }
            response_incident = requests.post(
                url, json=payload, headers=headers)

            try:
                return_value = fn(*args, **kwargs)

                url = settings.APP_URL + \
                    f"/api/v1/incidents/{response_incident.json()['data']['id']}/updates"
                payload = {
                    "message": return_value,
                    "status": 4
                }
                requests.post(url, json=payload, headers=headers)

                return return_value
            except Exception as error:
                url = settings.APP_URL + \
                    f"/api/v1/incidents/{response_incident.json()['data']['id']}/updates"
                payload = {
                    "message": f'{tender_source} tenders update failed: {error}',
                    "status": 2
                }
                requests.post(url, json=payload, headers=headers)
                raise

        return wrapper

    return decorator


def dt_to_json(dt):
    return dt.strftime(settings.JSON_DATETIME_FORMAT) if dt else None


def transform_vendor_name(vendor_name):
    vendor_name = vendor_name.upper()
    vendor_name = vendor_name.replace("(CO-CONTRACTOR)", "")
    vendor_name = vendor_name.replace("(GROUP LEADER)", "")
    vendor_name = vendor_name.strip()
    vendor_name = vendor_name.translate(str.maketrans('', '', string.punctuation))

    return vendor_name
