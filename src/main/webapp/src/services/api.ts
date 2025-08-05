/**
 * API service for communicating with backend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

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

class ApiService {
  private async fetchJson<T>(url: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${url}`);
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    return response.json();
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
  async getDualInvestmentProducts(): Promise<DualInvestmentProduct[]> {
    return this.fetchJson('/api/v1/dual-investment/products');
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
}

export const apiService = new ApiService();