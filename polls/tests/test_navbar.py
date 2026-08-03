from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class NavigationTemplateTests(SimpleTestCase):
    def test_base_template_renders_single_primary_navbar_with_vehicle_link(self):
        request = RequestFactory().get("/")
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_staff=False,
            username="teste",
        )
        request.resolver_match = SimpleNamespace(url_name="home")

        html = render_to_string("base.html", {"user": request.user}, request=request)

        self.assertEqual(
            html.count('class="navbar navbar-expand-lg navbar-dark bg-primary mb-4"'),
            1,
            "A base template deve renderizar apenas uma navbar principal.",
        )
        self.assertIn(">Veículos<", html)
