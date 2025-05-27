import re
import datetime
from django.utils import timezone
from playwright.sync_api import expect

from app.models import Event, User, Venue, Favorite
from app.test.test_e2e.base import BaseE2ETest

class FavoritesE2ETest(BaseE2ETest):

    def setUp(self):
        super().setUp()

        self.venue = Venue.objects.create(
            name="Lugar de prueba",
            address="Dirección falsa 123",
            city="Ciudad de prueba",
            capacity=100,
        )

        self.organizer = User.objects.create_user(
            username="test_organizer",
            email="organizer@ejemplo.com",
            password="password123",
            is_organizer=True,
        )

        self.user = User.objects.create_user(
            username="test_user",
            email="user@ejemplo.com",
            password="password123",
            is_organizer=False,
        )

        self.event1 = Event.objects.create(
            title="Test Event 1",
            description="Descripcion 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            available_tickets=100
        )

        self.event2 = Event.objects.create(
            title="Test Event 2",
            description="Descripcion 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            venue=self.venue,
            available_tickets=100
        )

    def test_add_remove_favorite(self):
        """Test agregando y eliminando favoritos para usuarios autenticados"""
        # Login como usuario normal
        self.login_user("test_user", "password123")

        # ingresando a los detalles del evento
        self.page.goto(f"{self.live_server_url}/events/{self.event1.id}/")

        # Verificar que el botón de agregar a favoritos esté visible
        favorite_button = self.page.get_by_role("button", name=re.compile("Añadir a favoritos"))
        expect(favorite_button).to_be_visible()

        # Clickear el botón de agregar a favoritos
        favorite_button.click()

        # Verificarque haya cambiado a "Quitar de favoritos"
        remove_button = self.page.get_by_role("button", name=re.compile("Quitar de favoritos"))
        expect(remove_button).to_be_visible()

        # ir a la página de favoritos
        self.page.goto(f"{self.live_server_url}/favorites/")

        # Verificar que el evento está en favoritos
        event_title = self.page.get_by_text("Test Event 1")
        expect(event_title).to_be_visible()

        # Sacar de favoritos
        remove_button = self.page.get_by_role("button", name=re.compile("Quitar de favoritos"))
        remove_button.click()

        # Verificar que redirecciona a los detalles del evento
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event1.id}/")

        # volver a la página de favoritos
        self.page.goto(f"{self.live_server_url}/favorites/")

        # Verificar que el evento ya no está en favoritos
        empty_message = self.page.get_by_text("No tienes eventos favoritos")
        expect(empty_message).to_be_visible()

    def test_favorites_page_requires_login(self):
        """Test que verifica que la página de favoritos requiere autenticación"""
        # Limpiar cookies para asegurarnos de que el usuario no está autenticado
        self.context.clear_cookies()

        # Intentar acceder a la página de favoritos sin autenticación
        self.page.goto(f"{self.live_server_url}/favorites/")

        # Verificar que redirecciona a la página de login
        expect(self.page).to_have_url(re.compile(r"/accounts/login/"))
