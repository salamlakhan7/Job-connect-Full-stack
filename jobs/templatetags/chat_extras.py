# jobs/templatetags/chat_extras.py
# from django import template

# register = template.Library()

# @register.filter
# def is_image(url):
#     if not url:
#         return False
#     url = url.lower()
#     return url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))


from django import template

register = template.Library()

@register.filter
def is_image(url):
    if not url:
        return False
    url = url.lower()
    return url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
