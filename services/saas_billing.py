import logging

logger = logging.getLogger("SaasBilling")

class SaasBillingService:
    def __init__(self):
        # In-memory tenant profiles
        self.tenants = {
            "tenant_default": {
                "org_name": "Default Org",
                "plan": "Free",
                "docs_uploaded": 4,
                "max_docs_allowed": 5,
                "billing_active": True
            },
            "tenant_enterprise": {
                "org_name": "EcoSteel Corp",
                "plan": "Enterprise",
                "docs_uploaded": 482,
                "max_docs_allowed": 100000,
                "billing_active": True
            }
        }
        # In-memory API keys
        self.api_keys = {
            "cl_live_key_9012": "tenant_enterprise"
        }

    def validate_api_key(self, api_key):
        return self.api_keys.get(api_key)

    def track_usage(self, tenant_id):
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False, "Tenant not found"
            
        if not tenant["billing_active"]:
            return False, "Subscription is inactive"
            
        if tenant["docs_uploaded"] >= tenant["max_docs_allowed"]:
            return False, f"Usage limit exceeded for plan: {tenant['plan']}"
            
        tenant["docs_uploaded"] += 1
        return True, "Usage approved"

    def process_stripe_webhook(self, event_type, payload):
        """
        Verifies Stripe events (invoice.paid, customer.subscription.updated).
        """
        logger.info(f"Processing Stripe Webhook event: {event_type}")
        customer_email = payload.get("data", {}).get("object", {}).get("customer_email")
        
        # Simulating lookup and billing activation
        if event_type == "invoice.paid" and customer_email:
            logger.info(f"Stripe payment success for: {customer_email}")
            return {"status": "billing_renewed", "email": customer_email}
            
        return {"status": "ignored", "event": event_type}

if __name__ == "__main__":
    billing = SaasBillingService()
    # Check limit check
    ok, msg = billing.track_usage("tenant_default")
    print("Default Tenant Usage 1:", ok, "-", msg)
    # Check limit again
    ok2, msg2 = billing.track_usage("tenant_default")
    print("Default Tenant Usage 2:", ok2, "-", msg2)
