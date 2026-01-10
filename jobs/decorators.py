from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def seeker_required(view_func):
    """Allow access only to users with 'seeker' role."""
    def wrapper(request, *args, **kwargs):
        user = request.user
        if hasattr(user, 'userprofile') and user.userprofile.role == 'seeker':
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access denied. Job seekers only.")
        return redirect('landing')
    return wrapper


def employer_required(view_func):
    """Allow access only to users with 'employer' role."""
    def wrapper(request, *args, **kwargs):
        user = request.user
        if hasattr(user, 'userprofile') and user.userprofile.role == 'employer':
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access denied. Employers only.")
        return redirect('landing')
    return wrapper


####################################################
# from django.shortcuts import redirect
# from django.contrib import messages
# from functools import wraps


# def seeker_required(view_func):
#     """Allow access only to users with 'seeker' role."""
#     @wraps(view_func)
#     def wrapper(request, *args, **kwargs):
#         user = request.user

#         if hasattr(user, 'userprofile') and user.userprofile.role == 'seeker':
#             return view_func(request, *args, **kwargs)

#         messages.error(request, "Access denied. Job seekers only.")
#         return redirect('login')   # ✅ FIXED
#     return wrapper


# def employer_required(view_func):
#     """Allow access only to users with 'employer' role."""
#     @wraps(view_func)
#     def wrapper(request, *args, **kwargs):
#         user = request.user

#         if hasattr(user, 'userprofile') and user.userprofile.role == 'employer':
#             return view_func(request, *args, **kwargs)

#         messages.error(request, "Access denied. Employers only.")
#         return redirect('login')   # ✅ FIXED
#     return wrapper
