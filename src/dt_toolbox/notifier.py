"""Notification handlers for SMTP and webhooks."""

import logging
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from .types import ExecutionSummary, NotificationConfig, NotificationLevel
from .utils import format_duration

logger = logging.getLogger(__name__)


class Notifier(ABC):
    """Abstract base class for notifiers."""

    @abstractmethod
    def send(
        self,
        summary: ExecutionSummary,
        level: NotificationLevel,
        recipients: list[str] | None = None,
    ) -> bool:
        """Send notification.

        Args:
            summary: Execution summary to send.
            level: Notification level.
            recipients: Optional list of recipients.

        Returns:
            True if sent successfully, False otherwise.
        """
        pass


class SMTPNotifier(Notifier):
    """SMTP email notifier."""

    def __init__(self, config: NotificationConfig):
        """Initialize SMTP notifier.

        Args:
            config: Notification configuration.
        """
        self.config = config

    def _create_email_body(self, summary: ExecutionSummary, level: NotificationLevel) -> str:
        """Create email body from execution summary.

        Args:
            summary: Execution summary.
            level: Notification level.

        Returns:
            HTML email body.
        """
        # Determine status emoji and color
        status_info = {
            NotificationLevel.SUCCESS: ("✅", "green", "Success"),
            NotificationLevel.WARNING: ("⚠️", "orange", "Warning"),
            NotificationLevel.ERROR: ("❌", "red", "Error"),
            NotificationLevel.CRITICAL: ("🚨", "darkred", "Critical"),
        }
        emoji, color, status_text = status_info.get(level, ("ℹ️", "blue", "Info"))

        duration = format_duration(summary.duration_seconds or 0)

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: {color};">{emoji} {summary.app_name} - {status_text}</h2>

            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Application:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{summary.app_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Owner:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{summary.owner}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Run ID:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;"><code>{summary.run_id}</code></td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Start Time:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{summary.start_time.isoformat()}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Duration:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{duration}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Exit Code:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{summary.exit_code}</td>
                </tr>
        """

        if summary.tags:
            html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Tags:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{', '.join(summary.tags)}</td>
                </tr>
            """

        if summary.log_file:
            html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Log File:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;"><code>{summary.log_file}</code></td>
                </tr>
            """

        if summary.log_url:
            html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Log URL:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;"><a href="{summary.log_url}">{summary.log_url}</a></td>
                </tr>
            """

        html += "</table>"

        if summary.error_message:
            html += f"""
            <h3 style="color: red;">Error Message:</h3>
            <pre style="background-color: #f5f5f5; padding: 10px; border: 1px solid #ddd; overflow-x: auto;">{summary.error_message}</pre>
            """

        if summary.stacktrace:
            html += f"""
            <h3>Stack Trace:</h3>
            <pre style="background-color: #f5f5f5; padding: 10px; border: 1px solid #ddd; overflow-x: auto;">{summary.stacktrace}</pre>
            """

        html += """
        </body>
        </html>
        """

        return html

    def send(
        self,
        summary: ExecutionSummary,
        level: NotificationLevel,
        recipients: list[str] | None = None,
    ) -> bool:
        """Send email notification.

        Args:
            summary: Execution summary.
            level: Notification level.
            recipients: Optional recipients list.

        Returns:
            True if sent successfully.
        """
        if not self.config.smtp_host or not self.config.smtp_user:
            logger.warning("SMTP not configured, skipping email notification")
            return False

        recipients = recipients or self.config.recipients
        if not recipients:
            logger.warning("No recipients specified, skipping email notification")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{level.value.upper()}] {summary.app_name} - Run {summary.run_id}"
            msg["From"] = self.config.smtp_user
            msg["To"] = ", ".join(recipients)

            # Create HTML body
            html_body = self._create_email_body(summary, level)
            msg.attach(MIMEText(html_body, "html"))

            # Send email
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()

                if self.config.smtp_password:
                    server.login(self.config.smtp_user, self.config.smtp_password)

                server.send_message(msg)

            logger.info(f"Email notification sent to {recipients}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False


class WebhookNotifier(Notifier):
    """Webhook notifier for Slack and Google Chat."""

    def __init__(self, config: NotificationConfig):
        """Initialize webhook notifier.

        Args:
            config: Notification configuration.
        """
        self.config = config

    def _create_slack_payload(self, summary: ExecutionSummary, level: NotificationLevel) -> dict:
        """Create Slack message payload.

        Args:
            summary: Execution summary.
            level: Notification level.

        Returns:
            Slack payload dictionary.
        """
        # Determine color based on level
        color_map = {
            NotificationLevel.SUCCESS: "good",
            NotificationLevel.WARNING: "warning",
            NotificationLevel.ERROR: "danger",
            NotificationLevel.CRITICAL: "danger",
        }
        color = color_map.get(level, "#439FE0")

        duration = format_duration(summary.duration_seconds or 0)

        fields = [
            {"title": "Application", "value": summary.app_name, "short": True},
            {"title": "Owner", "value": summary.owner, "short": True},
            {"title": "Run ID", "value": f"`{summary.run_id}`", "short": True},
            {"title": "Duration", "value": duration, "short": True},
            {"title": "Exit Code", "value": str(summary.exit_code), "short": True},
        ]

        if summary.tags:
            fields.append({"title": "Tags", "value": ", ".join(summary.tags), "short": True})

        if summary.log_url:
            fields.append(
                {"title": "Logs", "value": f"<{summary.log_url}|View Logs>", "short": False}
            )

        attachment = {
            "color": color,
            "title": f"{summary.app_name} - {level.value.upper()}",
            "fields": fields,
            "footer": "dt-toolbox",
            "ts": int(summary.start_time.timestamp()),
        }

        if summary.error_message:
            attachment["text"] = f"```{summary.error_message}```"

        return {"attachments": [attachment]}

    def _create_gchat_payload(self, summary: ExecutionSummary, level: NotificationLevel) -> dict:
        """Create Google Chat message payload.

        Args:
            summary: Execution summary.
            level: Notification level.

        Returns:
            Google Chat payload dictionary.
        """
        duration = format_duration(summary.duration_seconds or 0)

        # Build message text
        text = f"*{summary.app_name}* - {level.value.upper()}\n\n"
        text += f"• *Owner:* {summary.owner}\n"
        text += f"• *Run ID:* `{summary.run_id}`\n"
        text += f"• *Duration:* {duration}\n"
        text += f"• *Exit Code:* {summary.exit_code}\n"

        if summary.tags:
            text += f"• *Tags:* {', '.join(summary.tags)}\n"

        if summary.log_url:
            text += f"• *Logs:* {summary.log_url}\n"

        if summary.error_message:
            text += f"\n*Error:* ```{summary.error_message}```"

        return {"text": text}

    def send(
        self,
        summary: ExecutionSummary,
        level: NotificationLevel,
        recipients: list[str] | None = None,
    ) -> bool:
        """Send webhook notification.

        Args:
            summary: Execution summary.
            level: Notification level.
            recipients: Not used for webhooks.

        Returns:
            True if sent successfully.
        """
        if not self.config.webhook_url:
            logger.warning("Webhook URL not configured, skipping webhook notification")
            return False

        try:
            # Create payload based on webhook type
            if self.config.webhook_type == "slack":
                payload = self._create_slack_payload(summary, level)
            elif self.config.webhook_type == "gchat":
                payload = self._create_gchat_payload(summary, level)
            else:
                # Generic webhook - send full summary as JSON
                payload = summary.model_dump(mode="json")

            # Send webhook
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()

            logger.info(f"Webhook notification sent to {self.config.webhook_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False


def create_notifiers(config: NotificationConfig) -> list[Notifier]:
    """Create list of notifiers based on configuration.

    Args:
        config: Notification configuration.

    Returns:
        List of configured notifiers.
    """
    notifiers: list[Notifier] = []

    if config.smtp_host and config.smtp_user:
        notifiers.append(SMTPNotifier(config))

    if config.webhook_url:
        notifiers.append(WebhookNotifier(config))

    return notifiers
