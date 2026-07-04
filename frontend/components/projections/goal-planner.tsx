"use client";

/**
 * Goal Planner Component
 * ======================
 * Tab 2: Interactive goal calculator with growth chart
 */

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Target,
  Calendar,
  PiggyBank,
  TrendingUp,
  Plus,
  Trash2,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { useCalculateGoal } from "@/lib/hooks/use-finance-data";
import { formatPaise, formatPaiseCompact } from "@/lib/format";
import dynamic from "next/dynamic";

const ResponsiveContainer = dynamic(
  () => import("recharts").then((mod) => mod.ResponsiveContainer),
  { ssr: false }
);
const LineChart = dynamic(
  () => import("recharts").then((mod) => mod.LineChart),
  { ssr: false }
);
// @ts-expect-error - Recharts dynamic import type mismatch
const Line = dynamic(() => import("recharts").then((mod) => mod.Line), {
  ssr: false,
});
// @ts-expect-error - Recharts dynamic import type mismatch
const XAxis = dynamic(() => import("recharts").then((mod) => mod.XAxis), {
  ssr: false,
});
// @ts-expect-error - Recharts dynamic import type mismatch
const YAxis = dynamic(() => import("recharts").then((mod) => mod.YAxis), {
  ssr: false,
});
const CartesianGrid = dynamic(
  () => import("recharts").then((mod) => mod.CartesianGrid),
  { ssr: false }
);
// @ts-expect-error - Recharts dynamic import type mismatch
const Tooltip = dynamic(() => import("recharts").then((mod) => mod.Tooltip), {
  ssr: false,
});

interface SavedGoal {
  id: string;
  name: string;
  targetPaise: number;
  currentPaise: number;
  monthlyPaise: number;
  annualReturn: number;
  result: {
    months_needed: number | null;
    projected_date: string | null;
    total_contributed_paise: number;
    total_returns_paise: number;
    target_achievable: boolean;
  };
}

