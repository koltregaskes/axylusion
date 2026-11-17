"""Synthetic Python record-contract tests: no accounts, environment or network."""
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import json
import unittest

from contract import CONSENT_SOURCES, subscribe, confirm, update_preferences, unsubscribe

NOW = datetime(2026, 11, 15, 15, tzinfo=timezone.utc)


class ConsentRecordTests(unittest.TestCase):
    def subscribe(self, **changes):
        values = dict(subscriber_id='opaque-fixture-id', email='reader@example.invalid',
                      categories=['Audio'], consent=True, consentSource=CONSENT_SOURCES[0], now=NOW)
        return subscribe(**{**values, **changes})

    def test_approved_source_is_stored_with_consent_time_and_version(self):
        record = self.subscribe()
        self.assertEqual(record.consentSource, 'https://axylusion.com/newsletter.html')
        self.assertEqual(record.consentAt, '2026-11-15T15:00:00.000Z')
        self.assertEqual(record.consentVersion, 'creative-daily-v1')
        self.assertEqual(record.status, 'pending')
        with self.assertRaises(FrozenInstanceError):
            record.consentSource = 'other'
        with self.assertRaisesRegex(ValueError, 'consent source'):
            replace(record, consentSource='https://other.example')

    def test_invalid_and_missing_sources_are_rejected(self):
        for value in [None, '', [], {}, 'newsletter.html', 'http://axylusion.com/newsletter.html',
                      'https://other.example/newsletter.html', 'https://axylusion.com/newsletter.html?campaign=x',
                      'https://axylusion.com/newsletter.html#form', 'https://axylusion.com/newsletter.html/',
                      'https://axylusion.com/%6eewsletter.html', ' https://axylusion.com/newsletter.html']:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'consent source'):
                self.subscribe(consentSource=value)
        with self.assertRaisesRegex(ValueError, 'consent source'):
            subscribe(subscriber_id='fixture',email='a@example.invalid', categories=['Audio'],consent=True,now=NOW)

    def test_consent_evidence_survives_all_transitions_and_serialization(self):
        pending = self.subscribe()
        confirmed = confirm(pending, now=NOW + timedelta(seconds=1))
        updated = update_preferences(confirmed, ['Video'], now=NOW + timedelta(seconds=2))
        stopped = unsubscribe(updated, now=NOW + timedelta(seconds=3))
        for record in [pending, confirmed, updated, stopped]:
            snapshot = json.loads(json.dumps(record.snapshot()))
            self.assertEqual({key: snapshot[key] for key in ('consentAt', 'consentVersion', 'consentSource')},
                             {key: pending.snapshot()[key] for key in ('consentAt', 'consentVersion', 'consentSource')})
        self.assertEqual(stopped.status, 'unsubscribed')
        self.assertEqual(stopped.categories, ('Video',))
        self.assertEqual(unsubscribe(stopped, now=NOW + timedelta(seconds=4)), stopped)
        self.assertEqual(pending.status, 'pending')
        snapshot = stopped.snapshot(); snapshot['consentSource'] = 'tampered'
        self.assertEqual(stopped.consentSource, CONSENT_SOURCES[0])

    def test_invalid_consent_inputs_and_unconfirmed_updates_are_rejected(self):
        for value in [False, 'true', 1]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'consent'):
                self.subscribe(consent=value)
        for chosen in [[], ['Other'], 'Audio']:
            with self.subTest(chosen=chosen), self.assertRaisesRegex(ValueError, 'category'):
                self.subscribe(categories=chosen)
        for email in ['invalid', 'a@example.invalid\r\nBcc:x@y.invalid']:
            with self.assertRaisesRegex(ValueError, 'email'):
                self.subscribe(email=email)
        with self.assertRaisesRegex(ValueError, 'Confirmed'):
            update_preferences(self.subscribe(), ['Video'], now=NOW)

    def test_confirmation_expiry_replay_and_suppression(self):
        pending = self.subscribe()
        with self.assertRaisesRegex(ValueError, 'expired'):
            confirm(pending, now=NOW + timedelta(hours=24))
        confirmed = confirm(pending, now=NOW + timedelta(seconds=1))
        with self.assertRaisesRegex(ValueError, 'already'):
            confirm(confirmed, now=NOW + timedelta(seconds=2))
        stopped = unsubscribe(confirmed, now=NOW + timedelta(seconds=3))
        with self.assertRaisesRegex(ValueError, 'Confirmed'):
            update_preferences(stopped, ['Audio'], now=NOW + timedelta(seconds=4))


if __name__ == '__main__':
    unittest.main()
