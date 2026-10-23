"""Explicit transport-result adapter; never opens SMTP or calls a network API.

A future transport MUST call smtp_result(accepted) immediately after a positive
DATA response, before QUIT. Lost DATA response => ambiguous, never failure.
"""


class PublicationCoordinator:
    def __init__(self, registry):
        self.registry = registry

    def prepare(self, date, *, approved_for_send=False):
        return self.registry.reserve(date, approved_for_send=approved_for_send)

    def identity(self, token, *, language, destination):
        with self.registry._transaction() as db:
            row = db.execute('SELECT * FROM editions WHERE token=?', (token,)).fetchone()
            if not row:
                raise ValueError('Unknown attempt')
            return dict(row, label=f'Nº{row["number"]:03d}', language=language,
                        destination=destination, timezone='Africa/Abidjan')

    def smtp_result(self, token, *, outcome, evidence):
        if outcome == 'accepted':
            self.registry.confirm(token, evidence=evidence)
        elif outcome == 'failure':
            self.registry.fail(token, evidence=evidence)
        elif outcome == 'ambiguous':
            self.registry.ambiguous(token, evidence=evidence)
        else:
            raise ValueError('Unsupported outcome')

    def quit_failed(self, token, *, evidence):
        with self.registry._transaction() as db:
            row = db.execute('SELECT status FROM editions WHERE token=?', (token,)).fetchone()
            if not row or row['status'] != 'published' or not evidence.strip():
                raise ValueError('DATA acceptance must already be recorded')
            db.execute('INSERT INTO journal(token,event,evidence) VALUES (?,?,?)',
                       (token, 'quit_failed_after_acceptance', evidence))
