"""Account domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""

from typing import Any

from src.models.account import Account
from src.repositories.base import BaseRepository


class AccountRepository(BaseRepository):
    """Repository for managed account operations."""

    def get_all_accounts(self) -> list[dict[str, Any]]:
        """Get all active persistent accounts."""
        with self._get_conn() as conn:
            # Check which column names exist
            cur = conn.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cur.fetchall()]

            # Use correct column names based on schema
            if "bank" in columns:
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
                d["bank"] = d.pop("bank_name", d.get("bank"))
                d["account_number_last4"] = d.pop(
                    "account_number_masked", d.get("account_number_last4")
                )
                result.append(d)
        return result

    def get_all(self) -> list[Account]:
        """
        Return all active accounts as Account domain models.

        Maps the canonical `balance_paise` column into the `initial_balance`
        Money value object exposed by the Account model.
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, name, account_type AS type,
                       balance_paise AS initial_balance_paise
                FROM accounts
                WHERE is_active = 1
                ORDER BY name
            """).fetchall()
        return [Account.from_db_row(dict(row)) for row in rows]

    def create_account(
        self,
        name: str,
        bank: str,
        account_type: str = "savings",
        balance_paise: int = 0,
        account_number_last4: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any] | None:
        """Create a new persistent account."""
        with self._get_conn() as conn:
            # Check which column names exist
            cur = conn.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cur.fetchall()]

            # Use correct column names based on schema
            if "bank" in columns:
                # New schema
                cur = conn.execute(
                    """
                    INSERT INTO accounts (name, bank, account_type, balance_paise,
                                           account_number_last4, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        bank,
                        account_type,
                        balance_paise,
                        account_number_last4,
                        notes,
                    ),
                )
            else:
                # Old schema with bank_name/account_number_masked
                cur = conn.execute(
                    """
                    INSERT INTO accounts (name, bank_name, account_type, balance_paise,
                                           account_number_masked, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        bank,
                        account_type,
                        balance_paise,
                        account_number_last4,
                        notes,
                    ),
                )
            conn.commit()
        lastrowid = cur.lastrowid
        return self.get_account_by_id(lastrowid if lastrowid is not None else 0)

    def get_account_by_id(self, account_id: int | str) -> dict[str, Any] | None:
        """Get a single account by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM accounts WHERE id = ?", (account_id,)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        # Map old column names to new for API compatibility
        d["bank"] = d.pop("bank_name", d.get("bank"))
        d["account_number_last4"] = d.pop(
            "account_number_masked", d.get("account_number_last4")
        )
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
    ) -> dict[str, Any] | None:
        """Update an existing account. Only updates provided fields."""
        updates = {
            k: v
            for k, v in {
                "name": name,
                "bank": bank,
                "account_type": account_type,
                "balance_paise": balance_paise,
                "account_number_last4": account_number_last4,
                "notes": notes,
            }.items()
            if v is not None
        }

        if not updates:
            return self.get_account_by_id(account_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values()) + [account_id]

        with self._get_conn() as conn:
            conn.execute(f"UPDATE accounts SET {set_clause} WHERE id = ?", values)
            conn.commit()
        return self.get_account_by_id(account_id)

    def delete_account(self, account_id: int | str) -> bool:
        """Soft delete an account. Alias for deactivate_account()."""
        return self.deactivate_account(account_id)

    # ============================================================
    # Additional Filtering Methods (Phase 2)
    # ============================================================

    def get_accounts_by_type(self, account_type: str) -> list[dict[str, Any]]:
        """Get all active accounts filtered by account type."""
        with self._get_conn() as conn:
            cur = conn.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cur.fetchall()]

            if "bank" in columns:
                rows = conn.execute(
                    """
                    SELECT id, name, bank, account_type, account_number_last4,
                           balance_paise, is_active, created_at, updated_at
                    FROM accounts
                    WHERE is_active = 1 AND account_type = ?
                    ORDER BY bank, name
                    """,
                    (account_type,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, name, bank_name, account_type, account_number_masked,
                           balance_paise, is_active, created_at, updated_at
                    FROM accounts
                    WHERE is_active = 1 AND account_type = ?
                    ORDER BY bank_name, name
                    """,
                    (account_type,),
                ).fetchall()

            result = []
            for r in rows:
                d = dict(r)
                d["bank"] = d.pop("bank_name", d.get("bank"))
                d["account_number_last4"] = d.pop(
                    "account_number_masked", d.get("account_number_last4")
                )
                result.append(d)
        return result

    def get_accounts_by_institution(self, bank: str) -> list[dict[str, Any]]:
        """Get all active accounts filtered by bank/institution."""
        with self._get_conn() as conn:
            cur = conn.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cur.fetchall()]

            if "bank" in columns:
                rows = conn.execute(
                    """
                    SELECT id, name, bank, account_type, account_number_last4,
                           balance_paise, is_active, created_at, updated_at
                    FROM accounts
                    WHERE is_active = 1 AND bank = ?
                    ORDER BY name
                    """,
                    (bank,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, name, bank_name, account_type, account_number_masked,
                           balance_paise, is_active, created_at, updated_at
                    FROM accounts
                    WHERE is_active = 1 AND bank_name = ?
                    ORDER BY name
                    """,
                    (bank,),
                ).fetchall()

            result = []
            for r in rows:
                d = dict(r)
                d["bank"] = d.pop("bank_name", d.get("bank"))
                d["account_number_last4"] = d.pop(
                    "account_number_masked", d.get("account_number_last4")
                )
                result.append(d)
        return result

    def get_active_accounts(self) -> list[dict[str, Any]]:
        """Get all active accounts. Same as get_all_accounts() with explicit naming."""
        return self.get_all_accounts()

    def deactivate_account(self, account_id: int | str) -> bool:
        """Soft delete an account (set is_active to 0)."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE accounts SET is_active = 0, updated_at = datetime('now') WHERE id = ?",
                (account_id,),
            )
            conn.commit()
            changes_row = conn.execute("SELECT changes()").fetchone()
        return bool(changes_row[0]) if changes_row else False

    # ============================================================
    # Household / Multi-Owner Methods (Phase 1)
    # ============================================================

    def get_household_accounts(self, household_id: str) -> list[dict[str, Any]]:
        """Get all active accounts belonging to a household."""
        with self._get_conn() as conn:
            cur = conn.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cur.fetchall()]

            if "bank" in columns:
                rows = conn.execute(
                    """
                    SELECT id, name, bank, account_type, account_number_last4,
                           balance_paise, is_active, created_at, updated_at,
                           owner_id, household_id
                    FROM accounts
                    WHERE is_active = 1 AND household_id = ?
                    ORDER BY bank, name
                    """,
                    (household_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, name, bank_name, account_type, account_number_masked,
                           balance_paise, is_active, created_at, updated_at,
                           owner_id, household_id
                    FROM accounts
                    WHERE is_active = 1 AND household_id = ?
                    ORDER BY bank_name, name
                    """,
                    (household_id,),
                ).fetchall()

            result = []
            for r in rows:
                d = dict(r)
                d["bank"] = d.pop("bank_name", d.get("bank"))
                d["account_number_last4"] = d.pop(
                    "account_number_masked", d.get("account_number_last4")
                )
                result.append(d)
        return result

    def get_accounts_by_owner(
        self, owner_id: str, household_id: str = "primary"
    ) -> list[dict[str, Any]]:
        """Get all active accounts for a specific owner within a household."""
        with self._get_conn() as conn:
            cur = conn.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cur.fetchall()]

            if "bank" in columns:
                rows = conn.execute(
                    """
                    SELECT id, name, bank, account_type, account_number_last4,
                           balance_paise, is_active, created_at, updated_at,
                           owner_id, household_id
                    FROM accounts
                    WHERE is_active = 1 AND owner_id = ? AND household_id = ?
                    ORDER BY bank, name
                    """,
                    (owner_id, household_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, name, bank_name, account_type, account_number_masked,
                           balance_paise, is_active, created_at, updated_at,
                           owner_id, household_id
                    FROM accounts
                    WHERE is_active = 1 AND owner_id = ? AND household_id = ?
                    ORDER BY bank_name, name
                    """,
                    (owner_id, household_id),
                ).fetchall()

            result = []
            for r in rows:
                d = dict(r)
                d["bank"] = d.pop("bank_name", d.get("bank"))
                d["account_number_last4"] = d.pop(
                    "account_number_masked", d.get("account_number_last4")
                )
                result.append(d)
        return result

    def is_same_household(
        self, account_id_1: int | str, account_id_2: int | str
    ) -> bool:
        """Check if two accounts belong to the same household."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT
                    (SELECT household_id FROM accounts WHERE id = ?) AS h1,
                    (SELECT household_id FROM accounts WHERE id = ?) AS h2
                """,
                (account_id_1, account_id_2),
            ).fetchone()
        if not row:
            return False
        h1, h2 = row[0], row[1]
        if h1 is None or h2 is None:
            return False
        return bool(h1 == h2)

    def list_accounts(self) -> list[dict[str, Any]]:
        """Get all accounts for workspace services. Alias for get_all_accounts()."""
        return self.get_all_accounts()
