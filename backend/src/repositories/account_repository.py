"""Account domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""
from src.engines.balance_engine import (
    compute_account_balance,
    compute_running_balance,
    get_accounts_list,
)
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

    def get_accounts_list(self) -> list[dict]:
        """Get list of all accounts (banks) with their current balances."""
        return get_accounts_list(self.db_path)

    def create_account(
        self,
        name: str,
        bank: str,
        account_type: str = "savings",
        balance_paise: int = 0,
        account_number_last4: str | None = None,
        notes: str | None = None,
    ) -> dict:
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
        return self.get_account_by_id(cur.lastrowid)

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
            result = conn.execute(
                "SELECT changes()"
            ).fetchone()[0] > 0
        return result

    def compute_account_balance(
        self,
        account_id: str,
        starting_balance_paise: int = 0,
    ) -> dict:
        """Compute current balance for a single account."""
        return compute_account_balance(
            db_path=self.db_path,
            account_id=account_id,
            starting_balance_paise=starting_balance_paise,
        )

    def compute_running_balance(
        self,
        account_id: str | None = None,
        starting_balance_paise: int = 0,
    ) -> list[dict]:
        """Compute running balance by replaying all transactions chronologically."""
        return compute_running_balance(
            db_path=self.db_path,
            account_id=account_id,
            starting_balance_paise=starting_balance_paise,
        )
