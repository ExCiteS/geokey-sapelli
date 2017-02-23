"""Template tags for the extension."""

from django import template


register = template.Library()


@register.filter
def is_admin(project, user):
    """Tag wrapper to check if user is admin of the project (or superuser)."""
    return user.is_superuser or project.is_admin(user)


@register.filter
def can_contribute(project, user):
    """Tag wrapper to check if user can contribute to the project."""
    return user.is_superuser or project.can_contribute(user)
