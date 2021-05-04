from main.utils import is_mobile


def hook_user_agent(get_response):
    def middleware(request):
        user_agent = request.META["HTTP_USER_AGENT"]
        if is_mobile(user_agent):
            request.base_template = 'base_mobile.html'
        else:
            request.base_template = 'base.html'
        response = get_response(request)
        return response

    return middleware
