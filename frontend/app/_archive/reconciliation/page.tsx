"use client";

import { useState, useCallback } from "react";
import {
  scanReconciliations,
  createReconciliation,
} from "@/lib/api/client";
import { formatPaise } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, RefreshCw, Check, X, AlertCircle } from "lucide-react";
import type { PotentialMatch } from "@/types/reconciliation";

export default function ReconciliationPage() {
  const [matches, setMatches] = useState<PotentialMatch[]>([]);
  const [scanning, setScanning] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleScan = useCallback(async () => {
    setScanning(true);
    setMessage(null);
    try {
      const result = await scanReconciliations();
      setMatches(result.potential_matches);
      setMessage({ type: "success", text: `Found ${result.count} potential matches` });
    } catch (err) {
      setMessage({ type: "error", text: "Failed to scan for matches" });
    } finally {
      setScanning(false);
    }
  }, []);

  const handleConfirm = async (match: PotentialMatch, index: number) => {
    setActionInProgress(index);
    setMessage(null);
    try {
      await createReconciliation({
        debit_txn_id: match.debit_txn_id,
        credit_txn_id: match.credit_txn_id,
        amount: match.amount,
      });
      setMatches((prev) => prev.filter((_, i) => i !== index));
      setMessage({ type: "success", text: "Match confirmed successfully" });
    } catch (err) {
      setMessage({ type: "error", text: "Failed to confirm match" });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReject = async (index: number) => {
    setMatches((prev) => prev.filter((_, i) => i !== index));
    setMessage({ type: "success", text: "Match rejected" });
  };

  return (
    <div className="container mx-auto py-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reconciliation</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Match transactions across accounts
          </p>
        </div>
        <Button onClick={handleScan} disabled={scanning}>
          {scanning ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Scanning...</>
          ) : (
            <><RefreshCw className="mr-2 h-4 w-4" />Scan for Matches</>
          )}
        </Button>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${message.type === "success" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            {message.text}
          </div>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Suggested Matches</CardTitle>
        </CardHeader>
        <CardContent>
          {matches.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <RefreshCw className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No matches found. Click &quot;Scan for Matches&quot; to find potential reconciliations.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {matches.map((match, index) => (
                <div
                  key={`${match.debit_txn_id}-${match.credit_txn_id}`}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50"
                >
                  <div className="flex-1 grid grid-cols-2 gap-4">
                    <div>
                      <p className="font-medium">{match.debit_description}</p>
                      <p className="text-sm text-muted-foreground">
                        {match.debit_account_id} • {new Date(match.debit_date).toLocaleDateString()}
                      </p>
                      <p className="text-red-600 font-medium">-{formatPaise(Math.round(match.amount * 100))}</p>
                    </div>
                    <div>
                      <p className="font-medium">{match.credit_description}</p>
                      <p className="text-sm text-muted-foreground">
                        {match.credit_account_id} • {new Date(match.credit_date).toLocaleDateString()}
                      </p>
                      <p className="text-green-600 font-medium">+{formatPaise(Math.round(match.amount * 100))}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <Badge variant="outline" className="mr-2">
                      {match.date_diff_days === 0 ? "Same day" : `${match.date_diff_days} days diff`}
                    </Badge>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleConfirm(match, index)}
                      disabled={actionInProgress === index}
                    >
                      {actionInProgress === index ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600 hover:bg-red-50"
                      onClick={() => handleReject(index)}
                      disabled={actionInProgress === index}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
