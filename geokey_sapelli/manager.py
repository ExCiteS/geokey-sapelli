"""Manager for the extension."""

from django.db.models import Manager
from django.core.exceptions import PermissionDenied


class SapelliProjectManager(Manager):
    """Custom manager for geokey_sapelli.SapelliProject."""

    def get_list_for_administration(self, user):
        """
        Return all Sapelli projects the user can administrate.

        Parameters
        ----------
        user : geokey.users.models.User
            User projects are filtered for.

        Returns
        -------
        django.db.models.query.QuerySet
            List of Sapelli projects.
        """
        if user.is_superuser:
            return self.get_queryset()

        return self.get_queryset().filter(geokey_project__admins=user)

    def get_list_for_contribution(self, user):
        """
        Return all Sapelli projects the user can access and contribute to.

        Parameters
        ----------
        user : geokey.users.models.User
            User projects are filtered for.

        Returns
        -------
        List of Sapelli projects.
        """
        if user.is_superuser:
            return self.get_queryset()

        return [sapelli_project for sapelli_project in self.get_queryset() if sapelli_project.geokey_project.can_contribute(user)]

    def exists_for_contribution_by_sapelli_info(self, sapelli_project_id, sapelli_project_fingerprint):
        """
        Check for Sapelli project with the given Sapelli info.

        Parameters
        ----------
        sapelli_project_id : int
            Together with sapelli_project_fingerprint this uniquely identifies a SapelliProject
        sapelli_project_fingerprint : int
            Together with sapelli_project_id this uniquely identifies a SapelliProject

        Returns
        -------
        bool
        """
        try:
            self.get_single_for_contribution_by_sapelli_info(None, sapelli_project_id, sapelli_project_fingerprint)
        except (PermissionDenied, self.model.DoesNotExist):
            return False
        else:
            return True

    def get_single_for_contribution_by_sapelli_info(self, user, sapelli_project_id, sapelli_project_fingerprint):
        """
        Return a single Sapelli project, identified by the given
        sapelli_project_id and sapelli_project_fingerprint, that the user can
        access and contribute to (if user is provided).

        Parameters
        ----------
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
                if not user or sapelli_project.geokey_project.can_contribute(user):
                    return sapelli_project
                else:
                    raise PermissionDenied('User cannot contribute to project')
        raise self.model.DoesNotExist

    def get_single_for_administration(self, user, project_id):
        """
        Return a single Sapelli project the user can administrate.

        Parameters
        ----------
        user : geokey.users.models.User
            User projects are filtered for.
        project_id : int
            Identifies the GeoKey project in the database.

        Returns
        -------
        geokey_sapelli.SapelliProject
        """
        return self.get_list_for_administration(user).get(
            geokey_project__id=project_id)

    def get_single_for_contribution(self, user, project_id):
        """
        Return a single Sapelli project the user can access and contribute to.

        Parameters
        ----------
        user : geokey.users.models.User
            User projects are filtered for.
        project_id : int
            Identifies the GeoKey project in the database.

        Returns
        -------
        geokey_sapelli.SapelliProject
        """
        for sapelli_project in self.get_list_for_contribution(user):
            if sapelli_project.geokey_project.id == int(project_id):
                return sapelli_project
        raise self.model.DoesNotExist
