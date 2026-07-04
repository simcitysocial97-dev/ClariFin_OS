"use client";

/**
 * Projections Page
 * ================
 * Financial projections with three tabs:
 * 1. Net Worth Forecast
 * 2. Goal Planner
 * 3. What-If Simulator
 */

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Target, TrendingUp, GitCompare } from "lucide-react";
import { NetWorthForecast } from "@/components/projections/networth-forecast";
import { GoalPlanner } from "@/components/projections/goal-planner";
import { WhatIfSimulator } from "@/components/projections/whatif-simulator";

export default function ProjectionsPage() {
  const [activeTab, setActiveTab] = useState("forecast");

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Target className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-2xl font-bold">Financial Projections</h1>
          <p className="text-muted-foreground text-sm">
            Forecast net worth, plan goals, and run what-if scenarios
          </p>
        </div>
      </div>

      {/* Tabbed Layout */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <Card className="p-2">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="forecast" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              <span className="hidden sm:inline">Net Worth Forecast</span>
              <span className="sm:hidden">Forecast</span>
            </TabsTrigger>
            <TabsTrigger value="goals" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              <span className="hidden sm:inline">Goal Planner</span>
              <span className="sm:hidden">Goals</span>
            </TabsTrigger>
            <TabsTrigger value="whatif" className="flex items-center gap-2">
              <GitCompare className="h-4 w-4" />
              <span className="hidden sm:inline">What-If Simulator</span>
              <span className="sm:hidden">What-If</span>
            </TabsTrigger>
          </TabsList>
        </Card>

        <TabsContent value="forecast" className="mt-0">
          <NetWorthForecast />
        </TabsContent>

        <TabsContent value="goals" className="mt-0">
          <GoalPlanner />
        </TabsContent>

        <TabsContent value="whatif" className="mt-0">
          <WhatIfSimulator />
        </TabsContent>
      </Tabs>
    </div>
  );
}
