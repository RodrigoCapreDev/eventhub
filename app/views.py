import datetime

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Category, Event, User, Venue, Notification, NotificationPriority, UserNotification


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")

    category_id = request.GET.get("category")
    venue_id = request.GET.get("venue")
    date = request.GET.get("date")

    if category_id:
        events = events.filter(categories__id=category_id)

    if venue_id:
        events = events.filter(venue__id=venue_id)

    if date:
        events = events.filter(scheduled_at__date=date)

    categories = Category.objects.filter(is_active=True)
    venues = Venue.objects.all()

    return render(
        request,
        "app/events.html",
        {
            "events": events,
            "categories": categories,
            "venues": venues,
            "user_is_organizer": request.user.is_organizer,
        }
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    return render(request, "app/event_detail.html", {"event": event})


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")
    
    categories = Category.objects.filter(is_active=True)
    venues= Venue.objects.all()
    errors = {}

    event = {}

    if id is not None:
        event = get_object_or_404(Event, pk=id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        venue_id= request.POST.get("venue")
        description = request.POST.get("description", "").strip()
        date = request.POST.get("date")
        time = request.POST.get("time")
        selected_categories = request.POST.getlist("categories")

        venue = get_object_or_404(Venue, pk=venue_id)
        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            success, errors = Event.new(title, venue, description, scheduled_at, request.user)
            if success:
                event = Event.objects.get(title=title, organizer=request.user)
                event.categories.set(selected_categories)
                return redirect("events")
            else:
                event = {
                    "title": title,
                    "description": description,
                    "scheduled_at": scheduled_at,
                    "categories": Category.objects.filter(id__in=selected_categories),
                }
        else:
            event = get_object_or_404(Event, pk=id)
            success, errors = event.update(title,venue, description, scheduled_at, request.user)
            if success:
                event.categories.set(selected_categories)
                return redirect("events")

    return render(
        request,
        "app/event_form.html",
        {
            "event": event,
            "categories": categories,
            "venues": venues,
            "user_is_organizer": request.user.is_organizer,
            "errors": errors
        },
    )


@login_required
def categories(request):
    categories = Category.objects.all()
    return render(
        request,
        "app/categories.html",
        {
            "categories": categories,
            "user_is_organizer": request.user.is_organizer,
        }
    )


@login_required
def category_form(request, id=None):
    if not request.user.is_organizer:
        return redirect("categories")

    category = get_object_or_404(Category, pk=id) if id else None
    is_edit = category is not None
    errors = {}

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"

        errors = Category.validate(name, description, exclude_id=id)

        if category:
            category.name = name
            category.description = description
            category.is_active = is_active
        else:
            category = Category(name=name, description=description, is_active=is_active)

        if errors:
            return render(request, "app/category_form.html", {
                "errors": errors,
                "category": category,
                "is_edit": is_edit,
            })

        category.save()
        return redirect("categories")

    return render(request, "app/category_form.html", {
        "category": category,
        "is_edit": is_edit,
    })


@login_required
def category_delete(request, id):
    if not request.user.is_organizer:
        return redirect("categories")

    category = get_object_or_404(Category, pk=id)

    if request.method == "POST":
        category.delete()
        return redirect("categories")

    return redirect("categories")

@login_required
def category_detail(request, id):
    category = get_object_or_404(Category, pk=id)
    return render(request, "app/category_detail.html", {"category": category})


@login_required
def venues(request):
    venues = Venue.objects.all().order_by("name")
    return render(
        request,
        "app/venues.html",
        {"venues": venues, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def venue_detail(request, id):
    venue = get_object_or_404(Venue, pk=id)
    return render(
        request, 
        "app/venue_detail.html", 
        {"venue": venue ,"user_is_organizer": request.user.is_organizer},
    )

@login_required
def venue_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("venues")

    if request.method == "POST":
        venue = get_object_or_404(Venue, pk=id)
        venue.delete()
        return redirect("venues")

    return redirect("venues")

@login_required
def venue_form(request, id):

    errors={}
    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        city = request.POST.get("city")
        capacity = request.POST.get("capacity")
        contact = request.POST.get("contact")

        if id is None:

            sucess, errors= Venue.new(name, address, city, capacity, contact)

            if not sucess:
                venue = {
                    "name": name,
                    "address": address,
                    "city": city,
                    "capacity": capacity,
                    "contact": contact,
                }
                return render(request, "app/venue_form.html", {
                "errors": errors,
                "venue": venue,
                "user_is_organizer": request.user.is_organizer,
            })

            return redirect("venues")
        
        else:
            venue = get_object_or_404(Venue, pk=id)
            sucess, errors=venue.update(name, address, city, capacity, contact)
            if not sucess:
                return render(request, "app/venue_form.html", {
                "errors": errors,
                "venue": venue,
                "user_is_organizer": request.user.is_organizer,
            })
            return redirect("venue_detail",id)
        
    venue = {}
    if id is not None:
        venue = get_object_or_404(Venue, pk=id)

    return render(
        request,
        "app/venue_form.html",
        {"venue": venue, "user_is_organizer": request.user.is_organizer,},
    )

@login_required
def notifications(request):

    if request.user.is_organizer:
        notifications = Notification.objects.all().order_by("-created_at")
        user_notifications_dict = {}

        return render(
            request,
            "app/notifications_organizer.html",
            {"notifications": notifications, "user_is_organizer": True},
        )
    else:
        notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
        user_notifications = UserNotification.objects.filter(user=request.user, notification__in=notifications)
        user_notifications_dict = {un.notification.id: un for un in user_notifications}
        print(user_notifications_dict)
        return render(
            request,
            "app/notifications_user.html",
            {
                "notifications": notifications,
                "user_is_organizer": False,
                "user_notifications_dict": user_notifications_dict,},
        )


@login_required
def notification_form(request, id=None):
    notificationPrioritys= NotificationPriority.objects.all()
    events= Event.objects.all()
    users= User.objects.all()
    errors = {}
    if request.method == "POST":
        title = request.POST.get("title")
        message = request.POST.get("message")
        event_id = request.POST.get("event_id")
        event = get_object_or_404(Event, pk=event_id) if event_id else None
        priority_id = request.POST.get("priority")
        priority= get_object_or_404(NotificationPriority, pk=priority_id)
        addressee_type = request.POST.getlist("addressee_type")

        if "all" in addressee_type:
            selected_users = User.objects.all()
        elif "specific" in addressee_type:
            user_id= request.POST.get("specific_user_id")
            selected_users = get_object_or_404(User, pk=user_id) if user_id else None

        if id is None:
            success, errors = Notification.new(title, message, event,selected_users, priority)
            if not success:
                notification = {
                    "title": title,
                    "message": message,
                    "priority": NotificationPriority.objects.get(pk=priority_id),
                }
                return render(request, "app/notification_form.html", {
                    "errors": errors,
                    "notification": notification,
                    "user_is_organizer": request.user.is_organizer,
                })
            return redirect("notifications")
        
        else:
            notification = get_object_or_404(Notification, pk=id)
            success, errors = notification.update(title, message,event,selected_users,priority)
            if not success:
                return render(request, "app/notification_form.html", {
                    "errors": errors,
                    "notification": notification,
                    "user_is_organizer": request.user.is_organizer,
                     "events":events, "users":users, 
                     "notificationPrioritys":notificationPrioritys,}
                )
            return redirect("notifications")
        
    notification = {}
    if id is not None:
        notification = get_object_or_404(Notification, pk=id)

    return render(
        request,
        "app/notification_form.html",
        {"notification": notification, "user_is_organizer": request.user.is_organizer, "events":events, "users":users, "notificationPrioritys":notificationPrioritys,},
    )

@login_required
def notification_detail(request, id=None):
    notification = get_object_or_404(Notification, pk=id)

    if not request.user.is_organizer:
        return redirect("notifications")
    
    return render(request, "app/notification_detail.html", {
        "notification": notification,
        "user_is_organizer": request.user.is_organizer,
    })

@login_required
def notification_delete(request, id=None):
    user = request.user
    if not user.is_organizer:
        return redirect("notifications")

    if request.method == "POST":
        notification = get_object_or_404(Notification, pk=id)
        notification.delete()
        return redirect("notifications")

    return redirect("notifications")

@login_required
def mark_notification_read(request, notification_id):
    user = request.user
    notification = get_object_or_404(Notification, pk=notification_id)

    if request.method == "POST":
        try:
            user_notification = UserNotification.objects.get(user=user, notification=notification)
            user_notification.is_read = True
            user_notification.read_at = timezone.now()
            user_notification.save()
        except UserNotification.DoesNotExist:
            pass

    return redirect("notifications")

@login_required
def mark_all_notifications_read(request):
    user = request.user
    notifications = Notification.objects.filter(usernotification__user=user)

    if request.method == "POST":
        for notification in notifications:
            try:
                user_notification = UserNotification.objects.get(user=user, notification=notification)
                user_notification.is_read = True
                user_notification.read_at = timezone.now()
                user_notification.save()
            except UserNotification.DoesNotExist:
                pass

    return redirect("notifications")    