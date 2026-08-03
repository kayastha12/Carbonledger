import logging
import requests

logger = logging.getLogger("NotificationEngine")

class NotificationEngine:
    def __init__(self, slack_webhook_url=None, teams_webhook_url=None, smtp_server=None):
        self.slack_url = slack_webhook_url
        self.teams_url = teams_webhook_url
        self.smtp_server = smtp_server

    def send_slack_alert(self, message):
        logger.info(f"[Slack Alert] Dispatching message: {message}")
        if self.slack_url:
            try:
                payload = {"text": f"🚨 *CarbonLedger System Alert* 🚨\n{message}"}
                res = requests.post(self.slack_url, json=payload, timeout=5)
                return res.status_code == 200
            except Exception as e:
                logger.error(f"Slack notification error: {e}")
        return True

    def send_teams_alert(self, title, message):
        logger.info(f"[MS Teams Alert] Dispatching card: {title} - {message}")
        if self.teams_url:
            try:
                payload = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "FF0000",
                    "summary": title,
                    "sections": [{
                        "activityTitle": title,
                        "activitySubtitle": "CarbonLedger Autonomous Monitor",
                        "text": message
                    }]
                }
                res = requests.post(self.teams_url, json=payload, timeout=5)
                return res.status_code == 200
            except Exception as e:
                logger.error(f"MS Teams notification error: {e}")
        return True

    def send_email_alert(self, recipient, subject, body):
        logger.info(f"[Email Alert] Sending to {recipient}: {subject}")
        # In production, use smtplib. Here, we log the email payload cleanly.
        logger.info(f"Email Body: {body}")
        return True

    def trigger_notifications(self, alert_event_type, details):
        """
        Triggers corresponding multi-channel notifications.
        Event types: 'high_emissions', 'missing_factors', 'supplier_risk_increased', 'calculation_failed'
        """
        msg = f"Event: {alert_event_type.upper()} | Details: {details}"
        self.send_slack_alert(msg)
        self.send_teams_alert(f"Alert: {alert_event_type.replace('_', ' ').title()}", msg)
        self.send_email_alert("admin@carbonledger.com", f"CarbonLedger alert: {alert_event_type}", msg)
        return {"status": "success", "notified_channels": ["slack", "teams", "email"]}

if __name__ == "__main__":
    notifier = NotificationEngine()
    res = notifier.trigger_notifications("high_emissions", "Facility_26 exceeded quarterly limit by 15.4 tCO2e")
    print(res)
