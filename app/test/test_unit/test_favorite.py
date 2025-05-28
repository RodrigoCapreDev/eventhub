import datetime
from django.test import TestCase
from django.utils import timezone
from app.models import Favorite, Event, User, Venue

class FavoriteModelTest(TestCase):
    def setUp(self):
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

        self.event = Event.objects.create(
            title="Test Event",
            description="Descripcion de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            available_tickets=100
        )

    def test_favorite_creation(self):
        """Test que verifica la creacion del favorito"""
        favorite = Favorite.objects.create(
            user=self.user,
            event=self.event
        )

        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.event, self.event)

    def test_favorite_unique_constraint(self):
        """Test que verifica la relacion entre el usuario y el evento"""
        Favorite.objects.create(
            user=self.user,
            event=self.event
        )

        with self.assertRaises(Exception):
            Favorite.objects.create(
                user=self.user,
                event=self.event
            )

    def test_favorite_string_representation(self):
        """Test de la representacion de texto del favorito"""
        favorite = Favorite.objects.create(
            user=self.user,
            event=self.event
        )

        expected_string = f"{self.user.username} - {self.event.title}"
        self.assertEqual(str(favorite), expected_string)
