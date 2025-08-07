/**
 * WebSocket service for real-time data streaming
 */

import { message } from 'antd';

export type MessageType = 
  | 'price_update'
  | 'market_data'
  | 'trade_execution'
  | 'task_status'
  | 'system_alert'
  | 'portfolio_update'
  | 'ai_recommendation'
  | 'health_check';

export interface WSMessage {
  type: MessageType;
  data: any;
  timestamp: string;
}

export interface PriceUpdate {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  timestamp: string;
}

export interface TradeExecution {
  id: string;
  product_id: string;
  amount: number;
  status: 'SUCCESS' | 'FAILED' | 'PENDING';
  message?: string;
  executed_price?: number;
  timestamp: string;
}

export interface TaskStatusUpdate {
  task_id: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED';
  progress?: number;
  result?: any;
  error?: string;
}

export interface SystemAlert {
  level: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  title: string;
  message: string;
  timestamp: string;
  action?: string;
}

export interface PortfolioUpdate {
  total_value: number;
  total_invested: number;
  total_returns: number;
  active_investments: number;
  last_update: string;
}

export interface AIRecommendationUpdate {
  symbol: string;
  product_id: string;
  recommendation: 'BUY' | 'SELL' | 'HOLD';
  ai_score: number;
  confidence: number;
  reasons: string[];
  timestamp: string;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval: number = 5000;
  private maxReconnectAttempts: number = 10;
  private reconnectAttempts: number = 0;
  private listeners: Map<MessageType, Set<(data: any) => void>> = new Map();
  private isConnecting: boolean = false;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private messageQueue: WSMessage[] = [];
  private maxQueueSize: number = 100;

  constructor() {
    // Determine WebSocket URL based on environment
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.REACT_APP_WS_URL || window.location.host;
    this.url = `${protocol}//${host}/ws`;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        // Wait for existing connection attempt
        setTimeout(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            resolve();
          } else {
            reject(new Error('Connection in progress'));
          }
        }, 1000);
        return;
      }

      this.isConnecting = true;
      console.log('Connecting to WebSocket:', this.url);

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.flushMessageQueue();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();
          
          if (!event.wasClean) {
            this.attemptReconnect();
          }
        };

      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.listeners.clear();
    this.messageQueue = [];
  }

  /**
   * Send message through WebSocket
   */
  send(message: WSMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message if not connected
      this.queueMessage(message);
      // Try to reconnect
      this.connect().catch(console.error);
    }
  }

  /**
   * Subscribe to specific message type
   */
  subscribe(type: MessageType, callback: (data: any) => void): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    
    this.listeners.get(type)!.add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(type);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.listeners.delete(type);
        }
      }
    };
  }

  /**
   * Subscribe to price updates
   */
  subscribeToPriceUpdates(symbols: string[], callback: (data: PriceUpdate) => void): () => void {
    // Send subscription message
    this.send({
      type: 'price_update',
      data: { action: 'subscribe', symbols },
      timestamp: new Date().toISOString()
    });

    // Register callback
    return this.subscribe('price_update', callback);
  }

  /**
   * Subscribe to trade executions
   */
  subscribeToTradeExecutions(callback: (data: TradeExecution) => void): () => void {
    return this.subscribe('trade_execution', callback);
  }

  /**
   * Subscribe to task status updates
   */
  subscribeToTaskStatus(taskId: string, callback: (data: TaskStatusUpdate) => void): () => void {
    // Send subscription for specific task
    this.send({
      type: 'task_status',
      data: { action: 'subscribe', task_id: taskId },
      timestamp: new Date().toISOString()
    });

    return this.subscribe('task_status', (data) => {
      if (data.task_id === taskId) {
        callback(data);
      }
    });
  }

  /**
   * Subscribe to system alerts
   */
  subscribeToSystemAlerts(callback: (data: SystemAlert) => void): () => void {
    return this.subscribe('system_alert', callback);
  }

  /**
   * Subscribe to portfolio updates
   */
  subscribeToPortfolioUpdates(callback: (data: PortfolioUpdate) => void): () => void {
    return this.subscribe('portfolio_update', callback);
  }

  /**
   * Subscribe to AI recommendations
   */
  subscribeToAIRecommendations(callback: (data: AIRecommendationUpdate) => void): () => void {
    return this.subscribe('ai_recommendation', callback);
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection state
   */
  getState(): 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED' {
    if (!this.ws) return 'CLOSED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'OPEN';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'CLOSED';
    }
  }

  /**
   * Handle incoming message
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WSMessage = JSON.parse(event.data);
      
      // Handle heartbeat
      if (message.type === 'health_check') {
        this.handleHeartbeat(message);
        return;
      }

      // Notify listeners
      const callbacks = this.listeners.get(message.type);
      if (callbacks) {
        callbacks.forEach(callback => {
          try {
            callback(message.data);
          } catch (error) {
            console.error('Error in message callback:', error);
          }
        });
      }

      // Show system alerts as notifications
      if (message.type === 'system_alert') {
        this.showSystemAlert(message.data as SystemAlert);
      }

    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({
          type: 'health_check',
          data: { ping: true },
          timestamp: new Date().toISOString()
        });
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Handle heartbeat response
   */
  private handleHeartbeat(message: WSMessage): void {
    // Connection is alive, no action needed
    console.debug('Heartbeat received:', message.timestamp);
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      message.error('Connection lost. Please refresh the page.');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectInterval * this.reconnectAttempts, 30000);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Queue message for sending when connected
   */
  private queueMessage(message: WSMessage): void {
    if (this.messageQueue.length >= this.maxQueueSize) {
      this.messageQueue.shift(); // Remove oldest message
    }
    this.messageQueue.push(message);
  }

  /**
   * Send all queued messages
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift();
      if (message) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  /**
   * Show system alert as notification
   */
  private showSystemAlert(alert: SystemAlert): void {
    const msg = `${alert.title}: ${alert.message}`;
    const duration = alert.level === 'CRITICAL' ? 0 : 5;

    switch (alert.level) {
      case 'INFO':
        message.info(msg, duration);
        break;
      case 'WARNING':
        message.warning(msg, duration);
        break;
      case 'ERROR':
        message.error(msg, duration);
        break;
      case 'CRITICAL':
        message.error(msg, 0);
        break;
    }
  }
}

// Create singleton instance
const wsService = new WebSocketService();

// Auto-connect when module loads (optional)
if (process.env.REACT_APP_AUTO_CONNECT_WS === 'true') {
  wsService.connect().catch(console.error);
}

export default wsService;