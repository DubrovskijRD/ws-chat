from .auth import RegisterView, ConfirmationView, LoginView

views = (
    ('*', '/register', RegisterView),
    ('*', '/confirm', ConfirmationView),
    ('*', '/login', LoginView),
)