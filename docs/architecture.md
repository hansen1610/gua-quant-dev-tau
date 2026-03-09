# Architecture Overview

## Docker Network (`quantbot-net`)
10 microservices operating over a secure internal bridge network.

```mermaid
graph TD
    User([End User]) --> |HTTPS / WSS| NGINX((Nginx Proxy))
    
    subgraph QuantBot Architecture
    NGINX --> |Port 3000| FE(Next.js Dashboard)
    NGINX --> |Port 8000| API(FastAPI Gateway)
    
    API --> |Port 8001| SE(Strategy Engine)
    API --> |Port 8002| QR(Quant Research)
    API --> |Port 8003| ML(ML Engine)
    
    HB(Hummingbot Execution) <--> |Redis PubSub| SE
    MON(Monitoring Service) --> |Logs / Metrics| API
    
    SE --> |SQL| PG[(PostgreSQL)]
    HB --> |SQL| PG
    QR --> |SQL| PG
    
    SE --> |Cache| RD[(Redis)]
    HB --> |Cache| RD
    end
    
    HB <--> |WS + REST| API_EXC((Hyperliquid Perps API))
```

## Data Lifecycle Flow
1. **Hyperliquid Connector** inside Hummingbot pushes `l2Book` and `trades` stream directly to **Redis Pub/Sub** (`market:ticks`).
2. **Strategy Coordinator** decodes ticks concurrently against mapped rule sets (EMA Trend/Fibonacci).
3. Derived raw signals run through the **Institutional Risk Engine**.
4. Risk Engine dynamically calculates position size based on existing portfolio equity and validates limits (Daily Drawdown).
5. Approved Signals are pushed to `signals:execute` back to Hummingbot.
6. Execution response logged symmetrically into PostgreSQL `orders` and `trades_history` tables.
