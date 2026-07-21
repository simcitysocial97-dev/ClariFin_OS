/**
 * Cards Page - Stage 8E-C2 Production Visual System Migration
 *
 * Table Surface - Main analysis surface for credit cards.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface/Panel primitives, removed legacy padding.
 */

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
import { CreditCard, AlertCircle } from 'lucide-react'
import type { CardSummary } from '@/lib/hooks/use-cards'
import { Surface } from '@/components/primitives/surface/surface'
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel'
import { Stack } from '@/components/primitives/layout/stack'
import { Grid } from '@/components/primitives/layout/grid'

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
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Cards" />
          <PanelBody loading>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-40" />
              ))}
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    )
  }

  // Error state
  if (error) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Cards" />
          <PanelBody error={error.message}>
            <div className="p-4">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error loading cards</AlertTitle>
                <AlertDescription>
                  {error.message}. Please ensure the API server is running at http://localhost:8000
                </AlertDescription>
              </Alert>
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    )
  }

  // Empty state
  if (!cardsData || cardsData.total_cards === 0) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Cards" />
          <PanelBody empty emptyMessage="No credit cards found">
            <div className="p-4">
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
          </PanelBody>
        </Panel>
      </Surface>
    )
  }

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Cards" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            {/* Summary Cards */}
            <CardPortfolioHeader data={cardsData} loading={false} />

            {/* Cards Grid */}
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-3">
              {cardsData.cards.map((card) => (
                <CreditCardTile
                  key={card.card_id}
                  card={card}
                  onViewStatements={() => handleViewStatements(card)}
                  onValidate={() => handleValidate(card)}
                />
              ))}
            </Grid>
          </Stack>
        </PanelBody>
      </Panel>

      {/* Statement History Drawer - for card details */}
      <StatementHistoryDrawer
        card={selectedCard}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        statements={cardStatements}
      />
    </Surface>
  )
}