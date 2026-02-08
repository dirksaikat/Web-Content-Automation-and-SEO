from typing import Any
import asyncio
from disposable_email_domains import blocklist
import dns.resolver

CUSTOM_BLOCKLIST = {
    "ethereal.email",
    "mailinator.com",
    "tempmail.com",
}

DISPOSABLE_DOMAINS = set(blocklist.union(CUSTOM_BLOCKLIST))

TRUSTED_PROVIDERS = {
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "yahoo.com",
    "icloud.com",
    "protonmail.com",
    "aol.com",
    "mail.com",
}


def normalize_email(email: str) -> str:
    if not email or not isinstance(email, str):
        raise ValueError("Email cannot be empty")

    email = email.strip()

    try:
        local, domain = email.lower().split("@")
    except ValueError:
        raise ValueError("Invalid email format - missing @ symbol")

    # Gmail/Googlemail special handling
    if domain in ("gmail.com", "googlemail.com"):
        # Remove everything after + and all dots
        local = local.split("+")[0].replace(".", "")
        domain = "gmail.com"  # Normalize googlemail to gmail

    # Outlook/Hotmail/Live aliases
    elif domain in ("outlook.com", "hotmail.com", "live.com"):
        # Remove everything after +
        local = local.split("+")[0]

    # Generic +alias removal for other providers
    else:
        local = local.split("+")[0]

    normalized = f"{local}@{domain}"
    return normalized


def is_disposable_email(email: str) -> bool:
    try:
        domain = email.split("@")[1].lower()
        is_disposable = domain in DISPOSABLE_DOMAINS
        return is_disposable
    except (IndexError, AttributeError):
        return True  # Treat invalid emails as disposable (reject)


async def check_mx_records(domain: str) -> bool:
    try:
        # Run DNS query in thread pool to avoid blocking
        mx_records = await asyncio.to_thread(dns.resolver.resolve, domain, "MX")
        has_mx = len(list(mx_records)) > 0
        return has_mx
    except dns.resolver.NXDOMAIN:
        return False
    except dns.resolver.NoAnswer:
        return False
    except Exception as e:
        return False


def score_email_reputation(email: str, is_disposable: bool) -> int:
    try:
        domain = email.split("@")[1].lower()
    except (IndexError, AttributeError):
        return 0

    score = 50  # Base score for unknown domains

    # Trusted providers
    if domain in TRUSTED_PROVIDERS:
        score += 40
    # Educational institutions
    elif domain.endswith(".edu"):
        score += 35
    # Government
    elif domain.endswith(".gov"):
        score += 45
    # Corporate domains with MX records get slight bonus
    elif "." in domain and not domain.endswith(".com"):
        score += 10

    # Penalty for disposable
    if is_disposable:
        score -= 60

    # Clamp to 0-100
    final_score = max(0, min(100, score))
    return final_score


async def validate_email(email: str) -> dict[str, Any]:
    errors = []

    if not email or "@" not in email:
        return {
            "valid": False,
            "normalized": None,
            "errors": ["Invalid email format"],
            "reputation_score": 0,
            "is_disposable": False,
            "has_mx_records": False,
        }

    try:
        normalized = normalize_email(email)
    except ValueError as e:
        return {
            "valid": False,
            "normalized": None,
            "errors": [str(e)],
            "reputation_score": 0,
            "is_disposable": False,
            "has_mx_records": False,
        }

    is_disposable = is_disposable_email(email)
    if is_disposable:
        errors.append("Disposable email addresses are not allowed")

    domain = email.split("@")[1]
    has_mx = await check_mx_records(domain)
    if not has_mx:
        errors.append("Email domain does not accept mail")

    # Reputation score
    reputation = score_email_reputation(email=email, is_disposable=is_disposable)

    result = {
            "valid": len(errors) == 0,
            "normalized": normalized,
            "errors": errors,
            "reputation_score": reputation,
            "is_disposable": is_disposable,
            "has_mx_records": has_mx,
        }

    return result
