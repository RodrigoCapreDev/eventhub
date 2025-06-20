# Generated by Django 5.2 on 2025-05-02 19:33
from django.db import migrations
from django.utils.timezone import datetime, make_aware


def load_notification_data(apps, schema_editor):
    Notification = apps.get_model('app', 'Notification')
    User = apps.get_model('app', 'User')
    Event = apps.get_model('app', 'Event') 
    NotificationPriority = apps.get_model('app', 'NotificationPriority')
    Venue = apps.get_model('app', 'Venue')
    TicketType = apps.get_model('app', 'TicketType')
    
    user1, created = User.objects.get_or_create(
        username='jperez', email='jperez@gmail.com', password='password123',is_superuser=False, is_organizer=True)
    user1.save()
    
    general_ticket, _ = TicketType.objects.get_or_create(
        name='General',
        defaults={'price': 1000.00}
    )

    vip_ticket, _ = TicketType.objects.get_or_create(
        name='VIP',
        defaults={'price': 2500.00}
    )
    
    venue, _ = Venue.objects.get_or_create(
        name='Estadio Único',
        defaults={
            'address': 'Av. 25 y Av. 32',
            'city': 'La Plata',
            'capacity': 500,
            'contact': 'Martin 1122334455',
        }
    )
    
    event1, _ = Event.objects.get_or_create(
        title='Concierto de Jazz',
        defaults={
            'description': 'Concierto en vivo con artistas internacionales.',
            'scheduled_at': make_aware(datetime(2025, 6, 20, 17, 0)),
            'organizer': user1,
            'venue': venue,
            'available_tickets': 100
        }
    )
    
    medium_priority = NotificationPriority.objects.filter(id=2).first()

    if not medium_priority:
        medium_priority = None
    if not event1:
        event1 = None 

    # Crear notificación de prueba
    notification, created = Notification.objects.get_or_create(
        defaults={
            'title': '¡Recordatorio! Concierto de Jazz el 20 de junio',
            'message': '¡Recuerda que tu entrada para el Concierto de Jazz en el Teatro Central está confirmada! Nos vemos el 20 de junio a las 17:00. ¡No olvides traer tu entrada y disfrutar del evento!',
            'event': event1,
            'priority': medium_priority,
        }
    )

    notification.user.add(user1)  

def undo_notification_data(apps, schema_editor):
    Notification = apps.get_model('app', 'Notification')
    Notification.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_event_available_tickets'),
        ('app', '0004_tickettype_ticket'),
        ('app', '0012_auto_20250502_1608'),
    ]

    operations = [
        migrations.RunPython(load_notification_data, undo_notification_data),
    ]
