import aiosmtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Notificator:
    def __init__(self, email_sender, host, user, password, port=587, tls=True):
        self.email_sender = email_sender
        self.tls = tls
        self.host = host
        self.password = password
        self.user = user
        self.port = port

    async def send_email(self, to, subject, text, textType='plain', **params):
        """Send an outgoing email with the given parameters.

        :param sender: From whom the email is being sent
        :type sender: str

        :param to: A list of recipient email addresses.
        :type to: list

        :param subject: The subject of the email.
        :type subject: str

        :param text: The text of the email.
        :type text: str

        :param textType: Mime subtype of text, defaults to 'plain' (can be 'html').
        :type text: str

        :param params: An optional set of parameters. (See below)
        :type params; dict

        Optional Parameters:
        :cc: A list of Cc email addresses.
        :bcc: A list of Bcc email addresses.
        """

        # Default Parameters
        cc = params.get("cc", [])
        bcc = params.get("bcc", [])

        # Prepare Message
        msg = MIMEMultipart()
        msg.preamble = subject
        msg['Subject'] = subject
        msg['From'] = self.email_sender
        msg['To'] = ', '.join(to) if isinstance(to, list) else to
        if len(cc): msg['Cc'] = ', '.join(cc)
        if len(bcc): msg['Bcc'] = ', '.join(bcc)

        msg.attach(MIMEText(text, textType, 'utf-8'))

        # Contact SMTP server and send Message
        # context = ssl.create_default_context()
        async with aiosmtplib.SMTP(hostname=self.host, port=self.port) as client:
            try:
                await client.starttls(validate_certs=False)  # opportunistic TLS
            except aiosmtplib.SMTPException as exc:
                if 'starttls extension not supported' not in exc.message.lower():
                    raise
            await client.login(self.user, self.password)
            return await client.send_message(msg)
