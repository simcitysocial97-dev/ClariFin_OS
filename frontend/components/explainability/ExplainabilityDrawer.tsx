/**
 * ExplainabilityDrawer - Universal explainability drawer
 *
 * The ONLY explainability UI in the application.
 * Every future capability will reuse it.
 *
 * Does NOT know about:
 * - NetWorth
 * - Loans
 * - Cards
 * - Accounts
 * - Dashboard
 *
 * Only knows about: Explanation contract
 */

'use client'

import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
} from '@/components/ui/drawer'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { OverviewPanel } from './panels/OverviewPanel'
import { EvidencePanel } from './panels/EvidencePanel'
import { CalculationPanel } from './panels/CalculationPanel'
import { SourcesPanel } from './panels/SourcesPanel'
import { useExplainabilityDrawer } from './hooks/useExplainabilityDrawer'

/**
 * Universal explainability drawer
 */
export function ExplainabilityDrawer() {
  const {
    isOpen,
    activeTab,
    selectedExplanation,
    selectedRecommendation,
    close,
    setActiveTab,
  } = useExplainabilityDrawer()

  // Get the current explanation to display
  const explanation = selectedExplanation ?? (selectedRecommendation as any)

  if (!explanation) {
    return null
  }

  return (
    <Drawer open={isOpen} onOpenChange={close}>
      <DrawerContent>
        <DrawerHeader>
          <DrawerTitle>
            {selectedExplanation?.metric ?? selectedRecommendation?.recommendation}
          </DrawerTitle>
          <DrawerDescription>
            Explanation and evidence for this metric
          </DrawerDescription>
        </DrawerHeader>

        <ScrollArea className="flex-1 px-4">
          <Tabs
            value={activeTab}
            onValueChange={(value) => setActiveTab(value as any)}
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="calculation">Calculation</TabsTrigger>
              <TabsTrigger value="evidence">Evidence</TabsTrigger>
              <TabsTrigger value="sources">Sources</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="mt-4">
              <OverviewPanel explanation={explanation} />
            </TabsContent>

            <TabsContent value="calculation" className="mt-4">
              <CalculationPanel explanation={explanation} />
            </TabsContent>

            <TabsContent value="evidence" className="mt-4">
              <EvidencePanel explanation={explanation} />
            </TabsContent>

            <TabsContent value="sources" className="mt-4">
              <SourcesPanel explanation={explanation} />
            </TabsContent>
          </Tabs>
        </ScrollArea>
      </DrawerContent>
    </Drawer>
  )
}