'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, FileText, BarChart3, CreditCard, X, ChevronRight, ChevronLeft } from 'lucide-react';

interface TutorialStep {
  title: string;
  description: string;
  icon: React.ReactNode;
  target?: string;
}

const tutorialSteps: TutorialStep[] = [
  {
    title: 'Welcome to Bank Statement Parser',
    description: 'Your personal finance companion. Let\'s take a quick tour to get you started.',
    icon: <CreditCard className="h-8 w-8" />,
  },
  {
    title: 'Upload Your Statements',
    description: 'Drag and drop your bank statement PDFs. We support HDFC, ICICI, SBI, Axis, IDFC, IndusInd, and American Express.',
    icon: <Upload className="h-8 w-8" />,
  },
  {
    title: 'Automatic Extraction',
    description: 'We automatically extract transactions, categorize them, and calculate your spending patterns.',
    icon: <FileText className="h-8 w-8" />,
  },
  {
    title: 'Visualize Your Spending',
    description: 'View detailed analytics, track your expenses by category, and monitor your credit card bills.',
    icon: <BarChart3 className="h-8 w-8" />,
  },
];

interface TutorialProps {
  onComplete: () => void;
  onSkip: () => void;
}

export function Tutorial({ onComplete, onSkip }: TutorialProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if user has seen tutorial before
    const hasSeenTutorial = localStorage.getItem('hasSeenTutorial');
    if (!hasSeenTutorial) {
      setIsVisible(true);
    }
  }, []);

  const handleNext = () => {
    if (currentStep < tutorialSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    localStorage.setItem('hasSeenTutorial', 'true');
    setIsVisible(false);
    onComplete();
  };

  const handleSkip = () => {
    localStorage.setItem('hasSeenTutorial', 'true');
    setIsVisible(false);
    onSkip();
  };

  if (!isVisible) return null;

  const step = tutorialSteps[currentStep];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md relative">
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <CardHeader className="text-center pb-4">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4 text-primary">
            {step.icon}
          </div>
          <CardTitle className="text-xl">{step.title}</CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          <p className="text-muted-foreground text-center">
            {step.description}
          </p>

          {/* Progress dots */}
          <div className="flex justify-center gap-2">
            {tutorialSteps.map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full transition-colors ${
                  index === currentStep ? 'bg-primary' : 'bg-muted'
                }`}
              />
            ))}
          </div>

          {/* Navigation buttons */}
          <div className="flex justify-between items-center">
            <Button
              variant="ghost"
              onClick={handlePrevious}
              disabled={currentStep === 0}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>

            <div className="text-sm text-muted-foreground">
              {currentStep + 1} of {tutorialSteps.length}
            </div>

            <Button onClick={handleNext}>
              {currentStep === tutorialSteps.length - 1 ? 'Get Started' : 'Next'}
              {currentStep < tutorialSteps.length - 1 && (
                <ChevronRight className="h-4 w-4 ml-1" />
              )}
            </Button>
          </div>

          <Button variant="link" onClick={handleSkip} className="w-full">
            Skip tutorial
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

export function ResetTutorial() {
  const handleReset = () => {
    localStorage.removeItem('hasSeenTutorial');
    window.location.reload();
  };

  return (
    <Button variant="outline" size="sm" onClick={handleReset}>
      Show Tutorial Again
    </Button>
  );
}