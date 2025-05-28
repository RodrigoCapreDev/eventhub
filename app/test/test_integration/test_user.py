from django.test import Client, TestCase
from django.urls import reverse

from app.models import User


class RegisterViewBaseTest(TestCase):
    """Clase base para las pruebas de registro"""

    def setUp(self):
        # Crear un cliente para realizar solicitudes
        self.client = Client()
        # URL para la vista de registro
        self.register_url = reverse("register")
        # Crear un usuario existente para pruebas
        self.existing_user = User.objects.create_user(
            username="usuario_existente", email="existente@example.com", password="password123"
        )
        # Datos de usuario válidos para pruebas
        self.valid_user_data = {
            "email": "nuevo@example.com",
            "username": "nuevo_usuario",
            "password": "password123",
            "password-confirm": "password123",
        }


class RegisterViewLoadTest(RegisterViewBaseTest):
    """Tests para cargar la vista de registro"""

    def test_register_page_loads(self):
        """Test que verifica que la página de registro carga correctamente"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")


class RegisterViewSuccessTest(RegisterViewBaseTest):
    """Tests para registro exitoso"""

    def test_register_successful(self):
        """Test que verifica un registro exitoso"""
        response = self.client.post(self.register_url, self.valid_user_data)

        # Verificar redirección a events después del registro exitoso
        self.assertRedirects(response, reverse("events"))

        # Verificar que el usuario fue creado en la base de datos
        self.assertTrue(User.objects.filter(username="nuevo_usuario").exists())

        # Verificar que el usuario está autenticado
        user = User.objects.get(username="nuevo_usuario")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)


class RegisterViewValidationTest(RegisterViewBaseTest):
    """Tests para validación de errores en el registro"""

    def test_register_duplicate_email(self):
        """Test que verifica que no se puede registrar con un email existente"""
        data = self.valid_user_data.copy()
        data["email"] = "existente@example.com"

        response = self.client.post(self.register_url, data)

        # Verificar que se redirige de nuevo al formulario
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

        # Verificar que se muestra el error correcto
        self.assertIn("errors", response.context)
        self.assertIn("email", response.context["errors"])
        self.assertEqual(response.context["errors"]["email"], "Ya existe un usuario con este email")

        # Verificar que no se creó un nuevo usuario
        self.assertEqual(User.objects.count(), 2)  # hay un usuario jperez + creado en setUp

    def test_register_duplicate_username(self):
        """Test que verifica que no se puede registrar con un nombre de usuario existente"""
        data = self.valid_user_data.copy()
        data["username"] = "usuario_existente"

        response = self.client.post(self.register_url, data)

        # Verificar que se redirige de nuevo al formulario
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

        # Verificar que se muestra el error correcto
        self.assertIn("errors", response.context)
        self.assertIn("username", response.context["errors"])
        self.assertEqual(
            response.context["errors"]["username"],
            "Ya existe un usuario con este nombre de usuario",
        )

        # Verificar que no se creó un nuevo usuario
        self.assertEqual(User.objects.count(), 2)  # hay un usuario jperez + creado en setUp

    def test_register_password_mismatch(self):
        """Test que verifica que las contraseñas deben coincidir"""
        data = self.valid_user_data.copy()
        data["password-confirm"] = "diferente456"

        response = self.client.post(self.register_url, data)

        # Verificar que se redirige de nuevo al formulario
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

        # Verificar que se muestra el error correcto
        self.assertIn("errors", response.context)
        self.assertIn("password", response.context["errors"])
        self.assertEqual(response.context["errors"]["password"], "Las contraseñas no coinciden")

        # Verificar que no se creó un nuevo usuario
        self.assertEqual(User.objects.count(), 2)  # hay un usuario jperez + creado en setUp

    def test_register_missing_fields(self):
        """Test que verifica que todos los campos son requeridos"""
        # Enviar formulario vacío
        response = self.client.post(self.register_url, {})

        # Verificar que se redirige de nuevo al formulario
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

        # Verificar que se muestran los errores correctos
        self.assertIn("errors", response.context)
        self.assertIn("email", response.context["errors"])
        self.assertEqual(response.context["errors"]["email"], "El email es requerido")


class LoginViewBaseTest(TestCase):
    """Clase base para las pruebas de login"""

    def setUp(self):
        # Crear un cliente para realizar solicitudes
        self.client = Client()
        # URL para la vista de login
        self.login_url = reverse("login")
        # Crear un usuario para pruebas
        self.test_user = User.objects.create_user(
            username="usuario_test", email="test@example.com", password="password123"
        )
        # Datos de login válidos
        self.valid_credentials = {"username": "usuario_test", "password": "password123"}


class LoginViewLoadTest(LoginViewBaseTest):
    """Tests para cargar la vista de login"""

    def test_login_page_loads(self):
        """Test que verifica que la página de login carga correctamente"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")


class LoginViewSuccessTest(LoginViewBaseTest):
    """Tests para login exitoso"""

    def test_login_successful(self):
        """Test que verifica un login exitoso"""
        response = self.client.post(self.login_url, self.valid_credentials)

        # Verificar redirección a events después del login exitoso
        self.assertRedirects(response, reverse("events"))

        # Verificar que el usuario está autenticado
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.test_user.pk)


class LoginViewFailureTest(LoginViewBaseTest):
    """Tests para fallos en el login"""

    def test_login_invalid_credentials(self):
        """Test que verifica que no se puede iniciar sesión con credenciales inválidas"""
        # Credenciales con contraseña incorrecta
        invalid_credentials = {"username": "usuario_test", "password": "password_incorrecto"}

        response = self.client.post(self.login_url, invalid_credentials)

        # Verificar que se redirige de nuevo al formulario
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

        # Verificar que se muestra el error correcto
        self.assertIn("error", response.context)
        self.assertEqual(response.context["error"], "Usuario o contraseña incorrectos")

        # Verificar que el usuario no está autenticado
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_user_does_not_exist(self):
        """Test que verifica que no se puede iniciar sesión con un usuario que no existe"""
        # Credenciales con usuario inexistente
        nonexistent_user = {"username": "usuario_inexistente", "password": "password123"}

        response = self.client.post(self.login_url, nonexistent_user)

        # Verificar que se redirige de nuevo al formulario
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

        # Verificar que se muestra el error correcto
        self.assertIn("error", response.context)
        self.assertEqual(response.context["error"], "Usuario o contraseña incorrectos")

        # Verificar que el usuario no está autenticado
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_missing_fields(self):
        """Test que verifica el comportamiento cuando faltan campos en el formulario"""
        # Enviar formulario vacío
        response = self.client.post(self.login_url, {})

        # Verificar que se redirige de nuevo al formulario
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

        # Verificar que se muestra el error correcto
        self.assertIn("error", response.context)
        self.assertEqual(response.context["error"], "Usuario o contraseña incorrectos")

        # Verificar que el usuario no está autenticado
        self.assertNotIn("_auth_user_id", self.client.session)
