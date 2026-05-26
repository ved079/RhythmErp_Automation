'use client';

import React, { useState, useEffect } from 'react';
import Joyride, { Step, CallBackProps } from 'react-joyride';
import { Button } from '@/components/ui/button';

const steps: Step[] = [
  {
    target: '[data-tour-sidebar]',
    title: 'Navigation Sidebar',
    content: 'Access all major sections of the application from here. Click on different tabs to switch between Operations, Test Runner, Results, and more.',
    placement: 'right',
  },
  {
    target: '[data-tour-operations]',
    title: 'Operations Tab',
    content: 'View and manage all test operations. Filter by status, search for specific tests, and monitor execution progress in real-time.',
    placement: 'bottom',
  },
  {
    target: '[data-tour-run-button]',
    title: 'Run Tests',
    content: 'Click this button to execute selected tests. You can run individual tests or multiple tests at once based on your selection.',
    placement: 'bottom',
  },
  {
    target: '[data-tour-results]',
    title: 'Results Dashboard',
    content: 'View test execution results with detailed pass/fail statistics. Click on any test to see detailed logs and error information.',
    placement: 'top',
  },
  {
    target: '[data-tour-schedule]',
    title: 'Schedule Automation',
    content: 'Set up automated test runs on a schedule. Configure frequency, time, and which tests to include in automated runs.',
    placement: 'top',
  },
];

export function OnboardingTour() {
  const [run, setRun] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const hasCompletedTour = localStorage.getItem('tour-completed');
    if (!hasCompletedTour) {
      setTimeout(() => {
        setRun(true);
      }, 1000);
    }
  }, []);

  const handleJoyrideCallback = (data: CallBackProps) => {
    const { status, index } = data;
    
    if (['finished', 'skipped'].includes(status)) {
      localStorage.setItem('tour-completed', 'true');
      setRun(false);
    } else if (status === 'step:after') {
      setStepIndex(index);
    }
  };

  const restartTour = () => {
    localStorage.removeItem('tour-completed');
    setStepIndex(0);
    setRun(true);
  };

  return (
    <>
      <Joyride
        continuous
        run={run}
        steps={steps}
        stepIndex={stepIndex}
        callback={handleJoyrideCallback}
        styles={{
          options: {
            primaryColor: '#3b82f6',
            zIndex: 1000,
          },
          buttonNext: {
            backgroundColor: '#3b82f6',
          },
          buttonBack: {
            marginRight: 'auto',
          },
        }}
        locale={{
          back: 'Previous',
          close: 'Skip Tour',
          last: 'Get Started',
          next: 'Next',
        }}
        showProgress
        scrollToFirstStep
        disableScrolling={false}
        scrollOffset={200}
      />
      
      <Button
        variant="outline"
        size="sm"
        onClick={restartTour}
        className="fixed bottom-4 right-4 z-50 text-xs"
      >
        Take a Tour
      </Button>
    </>
  );
}
