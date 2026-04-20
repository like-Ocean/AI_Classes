import asyncio
import smtplib
import traceback
from email.message import EmailMessage
from core.config import settings


def _smtp_is_configured():
    return bool(settings.EFFECTIVE_SMTP_HOST and settings.EFFECTIVE_SMTP_FROM_EMAIL)


def _normalized_password(host: str, password: str):
    if host.lower().endswith("gmail.com"):
        return password.replace(" ", "")
    return password


def _send_email_sync(to_email: str, subject: str, body: str):
    smtp_host = settings.EFFECTIVE_SMTP_HOST
    smtp_port = settings.EFFECTIVE_SMTP_PORT
    smtp_username = settings.EFFECTIVE_SMTP_USERNAME
    smtp_password = _normalized_password(smtp_host, settings.EFFECTIVE_SMTP_PASSWORD)
    use_ssl = settings.EFFECTIVE_SMTP_USE_SSL
    use_tls = settings.EFFECTIVE_SMTP_USE_TLS

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EFFECTIVE_SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(body)

    if use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as smtp:
            if settings.USE_CREDENTIALS and smtp_username:
                smtp.login(smtp_username, smtp_password)
            smtp.send_message(msg)
        return

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
        if use_tls:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
        if settings.USE_CREDENTIALS and smtp_username:
            smtp.login(smtp_username, smtp_password)
        smtp.send_message(msg)


async def send_teacher_role_change_email(to_email: str, full_name: str, assigned: bool):
    if not _smtp_is_configured() or not to_email:
        return False

    site_url = f"{settings.APP_PROTOCOL}://{settings.APP_HOST}:{settings.APP_PORT}"

    if assigned:
        subject = "Роль изменена: Теперь вы учитель"
        body = (
            f"Здравствуйте, {full_name}.\n\n"
            "Ваша роль была изменена. Теперь вы имеете доступ к преподавательским функциям.\n"
            "Пожалуйста, войдите в систему снова, если вы уже вошли.\n"
            f"Платформа: {site_url}\n"
        )
    else:
        subject = "Роль изменена: Доступ преподавателя отменен"
        body = (
            f"Здравствуйте, {full_name}.\n\n"
            "Ваша роль была изменена. Доступ к преподавательским функциям был отменен.\n"
            "Если вы считаете, что это изменение является ошибочным, свяжитесь с администратором платформы.\n"
            f"Платформа: {site_url}\n"
        )

    try:
        await asyncio.to_thread(_send_email_sync, to_email, subject, body)
        return True
    except Exception as e:
        print(f"Failed to send role change email to {to_email}: {e}")
        traceback.print_exc()
        return False


async def send_password_reset_email(to_email: str, reset_link: str, full_name: str = ""):
    if not _smtp_is_configured() or not to_email:
        return False

    subject = "Сброс пароля"
    greeting = f"Здравствуйте, {full_name}." if full_name else "Здравствуйте."
    body = (
        f"{greeting}\n\n"
        "Мы получили запрос на сброс пароля.\n"
        "Чтобы задать новый пароль, перейдите по ссылке:\n"
        f"{reset_link}\n\n"
        f"Ссылка действует {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} минут.\n"
        "Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.\n"
    )

    try:
        await asyncio.to_thread(_send_email_sync, to_email, subject, body)
        return True
    except Exception as e:
        print(f"Failed to send password reset email to {to_email}: {e}")
        traceback.print_exc()
        return False