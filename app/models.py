from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


class User(AbstractUser):
    is_organizer = models.BooleanField(default=False)

    @classmethod
    def validate_new_user(cls, email, username, password, password_confirm):
        errors = {}

        if email is None:
            errors["email"] = "El email es requerido"
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Ya existe un usuario con este email"

        if username is None:
            errors["username"] = "El username es requerido"
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Ya existe un usuario con este nombre de usuario"

        if password is None or password_confirm is None:
            errors["password"] = "Las contraseñas son requeridas"
        elif password != password_confirm:
            errors["password"] = "Las contraseñas no coinciden"

        return errors
    

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @classmethod
    def validate(cls, name, description, exclude_id=None):
        errors = {}

        if not name.strip():
            errors["name"] = "El nombre no puede estar vacío"
        elif cls.objects.filter(name__iexact=name).exclude(pk=exclude_id).exists():
            errors["name"] = "Ya existe una categoría con ese nombre"

        if not description.strip():
            errors["description"] = "La descripción no puede estar vacía"

        return errors

    @classmethod
    def new(cls, name, description, is_active):
        name = name.strip()
        errors = cls.validate(name, description)

        if errors:
            return False, errors

        cls.objects.create(
            name=name.strip(),
            description=description.strip(),
            is_active=is_active
        )

        return True, None

    def update(self, name, description, is_active):
        if name:
            self.name = name.strip()
        self.description = description.strip()
        self.is_active = is_active
        self.save()


class Event(models.Model):

    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    venue= models.ForeignKey('Venue', on_delete=models.SET_NULL, related_name='events', null=True, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    available_tickets = models.IntegerField(default=0)


    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at, current_event_id=None):
        errors = {}

        if not title.strip():
            errors["title"] = "Por favor ingrese un título"
        elif cls.objects.filter(title__iexact=title).exclude(pk=current_event_id).exists():
            errors["title"] = "Ya existe un evento con ese título"

        if not description.strip():
            errors["description"] = "Por favor ingrese una descripción"

        if scheduled_at is None:
            errors["scheduled_at"] = "La fecha y hora del evento son requeridas"
        elif scheduled_at <= timezone.now():
            errors["scheduled_at"] = "La fecha del evento debe ser en el futuro"

        return errors

    @classmethod
    def new(cls, title, venue, description, scheduled_at, organizer):
        errors = cls.validate(title, description, scheduled_at)

        if errors:
            return False, errors

        cls.objects.create(
            title=title.strip(),
            venue=venue,
            description=description.strip(),
            scheduled_at=scheduled_at,
            organizer=organizer,
            available_tickets=venue.capacity if venue else 0,
        )

        return True, None

    def update(self, title=None, description=None, scheduled_at=None, venue=None, organizer=None):
        title = title if title is not None else self.title
        description = description if description is not None else self.description
        scheduled_at = scheduled_at if scheduled_at is not None else self.scheduled_at

        errors = self.validate(title, description, scheduled_at, current_event_id=self.pk)
        if errors:
            raise ValueError(errors)

        self.title = title
        self.description = description
        self.scheduled_at = scheduled_at
        if organizer is not None:
            self.organizer = organizer
        if venue is not None:
            self.venue = venue

        self.save()
        return True ,None

class Venue(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    capacity=models.IntegerField()
    contact=models.CharField(max_length=100)

    def __str__(self):
        return self.name

    @classmethod
    def validate(cls, name, venue_id, address, city):
        errors = {}
        if not name.strip():
            errors["name"] = "El nombre no puede estar vacío"
        elif cls.objects.filter(name__iexact=name).exclude(pk=venue_id).exists():
            errors["name"] = "Ya existe una Ubicación con ese nombre"

        if not address.strip():
            errors["address"] = "La dirección no puede estar vacía"
        elif cls.objects.filter(address__iexact=address, city__iexact=city).exclude(pk=venue_id).exists():
             errors["address"] = "Ya existe una ubicación con esa dirección en esta ciudad"

        return errors

    @classmethod
    def new(cls, name, address, city, capacity,contact):
        errors = cls.validate(name,None, address, city)

        if errors:
            return False, errors

        Venue.objects.create(
            name=name,
            address=address,
            city=city,
            capacity=capacity,
            contact=contact,
        )

        return True, None

    def update(self, name, address, city, capacity,contact):

        errors = self.validate(name, self.pk, self.address, self.city)
        if errors:
            return False, errors

        self.name = name or self.name
        self.address = address or self.address
        self.city = city or self.city
        self.capacity = capacity or self.capacity
        self.contact = contact or self.contact

        self.save()

        return True, None

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ratings')
    title = models.CharField(max_length=100)
    text = models.TextField(blank=True)
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.rating}⭐)"


