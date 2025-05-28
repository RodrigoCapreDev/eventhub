import datetime

from django.test import TestCase
from django.utils import timezone

from app.models import Event, User, Venue, Notification, Ticket
import uuid

class EventModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        self.venue = Venue.objects.create(
            name="Lugar de prueba", 
            address="Dirección falsa 123",
            city="Ciudad de prueba",
            capacity=100,
        )

    def test_event_creation(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
        )
        """Test que verifica la creación correcta de eventos"""
        self.assertEqual(event.title, "Evento de prueba")
        self.assertEqual(event.description, "Descripción del evento de prueba")
        self.assertEqual(event.organizer, self.organizer)
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)

    def test_event_validate_with_valid_data(self):
        """Test que verifica la validación de eventos con datos válidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("Título válido", "Descripción válida", scheduled_at)
        self.assertEqual(errors, {})

    def test_event_validate_with_empty_title(self):
        """Test que verifica la validación de eventos con título vacío"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("", "Descripción válida", scheduled_at)
        self.assertIn("title", errors)
        self.assertEqual(errors["title"], "Por favor ingrese un título")

    def test_event_validate_with_empty_description(self):
        """Test que verifica la validación de eventos con descripción vacía"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("Título válido", "", scheduled_at)
        self.assertIn("description", errors)
        self.assertEqual(errors["description"], "Por favor ingrese una descripción")

    def test_event_new_with_valid_data(self):
        """Test que verifica la creación de eventos con datos válidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        success, errors = Event.new(
            title="Nuevo evento",
            description="Descripción del nuevo evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
        )

        self.assertTrue(success)
        self.assertIsNone(errors)

        # Verificar que el evento fue creado en la base de datos
        new_event = Event.objects.get(title="Nuevo evento")
        self.assertEqual(new_event.description, "Descripción del nuevo evento")
        self.assertEqual(new_event.organizer, self.organizer)

    def test_event_new_with_invalid_data(self):
        """Test que verifica que no se crean eventos con datos inválidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        initial_count = Event.objects.count()

        # Intentar crear evento con título vacío
        success, errors = Event.new(
            title="",
            description="Descripción del evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
        )

        self.assertFalse(success)
        self.assertIn("title", errors)

        # Verificar que no se creó ningún evento nuevo
        self.assertEqual(Event.objects.count(), initial_count)

    def test_event_update(self):
        """Test que verifica la actualización de eventos"""
        new_title = "Título actualizado"
        new_description = "Descripción actualizada"
        new_scheduled_at = timezone.now() + datetime.timedelta(days=3)
        new_venue = Venue.objects.create(
            name="Nuevo lugar de prueba",
            address="Nueva dirección 456",
            city="Nueva ciudad de prueba",
            capacity=200,
        )

        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )

        event.update(
            title=new_title,
            description=new_description,
            scheduled_at=new_scheduled_at,
            organizer=self.organizer,
            venue=new_venue,
        )

        # Recargar el evento desde la base de datos
        updated_event = Event.objects.get(pk=event.pk)

        self.assertEqual(updated_event.title, new_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at.time(), new_scheduled_at.time())
        self.assertEqual(updated_event.venue, new_venue)

    def test_event_update_partial(self):
        """Test que verifica la actualización parcial de eventos"""
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )

        original_title = event.title
        original_scheduled_at = event.scheduled_at
        new_description = "Solo la descripción ha cambiado"
        original_venue = event.venue

        event.update(
            title=None,  # No cambiar
            description=new_description,
            scheduled_at=None,  # No cambiar
            organizer=None,  # No cambiar
            venue=None,  # No cambiar
        )

        # Recargar el evento desde la base de datos
        updated_event = Event.objects.get(pk=event.pk)

        # Verificar que solo cambió la descripción
        self.assertEqual(updated_event.title, original_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at, original_scheduled_at)
        self.assertEqual(updated_event.venue, original_venue)

    def test_event_filter_futuros(self):
        """Test que verifica que el filtrado de eventos futuros funciona correctamente"""
        pasado = timezone.now() - datetime.timedelta(days=1)
        futuro = timezone.now() + datetime.timedelta(days=1)

        # Crear evento pasado
        Event.objects.create(
            title="Evento pasado",
            description="Evento que ya pasó",
            scheduled_at=pasado,
            organizer=self.organizer,
            venue=self.venue,
        )
        # Crear evento futuro
        Event.objects.create(
            title="Evento futuro",
            description="Evento que será en el futuro",
            scheduled_at=futuro,
            organizer=self.organizer,
            venue=self.venue,
        )

        eventos_futuros = Event.objects.filter(scheduled_at__gte=timezone.now())

        # Verifico que solo esté el evento futuro
        self.assertTrue(all(e.scheduled_at >= timezone.now() for e in eventos_futuros))
        self.assertTrue(any(e.title == "Evento futuro" for e in eventos_futuros))
        self.assertFalse(any(e.title == "Evento pasado" for e in eventos_futuros))

    def test_event_update_creates_notification_when_date_or_venue_changes(self):
        """Test que verifica que se crea una notificación al actualizar la fecha o el lugar del evento"""
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
         # Crear usuarios con tickets
        user1 = User.objects.create_user(username="user1", email="user1@example.com", password="test123")
        user2 = User.objects.create_user(username="user2", email="user2@example.com", password="test123")

        # Crear tickets para esos usuarios
        Ticket.objects.create(
            user=user1,
            event=event,
            total_price=100.00,
            ticket_type_id=1,
            ticket_code=f"TEST-{uuid.uuid4().hex[:8]}"
        )
        Ticket.objects.create(
            user=user2,
            event=event,
            total_price=100.00,
            ticket_type_id=1,
            ticket_code=f"TEST-{uuid.uuid4().hex[:8]}"
        )

        # Asegurar que no tengan notificaciones previas
        self.assertEqual(Notification.objects.filter(user=user1).count(), 0)
        self.assertEqual(Notification.objects.filter(user=user2).count(), 0)

        # Cambiar la fecha del evento
        new_scheduled_at = timezone.now() + datetime.timedelta(days=2)
        event.update(scheduled_at=new_scheduled_at)

        # Cambiar el lugar del evento
        new_venue = Venue.objects.create(
            name="Nuevo lugar de prueba",
            address="Nueva dirección 456",
            city="Nueva ciudad de prueba",
            capacity=200,
        )
        event.update(venue=new_venue)

        # Verificar que se hayan creado notificaciones para ambos usuarios
        user_notifs = Notification.objects.filter(user=user1, event=event)
        user2_notifs = Notification.objects.filter(user=user2, event=event)

        self.assertEqual(user_notifs.count(), 2)
        self.assertEqual(user2_notifs.count(), 2)

        # Verificar los mensajes
        messages = list(user_notifs.values_list("message", flat=True))
        self.assertTrue(
        any("Nueva fecha" in msg for msg in messages),
        msg="No se encontró mensaje que confirme actualización de fecha"
        )
        self.assertTrue(
        any("Nuevo lugar" in msg for msg in messages),
        msg="No se encontró mensaje que confirme actualización de lugar"
        )

