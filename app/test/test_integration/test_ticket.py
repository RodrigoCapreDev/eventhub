import datetime

from django.test import Client, TestCase
from django.utils import timezone

from app.models import Category, Event, EventStatus, Ticket, TicketType, User, Venue


class BaseTicketTestCase(TestCase):
    """Clase base con la configuración común para todos los tests de tickets."""

    def setUp(self):
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear un usuario regular
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        # Crear categoría de prueba
        self.category = Category.objects.create(name="Categoría de prueba")

        # Crear venue de prueba
        self.venue = Venue.objects.create(
            name="Lugar de prueba",
            address="Calle Falsa 123",
            city="Ciudad Test",
            capacity=100,
        )

        # Crear algunos eventos de prueba
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        self.event1.categories.add(self.category)

        self.event2 = Event.objects.create(
            title="Evento 2",
            description="Descripción del evento 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            venue=self.venue,
        )
        self.event2.categories.add(self.category)

        #Tipos de ticket
        self.ticket_type = TicketType.objects.create(
            name="Entrada General",
            price=100.00,
        )

        # Cliente para hacer peticiones
        self.client = Client()


class EventStatusTicketIntegrationTest(BaseTicketTestCase):
    """Test que verifica la posibilidad de generar ticket dependiendo del estado del evento"""

    def test_user_can_buy_ticket_for_active_event(self):
        """Permite comprar ticket si el estado es activo"""
        self.event1.status = EventStatus.ACTIVE
        self.event1.available_tickets = 10
        self.event1.save()

        success, result = Ticket.new(self.event1, self.regular_user, self.ticket_type, 1)
        self.assertTrue(success)
        self.assertIsInstance(result, int)  # El código del ticket devuelto debe ser un string

    def test_user_can_buy_ticket_for_rescheduled_event(self):
        """Permite comprar ticket si el estado es reprogramado"""
        self.event1.previous_date = timezone.now() + datetime.timedelta(days=1)
        self.event1.scheduled_at = timezone.now() + datetime.timedelta(days=5)
        self.event1.status = EventStatus.RESCHEDULED
        self.event1.available_tickets = 10
        self.event1.save()

        success, result = Ticket.new(self.event1, self.regular_user, self.ticket_type, 1)
        self.assertTrue(success)
        self.assertIsInstance(result, int)  # El código del ticket devuelto debe ser un string

    def test_user_cannot_buy_ticket_for_sold_out_event(self):
        """No permite comprar ticket si el evento está agotado"""
        self.event1.available_tickets = 0
        self.event1.status = EventStatus.SOLD_OUT
        self.event1.save()

        success, errors = Ticket.new(self.event1, self.regular_user, self.ticket_type, 1)
        self.assertFalse(success)
        self.assertIn("status", errors)

    def test_user_cannot_buy_ticket_for_finished_event(self):
        """No permite comprar ticket si el evento ya finalizó"""
        self.event1.scheduled_at = timezone.now() - datetime.timedelta(days=5)
        self.event1.status = EventStatus.FINISHED
        self.event1.save()

        success, errors = Ticket.new(self.event1, self.regular_user, self.ticket_type, 1)
        self.assertFalse(success)
        self.assertIn("status", errors)

    def test_user_cannot_buy_ticket_for_cancelled_event(self):
        """No permite comprar ticket si el evento fue cancelado"""
        self.event1.status = EventStatus.CANCELLED
        self.event1.save()

        success, errors = Ticket.new(self.event1, self.regular_user, self.ticket_type, 1)
        self.assertFalse(success)
        self.assertIn("status", errors)


        