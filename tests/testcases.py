import django
from django.test import SimpleTestCase

# Settings configuration has to be outside of test cases
# to allow test discovery to work.
# May need to wrap in exception catcher, and/or put in test class.


class DjangoSetupTestCase(SimpleTestCase):

    def setUp(self):

        django.setup()

        return super().setUp()
