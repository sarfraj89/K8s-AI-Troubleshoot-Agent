import { useEffect, useRef, useState } from 'react';
import { insforgeClient, CHANNELS } from '../services/insforge';
import { ProgressStep, ProgressUpdate } from '../types';

const STEPS: ProgressStep[] = [
  'pods',
  'logs',
  'events',
  'deployments',
  'network',
  'ai',
  'complete',
];

const createInitialProgress = (): ProgressUpdate[] =>
  STEPS.map((step) => ({ step, status: 'pending', message: '' }));

const mergeProgressUpdate = (
  progress: ProgressUpdate[],
  update: ProgressUpdate,
): ProgressUpdate[] =>
  progress.map((step) =>
    step.step === update.step ? { ...step, ...update } : step,
  );

export function useInvestigationProgress(userId: string | undefined) {
  const [progress, setProgress] = useState<ProgressUpdate[]>(createInitialProgress);
  const [hasRealtimeUpdates, setHasRealtimeUpdates] = useState(false);
  const hasRealtimeUpdatesRef = useRef(false);

  useEffect(() => {
    if (!userId) return;

    const channel = CHANNELS.USER_PROGRESS(userId);
    const handleProgress = (message: ProgressUpdate) => {
      hasRealtimeUpdatesRef.current = true;
      setHasRealtimeUpdates(true);
      setProgress((prev) => mergeProgressUpdate(prev, message));
    };

    try {
      insforgeClient.realtime.on<ProgressUpdate>('progress', handleProgress);
      insforgeClient.realtime.on('error', (error) => {
        console.warn('InsForge realtime error:', error);
      });

      insforgeClient.realtime.connect().then(async () => {
        const subscription = await insforgeClient.realtime.subscribe(channel);
        if (!subscription.ok) {
          console.warn('Failed to subscribe to progress channel:', subscription.error);
        }
      });

      return () => {
        insforgeClient.realtime.off('progress', handleProgress);
        insforgeClient.realtime.unsubscribe(channel);
      };
    } catch (error) {
      console.warn('Failed to subscribe to progress updates:', error);
    }
  }, [userId]);

  const resetProgress = () => {
    hasRealtimeUpdatesRef.current = false;
    setHasRealtimeUpdates(false);
    setProgress(createInitialProgress());
  };

  const startFallbackProgress = () => {
    let stepIndex = 0;

    const interval = window.setInterval(() => {
      setProgress((prev) => {
        if (hasRealtimeUpdatesRef.current) {
          window.clearInterval(interval);
          return prev;
        }

        return prev.map((step, index) => {
          if (index < stepIndex) {
            return { ...step, status: 'completed' };
          }

          if (index === stepIndex) {
            return { ...step, status: 'in-progress' };
          }

          return step;
        });
      });

      stepIndex += 1;
      if (stepIndex >= STEPS.length) {
        window.clearInterval(interval);
      }
    }, 900);

    return () => window.clearInterval(interval);
  };

  const completeProgress = () => {
    setProgress((prev) => prev.map((step) => ({ ...step, status: 'completed' })));
  };

  const failProgress = () => {
    setProgress((prev) =>
      prev.map((step) =>
        step.status === 'completed' ? step : { ...step, status: 'error' },
      ),
    );
  };

  return {
    progress,
    hasRealtimeUpdates,
    resetProgress,
    startFallbackProgress,
    completeProgress,
    failProgress,
  };
}
