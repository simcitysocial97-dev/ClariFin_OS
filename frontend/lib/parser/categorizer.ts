/**
 * Transaction Categorizer
 * Categorizes transactions based on description keywords
 */

const CATEGORY_KEYWORDS: Record<string, string[]> = {
  'Food & Dining': ['restaurant', 'food', 'dining', 'swiggy', 'zomato', 'uber eats', 'dominos', 'pizza', 'cafe', 'coffee', 'starbucks', 'mcdonalds', 'kfc', 'burger', 'foodpanda', 'eat', 'kitchen', 'biryani', 'dhaba', 'hotel', 'lunch', 'dinner', 'breakfast'],
  'Shopping': ['amazon', 'flipkart', 'myntra', 'ajio', 'snapdeal', 'shopify', 'shopping', 'retail', 'store', 'mart', 'mall', 'bazaar', 'market', 'purchase', 'buy', 'order'],
  'Transportation': ['uber', 'ola', 'rapido', 'auto', 'taxi', 'cab', 'fuel', 'petrol', 'diesel', 'hpcl', 'bpcl', 'indian oil', 'metro', 'bus', 'train', 'railway', 'irctc', 'travel', 'transport', 'toll', 'parking'],
  'Bills & Utilities': ['electricity', 'water', 'gas', 'bill', 'utility', 'recharge', 'mobile', 'broadband', 'wifi', 'internet', 'dth', 'tatasky', 'airtel', 'jio', 'vodafone', 'idea', 'bsnl', 'postpaid', 'prepaid'],
  'Entertainment': ['movie', 'cinema', 'pvr', 'inox', 'bookmyshow', 'netflix', 'prime', 'hotstar', 'disney', 'sony', 'zee5', 'spotify', 'gaana', 'wynk', 'youtube', 'entertainment', 'game', 'gaming', 'playstation', 'xbox'],
  'Healthcare': ['hospital', 'clinic', 'pharmacy', 'medical', 'medicine', 'doctor', 'health', 'healthcare', 'apollo', 'medanta', 'fortis', 'max', 'diagnostic', 'lab', 'test', 'consultation'],
  'Education': ['school', 'college', 'university', 'education', 'course', 'tuition', 'fee', 'exam', 'book', 'library', 'coaching', 'institute', 'academy', 'learning', 'udemy', 'coursera', 'byjus', 'unacademy'],
  'Groceries': ['grocery', 'supermarket', 'bigbasket', 'grofers', 'blinkit', 'zepto', 'dmart', 'reliance fresh', 'more', 'spencer', 'big bazaar', 'vegetable', 'fruit', 'milk', 'dairy', 'provision'],
  'Travel': ['flight', 'airline', 'indigo', 'air india', 'spicejet', 'vistara', 'goair', 'hotel', 'booking', 'makemytrip', 'goibibo', 'yatra', 'cleartrip', 'expedia', 'agoda', 'airbnb', 'oyo', 'vacation', 'holiday', 'trip', 'tour'],
  'Other': []
};

export function categorizeTransaction(transaction: { description: string; amount: number }): string {
  const description = transaction.description.toLowerCase();
  
  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    for (const keyword of keywords) {
      if (description.includes(keyword.toLowerCase())) {
        return category;
      }
    }
  }
  
  return 'Other';
}