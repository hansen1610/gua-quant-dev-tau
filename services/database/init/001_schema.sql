-- ════════════════════════════════════════════════════════════
-- QuantBot Infra — PostgreSQL Schema
-- Institutional Trading Database
-- ════════════════════════════════════════════════════════════

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Users & Auth ─────────────────────────────────────────
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer'
        CHECK (role IN ('admin', 'risk_officer', 'viewer')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    settings JSONB DEFAULT '{}'
);

-- ── Audit Logs ───────────────────────────────────────────
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Trading Assets ───────────────────────────────────────
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    min_size DECIMAL(20,10) NOT NULL,
    price_decimals INT NOT NULL DEFAULT 2,
    size_decimals INT NOT NULL DEFAULT 4,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'
);

-- ── Strategies ───────────────────────────────────────────
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT false,
    risk_per_trade DECIMAL(5,4) DEFAULT 0.02,
    max_daily_drawdown DECIMAL(5,4) DEFAULT 0.05,
    max_exposure DECIMAL(5,4) DEFAULT 0.30,
    kill_switch BOOLEAN DEFAULT false,
    auto_disable_rules JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Orders ───────────────────────────────────────────────
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(100),
    strategy_id UUID REFERENCES strategies(id),
    asset_id INT REFERENCES assets(id),
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('market', 'limit', 'stop', 'stop_limit')),
    quantity DECIMAL(20,10) NOT NULL,
    price DECIMAL(20,10),
    stop_price DECIMAL(20,10),
    filled_quantity DECIMAL(20,10) DEFAULT 0,
    filled_price DECIMAL(20,10),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'submitted', 'partial', 'filled', 'cancelled', 'rejected', 'error')),
    slippage DECIMAL(10,6),
    commission DECIMAL(20,10),
    latency_ms INT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Positions ────────────────────────────────────────────
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID REFERENCES strategies(id),
    asset_id INT REFERENCES assets(id),
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short')),
    entry_price DECIMAL(20,10) NOT NULL,
    current_price DECIMAL(20,10),
    quantity DECIMAL(20,10) NOT NULL,
    unrealized_pnl DECIMAL(20,10) DEFAULT 0,
    realized_pnl DECIMAL(20,10) DEFAULT 0,
    stop_loss DECIMAL(20,10),
    take_profit DECIMAL(20,10),
    leverage DECIMAL(5,2) DEFAULT 1.0,
    funding_paid DECIMAL(20,10) DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'closed', 'liquidated')),
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

-- ── Trades (filled orders = trade record) ────────────────
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id),
    position_id UUID REFERENCES positions(id),
    strategy_id UUID REFERENCES strategies(id),
    asset_id INT REFERENCES assets(id),
    side VARCHAR(10) NOT NULL,
    price DECIMAL(20,10) NOT NULL,
    quantity DECIMAL(20,10) NOT NULL,
    commission DECIMAL(20,10) DEFAULT 0,
    slippage DECIMAL(10,6) DEFAULT 0,
    pnl DECIMAL(20,10),
    pnl_pct DECIMAL(10,6),
    funding_rate DECIMAL(10,8),
    latency_ms INT,
    metadata JSONB DEFAULT '{}',
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Equity Snapshots ─────────────────────────────────────
CREATE TABLE equity_snapshots (
    id BIGSERIAL PRIMARY KEY,
    total_equity DECIMAL(20,10) NOT NULL,
    available_balance DECIMAL(20,10) NOT NULL,
    unrealized_pnl DECIMAL(20,10) DEFAULT 0,
    daily_pnl DECIMAL(20,10) DEFAULT 0,
    daily_pnl_pct DECIMAL(10,6) DEFAULT 0,
    drawdown_pct DECIMAL(10,6) DEFAULT 0,
    max_drawdown_pct DECIMAL(10,6) DEFAULT 0,
    exposure_pct DECIMAL(10,6) DEFAULT 0,
    num_open_positions INT DEFAULT 0,
    snapshot_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Risk Events ──────────────────────────────────────────
CREATE TABLE risk_events (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL
        CHECK (severity IN ('info', 'warning', 'critical', 'emergency')),
    description TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    action_taken VARCHAR(100),
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- ── Backtest Results ─────────────────────────────────────
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID REFERENCES strategies(id),
    asset_symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(20,10) NOT NULL,
    final_capital DECIMAL(20,10) NOT NULL,
    total_return DECIMAL(10,6),
    sharpe_ratio DECIMAL(10,6),
    sortino_ratio DECIMAL(10,6),
    calmar_ratio DECIMAL(10,6),
    max_drawdown DECIMAL(10,6),
    win_rate DECIMAL(10,6),
    profit_factor DECIMAL(10,6),
    expectancy DECIMAL(20,10),
    total_trades INT,
    winning_trades INT,
    losing_trades INT,
    avg_win DECIMAL(20,10),
    avg_loss DECIMAL(20,10),
    equity_curve JSONB,
    monthly_returns JSONB,
    parameters JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Monte Carlo Results ──────────────────────────────────
CREATE TABLE monte_carlo_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_id UUID REFERENCES backtest_results(id),
    num_simulations INT NOT NULL DEFAULT 10000,
    confidence_intervals JSONB NOT NULL,
    worst_case_drawdown DECIMAL(10,6),
    risk_of_ruin DECIMAL(10,6),
    probability_profit DECIMAL(10,6),
    median_return DECIMAL(10,6),
    distribution_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── ML Model Metadata ────────────────────────────────────
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    version INT NOT NULL DEFAULT 1,
    accuracy DECIMAL(10,6),
    parameters JSONB,
    training_metrics JSONB,
    file_path VARCHAR(255),
    is_active BOOLEAN DEFAULT false,
    trained_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── System Health Logs ───────────────────────────────────
CREATE TABLE health_logs (
    id BIGSERIAL PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('healthy', 'degraded', 'unhealthy', 'offline')),
    cpu_pct DECIMAL(5,2),
    memory_mb DECIMAL(10,2),
    latency_ms INT,
    details JSONB DEFAULT '{}',
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ──────────────────────────────────────────────
CREATE INDEX idx_orders_strategy ON orders(strategy_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_positions_strategy ON positions(strategy_id);
CREATE INDEX idx_trades_executed ON trades(executed_at DESC);
CREATE INDEX idx_trades_strategy ON trades(strategy_id);
CREATE INDEX idx_equity_snapshot_at ON equity_snapshots(snapshot_at DESC);
CREATE INDEX idx_risk_events_type ON risk_events(event_type);
CREATE INDEX idx_risk_events_severity ON risk_events(severity);
CREATE INDEX idx_health_logs_service ON health_logs(service_name);
CREATE INDEX idx_health_logs_checked ON health_logs(checked_at DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- ── Seed Default Assets ──────────────────────────────────
INSERT INTO assets (symbol, display_name, min_size, price_decimals, size_decimals) VALUES
    ('BTC-USD', 'Bitcoin', 0.0001, 1, 5),
    ('ETH-USD', 'Ethereum', 0.001, 2, 4),
    ('SOL-USD', 'Solana', 0.01, 3, 3),
    ('ARB-USD', 'Arbitrum', 0.1, 4, 2),
    ('DOGE-USD', 'Dogecoin', 1.0, 5, 1);

-- ── Seed Default Admin User (password: change_me) ───────
INSERT INTO users (username, password_hash, role) VALUES
    ('admin', crypt('change_me', gen_salt('bf')), 'admin');
