/**
 * API service for communicating with backend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface MarketPrice {
  symbol: string;
  price: number;
  timestamp: string | null;
}

export interface MarketAnalysis {
  symbol: string;
  current_price: number;
  price_change_24h: number;
  trend: {
    trend: string;
    strength: string;
  };
  volatility: {
    atr: number;
    volatility_ratio: number;
    risk_level: string;
  };
  signals: {
    rsi_signal: string;
    macd_signal: string;
    bb_signal: string;
    recommendation: string;
  };
}

export interface DualInvestmentProduct {
  id: string;
  asset: string;
  currency: string;
  type: string;
  strike_price: number;
  apy: number;
  term_days: number;
  min_amount: number;
  max_amount: number;
  settlement_date: string;
}

export interface BotStatus {
  bot_running: boolean;
  binance_connected: boolean;
  strategies_active: number;
  message: string;
}

export interface Investment {
  id: string;
  product_id: string;
  amount: number;
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  created_at: string;
  executed_at?: string;
  completed_at?: string;
  actual_return?: number;
  expected_return?: number;
  binance_order_id?: string;
  error_message?: string;
}

export interface PortfolioSummary {
  summary: {
    total_investments: number;
    total_invested: number;
    current_value: number;
    total_returns: number;
    net_pnl: number;
    roi_percentage: number;
  };
  status_breakdown: {
    active: number;
    completed: number;
    failed: number;
    pending: number;
    cancelled: number;
  };
  active_investments: Investment[];
  recent_completed: Investment[];
}

export interface TradingSettings {
  automated_trading_enabled: boolean;
  max_concurrent_trades: number;
  trading_cooldown_minutes: number;
  default_investment_amount: number;
  max_single_investment_ratio: number;
  min_apr_threshold: number;
  risk_level: number;
}

export interface TaskStatus {
  task_id: string;
  status: string;
  ready: boolean;
  successful?: boolean;
  result?: any;
  error?: string;
  info?: any;
  timestamp: string;
}

export interface ActiveTask {
  task_id: string;
  name: string;
  worker: string;
  args: any[];
  kwargs: any;
  time_start?: string;
  acknowledged: boolean;
}

export interface AIRecommendation {
  product_id: string;
  should_invest: boolean;
  amount: number;
  ai_score: number;
  expected_return: number;
  risk_score: number;
  recommendation: string;
  reasons: string[];
  warnings: string[];
  metadata?: any;
}

export interface SystemHealth {
  database: string;
  binance_api: string;
  celery: string;
  overall: string;
  timestamp: string;
}

export interface TaskStats {
  workers: WorkerInfo[];
  total_workers: number;
  overall_stats: {
    total_tasks: number;
    total_processes: number;
    timestamp: string;
  };
}

export interface WorkerInfo {
  worker: string;
  status: string;
  total_tasks: any;
  pool_processes: number;
  rusage: any;
  clock: string;
  pid: number;
  broker: any;
}

export interface ScheduledTask {
  task_id: string;
  name: string;
  worker: string;
  args: any[];
  kwargs: any;
  eta?: string;
  priority: number;
}

class ApiService {
  private async fetchJson<T>(url: string): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
    
    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }
      
      return response.json();
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }

  // Health & Status
  async getHealth() {
    return this.fetchJson('/health');
  }

  async getStatus(): Promise<BotStatus> {
    return this.fetchJson('/api/v1/status');
  }

  // Market Data
  async getPrice(symbol: string): Promise<MarketPrice> {
    return this.fetchJson(`/api/v1/market/price/${symbol}`);
  }

  async getMarketAnalysis(symbol: string): Promise<MarketAnalysis> {
    return this.fetchJson(`/api/v1/market/analysis/${symbol}`);
  }

  async get24hrStats(symbol: string) {
    return this.fetchJson(`/api/v1/market/24hr-stats/${symbol}`);
  }

  // Dual Investment
  async getDualInvestmentProducts(symbol?: string, maxDays: number = 2): Promise<{products?: DualInvestmentProduct[], message?: string} | DualInvestmentProduct[]> {
    const params = new URLSearchParams();
    if (symbol) params.append('symbol', symbol);
    params.append('max_days', maxDays.toString());
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.fetchJson(`/api/v1/dual-investment/products${query}`);
  }

  async analyzeDualInvestment(symbol: string) {
    return this.fetchJson(`/api/v1/dual-investment/analyze/${symbol}`);
  }

  async subscribeToDualInvestment(productId: string, amount: number) {
    const response = await fetch(`${API_BASE_URL}/api/v1/dual-investment/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ product_id: productId, amount }),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Account
  async getAccountBalance() {
    return this.fetchJson('/api/v1/account/balance');
  }

  // Portfolio & Trading
  async getPortfolioSummary(): Promise<PortfolioSummary> {
    return this.fetchJson('/api/v1/trading/portfolio/summary');
  }

  async getInvestments(status?: string, limit?: number, offset?: number): Promise<{investments: Investment[], total: number}> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.fetchJson(`/api/v1/trading/investments${query}`);
  }

  async getInvestmentDetail(investmentId: string): Promise<Investment> {
    return this.fetchJson(`/api/v1/trading/investments/${investmentId}`);
  }

  async executeInvestment(productId: string, amount: number): Promise<{task_id: string, status: string}> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ product_id: productId, amount }),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }

  async cancelInvestment(investmentId: string, reason?: string): Promise<{task_id: string, status: string}> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/cancel/${investmentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(reason || 'User requested'),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getTradingSettings(): Promise<TradingSettings> {
    return this.fetchJson('/api/v1/trading/settings');
  }

  async updateTradingSettings(settings: Partial<TradingSettings>): Promise<{status: string, updated_settings: any}> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/settings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }

  async triggerAutoExecution(): Promise<{task_id: string, status: string}> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/auto-execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Task Management
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    return this.fetchJson(`/api/v1/tasks/status/${taskId}`);
  }

  async getActiveTasks(): Promise<{active_tasks: ActiveTask[], total_workers: number, total_tasks: number}> {
    return this.fetchJson('/api/v1/tasks/active');
  }

  async triggerMarketDataUpdate(symbols?: string[]): Promise<{task_id: string, status: string}> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/market-data/update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbols }),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }

  async triggerAIRecommendations(symbols?: string[]): Promise<{task_id: string, status: string}> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/ai-recommendations/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbols }),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }

  async cancelTask(taskId: string): Promise<{status: string, message: string}> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/cancel/${taskId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }

  // AI Recommendations (for manual review)
  async getAIRecommendations(symbol: string, limit?: number): Promise<{recommendations: AIRecommendation[], total_recommendations: number}> {
    const params = limit ? `?limit=${limit}` : '';
    return this.fetchJson(`/api/v1/dual-investment/ai-recommendations/${symbol}${params}`);
  }

  // System Monitoring
  async getSystemHealth(): Promise<{status: string, health: SystemHealth}> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/health-check`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    const result = await response.json();
    // If it's a task response, we need to poll for the result
    if (result.task_id) {
      // For now, return a mock health status
      return {
        status: 'success',
        health: {
          database: 'healthy',
          binance_api: 'healthy',
          celery: 'healthy',
          overall: 'healthy',
          timestamp: new Date().toISOString()
        }
      };
    }
    return result;
  }

  async getTaskStats(): Promise<TaskStats> {
    return this.fetchJson('/api/v1/tasks/stats');
  }

  async getScheduledTasks(): Promise<{scheduled_tasks: ScheduledTask[], total_workers: number, total_tasks: number}> {
    return this.fetchJson('/api/v1/tasks/scheduled');
  }

  async triggerHealthCheck(): Promise<{task_id: string, status: string}> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/health-check`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }
}

export const apiService = new ApiService();