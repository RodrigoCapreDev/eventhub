import datetime
import uuid

from django.test import TestCase
from django.utils import timezone

from app.models import Event, EventStatus, Notification, Ticket, User, Venue


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

        eventos_futuros = Event.upcoming()
        titulos = list(eventos_futuros.values_list("title", flat=True))

        self.assertIn("Evento futuro", titulos)
        self.assertNotIn("Evento pasado", titulos)

    def test_event_status_activo_por_defecto(self):
        """Test que verifica que los eventos nuevos son activos por defecto"""
        event = Event.objects.create(
            title="Evento activo",
            description="El nuevo evento debería ser activo por defecto",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        self.assertEqual(event.status, EventStatus.ACTIVE)
    
    def test_event_status_agotado(self):
        """Test que verifica que un evento se marca como agotado cuando no hay entradas disponibles"""
        event = Event.objects.create(
            title="Evento agotado",
            description="Evento sin entradas disponibles",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            available_tickets=0,
        )
        event.update_status()
        self.assertEqual(event.status, EventStatus.SOLD_OUT)

    def test_event_status_finalizado(self):
        """Test que verifica que un evento se marca como finalizado cuando la fecha programada ya ha pasado"""
        event = Event.objects.create(
            title="Evento finalizado",
            description="Evento que ya ha finalizado",
            scheduled_at=timezone.now() - datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        event.update_status()
        self.assertEqual(event.status, EventStatus.FINISHED)

    def test_event_status_reprogramado(self):
        """Test que verifica que un evento se marca como reprogramado cuando la fecha programada cambia"""
        event = Event.objects.create(
            title="Evento reprogramado",
            description="Evento que ha sido reprogramado",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            venue=self.venue,
        )
        new_scheduled_at = timezone.now() + datetime.timedelta(days=3)
        event.update(scheduled_at=new_scheduled_at)
        self.assertEqual(event.status, EventStatus.RESCHEDULED)
    
    def test_event_status_priority_cancelled(self):
        """Test que verifica que un evento cancelado tiene prioridad sobre otros estados"""
        event = Event.objects.create(
            title="Evento cancelado",
            description="Evento que ha sido cancelado",
            scheduled_at=timezone.now() - datetime.timedelta(days=2),
            previous_date=timezone.now() - datetime.timedelta(days=5),
            available_tickets=0,
            organizer=self.organizer,
            venue=self.venue,
            status=EventStatus.CANCELLED,
        )
        event.update_status()
        self.assertEqual(event.status, EventStatus.CANCELLED)

    def test_event_status_priority_soldout_over_rescheduled(self):
        """Test que verifica que un evento agotado tiene prioridad sobre reprogramado"""
        event = Event.objects.create(
            title="Evento agotado y reprogramado",
            description="Evento que ha sido reprogramado y agotado",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            previous_date=timezone.now() + datetime.timedelta(days=1),
            available_tickets=0,
            organizer=self.organizer,
            venue=self.venue,
        )
        event.update_status()
        self.assertEqual(event.status, EventStatus.SOLD_OUT)
    
    def test_event_status_priority_finished_over_soldout(self):
        """Test que verifica que un evento finalizado tiene prioridad sobre agotado"""
        event = Event.objects.create(
            title="Evento agotado y finalizado",
            description="Evento que ha sido finalizado y agotado",
            scheduled_at=timezone.now() - datetime.timedelta(days=2),
            available_tickets=0,
            organizer=self.organizer,
            venue=self.venue,
        )
        event.update_status()
        self.assertEqual(event.status, EventStatus.FINISHED)
    
    def test_event_status_remember_redschedule_after_soldout(self):
        """Test que verifica que un evento reprogramado recuerda su estado después de ser agotado"""
        event = Event.objects.create(
            title="Evento reprogramado con mas entradas",
            description="Evento que ha sido reprogramado, se ha agotado y se le han añadido más entradas",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            previous_date=timezone.now() + datetime.timedelta(days=1),
            available_tickets=10,
            organizer=self.organizer,
            venue=self.venue,
        )
        event.update_status()
        self.assertEqual(event.status, EventStatus.RESCHEDULED)

    def test_event_status_remember_active_after_soldout(self):
        """Test que verifica que un evento activo recuerda su estado después de ser agotado"""
        event = Event.objects.create(
            title="Evento activo después de agotado",
            description="Evento que ha sido agotado y se le han añadido más entradas",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            available_tickets=10,
            organizer=self.organizer,
            venue=self.venue,
            status=EventStatus.SOLD_OUT,
        )
        event.update_status()
        self.assertEqual(event.status, EventStatus.ACTIVE)


    def test_event_sends_notification_when_date_changes(self):
        event = Event.objects.create(
            title="Evento test fecha",
            description="Desc",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )

        user = User.objects.create_user(username="user_date", password="pass")
        Ticket.objects.create(
            user=user,
            event=event,
            total_price=100.00,
            ticket_type_id=1,
            ticket_code=f"TEST-{uuid.uuid4().hex[:8]}"
        )

        self.assertEqual(Notification.objects.filter(user=user).count(), 0)

        new_date = timezone.now() + datetime.timedelta(days=3)
  
        event.update(
            title=event.title,
            description=event.description,
            scheduled_at=new_date,
            organizer=event.organizer,
            venue=event.venue,
        )

        notifs = Notification.objects.filter(user=user, event=event)
        self.assertEqual(notifs.count(), 1)
        self.assertIn("fecha", notifs.first().message.lower())

    def test_event_sends_notification_when_venue_changes(self):
        event = Event.objects.create(
            title="Evento test lugar",
            description="Desc",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )

        user = User.objects.create_user(username="user_venue", password="pass")
        Ticket.objects.create(
            user=user,
            event=event,
            total_price=100.00,
            ticket_type_id=1,
            ticket_code=f"TEST-{uuid.uuid4().hex[:8]}"
        )

        self.assertEqual(Notification.objects.filter(user=user).count(), 0)

        new_venue = Venue.objects.create(
            name="Nuevo Lugar",
            address="Nueva Dirección",
            city="Otra Ciudad",
            capacity=200,
        )

        event.update(
            title=event.title,
            description=event.description,
            scheduled_at=event.scheduled_at,
            organizer=event.organizer,
            venue=new_venue,
        )

        notifs = Notification.objects.filter(user=user, event=event)
        self.assertEqual(notifs.count(), 1)
        self.assertIn("lugar", notifs.first().message.lower())

        
        