"""Tests for all serializers of the extension."""

from django.test import TestCase
from django.contrib.auth.models import AnonymousUser

from geokey.projects.tests.model_factories import UserFactory
from geokey_sapelli.serializers import SapelliLogFileSerializer
from geokey_sapelli.tests.model_factories import SapelliLogFileFactory


class SapelliLogFileSerializerTest(TestCase):
    """Tests for SapelliLogFileSerializer."""

    def test_get_file_type(self):
        """Test method `get_file_type`."""
        sapelli_log_file = SapelliLogFileFactory.create()

        serializer = SapelliLogFileSerializer(
            sapelli_log_file,
            context={'user': sapelli_log_file.creator})
        self.assertEqual(
            serializer.get_file_type(sapelli_log_file),
            'SapelliLogFile')

    def test_get_isowner(self):
        """Test method `get_isowner`."""
        owner = UserFactory.create()
        sapelli_log_file = SapelliLogFileFactory.create(**{'creator': owner})

        serializer = SapelliLogFileSerializer(
            sapelli_log_file,
            context={'user': owner})
        self.assertTrue(serializer.get_isowner(sapelli_log_file))

        serializer = SapelliLogFileSerializer(
            sapelli_log_file,
            context={'user': UserFactory.create()})
        self.assertFalse(serializer.get_isowner(sapelli_log_file))

        serializer = SapelliLogFileSerializer(
            sapelli_log_file,
            context={'user': AnonymousUser()})
        self.assertFalse(serializer.get_isowner(sapelli_log_file))

    def test_get_url(self):
        """Test method `get_url`."""
        sapelli_log_file = SapelliLogFileFactory.create()

        serializer = SapelliLogFileSerializer(
            sapelli_log_file,
            context={'user': sapelli_log_file.creator})
        self.assertEqual(
            serializer.get_url(sapelli_log_file),
            sapelli_log_file.file.url)
