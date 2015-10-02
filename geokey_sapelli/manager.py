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

    def exists_by_sapelli_info(self, user, sapelli_project_id, sapelli_project_fingerprint):
        """
        Checks whether or not there is a SapelliProject with the given
		sapelli_project_id and sapelli_project_fingerprint which the user can
		access and contribute to.
        Currently this is restricted to project admins.

        Parameter
        ---------
        user : geokey.users.models.User
            User projects are filtered for
        sapelli_project_id : int
            Together with sapelli_project_fingerprint this uniquely identifies a SapelliProject
        sapelli_project_fingerprint : int
            Together with sapelli_project_id this uniquely identifies a SapelliProject
        Returns
        -------
        bool
        """
        try:
            self.get_single_by_sapelli_info(user, sapelli_project_id, sapelli_project_fingerprint)
        except self.model.DoesNotExist:
            return False
        else:
            return True
    
    def get_single_by_sapelli_info(self, user, sapelli_project_id, sapelli_project_fingerprint):
        """
        Returns a single Sapelli project, identified by the given
		sapelli_project_id and sapelli_project_fingerprint which the user can the user can access and contribute to.
        Currently this is restricted to project admins.

        Parameter
        ---------
        user : geokey.users.models.User
            User projects are filtered for
        sapelli_project_id : int
            Together with sapelli_project_fingerprint this uniquely identifies a SapelliProject
        sapelli_project_fingerprint : int
            Together with sapelli_project_id this uniquely identifies a SapelliProject
        Returns
        -------
        geokey_sapelli.SapelliProject
        """
        return self.get_list(user).get(sapelli_id=sapelli_project_id, sapelli_fingerprint=sapelli_project_fingerprint)
    
    def get_single(self, user, project_id):
        """
        Returns a single Sapelli project the user can access and contribute to.
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
