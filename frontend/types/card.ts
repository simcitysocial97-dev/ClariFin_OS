export interface CreditCard {
  id: string;
  bankName: string;
  cardNumber: string;
  creditLimit: number;
  totalAmountDue: number;
  minimumAmountDue: number;
  dueDate: string;
  billCycleStart: string;
  billCycleEnd: string;
  openingBalance?: number;
}
