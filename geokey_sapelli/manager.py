from django.db.models import Manager
from django.core.exceptions import PermissionDenied


class SapelliProjectManager(Manager):
    """
    Custom manager for geokey_sapelli.SapelliProject.
    """
    def get_list_for_administration(self, user):
        """
        Returns all SapelliProjects the user can administrate.

        Parameter
        ---------
        user : geokey.users.models.User
            User projects are filtered for

        Returns
        -------
        django.db.models.query.QuerySet
            List of geokey_sapelli.SapelliProject
        """
        return self.get_queryset().filter(geokey_project__admins=user)

    def get_list_for_contribution(self, user):
        """
        Returns all SapelliProjects the user can access and contribute to.

        Parameter
        ---------
        user : geokey.users.models.User
            User projects are filtered for

        Returns
        -------
        List of geokey_sapelli.SapelliProject
        """
        return [sapelli_project for sapelli_project in self.get_queryset() if sapelli_project.geokey_project.can_contribute(user)]

    def exists_for_contribution_by_sapelli_info(self, user, sapelli_project_id, sapelli_project_fingerprint):
        """
        Checks whether or not there is a SapelliProject with the given sapelli_project_id and
        sapelli_project_fingerprint which the user can access and contribute to.

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
            self.get_single_for_contribution_by_sapelli_info(user, sapelli_project_id, sapelli_project_fingerprint)
        except (PermissionDenied, self.model.DoesNotExist):
            return False
        else:
            return True

    def get_single_for_contribution_by_sapelli_info(self, user, sapelli_project_id, sapelli_project_fingerprint):
        """
        Returns a single Sapelli project, identified by the given sapelli_project_id and
        sapelli_project_fingerprint which the user can the user can access and contribute to.

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
        for sapelli_project in self.get_queryset():
            if sapelli_project.sapelli_id == int(sapelli_project_id) and sapelli_project.sapelli_fingerprint == int(sapelli_project_fingerprint):
                if sapelli_project.geokey_project.can_contribute(user):
                    return sapelli_project
                else:
                    raise PermissionDenied('User cannot contribute to project (id: %s).' % sapelli_project.geokey_project.id)
        raise self.model.DoesNotExist

    def get_single_for_administration(self, user, project_id):
        """
        Returns a single Sapelli project the user can administrate.

        Parameter
        ---------
        user : geokey.users.models.User
            User projects are filtered for
        project_id : int
            Identifies the GeoKey project in the data base

        Returns
        -------
        geokey_sapelli.SapelliProject
        """
        return self.get_list_for_administration(user).get(pk=project_id)

    def get_single_for_contribution(self, user, project_id):
        """
        Returns a single Sapelli project the user can access and contribute to.

        Parameter
        ---------
        user : geokey.users.models.User
            User projects are filtered for
        project_id : int
            Identifies the GeoKey project in the data base

        Returns
        -------
        geokey_sapelli.SapelliProject
        """
        for sapelli_project in self.get_list_for_contribution(user):
            if sapelli_project.geokey_project.id == int(project_id):
                return sapelli_project
        raise self.model.DoesNotExist