class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    ticket_type = models.ForeignKey("TicketType", on_delete=models.CASCADE, related_name="tickets")
    ticket_code = models.CharField(max_length=50, unique=True, blank=True)
    buy_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    old_total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    @classmethod
    def validate(cls, event, user, ticket_type, quantity):
        errors = {}

        if event is None:
            errors["event"] = "El evento es requerido"

        if user is None:
            errors["user"] = "El usuario es requerido"

        if ticket_type is None:
            errors["ticket_type"] = "El tipo de ticket es requerido"

        if quantity is None or not isinstance(quantity, int) or quantity <= 0:
            errors["quantity"] = "La cantidad de tickets debe ser un número entero mayor a 0"

        return errors

    @classmethod
    def new(cls, event, user, ticket_type, quantity):
        errors = Ticket.validate(event, user, ticket_type, quantity)
        if len(errors.keys()) > 0:
            return False, errors
        if event.available_tickets < quantity:
            return False, {"error": "No hay suficientes entradas disponibles"}
        event.available_tickets -= quantity
        event.save()

        ticket = Ticket.objects.create(
            event=event,
            user=user,
            ticket_type=ticket_type,
            quantity=quantity,
            total_price=ticket_type.price * quantity
        )
        ticket.ticket_code = ticket.id #Figura como error, pero al crear ejectuar Ticket.create() se genera id, por lo que deberia poder copiarlo en ticket_code
        ticket.save()
        return True, ticket.ticket_code


    def update(self, ticket_type, quantity):
        self.event.available_tickets -= quantity - self.quantity
        if self.event.available_tickets < 0:
            return False, {"error": "No hay suficientes entradas disponibles"}
        self.event.save()
        if quantity is None or not isinstance(quantity, int) or quantity <= 0:
            return False, {"quantity": "La cantidad de tickets debe ser mayor a 0"}
        self.modified_date = now()
        if not self.user.is_organizer and now() > self.buy_date + timedelta(minutes=30):
            return False, {"error": "El ticket solo se puede modificar en los 30 minutos posteriores a su creacion"}
        self.ticket_type = ticket_type or self.ticket_type
        self.quantity = quantity or self.quantity
        if quantity is not None or ticket_type is not None:
            self.old_total_price = self.total_price
            self.total_price = ticket_type.price * self.quantity
        self.modified_date = now()
        self.save()
        self.event.available_tickets -= quantity - self.quantity
        return True, None

    def delete(self, user_is_organizer):
        if user_is_organizer:
            self.event.available_tickets += self.quantity
            self.event.save()
            super().delete()
            return True, None
        if not user_is_organizer and now() < self.buy_date + timedelta(minutes=30):
            self.event.available_tickets += self.quantity
            self.event.save()
            super().delete()
            return True, None
        else:
            return False, {"error": "El ticket solo se puede eliminar en los 30 minutos posteriores a su creacion"}

class TicketType(models.Model):
    name = models.CharField(max_length=25)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @classmethod
    def validate(cls, name, price):
        errors = {}
        if cls.objects.filter(name=name).exists():
            errors["name"] = "Ya existe un tipo de ticket con ese nombre"
        if name == "":
            errors["name"] = "El nombre es requerido"
        if price is None or not isinstance(price, (int, float)) or price <= 0:
            errors["price"] = "El precio debe ser un número mayor a 0"

        return errors

    @classmethod
    def new(cls, name, price):
        errors = TicketType.validate(name, price)

        if len(errors.keys()) > 0:
            return False, errors

        TicketType.objects.create(
            name=name,
            price=price,
        )

        return True, None

    def update(self, price):
        if price is None or not isinstance(price, (int, float)) or price <= 0:
            return False, {"price": "El precio debe ser un número mayor a 0"}
        self.price = price
        self.save()

        return True, None
class Notification(models.Model):
    title=models.CharField(max_length=200)
    message=models.TextField()
    event=models.ForeignKey(Event, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    user=models.ManyToManyField(User,through='UserNotification', related_name='notifications')
    created_at=models.DateTimeField(auto_now_add=True)
    priority=models.ForeignKey('NotificationPriority', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, id, title, message,event, users):
        errors = {}
        if not title.strip():
            errors["title"] = "El título no puede estar vacío"
        if not message.strip():
            errors["message"] = "El mensaje no puede estar vacío"
        if event is None:
            errors["event"] = "El evento no puede ser nulo"
        if users is None:
            errors["users"] = "Los usuarios no pueden ser nulos"
        return errors

    @classmethod
    def new(cls, title, message, event, users, priority):
        errors = cls.validate(None,title, message, event, users)

        if errors:
            return False, errors

        notification = Notification.objects.create(
            title=title.strip(),
            message=message.strip(),
            event=event,
            priority=priority,
        )
        if isinstance(users, User):
            users = [users]
        notification.user.set(users)


        return True, None

    def update(self, title, message, event, users, priority):
        errors = self.validate(self.pk,title, message, event, users)

        if errors:
            return False, errors

        self.title = title.strip()
        self.message = message.strip()
        self.event = event
        if isinstance(users, User):
            users = [users]
        self.user.set(users)
        self.priority = priority
        self.save()

        return True, None


class NotificationPriority(models.Model):
    description=models.CharField(max_length=200, unique=True)
    def __str__(self):
        return self.description

    @classmethod
    def new(cls, description):
        description = description.strip()
        errors = {}

        if errors:
            return False, errors

        cls.objects.create(
            description=description.strip(),
        )

        return True, None

    def update(self, description):
        if description:
            self.description = description.strip()
        self.save()

class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification = models.ForeignKey('Notification', on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'notification')


#Señal para crear notificaciones de usuario al agregar un evento
@receiver(m2m_changed, sender=Notification.user.through)
def create_user_notifications(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        for user_id in pk_set:
            user = User.objects.get(pk=user_id)
            UserNotification.objects.get_or_create(user=user, notification=instance)

class Comment(models.Model):
    title = models.CharField(max_length=100)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='comments')

    def __str__(self):
        return f"{self.title} - {self.user.username}"