from .auth import RegisterView, ConfirmationView, LoginView, ResetPasswordConfirmView, ResetPasswordView

views = (
    ('*', '/register', RegisterView),
    ('*', '/confirm', ConfirmationView),
    ('*', '/login', LoginView),
    ('*', '/reset_password', ResetPasswordView),
    ('*', '/reset_password_confirm', ResetPasswordConfirmView),
)
