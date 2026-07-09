"""Account domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""
from src.models.account import Account
from src.repositories.base import BaseRepository


class AccountRepository(BaseRepository):
    """Repository for managed account operations."""

    def get_all_accounts(self) -> list[dict]:
        """Get all active persistent accounts."""
        with self._get_conn() as conn:
            # Check which column names exist
            cur = conn.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cur.fetchall()]

            # Use correct column names based on schema
            if 'bank' in columns:
                # New schema
                rows = conn.execute("""
                    SELECT id, name, bank, account_type, account_number_last4,
                           balance_paise, is_active, created_at, updated_at
                    FROM accounts
                    WHERE is_active = 1
                    ORDER BY bank, name
                """).fetchall()
            else:
                # Old schema with bank_name/account_number_masked
                rows = conn.execute("""
                    SELECT id, name, bank_name, account_type, account_number_masked,
                           balance_paise, is_active, created_at, updated_at
                    FROM accounts
                    WHERE is_active = 1
                    ORDER BY bank_name, name
                """).fetchall()

            # Map DB column names to API field names
            result = []
            for r in rows:
                d = dict(r)
                d['bank'] = d.pop('bank_name', d.get('bank'))
                d['account_number_last4'] = d.pop('account_number_masked', d.get('account_number_last4'))
                result.append(d)
        return result

    def get_all(self) -> list[Account]:
        """
        Return all active accounts as Account domain models.

        Maps the canonical `balance_paise` column into the `initial_balance`
        Money value object exposed by the Account model.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, name, account_type AS type,
                       balance_paise AS initial_balance_paise
                FROM accounts
                WHERE is_active = 1
                ORDER BY name
            """
            ).fetchall()
        return [Account.from_db_row(dict(row)) for row in rows]

    def create_account(
        self,
        name: str,
        bank: str,
        account_type: str = "savings",
        balance_paise: int = 0,
        account_number_last4: str | None = None,
        notes: str | None = None,
    ) -> dict | None:
        """Create a new persistent account."""
        with self._get_conn() as conn:
            # Check which column names exist
            cur = conn.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cur.fetchall()]

            # Use correct column names based on schema
            if 'bank' in columns:
                # New schema
                cur = conn.execute("""
                    INSERT INTO accounts (name, bank, account_type, balance_paise,
                                           account_number_last4, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (name, bank, account_type, balance_paise,
                          account_number_last4, notes))
            else:
                # Old schema with bank_name/account_number_masked
                cur = conn.execute("""
                    INSERT INTO accounts (name, bank_name, account_type, balance_paise,
                                           account_number_masked, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (name, bank, account_type, balance_paise,
                          account_number_last4, notes))
            conn.commit()
        lastrowid = cur.lastrowid
        return self.get_account_by_id(lastrowid if lastrowid is not None else 0)

    def get_account_by_id(self, account_id: int | str) -> dict | None:
        """Get a single account by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM accounts WHERE id = ?", (account_id,)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        # Map old column names to new for API compatibility
        d['bank'] = d.pop('bank_name', d.get('bank'))
        d['account_number_last4'] = d.pop('account_number_masked', d.get('account_number_last4'))
        return d

    def update_account(
        self,
        account_id: int | str,
        name: str | None = None,
        bank: str | None = None,
        account_type: str | None = None,
        balance_paise: int | None = None,
        account_number_last4: str | None = None,
        notes: str | None = None,
    ) -> dict | None:
        """Update an existing account. Only updates provided fields."""
        updates = {k: v for k, v in {
            "name": name,
            "bank": bank,
            "account_type": account_type,
            "balance_paise": balance_paise,
            "account_number_last4": account_number_last4,
            "notes": notes,
        }.items() if v is not None}

        if not updates:
            return self.get_account_by_id(account_id)

        set_clause = ', '.join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values()) + [account_id]

        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE accounts SET {set_clause} WHERE id = ?", values
            )
            conn.commit()
        return self.get_account_by_id(account_id)

    def delete_account(self, account_id: int | str) -> bool:
        """Soft delete an account."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE accounts SET is_active = 0, updated_at = datetime('now') WHERE id = ?",
                (account_id,)
            )
            conn.commit()
            changes_row = conn.execute("SELECT changes()").fetchone()
        return bool(changes_row[0]) if changes_row else False

