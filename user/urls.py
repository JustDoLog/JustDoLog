from django.urls import path

from . import views

urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("follow/<str:username>/", views.FollowUserView.as_view(), name="follow_user"),
    path("profile/update/", views.update_profile, name="update_profile"),
    path("profile/upload-image/", views.upload_profile_image, name="upload_profile_image"),
    path("profile/remove-image/", views.remove_profile_image, name="remove_profile_image"),
    path("profile/toggle-edit/", views.toggle_edit_mode, name="toggle_edit_mode"),
    path("profile/form/", views.profile_form, name="profile_form"),
    path("delete/", views.account_delete, name="account_delete"),
]