export function GoalPlanner() {
  const [goals, setGoals] = useState<SavedGoal[]>([]);
  const [name, setName] = useState("");
  const [target, setTarget] = useState("");
  const [current, setCurrent] = useState("0");
  const [monthly, setMonthly] = useState("");
  const [annualReturn, setAnnualReturn] = useState(8);
  const [showResults, setShowResults] = useState(false);

  const { data: result, loading: calculating } = useCalculateGoal();

  const handleCalculate = () => {
    setShowResults(true);
  };

  const handleSaveGoal = () => {
    if (!result || !name) return;

    const newGoal: SavedGoal = {
      id: Date.now().toString(),
      name,
      targetPaise: Math.round(parseFloat(target) * 100),
      currentPaise: Math.round(parseFloat(current || "0") * 100),
      monthlyPaise: Math.round(parseFloat(monthly) * 100),
      annualReturn,
      result: {
        months_needed: result.months_needed,
        projected_date: result.projected_date,
        total_contributed_paise: result.total_contributed_paise,
        total_returns_paise: result.total_returns_paise,
        target_achievable: result.target_achievable,
      },
    };

    setGoals((prev) => [...prev, newGoal]);
    setName("");
    setTarget("");
    setCurrent("0");
    setMonthly("");
    setAnnualReturn(8);
    setShowResults(false);
  };

  const handleDeleteGoal = (id: string) => {
    setGoals((prev) => prev.filter((g) => g.id !== id));
  };

  const chartData = useMemo(() => {
    if (!result || !result.months_needed) return [];

    const data = [];
    const monthlyPaise = Math.round(parseFloat(monthly) * 100);
    const currentPaise = Math.round(parseFloat(current || "0") * 100);
    const monthlyRate = annualReturn / 100 / 12;
    let accumulated = currentPaise;

    for (let month = 0; month <= result.months_needed; month++) {
      data.push({
        month,
        amount: Math.round(accumulated),
        label: month === 0 ? "Start" : `Month ${month}`,
      });
      accumulated = accumulated * (1 + monthlyRate) + monthlyPaise;
    }

    return data;
  }, [result, monthly, current, annualReturn]);

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Plan Your Goal
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="goal-name">Goal Name</Label>
              <Input
                id="goal-name"
                placeholder="e.g., Emergency Fund, House Down Payment"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="target-amount">Target Amount (₹)</Label>
              <Input
                id="target-amount"
                type="number"
                placeholder="500000"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="current-savings">Current Savings (₹)</Label>
              <Input
                id="current-savings"
                type="number"
                placeholder="0"
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="monthly-contribution">Monthly Contribution (₹)</Label>
              <Input
                id="monthly-contribution"
                type="number"
                placeholder="10000"
                value={monthly}
                onChange={(e) => setMonthly(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Expected Annual Return</Label>
              <span className="text-sm font-medium">{annualReturn}%</span>
            </div>
            <Slider
              value={[annualReturn]}
              onValueChange={(value) => setAnnualReturn(value[0] ?? 8)}
              min={0}
              max={15}
              step={0.5}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0%</span>
              <span>Conservative</span>
              <span>Aggressive</span>
              <span>15%</span>
            </div>
          </div>

          <Button
            onClick={handleCalculate}
            disabled={calculating || !target || !monthly}
            className="w-full"
          >
            {calculating ? "Calculating..." : "Calculate"}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {showResults && result && (
        <Card className={result.target_achievable ? "border-green-500/50" : "border-red-500/50"}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              {result.target_achievable ? (
                <>
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  Goal Achievable!
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  Goal Not Achievable
                </>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {result.target_achievable && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      Months Needed
                    </p>
                    <p className="text-2xl font-bold">{result.months_needed}</p>
                  </div>
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      Target Date
                    </p>
                    <p className="text-lg font-bold">
                      {result.projected_date
                        ? new Date(result.projected_date).toLocaleDateString(
                            "en-IN",
                            { month: "short", year: "numeric" }
                          )
                        : "-"}
                    </p>
                  </div>
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <PiggyBank className="h-3 w-3" />
                      Total Contributed
                    </p>
                    <p className="text-lg font-bold">
                      {formatPaiseCompact(result.total_contributed_paise)}
                    </p>
                  </div>
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" />
                      Returns Earned
                    </p>
                    <p className="text-lg font-bold text-green-500">
                      {formatPaiseCompact(result.total_returns_paise)}
                    </p>
                  </div>
                </div>

                {/* Growth Chart */}
                {chartData.length > 0 && (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                          dataKey="month"
                          tick={{ fontSize: 12 }}
                          tickFormatter={(value) =>
                            value % 12 === 0 ? `Y${value / 12}` : ""
                          }
                        />
                        <YAxis
                          tick={{ fontSize: 12 }}
                          tickFormatter={(value) => formatPaiseCompact(value)}
                          width={80}
                        />
                        <Tooltip
                          formatter={(value) => [
                            formatPaise(Number(value)),
                            "Amount",
                          ]}
                          labelFormatter={(label) => `Month ${label}`}
                        />
                        <Line
                          type="monotone"
                          dataKey="amount"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                <Button onClick={handleSaveGoal} className="w-full" variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  Save Goal
                </Button>
              </>
            )}

            {!result.target_achievable && (
              <div className="text-center py-4">
                <p className="text-muted-foreground">{result.reason}</p>
                <p className="text-sm mt-2">
                  Try increasing your monthly contribution or adjusting your target.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Saved Goals */}
      {goals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Saved Goals ({goals.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              <div className="space-y-3">
                {goals.map((goal) => (
                  <div
                    key={goal.id}
                    className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{goal.name}</p>
                        <Badge variant="outline">
                          {goal.annualReturn}% return
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Target: {formatPaise(goal.targetPaise)} •{" "}
                        {goal.result.months_needed} months
                      </p>
                      {goal.result.projected_date && (
                        <p className="text-xs text-muted-foreground">
                          By{" "}
                          {new Date(goal.result.projected_date).toLocaleDateString(
                            "en-IN",
                            { month: "long", year: "numeric" }
                          )}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteGoal(goal.id)}
                      className="text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
