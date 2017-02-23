"""Tests for Sapelli tags of the extension."""

from django.test import TestCase

from geokey.projects.tests.model_factories import UserFactory, ProjectFactory
from geokey_sapelli.templatetags import sapelli_tags


class IsAdminTest(TestCase):
    """Test tag `is_admin`."""

    def setUp(self):
        """Set up test."""
        self.admin = UserFactory.create()
        self.contributor = UserFactory.create()
        self.regular_user = UserFactory.create()
        self.project = ProjectFactory.create(
            add_admins=[self.admin],
            add_contributors=[self.contributor],
            **{'isprivate': True})

    def test_when_user_is_admin(self):
        """Test with admin."""
        self.assertTrue(
            sapelli_tags.is_admin(self.project, self.admin))

    def test_when_user_is_contributor(self):
        """Test with contributor."""
        self.assertFalse(
            sapelli_tags.is_admin(self.project, self.contributor))

    def test_when_user_is_regular(self):
        """Test with regular user."""
        self.assertFalse(
            sapelli_tags.is_admin(self.project, self.regular_user))


class CanContributeTest(TestCase):
    """Test tag `can_contribute."""

    def setUp(self):
        """Set up test."""
        self.admin = UserFactory.create()
        self.contributor = UserFactory.create()
        self.regular_user = UserFactory.create()
        self.project = ProjectFactory.create(
            add_admins=[self.admin],
            add_contributors=[self.contributor],
            **{'isprivate': True})

    def test_when_user_is_admin(self):
        """Test with admin."""
        self.assertTrue(
            sapelli_tags.can_contribute(self.project, self.admin))

    def test_when_user_is_contributor(self):
        """Test with contributor."""
        self.assertTrue(
            sapelli_tags.can_contribute(self.project, self.contributor))

    def test_when_user_is_regular(self):
        """Test with regular user."""
        self.assertFalse(
            sapelli_tags.can_contribute(self.project, self.regular_user))
