from django.db.models import Manager


class SapelliProjectManager(Manager):
    """
    Custom manager for geokey_sapelli.SapelliProject.
    """
    def get_list(self, user):
        """
        Returns all projects the user can access and contribute to.
        Currently this is restricted to project admins.

        Parameter
        ---------
        user : geokey.users.models.User
            User projects are filtered for

        Returns
        -------
        django.db.models.query.QuerySet
            List of geokey_sapelli.SapelliProject
        """
        return self.get_queryset().filter(project__admins=user)

    def get_single(self, user, project_id):
        """
        Returns a single projects the user can access and contribute to.
        Currently this is restricted to project admins.

        Parameter
        ---------
        user : geokey.users.models.User
            User projects are filtered for
        project_id : int
            Identifies the project in the data base

        Returns
        -------
        geokey_sapelli.SapelliProject
        """
        return self.get_list(user).get(pk=project_id)
