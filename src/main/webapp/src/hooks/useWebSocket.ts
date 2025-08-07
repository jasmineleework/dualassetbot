/**
 * React hooks for WebSocket integration
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import wsService, {
  MessageType,
  PriceUpdate,
  TradeExecution,
  TaskStatusUpdate,
  SystemAlert,
  PortfolioUpdate,
  AIRecommendationUpdate
} from '../services/websocket';

/**
 * Hook for WebSocket connection management
 */
export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(wsService.isConnected());
  const [connectionState, setConnectionState] = useState(wsService.getState());

  useEffect(() => {
    // Connect on mount
    wsService.connect().catch(console.error);

    // Monitor connection state
    const interval = setInterval(() => {
      setIsConnected(wsService.isConnected());
      setConnectionState(wsService.getState());
    }, 1000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const reconnect = useCallback(() => {
    return wsService.connect();
  }, []);

  const disconnect = useCallback(() => {
    wsService.disconnect();
  }, []);

  return {
    isConnected,
    connectionState,
    reconnect,
    disconnect
  };
}

/**
 * Hook for price updates
 */
export function usePriceUpdates(symbols: string[]) {
  const [prices, setPrices] = useState<Record<string, PriceUpdate>>({});
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    if (symbols.length === 0) return;

    const unsubscribe = wsService.subscribeToPriceUpdates(symbols, (data) => {
      setPrices(prev => ({
        ...prev,
        [data.symbol]: data
      }));
      setLastUpdate(new Date());
    });

    return unsubscribe;
  }, [symbols.join(',')]); // Re-subscribe when symbols change

  return { prices, lastUpdate };
}

/**
 * Hook for trade execution updates
 */
export function useTradeExecutions(onExecution?: (execution: TradeExecution) => void) {
  const [executions, setExecutions] = useState<TradeExecution[]>([]);
  const [lastExecution, setLastExecution] = useState<TradeExecution | null>(null);

  useEffect(() => {
    const unsubscribe = wsService.subscribeToTradeExecutions((data) => {
      setExecutions(prev => [data, ...prev].slice(0, 50)); // Keep last 50
      setLastExecution(data);
      onExecution?.(data);
    });

    return unsubscribe;
  }, [onExecution]);

  return { executions, lastExecution };
}

/**
 * Hook for task status updates
 */
export function useTaskStatus(taskId: string | null) {
  const [status, setStatus] = useState<TaskStatusUpdate | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!taskId) return;

    const unsubscribe = wsService.subscribeToTaskStatus(taskId, (data) => {
      setStatus(data);
      setIsComplete(data.status === 'SUCCESS' || data.status === 'FAILED');
    });

    return unsubscribe;
  }, [taskId]);

  return { status, isComplete };
}

/**
 * Hook for system alerts
 */
export function useSystemAlerts(maxAlerts: number = 10) {
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const unsubscribe = wsService.subscribeToSystemAlerts((data) => {
      setAlerts(prev => [data, ...prev].slice(0, maxAlerts));
      setUnreadCount(prev => prev + 1);
    });

    return unsubscribe;
  }, [maxAlerts]);

  const markAllRead = useCallback(() => {
    setUnreadCount(0);
  }, []);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
    setUnreadCount(0);
  }, []);

  return { alerts, unreadCount, markAllRead, clearAlerts };
}

/**
 * Hook for portfolio updates
 */
export function usePortfolioUpdates() {
  const [portfolio, setPortfolio] = useState<PortfolioUpdate | null>(null);
  const [updateCount, setUpdateCount] = useState(0);

  useEffect(() => {
    const unsubscribe = wsService.subscribeToPortfolioUpdates((data) => {
      setPortfolio(data);
      setUpdateCount(prev => prev + 1);
    });

    return unsubscribe;
  }, []);

  return { portfolio, updateCount };
}

/**
 * Hook for AI recommendations
 */
export function useAIRecommendations(symbols?: string[]) {
  const [recommendations, setRecommendations] = useState<Record<string, AIRecommendationUpdate>>({});
  const [latestRecommendation, setLatestRecommendation] = useState<AIRecommendationUpdate | null>(null);

  useEffect(() => {
    const unsubscribe = wsService.subscribeToAIRecommendations((data) => {
      // Filter by symbols if provided
      if (symbols && !symbols.includes(data.symbol)) {
        return;
      }

      setRecommendations(prev => ({
        ...prev,
        [data.symbol]: data
      }));
      setLatestRecommendation(data);
    });

    return unsubscribe;
  }, [symbols?.join(',')]);

  return { recommendations, latestRecommendation };
}

/**
 * Hook for WebSocket message subscription
 */
export function useWebSocketSubscription<T = any>(
  type: MessageType,
  callback?: (data: T) => void
) {
  const [data, setData] = useState<T | null>(null);
  const [messageCount, setMessageCount] = useState(0);
  const callbackRef = useRef(callback);

  // Update callback ref
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const unsubscribe = wsService.subscribe(type, (messageData) => {
      setData(messageData);
      setMessageCount(prev => prev + 1);
      callbackRef.current?.(messageData);
    });

    return unsubscribe;
  }, [type]);

  return { data, messageCount };
}

/**
 * Hook for real-time connection indicator
 */
export function useConnectionIndicator() {
  const { isConnected, connectionState } = useWebSocket();
  const [showIndicator, setShowIndicator] = useState(true);

  useEffect(() => {
    if (isConnected) {
      // Hide indicator after 3 seconds when connected
      const timer = setTimeout(() => {
        setShowIndicator(false);
      }, 3000);
      return () => clearTimeout(timer);
    } else {
      // Always show when disconnected
      setShowIndicator(true);
    }
  }, [isConnected]);

  const getIndicatorColor = () => {
    switch (connectionState) {
      case 'OPEN':
        return '#52c41a';
      case 'CONNECTING':
        return '#faad14';
      case 'CLOSING':
      case 'CLOSED':
        return '#f5222d';
      default:
        return '#d9d9d9';
    }
  };

  const getIndicatorText = () => {
    switch (connectionState) {
      case 'OPEN':
        return 'Connected';
      case 'CONNECTING':
        return 'Connecting...';
      case 'CLOSING':
        return 'Disconnecting...';
      case 'CLOSED':
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  return {
    showIndicator,
    isConnected,
    connectionState,
    color: getIndicatorColor(),
    text: getIndicatorText()
  };
}