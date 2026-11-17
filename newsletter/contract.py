"""Immutable Python persistence record contract, aligned with contract.mjs.

The backend must authenticate confirmation/preference/unsubscribe requests before
these record transitions. Token verification and fake transport live in the JS
service; this module is neither an endpoint nor a second sending service.
"""
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

DIRECTORY = Path(__file__).resolve().parent
POLICY = json.loads((DIRECTORY / 'consent.json').read_text(encoding='utf-8'))
CATEGORIES = tuple(json.loads((DIRECTORY / 'categories.json').read_text(encoding='utf-8'))['categories'])
CONSENT_SOURCES = tuple(POLICY['allowedSources'])


def consent_source(value):
    if not isinstance(value, str) or value not in CONSENT_SOURCES:
        raise ValueError('Allowlisted consent source required')
    return value


def selected_categories(values):
    if not isinstance(values, (list, tuple)) or not values or any(value not in CATEGORIES for value in values):
        raise ValueError('Choose at least one valid category')
    return tuple(value for value in CATEGORIES if value in values)


def stamp(now):
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError('An injected timezone-aware clock value is required')
    return now.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


@dataclass(frozen=True)
class SubscriberRecord:
    id: str
    email: str
    categories: tuple[str, ...]
    consentAt: str
    consentVersion: str
    consentSource: str
    status: str = 'pending'
    confirmedAt: str | None = None
    preferencesUpdatedAt: str | None = None
    unsubscribedAt: str | None = None
    subscriptionVersion: int = 1

    def __post_init__(self):
        consent_source(self.consentSource)

    def snapshot(self):
        record = asdict(self)
        record['categories'] = list(self.categories)
        return record


def subscribe(*, subscriber_id, email, categories, consent, consentSource=None, now):
    if consent is not True:
        raise ValueError('Explicit consent required')
    source = consent_source(consentSource)
    if not isinstance(email, str) or len(email) > 254 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", email):
        raise ValueError('Invalid email address')
    if not isinstance(subscriber_id, str) or not subscriber_id:
        raise ValueError('Backend-assigned opaque subscriber ID required')
    return SubscriberRecord(subscriber_id, email.lower(), selected_categories(categories),
                            stamp(now), POLICY['consentVersion'], source)


def confirm(record, *, now):
    current = datetime.fromisoformat(stamp(now).replace('Z', '+00:00'))
    given = datetime.fromisoformat(record.consentAt.replace('Z', '+00:00'))
    if record.status != 'pending' or not given <= current < given + timedelta(hours=24):
        raise ValueError('Confirmation already used, expired or subscription stopped')
    return replace(record, status='confirmed', confirmedAt=stamp(now))


def update_preferences(record, categories, *, now):
    if record.status != 'confirmed':
        raise ValueError('Confirmed subscription required')
    return replace(record, categories=selected_categories(categories), preferencesUpdatedAt=stamp(now))


def unsubscribe(record, *, now):
    if record.status == 'unsubscribed':
        return record
    if record.status != 'confirmed':
        raise ValueError('Confirmed subscription required')
    return replace(record, status='unsubscribed', unsubscribedAt=stamp(now))
