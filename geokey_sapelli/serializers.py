"""All serializers for the extension."""

from rest_framework import serializers

from geokey.users.serializers import UserSerializer
from geokey_sapelli.models import SapelliLogFile


class SapelliLogFileSerializer(serializers.ModelSerializer):
    """Serializer for geokey_sapelli.models.SapelliLogFile instances."""

    creator = UserSerializer(fields=('id', 'display_name'))
    isowner = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()

    class Meta:
        """Class meta information."""

        model = SapelliLogFile
        fields = (
            'id', 'name', 'created_at', 'uploaded_at', 'creator', 'isowner',
            'url', 'file_type')

    def get_file_type(self, obj):
        """
        Return the type of the SapelliLogFile.

        Parameters
        ----------
        obj : geokey_sapelli.models.SapelliLogFile
            The instance that is being serialised.

        Returns
        -------
        str
            The type of the instance, in this case it's 'SapelliLogFile'.
        """
        return obj.type_name

    def get_isowner(self, obj):
        """
        Return `True` if the user is the creator of this file.

        Parameters
        ----------
        obj : geokey_sapelli.models.SapelliLogFile
            The instance that is being serialised.

        Returns
        -------
        Boolean
            Indicating if user created the file.
        """
        user = self.context.get('user')

        if not user.is_anonymous():
            return obj.creator == user

        return False

    def get_url(self, obj):
        """
        Return the URL to access this file.

        Parameters
        ----------
        obj : geokey_sapelli.models.SapelliLogFile
            The instance that is being serialised.

        Returns
        -------
        str
            The URL to access the file on client side.
        """
        return obj.file.url
