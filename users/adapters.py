from allauth.account.adapter import DefaultAccountAdapter


class RoleBasedAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if user.is_staff or user.is_superuser:
            return "/admin-dashboard/"
        return "/dashboard/"
