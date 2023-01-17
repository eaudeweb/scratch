from .models import Profile


def emails_to_notify():
    return Profile.objects.filter(
        notify=True).values_list("user__email", flat=True).distinct()