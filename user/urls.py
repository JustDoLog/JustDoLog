from django.urls import path

from . import views

urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("delete/", views.AccountDeleteView.as_view(), name="account_delete"),
    path("follow/<str:username>/", views.FollowUserView.as_view(), name="follow_user"),
]
