from django.db import migrations


_CREATE_FUNCTION = """
CREATE OR REPLACE FUNCTION prevent_wallet_transaction_modification()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'wallet_transactions is append-only: UPDATE and DELETE are not permitted';
END;
$$ LANGUAGE plpgsql;
"""

_CREATE_UPDATE_TRIGGER = """
CREATE TRIGGER no_wallet_transaction_update
BEFORE UPDATE ON wallet_transactions
FOR EACH ROW EXECUTE FUNCTION prevent_wallet_transaction_modification();
"""

_CREATE_DELETE_TRIGGER = """
CREATE TRIGGER no_wallet_transaction_delete
BEFORE DELETE ON wallet_transactions
FOR EACH ROW EXECUTE FUNCTION prevent_wallet_transaction_modification();
"""

_DROP_TRIGGERS = """
DROP TRIGGER IF EXISTS no_wallet_transaction_update ON wallet_transactions;
DROP TRIGGER IF EXISTS no_wallet_transaction_delete ON wallet_transactions;
DROP FUNCTION IF EXISTS prevent_wallet_transaction_modification();
"""


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0011_wallet_security'),
    ]

    operations = [
        migrations.RunSQL(
            sql=_CREATE_FUNCTION + _CREATE_UPDATE_TRIGGER + _CREATE_DELETE_TRIGGER,
            reverse_sql=_DROP_TRIGGERS,
        ),
    ]
