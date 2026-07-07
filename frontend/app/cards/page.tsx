'use client'

import { useState } from 'react'
import { useCards } from '@/lib/hooks/use-cards'
import { useStatementsQuery } from '@/lib/hooks/use-query-finance'
import { CardPortfolioHeader } from '@/components/cards/card-portfolio-header'
import { CreditCardTile } from '@/components/cards/credit-card-tile'
import { StatementHistoryDrawer } from '@/components/cards/statement-history-drawer'
import { EmptyState } from '@/components/ui/empty-state'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { CreditCard, Plus, AlertCircle } from 'lucide-react'
import Link from 'next/link'
import type { CardSummary } from '@/lib/hooks/use-cards'

export default function CardsPage() {
  const { data: cardsData, loading, error } = useCards()
  const { data: allStatements } = useStatementsQuery()
  const [selectedCard, setSelectedCard] = useState<CardSummary | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  // Filter statements for selected card
  const cardStatements = selectedCard
    ? allStatements?.filter(
        (stmt) => stmt.bank === selectedCard.bank && stmt.card_last4 === selectedCard.card_last4
      ) || []
    : []

  const handleViewStatements = (card: CardSummary) => {
    setSelectedCard(card)
    setDrawerOpen(true)
  }

  const handleValidate = (card: CardSummary) => {
    // TODO: Implement validation API call
    console.log('Validate card:', card.card_id)
  }

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <Skeleton className="h-10 w-48" />
            <Skeleton className="h-4 w-64 mt-2" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-card border rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-muted rounded mb-2" />
              <div className="h-6 bg-muted rounded" />
            </div>
          ))}
        </div>
        
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="border rounded-lg p-4 space-y-3">
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <div className="flex gap-2 pt-4">
                <Skeleton className="h-10 flex-1" />
                <Skeleton className="h-10 flex-1" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Credit Cards</h1>
            <p className="text-muted-foreground mt-1">
              Manage your cards and view details
            </p>
          </div>
          <Link href="/dashboard?upload=true">
            <button className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background bg-primary text-primary-foreground hover:bg-primary/90 h-10 py-2 px-4">
              <Plus className="mr-2 h-4 w-4" />
              Add Card
            </button>
          </Link>
        </div>
        
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error loading cards</AlertTitle>
          <AlertDescription>
            {error.message}. Please ensure the API server is running at http://localhost:8000
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  // Empty state
  if (!cardsData || cardsData.total_cards === 0) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Credit Cards</h1>
            <p className="text-muted-foreground mt-1">
              Manage your cards and view details
            </p>
          </div>
          <Link href="/dashboard?upload=true">
            <button className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background bg-primary text-primary-foreground hover:bg-primary/90 h-10 py-2 px-4">
              <Plus className="mr-2 h-4 w-4" />
              Add Card
            </button>
          </Link>
        </div>
        
        <EmptyState
          icon={<CreditCard className="h-10 w-10" />}
          title="No credit cards found"
          description="Import a credit card statement to get started. We'll automatically extract and display your card information."
          action={{
            label: "Upload Statement",
            href: "/dashboard?upload=true"
          }}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Credit Cards</h1>
          <p className="text-muted-foreground mt-1">
            Manage your cards and view details
          </p>
        </div>
        <Link href="/dashboard?upload=true">
          <button className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background bg-primary text-primary-foreground hover:bg-primary/90 h-10 py-2 px-4">
            <Plus className="mr-2 h-4 w-4" />
            Add Card
          </button>
        </Link>
      </div>

      <CardPortfolioHeader data={cardsData} loading={false} />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {cardsData.cards.map((card) => (
          <CreditCardTile
            key={card.card_id}
            card={card}
            onViewStatements={() => handleViewStatements(card)}
            onValidate={() => handleValidate(card)}
          />
        ))}
      </div>

      <StatementHistoryDrawer
        card={selectedCard}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        statements={cardStatements}
      />
    </div>
  )
}