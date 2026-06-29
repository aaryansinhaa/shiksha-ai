import { useEffect, useRef } from 'react';
import axios from 'axios';
import { useChatStore } from '../store/useChatStore';

interface MouseTrace {
  x: number;
  y: number;
  page_width: number;
  page_height: number;
  timestamp: number;
}

export const useMouseTracker = () => {
  const { userId, client } = useChatStore();
  const tracesRef = useRef<MouseTrace[]>([]);
  const lastSampleRef = useRef<number>(0);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const now = Date.now();
      // Sample mouse position every 100ms
      if (now - lastSampleRef.current > 100) {
        lastSampleRef.current = now;
        tracesRef.current.push({
          x: e.clientX,
          y: e.clientY,
          page_width: window.innerWidth,
          page_height: window.innerHeight,
          timestamp: now
        });
      }

      // Flush batch when buffer reaches 30 samples
      if (tracesRef.current.length >= 30) {
        flushTraces();
      }
    };

    const flushTraces = async () => {
      if (tracesRef.current.length === 0) return;
      const batch = [...tracesRef.current];
      tracesRef.current = [];

      try {
        await axios.post('/log/mouse_traces', {
          user_id: userId,
          user_client: client,
          session_id: 'session_1',
          traces: batch
        });
      } catch (err) {
        // Silently fail telemetry flush to preserve UI performance
      }
    };

    const handleVisibilityChange = async () => {
      try {
        await axios.post('/log/tab_event', {
          user_id: userId,
          user_client: client,
          event_type: document.hidden ? 'tab_blur' : 'tab_focus',
          timestamp: Date.now()
        });
      } catch (err) {
        // Silently ignore
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    const interval = setInterval(flushTraces, 10000);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      clearInterval(interval);
      flushTraces();
    };
  }, [userId, client]);
};
