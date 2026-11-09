
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export interface SimulationRequest {
  order_count: number;
  seed: number | null;
  interval_seconds: number;
  buffer_capacity: number;
}

export interface SimulationTrade {
  symbol: string;
  maker_order_id: string;
  taker_order_id: string;
  price_ticks: number;
  quantity: number;
}

export interface SimulationOrderBook {
  symbol: string;
  active_order_count: number;
  best_bid: number | null;
  best_ask: number | null;
}

export interface SimulationResponse {
  status: string;
  summary: {
    orders_generated: number;
    orders_processed: number;
    trade_count: number;
    buffer_high_watermark: number;
  };
  trades: SimulationTrade[];
  order_books: SimulationOrderBook[];
  performance: {
    orders_processed: number;
    trades_executed: number;
    throughput_orders_per_second: number;
    elapsed_ns: number;
    latency_min_ns: number;
    latency_max_ns: number;
    latency_p50_ns: number;
    latency_p95_ns: number;
    latency_p99_ns: number;
  };
}

export async function runSimulation(
  request: SimulationRequest,
): Promise<SimulationResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/simulator/run`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    },
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Simulation request failed");
  }

  return response.json() as Promise<SimulationResponse>;
}
