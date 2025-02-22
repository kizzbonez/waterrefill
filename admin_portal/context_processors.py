from django.apps import apps

def inaccessible_apps_context(request):
    """Returns a list of apps that the user CANNOT access."""
    if not request.user or not request.user.is_authenticated:
        return {"inaccessible_apps": []}  # Return empty list for unauthenticated users

    user = request.user
    inaccessible_apps = []
    installed_apps = apps.get_app_configs()  # Get all installed Django apps

    for app in installed_apps:
        models = app.get_models()
        has_access = False

        for model in models:
            # Check if the user has view permission for any model in the app
            perm_codename = f"{model._meta.app_label}.view_{model._meta.model_name}"
            if user.has_perm(perm_codename):
                has_access = True
                break  # If at least one model is accessible, allow the app

        if not has_access:
            inaccessible_apps.append(app.label)  # Store the app label

    return {"inaccessible_apps": inaccessible_apps}






