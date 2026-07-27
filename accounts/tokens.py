"""Token generators for account-related one-time links.

Classes:
    AccountActivationTokenGenerator: One-time token generator for account
        activation links, scoped by a dedicated key salt so its tokens are
        not interchangeable with password-reset tokens.
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Generate one-time tokens for account activation links.

    Uses a dedicated ``key_salt`` so activation tokens cannot be substituted
    for password-reset tokens (which rely on Django's default salt), and vice
    versa. Like the base generator, tokens are also derived from the user's
    password hash, so they are single-use and expire once the password is set.
    """

    key_salt = "accounts.tokens.AccountActivationTokenGenerator"


account_activation_token_generator = AccountActivationTokenGenerator()
