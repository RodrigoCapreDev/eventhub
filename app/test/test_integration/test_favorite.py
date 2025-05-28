from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime

from app.models import User, Event, Venue, Favorite

class FavoriteViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="test_user",
            email="user@ejemplo.com",
            password="password123",
            is_organizer=False,
        )

        self.organizer = User.objects.create_user(
            username="test_organizer",
            email="organizer@ejemplo.com",
            password="password123",
            is_organizer=True,
        )

        self.venue = Venue.objects.create(
            name="Lugar de prueba",
            address="Dirección falsa 123",
            city="Ciudad de prueba",
            capacity=100,
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

    def test_toggle_favorite_authenticated(self):
        """Test agregando y eliminando favoritos para usuarios autenticados"""
        # Login
        self.client.login(username="test_user", password="password123")

        # Agregar a favoritos
        response = self.client.post(reverse('toggle_favorite', args=[self.event1.id]))

        # Verificar el redirect
        self.assertRedirects(response, reverse('event_detail', args=[self.event1.id]))

        # Verificar que el favorito fue agregado
        self.assertTrue(Favorite.objects.filter(user=self.user, event=self.event1).exists())

        # Remover de favoritos
        response = self.client.post(reverse('toggle_favorite', args=[self.event1.id]))

        # Verificar que el favorito fue eliminado
        self.assertFalse(Favorite.objects.filter(user=self.user, event=self.event1).exists())

    def test_toggle_favorite_unauthenticated(self):
        """Test intentando agregar favoritos sin autenticación"""
        # intentar agregar a favoritos sin autenticación
        response = self.client.post(reverse('toggle_favorite', args=[self.event1.id]))

        # Verificar que el usuario no autenticado es redirigido a la página de login
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('toggle_favorite', args=[self.event1.id])}"
        )

    def test_user_favorites_view(self):
        """Test la vista de favoritos del usuario autenticado"""
        # Login
        self.client.login(username="test_user", password="password123")

        # creando favoritos
        Favorite.objects.create(user=self.user, event=self.event1)
        Favorite.objects.create(user=self.user, event=self.event2)

        # Accediendo a la vista de favoritos del usuario
        response = self.client.get(reverse('user_favorites'))

        # Verificar el status code y la plantilla utilizada
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/favorites.html')

        # Verificar que los eventos favoritos están en el contexto
        favorites = response.context['favorites']
        self.assertEqual(favorites.count(), 2)
        self.assertIn(self.event1, [f.event for f in favorites])
        self.assertIn(self.event2, [f.event for f in favorites])
