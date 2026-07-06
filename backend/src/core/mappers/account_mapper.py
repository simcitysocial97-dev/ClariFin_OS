"""
Account Mapper
==============

Transforms account domain objects into AccountDTO instances.
This is the ONLY location where account API responses are constructed.
"""

from typing import List, Optional
from core.domain.money import Money
from core.dtos.account_dto import AccountDTO, AccountListResponse


class AccountMapper:
    """
    Mapper for account domain objects to DTOs.
    
    Responsibilities:
    - Transform domain Account objects to AccountDTO
    - Add backward compatibility fields (_rupees)
    - Ensure all monetary fields have explicit units (_paise suffix)
    """
    
    @staticmethod
    def to_dto(
        account_id: str,
        name: str,
        bank_name: str,
        account_type: str,
        balance: Money,
        last_updated: str,
        include_rupees_field: bool = True
    ) -> AccountDTO:
        """
        Convert account data to AccountDTO.
        
        Args:
            account_id: Unique account identifier
            name: Account name
            bank_name: Bank name
            account_type: Account type (Savings, Current, FD, RD)
            balance: Money instance representing balance
            last_updated: Last update timestamp (ISO format)
            include_rupees_field: If True, include deprecated balance_rupees field
            
        Returns:
            AccountDTO instance
        """
        dto_data = {
            "id": account_id,
            "name": name,
            "bank_name": bank_name,
            "account_type": account_type,
            "balance_paise": balance.paise,
            "last_updated": last_updated,
        }
        
        # TODO: Remove in Phase 2 - backward compatibility
        if include_rupees_field:
            dto_data["balance_rupees"] = balance.to_rupees()
        
        return AccountDTO(**dto_data)
    
    @staticmethod
    def to_list_response(
        accounts: List[tuple],
        include_rupees_field: bool = True
    ) -> AccountListResponse:
        """
        Convert list of account tuples to AccountListResponse.
        
        Args:
            accounts: List of tuples from database:
                (id, name, bank_name, account_type, balance_paise, last_updated)
            include_rupees_field: If True, include deprecated balance_rupees field
            
        Returns:
            AccountListResponse instance
        """
        account_dtos = []
        total_balance_paise = 0
        
        for acc in accounts:
            account_id, name, bank_name, account_type, balance_paise, last_updated = acc
            
            # Create Money instance from paise
            balance = Money(balance_paise)
            total_balance_paise += balance_paise
            
            # Convert to DTO
            dto = AccountMapper.to_dto(
                account_id=account_id,
                name=name,
                bank_name=bank_name,
                account_type=account_type,
                balance=balance,
                last_updated=last_updated,
                include_rupees_field=include_rupees_field
            )
            account_dtos.append(dto)
        
        return AccountListResponse(
            accounts=account_dtos,
            total_accounts=len(account_dtos),
            total_balance_paise=total_balance_paise
        )
    
    @staticmethod
    def to_dict(
        account_id: str,
        name: str,
        bank_name: str,
        account_type: str,
        balance: Money,
        last_updated: str,
        include_rupees_field: bool = True
    ) -> dict:
        """
        Convert account data to dictionary (for direct JSON response).
        
        Args:
            Same as to_dto()
            
        Returns:
            Dictionary suitable for JSON serialization
        """
        dto = AccountMapper.to_dto(
            account_id=account_id,
            name=name,
            bank_name=bank_name,
            account_type=account_type,
            balance=balance,
            last_updated=last_updated,
            include_rupees_field=include_rupees_field
        )
        return dto.model_dump()