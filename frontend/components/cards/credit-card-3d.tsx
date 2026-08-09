'use client';

import { useState } from 'react';
import type { CreditCard as CreditCardType } from '@/types/card';
import { CreditCard, Calendar, IndianRupee, Wallet } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface CreditCard3DProps {
  card: CreditCardType;
  status: { label: string; color: string };
  onClick?: () => void;
}

export function CreditCard3D({ card, status, onClick }: CreditCard3DProps) {
  const [isFlipped, setIsFlipped] = useState(false);

  const getCardGradient = (bankName: string) => {
    const gradients: Record<string, string> = {
      'HDFC Bank': 'from-blue-600 to-blue-800',
      'ICICI Bank': 'from-orange-500 to-red-600',
      'SBI Card': 'from-blue-500 to-blue-700',
      'Axis Bank': 'from-red-500 to-red-700',
      'IDFC First Bank': 'from-green-500 to-green-700',
      'IndusInd Bank': 'from-purple-500 to-purple-700',
      'American Express': 'from-gray-600 to-gray-800',
    };
    return gradients[bankName] || 'from-slate-600 to-slate-800';
  };

  const formatCardNumber = (number: string) => {
    if (!number) return '•••• •••• •••• ••••';
    const last4 = number.slice(-4);
    return `•••• •••• •••• ${last4}`;
  };

  return (
    <div 
      className="relative w-full h-56 cursor-pointer perspective-1000"
      onMouseEnter={() => setIsFlipped(true)}
      onMouseLeave={() => setIsFlipped(false)}
      onClick={onClick}
    >
      <div 
        className={`relative w-full h-full transition-transform duration-700 transform-style-preserve-3d ${
          isFlipped ? 'rotate-y-180' : ''
        }`}
        style={{
          transformStyle: 'preserve-3d',
          transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
        }}
      >
        {/* Front of card */}
        <div 
          className={`absolute inset-0 w-full h-full rounded-xl bg-gradient-to-br ${getCardGradient(card.bankName)} p-6 text-white shadow-xl backface-hidden`}
          style={{ backfaceVisibility: 'hidden' }}
        >
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center gap-2">
              <CreditCard className="h-6 w-6" />
              <span className="font-semibold text-lg">{card.bankName}</span>
            </div>
            <Badge 
              variant="secondary" 
              className={`${status.color.replace('bg-', 'bg-opacity-80 text-')} backdrop-blur-sm`}
            >
              {status.label}
            </Badge>
          </div>

          <div className="mt-8">
            <div className="font-mono text-xl tracking-wider mb-4">
              {formatCardNumber(card.cardNumber)}
            </div>
            
            <div className="flex justify-between items-end">
              <div>
                <p className="text-xs text-white/70 mb-1">Credit Limit</p>
                <p className="font-semibold text-lg">
                  ₹{(card.creditLimit || 0).toLocaleString('en-IN')}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-white/70 mb-1">Amount Due</p>
                <p className="font-semibold text-lg">
                  ₹{(card.totalAmountDue || 0).toLocaleString('en-IN')}
                </p>
              </div>
            </div>
          </div>

          <div className="absolute bottom-4 right-4">
            <div className="w-12 h-8 bg-gradient-to-r from-yellow-400 to-yellow-600 rounded opacity-80" />
          </div>
        </div>

        {/* Back of card */}
        <div 
          className={`absolute inset-0 w-full h-full rounded-xl bg-gradient-to-br ${getCardGradient(card.bankName)} p-6 text-white shadow-xl`}
          style={{ 
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
          }}
        >
          <div className="w-full h-8 bg-black/30 rounded mb-4" />
          
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Calendar className="h-5 w-5 text-white/70" />
              <div>
                <p className="text-xs text-white/70">Due Date</p>
                <p className="font-semibold">{card.dueDate || 'N/A'}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <IndianRupee className="h-5 w-5 text-white/70" />
              <div>
                <p className="text-xs text-white/70">Minimum Due</p>
                <p className="font-semibold">
                  ₹{(card.minimumAmountDue || 0).toLocaleString('en-IN')}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Wallet className="h-5 w-5 text-white/70" />
              <div>
                <p className="text-xs text-white/70">Available Credit</p>
                <p className="font-semibold">
                  ₹{((card.creditLimit || 0) - (card.totalAmountDue || 0)).toLocaleString('en-IN')}
                </p>
              </div>
            </div>
          </div>

          <div className="absolute bottom-4 left-4 right-4">
            <p className="text-xs text-white/60 text-center">
              Hover to flip back
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}