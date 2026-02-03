import { useEffect, useRef } from 'react';

/**
 * Custom hook for polling with automatic cleanup
 * @param {Function} callback - Function to execute on each poll
 * @param {number} interval - Polling interval in milliseconds
 * @param {boolean} enabled - Whether polling is enabled
 */
export const usePolling = (callback, interval, enabled = true) => {
  const savedCallback = useRef();
  const intervalId = useRef();

  // Remember the latest callback
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the interval
  useEffect(() => {
    const tick = () => {
      if (savedCallback.current) {
        savedCallback.current();
      }
    };

    if (enabled && interval) {
      // Execute immediately
      tick();
      
      // Then set up interval
      intervalId.current = setInterval(tick, interval);
      
      return () => {
        if (intervalId.current) {
          clearInterval(intervalId.current);
        }
      };
    }
  }, [interval, enabled]);

  // Manual stop function
  const stopPolling = () => {
    if (intervalId.current) {
      clearInterval(intervalId.current);
    }
  };

  return { stopPolling };
};

export default usePolling;