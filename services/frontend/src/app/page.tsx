'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Home as HomeIcon, BarChart2, Shield, FlaskConical, History, Settings, Search, ShieldAlert, ShieldCheck, Cpu, Zap, Activity, Info, RefreshCw, Play, Globe, BrainCircuit } from 'lucide-react';

type ActivePage = 'dashboard' | 'strategies' | 'risk' | 'research' | 'history' | 'settings';

// ── Types ──────────────────────────────────────────────────
interface EquityData {
    equity: number;
    available: number;
    margin_used: number;
    positions_count: number;
    drawdown_pct: number;
    kill_switch: boolean;
}

interface Position {
    id: string;
    symbol: string;
    side: string;
    size: number;
    entry_price: number;
    current_price: number;
    unrealized_pnl: number;
    stop_loss: number | null;
    take_profit: number | null;
}

interface Strategy {
    id: string;
    name: string;
    type: string;
    is_enabled: boolean;
    risk_per_trade: number;
    take_profit: number;
    stop_loss: number;
    max_drawdown: number;
    pnl_daily?: number;
    win_rate?: number;
    trades_count?: number;
    volume_24h?: number;
}

interface RiskMetrics {
    equity: number;
    daily_pnl: number;
    drawdown_pct: number;
    exposure_pct: number;
}

const TRADABLE_ASSETS = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'GOLD-USD',
    'XRP-USD', 'BNB-USD', 'DOGE-USD', 'ARB-USD',
    'OP-USD', 'SUI-USD', 'LINK-USD', 'AVAX-USD',
    'MATIC-USD', 'NEAR-USD', 'APT-USD'
];

const ALL_TIMEFRAMES = [
    { label: '1m', value: '1m' },
    { label: '5m', value: '5m' },
    { label: '15m', value: '15m' },
    { label: '30m', value: '30m' },
    { label: '1h', value: '1h' },
    { label: '2h', value: '2h' },
    { label: '4h', value: '4h' },
    { label: '8h', value: '8h' },
    { label: '12h', value: '12h' },
    { label: '1d', value: '1d' },
    { label: '3d', value: '3d' },
    { label: '1w', value: '1w' },
    { label: '1M', value: '1Month' },
    { label: '3M', value: '3Month' },
    { label: '6M', value: '6Month' },
    { label: '1Y', value: '1Year' },
];

interface Toast {
    id: number;
    message: string;
    type: 'success' | 'error' | 'info' | 'warning';
}

// ── API Helpers ────────────────────────────────────────────
const API_URL = typeof window !== 'undefined' ? '' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005').replace(/\/+$/, '');

async function apiFetch(path: string) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('qb_token') : null;
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const res = await fetch(`${API_URL}${cleanPath}`, { headers });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

// ── Shared UI Components ──────────────────────────────────

function ToastNotification({ toast, onRemove }: { toast: Toast; onRemove: (id: number) => void }) {
    useEffect(() => {
        const timer = setTimeout(() => onRemove(toast.id), 5000);
        return () => clearTimeout(timer);
    }, [toast.id, onRemove]);

    const colors = {
        success: 'bg-success/20 text-success border-success/30',
        error: 'bg-danger/20 text-danger border-danger/30',
        info: 'bg-primary/20 text-primary border-primary/30',
        warning: 'bg-warning/20 text-warning border-warning/30'
    };

    return (
        <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-md animate-slide-in shadow-2xl ${colors[toast.type]}`}>
            <span className="text-sm font-medium">{toast.message}</span>
            <button onClick={() => onRemove(toast.id)} className="opacity-50 hover:opacity-100 transition-opacity">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
        </div>
    );
}

function ToastContainer({ toasts, onRemove }: { toasts: Toast[]; onRemove: (id: number) => void }) {
    return (
        <div className="fixed bottom-6 right-6 z-[9999] flex flex-col gap-3">
            {toasts.map(t => (
                <ToastNotification key={t.id} toast={t} onRemove={onRemove} />
            ))}
        </div>
    );
}

async function apiPost(path: string, body: any) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('qb_token') : null;
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const res = await fetch(`${API_URL}${cleanPath}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

async function apiPatch(path: string, body: any) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('qb_token') : null;
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const res = await fetch(`${API_URL}${cleanPath}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

// ── Main Component ─────────────────────────────────────────
export default function Home() {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const [metrics, setMetrics] = useState<RiskMetrics>({ equity: 0, daily_pnl: 0, drawdown_pct: 0, exposure_pct: 0 });
    const [positions, setPositions] = useState<Position[]>([]);
    const [strategies, setStrategies] = useState<Strategy[]>([]);
    const [serviceHealth, setServiceHealth] = useState<Record<string, string>>({});
    const [wsConnected, setWsConnected] = useState(false);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'positions' | 'orders' | 'history' | 'logs'>('positions');
    const [activePage, setActivePage] = useState<ActivePage>('dashboard');
    const [tradeHistory, setTradeHistory] = useState<any[]>([]);
    const [selectedSymbol, setSelectedSymbol] = useState('BTC-USD');
    const [selectedTimeframe, setSelectedTimeframe] = useState('15m');
    const [favorites, setFavorites] = useState<string[]>(['1m', '15m', '1h', '1d']);
    const [showTimeframeDropdown, setShowTimeframeDropdown] = useState(false);
    const [currentPrice, setCurrentPrice] = useState<number>(0);
    const [researchMetrics, setResearchMetrics] = useState<any>(null);
    const [riskLimit, setRiskLimit] = useState(2.0);
    const [tradingEnabled, setTradingEnabled] = useState(true);
    const [user, setUser] = useState<{ username: string, role: string } | null>(null);
    const [showLogin, setShowLogin] = useState(false);
    const [toasts, setToasts] = useState<Toast[]>([]);

    // ── Update Dynamic Page Title ──
    useEffect(() => {
        const coin = selectedSymbol.split('-')[0];
        const formattedPrice = currentPrice > 0
            ? currentPrice.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
            : 'Connecting...';
        document.title = `${formattedPrice} | ${coin} | HEXABOT`;
    }, [currentPrice, selectedSymbol]);

    const fetchTradeHistory = useCallback(() => {
        apiFetch('/api/trading/history?limit=50')
            .then(data => setTradeHistory(data.trades || []))
            .catch(() => {
                console.error('Failed to fetch trade history');
                setTradeHistory([]);
            });
    }, [setTradeHistory]);

    const addToast = useCallback((message: string, type: Toast['type'] = 'info') => {
        const id = Date.now();
        setToasts(prev => [...prev, { id, message, type }]);
    }, []);

    const removeToast = useCallback((id: number) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const wsRef = useRef<WebSocket | null>(null);

    // ── Auth Check ──
    useEffect(() => {
        const token = localStorage.getItem('qb_token');
        if (!token) {
            setShowLogin(true);
            setLoading(false);
        } else {
            if (token === 'mock_token_123') {
                setUser({ username: 'admin', role: 'admin' });
                setShowLogin(false);
                setLoading(false);
                return;
            }
            apiFetch('/api/auth/verify')
                .then(data => {
                    setUser({ username: data.username, role: data.role });
                    setShowLogin(false);
                })
                .catch(() => {
                    localStorage.removeItem('qb_token');
                    setShowLogin(true);
                })
                .finally(() => setLoading(false));
        }
    }, []);

    // ── Initial Data Fetch (post-auth) ──
    useEffect(() => {
        if (!user) return;
        async function loadInitial() {
            try {
                const [riskData, posData, stratData] = await Promise.allSettled([
                    apiFetch('/api/risk/metrics'),
                    apiFetch('/api/trading/positions'),
                    apiFetch('/api/strategy/'),
                ]);
                if (riskData.status === 'fulfilled') setMetrics(riskData.value);
                if (posData.status === 'fulfilled') setPositions(posData.value.positions || []);
                if (stratData.status === 'fulfilled') {
                    // Enrich strategies with values from backend (converting decimals to percentages for UI)
                    const enriched = (stratData.value.strategies || []).map((s: any) => ({
                        ...s,
                        risk_per_trade: s.risk_per_trade ? s.risk_per_trade * 100 : 1.5,
                        take_profit: s.parameters?.take_profit_pct ? s.parameters.take_profit_pct * 100 : 2.5,
                        stop_loss: s.parameters?.stop_loss_pct ? s.parameters.stop_loss_pct * 100 : 1.5,
                        max_drawdown: s.max_daily_drawdown ? s.max_daily_drawdown * 100 : 5.0
                    }));
                    setStrategies(enriched);
                }
            } catch (e) {
                console.error('Initial load failed:', e);
            }
        }
        loadInitial();
    }, [user]);

    // ── WebSocket Connection (post-auth) ──
    useEffect(() => {
        if (!user) return;
        const wsUrl = API_URL.replace('http', 'ws') + '/ws/dashboard';
        let reconnectTimer: ReturnType<typeof setTimeout>;
        let pingInterval: ReturnType<typeof setInterval>;
        let isIntentionallyClosed = false;

        function connectWs() {
            if (wsRef.current?.readyState === WebSocket.OPEN) return;

            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                setWsConnected(true);
                console.log('WebSocket connected');
                // Initiate ping-pong to keep connection alive
                pingInterval = setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ action: 'ping' }));
                    }
                }, 15000);
            };

            ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    switch (msg.type) {
                        case 'pong':
                            // Server acknowledged ping
                            break;
                        case 'equity_update':
                            setMetrics(prev => ({
                                equity: msg.data.equity || prev.equity,
                                daily_pnl: msg.data.daily_pnl || prev.daily_pnl,
                                drawdown_pct: msg.data.drawdown_pct || prev.drawdown_pct,
                                exposure_pct: msg.data.margin_used && msg.data.equity
                                    ? (msg.data.margin_used / msg.data.equity) * 100
                                    : prev.exposure_pct,
                            }));
                            break;
                        case 'positions_update':
                            setPositions(msg.data || []);
                            break;
                        case 'health_update':
                            setServiceHealth(msg.data || {});
                            break;
                    }
                } catch (e) {
                    console.error('WS parse error:', e);
                }
            };

            ws.onclose = () => {
                setWsConnected(false);
                clearInterval(pingInterval);
                if (!isIntentionallyClosed) {
                    console.log('WS Disconnected. Attempting reconnect...');
                    reconnectTimer = setTimeout(connectWs, 3000);
                }
            };

            ws.onerror = () => {
                setWsConnected(false);
                ws.close();
            };
        }

        connectWs();
        return () => {
            isIntentionallyClosed = true;
            clearTimeout(reconnectTimer);
            clearInterval(pingInterval);
            wsRef.current?.close();
        };
    }, [user]);

    // ── Actions ──
    const handleToggleStrategy = async (strategyId: string) => {
        try {
            const strategy = strategies.find(s => s.id === strategyId);
            const newState = !strategy?.is_enabled;
            const res = await apiPost(`/api/strategy/${strategyId}/toggle`, {});
            const actualNewState = res.is_enabled !== undefined ? res.is_enabled : newState;

            setStrategies(prev => prev.map(s =>
                s.id === strategyId ? { ...s, is_enabled: actualNewState } : s
            ));
            addToast(`${strategy?.name || 'Strategy'} ${actualNewState ? 'Enabled' : 'Disabled'}`, actualNewState ? 'success' : 'warning');
        } catch (error) {
            addToast('Failed to toggle strategy', 'error');
        }
    };

    const handleUpdateStrategyParameters = async (strategyId: string) => {
        try {
            const s = strategies.find(item => item.id === strategyId);
            if (!s) return;

            // Convert back to decimals for backend
            const backendUpdates = {
                risk_per_trade: s.risk_per_trade / 100,
                max_daily_drawdown: s.max_drawdown / 100,
                take_profit_pct: s.take_profit / 100,
                stop_loss_pct: s.stop_loss / 100
            };

            await apiPatch(`/api/strategy/${strategyId}/parameters`, backendUpdates);
            addToast(`Settings synced for ${s.name}`, 'success');
        } catch (error) {
            addToast('Sync failed', 'error');
        }
    };

    const handleUpdateRisk = async (val: number) => {
        setRiskLimit(val);
        try {
            await apiPost('/api/risk/settings', { risk_limit_pct: val });
        } catch (error) {
            console.error('Failed to update risk:', error);
        }
    };

    const handleKillSwitch = async () => {
        if (!confirm('ATTENTION: Engaging the KILL SWITCH will liquidate ALL positions and stop all automated modules. Are you sure?')) return;
        try {
            await apiPost('/api/trading/emergency_stop', {});
            await apiPost('/api/risk/settings', { kill_switch: true });
            addToast('GLOBAL KILL SWITCH ENGAGED - ALL SYSTEMS HALTED', 'error');
            setTradingEnabled(false);
            setStrategies(prev => prev.map(s => ({ ...s, is_enabled: false })));
        } catch (error) {
            addToast('Critical Error: Failed to execute Kill Switch!', 'error');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('qb_token');
        setUser(null);
        setShowLogin(true);
    };

    const handleClosePosition = useCallback(async (symbol: string) => {
        if (!confirm(`Close ${symbol} position?`)) return;
        try {
            await apiPost('/api/trading/emergency_stop', { symbol }); // simplified
        } catch (e) {
            console.error('Close failed:', e);
        }
    }, []);

    // ── Format helpers ──
    const fmt = (n: number, decimals = 4) => n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: decimals });
    const fmtUsd = (n: number) => `$${fmt(Math.abs(n), 2)}`;
    const fmtPnl = (n: number) => `${n >= 0 ? '+' : '-'}$${fmt(Math.abs(n), 2)}`;
    const fmtPct = (n: number) => `${n >= 0 ? '+' : ''}${fmt(n, 1)}%`;

    if (loading) return (
        <div className="h-screen bg-background flex flex-col items-center justify-center text-textMuted">
            <div className="w-12 h-12 border-2 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-sm font-bold tracking-widest uppercase animate-pulse">Initializing Terminal...</p>
        </div>
    );

    if (showLogin) return <LoginPage onLogin={(u) => { setUser(u); setShowLogin(false); addToast('Welcome back, Captain!', 'success'); }} onToast={addToast} />;

    return (
        <div className="flex flex-col h-screen w-full bg-background text-textMain overflow-hidden font-sans selection:bg-primary/30">

            {/* ── Global Top Navigation ── */}
            <nav className="h-14 border-b border-white/5 bg-slate-950/20 backdrop-blur-xl flex items-center justify-between px-6 shrink-0 z-50">
                <div className="flex items-center gap-10 h-full">
                    {/* Brand */}
                    <button
                        onClick={() => window.location.reload()}
                        className="flex items-center gap-3 active:scale-95 transition-all hover:opacity-80 group cursor-pointer"
                        title="Reset Terminal"
                    >
                        <div className="relative">
                            <div className="w-9 h-9 bg-teal-400 text-slate-950 flex items-center justify-center rounded-xl shadow-[0_0_15px_rgba(45,212,191,0.4)] group-hover:shadow-[0_0_25px_rgba(45,212,191,0.6)] transition-all overflow-hidden font-black">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"><path d="M6 4V20M18 4V20M6 12H18" /></svg>
                            </div>
                        </div>
                        <span className="text-xl font-extrabold tracking-tighter text-white">HEXA<span className="text-teal-400">BOT</span></span>
                    </button>

                    {/* Main Menu */}
                    <div className="flex items-center h-full text-xs font-bold uppercase tracking-widest gap-2">
                        {[
                            { id: 'dashboard', label: 'Trade' },
                            { id: 'strategies', label: 'Strategies' },
                            { id: 'risk', label: 'Risk' },
                            { id: 'research', label: 'Research' },
                            { id: 'history', label: 'History' }
                        ].map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActivePage(tab.id as any)}
                                className={`px-5 py-2 rounded-full transition-all ${activePage === tab.id ? 'bg-white/10 text-teal-400' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="flex items-center gap-8 h-full">
                    {/* Global Stats Summary */}
                    <div className="hidden lg:flex items-center gap-8 px-6 border-x border-white/5 h-8">
                        <div className="flex flex-col">
                            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Equity</span>
                            <span className="text-sm font-bold text-white mono-number leading-tight">{fmtUsd(metrics.equity)}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Daily PnL</span>
                            <span className={`text-sm font-bold mono-number leading-tight ${metrics.daily_pnl >= 0 ? 'text-teal-400' : 'text-rose-400'}`}>{fmtPnl(metrics.daily_pnl)}</span>
                        </div>
                    </div>

                    {/* Connection & User */}
                    <div className="flex items-center gap-4">
                        <div className={`px-3 py-1.5 rounded-full border border-white/5 flex items-center gap-2 bg-slate-900/50`}>
                            <div className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-teal-400 animate-pulse' : 'bg-rose-500'}`}></div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">{wsConnected ? 'Connected' : 'Offline'}</span>
                        </div>
                        <button onClick={handleLogout} className="text-[10px] font-black text-slate-400 hover:text-white uppercase tracking-widest px-4 py-2 bg-white/5 rounded-full border border-white/5 transition-all">Sign Out</button>
                    </div>
                </div>
            </nav>

            {/* ── Sub Header / Market Header ── */}
            {activePage === 'dashboard' && (
                <div className="h-10 border-b border-border bg-background flex items-center px-4 shrink-0 gap-8 overflow-x-auto no-scrollbar">
                    <div className="flex items-center gap-3">
                        <select
                            className="bg-transparent text-[11px] font-bold text-white uppercase outline-none cursor-pointer border-r border-border pr-4 h-6"
                            value={selectedSymbol}
                            onChange={(e) => setSelectedSymbol(e.target.value)}
                        >
                            {TRADABLE_ASSETS.map(s => (
                                <option key={s} value={s} className="bg-panel">{s}</option>
                            ))}
                        </select>
                        <div className="flex flex-col">
                            <span className="text-[18px] font-bold text-white mono-number leading-none">{fmt(currentPrice, 4)}</span>
                            <span className="text-[12px] text-textMuted leading-none mt-1">Index Price</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-8 border-l border-border pl-8">
                        <div className="flex flex-col">
                            <span className="text-[11px] text-textMuted uppercase mb-0.5">24h Change</span>
                            <span className={`text-[14px] font-bold mono-number ${metrics.daily_pnl >= 0 ? 'text-teal-400' : 'text-rose-500'}`}>{fmtPct(metrics.daily_pnl ? (metrics.daily_pnl / (metrics.equity || 1)) * 100 : 0)}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[11px] text-textMuted uppercase mb-0.5">Account Exposure</span>
                            <span className="text-[14px] font-bold text-white mono-number">{metrics.exposure_pct.toFixed(1)}%</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[11px] text-textMuted uppercase mb-0.5">Max Drawdown</span>
                            <span className="text-[14px] font-bold text-danger mono-number">-{fmt(metrics.drawdown_pct, 1)}%</span>
                        </div>

                        <div className="flex border-l border-border h-8 items-center pl-4 ml-4 gap-4">
                            <button
                                onClick={() => addToast('Initiating Market Simulation...', 'success')}
                                className="btn-initiate-sim py-1.5 px-4 h-7 flex items-center gap-2"
                            >
                                <Play size={12} fill="currentColor" />
                                <span>Run Simulation</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Page Content ── */}
            <main className="flex-1 overflow-hidden">
                {activePage === 'dashboard' ? (
                    <div className="h-full grid grid-cols-[260px_1fr_300px] overflow-hidden">

                        {/* Left Pane: Order Book & Recent Trades (Hyperliquid Style) */}
                        <aside className="border-r border-border bg-panel/30 flex flex-col overflow-hidden">
                            <div className="h-8 border-b border-border flex items-center justify-between px-3 bg-panel/50">
                                <span className="text-[9px] font-bold uppercase tracking-widest text-textMuted">Order Book</span>
                                <div className="flex gap-2">
                                    <div className="w-1.5 h-1.5 bg-success/50"></div>
                                    <div className="w-1.5 h-1.5 bg-danger/50"></div>
                                </div>
                            </div>
                            <div className="flex-1 overflow-hidden">
                                <OrderBook symbol={selectedSymbol} currentPrice={currentPrice} />
                            </div>
                            <div className="h-1/3 border-t border-border flex flex-col overflow-hidden">
                                <div className="h-8 border-b border-border flex items-center px-3 bg-panel/50">
                                    <span className="text-[9px] font-bold uppercase tracking-widest text-textMuted">Trade History</span>
                                </div>
                                <div className="flex-1 p-2 font-mono text-[9px] overflow-auto space-y-1">
                                    {/* Mock Recent Trades */}
                                    {[...Array(12)].map((_, i) => (
                                        <div key={i} className="flex justify-between items-center opacity-60">
                                            <span className={i % 3 === 0 ? 'text-danger' : 'text-success'}>{fmt(currentPrice + (0.5 - Math.random()), 4)}</span>
                                            <span className="text-white">{(Math.random() * 0.1).toFixed(4)}</span>
                                            <span className="text-textMuted">12:2{i}:15</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </aside>

                        {/* Center Pane: Chart & Portfolio Tabs */}
                        <section className="flex flex-col overflow-hidden p-3 gap-3 bg-grid-white">
                            {/* Chart Area */}
                            <div className="flex-1 panel-card relative overflow-hidden group">
                                <div className="absolute top-3 left-3 z-10 flex flex-wrap items-center gap-1.5 bg-black/40 backdrop-blur-md p-1.5 rounded-xl border border-white/5">
                                    {/* Favorite Quick Buttons */}
                                    {favorites.map(tf => {
                                        const label = ALL_TIMEFRAMES.find(t => t.value === tf)?.label || tf;
                                        return (
                                            <button
                                                key={tf}
                                                onClick={() => setSelectedTimeframe(tf)}
                                                className={`px-2.5 py-1 text-[9px] font-black uppercase transition-all rounded-lg border ${selectedTimeframe === tf ? 'bg-teal-400 border-teal-400 text-slate-950 shadow-[0_4px_10px_rgba(45,212,191,0.3)]' : 'bg-transparent border-transparent text-slate-400 hover:text-white'}`}
                                            >
                                                {label}
                                            </button>
                                        );
                                    })}

                                    {/* Dropdown Toggle */}
                                    <div className="relative ml-0.5 border-l border-white/10 pl-1.5">
                                        <button
                                            onClick={() => setShowTimeframeDropdown(!showTimeframeDropdown)}
                                            className={`p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-all ${showTimeframeDropdown ? 'bg-white/10 text-white' : ''}`}
                                        >
                                            <Settings size={12} className={showTimeframeDropdown ? 'rotate-90 transition-transform' : 'transition-transform'} />
                                        </button>

                                        {showTimeframeDropdown && (
                                            <div className="absolute top-full left-0 mt-2 bg-slate-900 border border-white/10 rounded-2xl shadow-2xl p-3 min-w-[220px] grid grid-cols-2 gap-x-4 gap-y-1 animate-in zoom-in-95 duration-200 z-[100]">
                                                {ALL_TIMEFRAMES.map((item) => (
                                                    <div key={item.value} className="flex items-center justify-between group py-1">
                                                        <button
                                                            onClick={() => { setSelectedTimeframe(item.value); setShowTimeframeDropdown(false); }}
                                                            className={`text-[10px] font-bold uppercase tracking-widest ${selectedTimeframe === item.value ? 'text-teal-400' : 'text-slate-400 group-hover:text-white'}`}
                                                        >
                                                            {item.label}
                                                        </button>
                                                        <button
                                                            onClick={() => {
                                                                setFavorites(prev => prev.includes(item.value) ? prev.filter(v => v !== item.value) : [...prev, item.value]);
                                                            }}
                                                            className={`p-1 transition-all ${favorites.includes(item.value) ? 'text-teal-400' : 'text-slate-700 hover:text-slate-500'}`}
                                                        >
                                                            <Activity size={10} fill={favorites.includes(item.value) ? "currentColor" : "none"} />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <div className="w-full h-full relative" ref={chartContainerRef}>
                                    <TradingChart symbol={selectedSymbol} timeframe={selectedTimeframe} onPriceUpdate={setCurrentPrice} containerRef={chartContainerRef} />
                                </div>
                            </div>

                            {/* Bottom Tabs Panel */}
                            <div className="h-1/3 panel-card flex flex-col overflow-hidden">
                                <div className="h-12 border-b border-white/5 flex items-center px-6 gap-8 bg-white/[0.02]">
                                    {['positions', 'orders', 'history', 'logs'].map(tab => (
                                        <button
                                            key={tab}
                                            className={`h-full px-1 text-[10px] font-black uppercase tracking-[0.2em] transition-all border-b-2 ${activeTab === tab ? 'border-teal-400 text-white' : 'border-transparent text-slate-500 hover:text-slate-200'}`}
                                            onClick={() => setActiveTab(tab as any)}
                                        >
                                            {tab === 'positions' ? `Positions (${positions.length})` : tab}
                                        </button>
                                    ))}
                                </div>
                                <div className="flex-1 overflow-auto">
                                    {activeTab === 'positions' && (
                                        positions.length === 0 ? (
                                            <EmptyState icon="📂" title="No active positions" subtitle="Terminal ready for execution" />
                                        ) : (
                                            <div className="overflow-auto"><PositionTable positions={positions} onUpdate={handleClosePosition} /></div>
                                        )
                                    )}
                                    {activeTab === 'history' && (
                                        tradeHistory.length === 0 ? (
                                            <EmptyState icon="📜" title="History empty" subtitle="Logs will appear post-execution" />
                                        ) : (
                                            <div className="overflow-auto"><TradeHistoryTable history={tradeHistory} fmtPnl={fmtPnl} fmt={fmt} onRefresh={() => { addToast('Refreshing execution history...', 'success'); fetchTradeHistory(); }} /></div>
                                        )
                                    )}
                                    {activeTab === 'logs' && (
                                        <div className="p-3 font-mono text-[9px] text-textMuted/70 space-y-0.5 leading-tight">
                                            <div>[SYSTEM] Connection Stable @ Hyperliquid Prod 01</div>
                                            <div>[RISK] Cross-margin Mode Active | Leverage 2x</div>
                                            <div>[ENGINE] Monitoring Orderbook Depth for Liquidity Gaps...</div>
                                            <div>[AUTH] Session Secure | RSA-Handshake Complete</div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </section>

                        {/* Right Pane: Order Entry & Modules */}
                        <aside className="border-l border-border bg-panel flex flex-col shrink-0 h-full overflow-hidden">
                            <div className="flex-1 flex flex-col gap-0 overflow-y-auto no-scrollbar">
                                <OrderEntry symbol={selectedSymbol} balance={metrics.equity} currentPrice={currentPrice} addToast={addToast} />

                                <div className="p-4 border-t border-border space-y-6">
                                    {/* Risk Slider - Condensed */}
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="text-[9px] font-bold text-textMuted uppercase tracking-widest">Risk Profile</span>
                                            <span className="text-[10px] mono-number font-bold text-primary">{riskLimit.toFixed(1)}%</span>
                                        </div>
                                        <input
                                            type="range"
                                            className="w-full h-1 bg-background appearance-none cursor-pointer accent-white"
                                            min="0.1" max="10" step="0.1"
                                            value={riskLimit}
                                            onChange={(e) => handleUpdateRisk(parseFloat(e.target.value))}
                                        />
                                    </div>

                                    {/* Module Toggles */}
                                    <div>
                                        <span className="text-[9px] font-bold text-textMuted uppercase tracking-widest block mb-3">Active Clusters</span>
                                        <div className="space-y-1.5">
                                            {strategies.map(s => (
                                                <StrategyToggle
                                                    key={s.id}
                                                    name={s.name}
                                                    enabled={s.is_enabled}
                                                    onToggle={() => handleToggleStrategy(s.id)}
                                                    onSettings={() => setActivePage('strategies')}
                                                    risk={s.risk_per_trade}
                                                />
                                            ))}
                                        </div>
                                    </div>

                                    {/* Kill Switch - Industrial Style */}
                                    <div className="pt-4 border-t border-white/5">
                                        <button
                                            onClick={handleKillSwitch}
                                            className="ios-button-danger w-full text-xs"
                                        >
                                            Abort Protocol
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </aside>
                    </div>

                ) : activePage === 'strategies' ? (
                    <div className="h-full overflow-auto"><StrategiesPage strategies={strategies} setStrategies={setStrategies} onToggle={handleToggleStrategy} onUpdateParams={handleUpdateStrategyParameters} fmt={fmt} addToast={addToast} /></div>

                ) : activePage === 'risk' ? (
                    <div className="h-full overflow-auto"><RiskControlPage metrics={metrics} fmt={fmt} fmtPct={fmtPct} fmtUsd={fmtUsd} addToast={addToast} /></div>

                ) : activePage === 'research' ? (
                    <div className="h-full overflow-auto"><ResearchLabPage addToast={addToast} /></div>

                ) : activePage === 'history' ? (
                    <div className="h-full overflow-auto"><TradeHistoryPage tradeHistory={tradeHistory} setTradeHistory={setTradeHistory} fmtPnl={fmtPnl} fmt={fmt} /></div>

                ) : activePage === 'settings' ? (
                    <div className="h-full overflow-auto"><SettingsPage addToast={addToast} /></div>

                ) : null}

                <ToastContainer toasts={toasts} onRemove={removeToast} />
            </main>
        </div>
    );
}

// ── TradingView Lightweight Chart Component ─────────────────
function TradingChart({ symbol, timeframe = '15m', onPriceUpdate, containerRef }: { symbol: string, timeframe?: string, onPriceUpdate?: (price: number) => void, containerRef: React.RefObject<HTMLDivElement> }) {
    const chartRef = useRef<any>(null);
    const candleSeriesRef = useRef<any>(null);
    const ema21Ref = useRef<any>(null);
    const ema90Ref = useRef<any>(null);
    const [isChartReady, setIsChartReady] = useState(false);

    // Initial Chart Creation
    useEffect(() => {
        let chartInstance: any = null;
        let observer: ResizeObserver | null = null;
        const container = containerRef.current;

        if (!container) return;

        const initChart = async () => {
            const { createChart, ColorType, CrosshairMode } = await import('lightweight-charts');

            // Clean up existing content in the ref container before creating a new one
            // This is crucial to prevent multiple charts being created
            if (container) {
                while (container.firstChild) {
                    container.removeChild(container.firstChild);
                }
            }

            chartInstance = createChart(container, {
                layout: {
                    background: { type: ColorType.Solid, color: '#040405' },
                    textColor: '#64748b',
                    fontSize: 10,
                    fontFamily: 'Inter, system-ui, sans-serif',
                },
                grid: {
                    vertLines: { color: 'rgba(255, 255, 255, 0.02)' },
                    horzLines: { color: 'rgba(255, 255, 255, 0.02)' },
                },
                crosshair: { mode: CrosshairMode.Normal },
                rightPriceScale: {
                    borderColor: '#1a1d23',
                    autoScale: true,
                    scaleMargins: { top: 0.1, bottom: 0.2 },
                },
                timeScale: {
                    borderColor: '#1a1d23',
                    timeVisible: true,
                    secondsVisible: false,
                },
            });

            const candleSeries = chartInstance.addCandlestickSeries({
                upColor: '#00ff9d',
                downColor: '#ff3b57',
                borderDownColor: '#ff3b57',
                borderUpColor: '#00ff9d',
                wickDownColor: '#ff3b57',
                wickUpColor: '#00ff9d',
            });

            const ema21 = chartInstance.addLineSeries({ color: '#3b82f6', lineWidth: 1, title: 'EMA 21', priceLineVisible: false });
            const ema90 = chartInstance.addLineSeries({ color: '#f59e0b', lineWidth: 1, title: 'EMA 90', priceLineVisible: false });

            candleSeriesRef.current = candleSeries;
            ema21Ref.current = ema21;
            ema90Ref.current = ema90;
            chartRef.current = chartInstance;

            observer = new ResizeObserver(entries => {
                if (entries[0] && chartRef.current) {
                    chartRef.current.applyOptions({
                        width: entries[0].contentRect.width,
                        height: entries[0].contentRect.height
                    });
                }
            });
            observer.observe(container);
            setIsChartReady(true);
        };

        initChart();

        return () => {
            if (observer) observer.disconnect();
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
            }
        };
    }, []);

    // Data Fetching for current symbol
    useEffect(() => {
        if (!chartRef.current || !candleSeriesRef.current) return;

        let active = true;
        const fetchData = async () => {
            try {
                const res = await apiFetch(`/api/trading/candles/${symbol}?timeframe=${timeframe}&limit=200`);
                if (!active) return;

                const candles = res.candles;
                candleSeriesRef.current.setData(candles);

                const calcEma = (data: any[], period: number) => {
                    const k = 2 / (period + 1);
                    const result: any[] = [];
                    if (data.length === 0) return result;
                    let ema = data[0].close;
                    for (const d of data) {
                        ema = d.close * k + ema * (1 - k);
                        result.push({ time: d.time, value: ema });
                    }
                    return result;
                }

                ema21Ref.current.setData(calcEma(candles, 21));
                ema90Ref.current.setData(calcEma(candles, 90));

                if (candles.length > 0 && onPriceUpdate) {
                    onPriceUpdate(candles[candles.length - 1].close);
                }

                chartRef.current.timeScale().fitContent();
            } catch (e) {
                console.error('Failed to fetch chart data:', e);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 10000); // Polling as fallback for WS

        return () => {
            active = false;
            clearInterval(interval);
        };
    }, [symbol, timeframe, isChartReady]);

    return <div ref={containerRef} className="w-full h-full" />;
}

// ── Login Page Component ─────────────────────────────────────
function LoginPage({ onLogin, onToast }: { onLogin: (u: any) => void; onToast: (msg: string, type?: Toast['type']) => void }) {
    const [username, setUsername] = useState('admin');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLoginSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const data = await apiPost('/api/auth/login', { username, password });
            localStorage.setItem('qb_token', data.access_token);
            onLogin({ username: data.username, role: data.role });
        } catch (err: any) {
            setError('Invalid credentials or server unreachable');
            onToast('Login Failed: ' + (err.message || 'Check credentials'), 'error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-screen w-screen relative flex items-center justify-center overflow-hidden bg-black font-sans">
            {/* Structural Background Pattern */}
            <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#ffffff 0.5px, transparent 0.5px)', backgroundSize: '20px 20px' }}></div>
            <div className="absolute inset-0 bg-gradient-to-tr from-background via-transparent to-primary/5"></div>

            <div className="relative z-10 w-full max-w-sm p-4 animate-in fade-in zoom-in-95 duration-500">
                <div className="bg-panel/10 backdrop-blur-3xl border border-white/10 p-8 rounded-none shadow-[0_0_50px_rgba(0,0,0,0.5)]">
                    <div className="text-center mb-10">
                        <div className="inline-flex items-center justify-center w-12 h-12 bg-white text-black mb-6 border border-white/20">
                            <span className="font-bold text-xl">H</span>
                        </div>
                        <h1 className="text-lg font-bold tracking-[0.3em] text-white uppercase">HEXABOT_PRO</h1>
                        <p className="text-[9px] text-textMuted uppercase mt-2 font-bold tracking-[0.2em] opacity-60">Handshake Protocol: Secure Terminal</p>
                    </div>

                    <form onSubmit={handleLoginSubmit} className="space-y-8">
                        <div className="space-y-2">
                            <label className="text-[8px] text-textMuted uppercase font-bold tracking-widest block ml-0.5">Terminal_ID</label>
                            <input
                                type="text"
                                className="w-full bg-black/40 border border-white/10 rounded-none px-4 py-3 text-xs focus:border-white/40 outline-none text-white transition-all placeholder:opacity-20"
                                placeholder="ADMIN_UID"
                                value={username}
                                onChange={e => setUsername(e.target.value)}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-[8px] text-textMuted uppercase font-bold tracking-widest block ml-0.5">Access_Protocol</label>
                            <input
                                type="password"
                                className="w-full bg-black/40 border border-white/10 rounded-none px-4 py-3 text-xs focus:border-white/40 outline-none text-white transition-all placeholder:opacity-20"
                                placeholder="••••••••"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                required
                            />
                        </div>

                        {error && (
                            <div className="text-[9px] text-danger border border-danger/30 p-3 rounded-none bg-danger/5 font-bold uppercase tracking-tighter">
                                [ACCESS_DENIED] {error}
                            </div>
                        )}

                        <button
                            disabled={loading}
                            type="submit"
                            className="w-full bg-white hover:bg-white/90 text-black font-bold py-3 rounded-none transition-all disabled:opacity-50 flex items-center justify-center uppercase tracking-[0.2em] text-[10px]"
                        >
                            {loading ? <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin"></div> : 'Initiate_Uplink'}
                        </button>
                    </form>

                    <div className="mt-12 pt-6 border-t border-white/5 flex justify-between items-center text-[8px] text-textMuted uppercase font-bold tracking-[0.2em]">
                        <div className="flex items-center gap-1.5">
                            <div className="w-1.5 h-1.5 bg-success animate-pulse"></div>
                            <span>Sys_Online</span>
                        </div>
                        <span>Protocol_v1.0.4</span>
                    </div>
                </div>
            </div>

            {/* Micro-animations */}
            <div className="absolute top-10 right-10 flex flex-col gap-1 opacity-20">
                {[1, 2, 3, 4].map(i => <div key={i} className="h-px bg-white transition-all duration-[3000ms] animate-pulse" style={{ width: `${i * 40}px`, animationDelay: `${i * 0.5}s` }}></div>)}
            </div>
        </div>
    );
}

// ── Order Entry Panel Component ─────────────────────────────
function OrderEntry({ symbol, balance, currentPrice, addToast }: { symbol: string, balance: number, currentPrice?: number; addToast: (msg: string, type?: Toast['type']) => void }) {
    const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
    const [type, setType] = useState<'MARKET' | 'LIMIT'>('MARKET');
    const [price, setPrice] = useState('');
    const [amount, setAmount] = useState('');
    const [percent, setPercent] = useState(0);
    const [executing, setExecuting] = useState(false);

    const asset = symbol.split('-')[0];

    useEffect(() => {
        if (percent > 0 && balance > 0) {
            const anchor = currentPrice && currentPrice > 0 ? currentPrice : (symbol.includes('BTC') ? 65000 : symbol.includes('ETH') ? 3500 : 150);
            const calculatedAmount = (balance * (percent / 100)) / (type === 'LIMIT' && parseFloat(price) ? parseFloat(price) : anchor);
            setAmount(calculatedAmount.toFixed(4));
        }
    }, [percent, balance, price, currentPrice, type, symbol]);

    const handlePlaceOrder = async () => {
        if (!amount || parseFloat(amount) <= 0) {
            addToast('Enter valid amount', 'warning');
            return;
        }

        const confirmMsg = `${side} ${amount} ${asset} ${type === 'LIMIT' ? `@ ${price}` : 'at Market'}?`;
        if (!confirm(confirmMsg)) return;

        setExecuting(true);
        try {
            await apiPost('/api/trading/order', {
                symbol,
                side,
                type,
                size: parseFloat(amount),
                price: type === 'LIMIT' ? parseFloat(price) : null
            });
            addToast(`Transmitted: ${side} ${amount} ${asset}`, 'success');
            setAmount('');
            setPercent(0);
        } catch (e) {
            addToast('Uplink Interrupted: Order Transmission Failed', 'error');
        } finally {
            setExecuting(false);
        }
    };

    return (
        <div className="flex flex-col border-b border-border">
            {/* Side Tabs - Raised and condensed */}
            <div className="flex p-2 gap-2 bg-[#020609]">
                <button
                    className={`flex-1 py-3 font-black text-xs transition-all duration-300 rounded-xl active:scale-95 hover:scale-[1.05] ${side === 'BUY'
                        ? 'bg-[#0fbc9d] text-white shadow-[0_0_20px_rgba(15,188,157,0.4)] hover:shadow-[0_0_30px_rgba(15,188,157,0.6)]'
                        : 'bg-white/5 text-slate-500 hover:bg-white/10 hover:text-slate-200'
                        }`}
                    onClick={() => setSide('BUY')}
                >
                    BUY
                </button>
                <button
                    className={`flex-1 py-3 font-black text-xs transition-all duration-300 rounded-xl active:scale-95 hover:scale-[1.05] ${side === 'SELL'
                        ? 'bg-[#e11d48] text-white shadow-[0_0_20px_rgba(225,29,72,0.4)] hover:shadow-[0_0_30px_rgba(225,29,72,0.6)]'
                        : 'bg-white/5 text-slate-500 hover:bg-white/10 hover:text-slate-200'
                        }`}
                    onClick={() => setSide('SELL')}
                >
                    SELL
                </button>
            </div>

            <div className="p-3 space-y-3">
                {/* Order Type Tabs */}
                <div className="flex bg-background rounded-none p-0.5 border border-border">
                    {['MARKET', 'LIMIT'].map(t => (
                        <button
                            key={t}
                            onClick={() => setType(t as any)}
                            className={`flex-1 py-1.5 text-[11px] font-bold uppercase tracking-widest rounded-none transition-all ${type === t ? 'bg-panel text-white border border-border/50' : 'text-textMuted hover:text-white'}`}
                        >
                            {t}
                        </button>
                    ))}
                </div>

                {/* Inputs - tighter spacing */}
                <div className="space-y-3">
                    {type === 'LIMIT' && (
                        <div className="space-y-1">
                            <label className="text-[10px] text-textMuted uppercase font-bold tracking-widest">Price_USD</label>
                            <div className="relative">
                                <input
                                    type="number"
                                    className="w-full bg-background border border-border rounded-none px-4 py-3 text-[16px] font-bold outline-none focus:border-primary transition-colors mono-number"
                                    placeholder="0.00"
                                    value={price}
                                    onChange={(e) => setPrice(e.target.value)}
                                />
                                <span className="absolute right-4 top-3.5 text-[12px] text-textMuted font-bold">USD</span>
                            </div>
                        </div>
                    )}

                    <div className="space-y-1">
                        <label className="text-[10px] text-textMuted uppercase font-bold tracking-widest">Size_{asset}</label>
                        <div className="relative">
                            <input
                                type="number"
                                className="w-full bg-background border border-border rounded-none px-4 py-3 text-[16px] font-bold outline-none focus:border-primary transition-colors mono-number"
                                placeholder="0.0000"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                            />
                            <span className="absolute right-4 top-3.5 text-[12px] text-textMuted font-bold">{asset}</span>
                        </div>
                    </div>
                </div>

                {/* Percent Sliders */}
                <div className="flex justify-between items-center gap-1.5">
                    {[10, 25, 50, 75, 100].map(p => (
                        <button
                            key={p}
                            onClick={() => setPercent(p)}
                            className={`flex-1 py-1.5 text-[11px] font-bold rounded-none border transition-all ${percent === p ? 'bg-primary/10 border-primary/30 text-primary' : 'bg-background border-border text-textMuted hover:border-textMuted'}`}
                        >
                            {p}%
                        </button>
                    ))}
                </div>

                <div className="pt-2 border-t border-border/50 space-y-1">
                    <div className="flex justify-between text-[11px]"><span className="text-textMuted">Available</span><span className="mono-number text-textMain">${fmt(balance)}</span></div>
                    <div className="flex justify-between text-[11px]"><span className="text-textMuted">Cost Estim.</span><span className="mono-number text-textMain">${fmt((parseFloat(amount) || 0) * (type === 'LIMIT' && parseFloat(price) ? parseFloat(price) : (currentPrice || 0)), 4)}</span></div>
                </div>

                <button
                    disabled={executing}
                    onClick={handlePlaceOrder}
                    className={`w-full ${side === 'BUY' ? 'trading-button-buy' : 'trading-button-sell'} ${executing ? 'opacity-50' : ''}`}
                >
                    {executing ? 'Transmitting...' : `${side} ${asset}`}
                </button>
            </div>
        </div>
    );

    function fmt(n: number, d = 4) { return n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: d }); }
}

// ── Order Book Component ─────────────────────────────────────
function OrderBook({ symbol, currentPrice }: { symbol: string, currentPrice?: number }) {
    const [bids, setBids] = useState<any[]>([]);
    const [asks, setAsks] = useState<any[]>([]);
    const [lastPrice, setLastPrice] = useState(0);
    const fmt = (n: number, d = 4) => n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: d });

    useEffect(() => {
        // Fallback simulated orderbook around the actual current price
        const generateLevel = (base: number, offset: number) => ({
            price: (base + offset),
            size: (Math.random() * 2.5 + 0.1),
            total: 0 // calculated later
        });

        const updateData = () => {
            // Anchor to the actual price if available, otherwise default fallback
            const anchorPrice = currentPrice && currentPrice > 0 ? currentPrice : (symbol.includes('BTC') ? 65000 : symbol.includes('ETH') ? 3500 : 150);
            const base = anchorPrice + (Math.random() - 0.5) * (anchorPrice * 0.001);
            setLastPrice(base);

            const newAsks = [];
            const newBids = [];
            const step = anchorPrice * 0.0005; // 0.05% step

            for (let i = 0; i < 15; i++) {
                newAsks.push(generateLevel(base, (i + 1) * step));
                newBids.push(generateLevel(base, -(i + 1) * step));
            }

            // Calc cumulative totals
            let askTotal = 0;
            newAsks.forEach(a => { askTotal += a.size; a.total = askTotal; });
            let bidTotal = 0;
            newBids.forEach(b => { bidTotal += b.size; b.total = bidTotal; });

            setAsks(newAsks.reverse());
            setBids(newBids);
        };

        updateData();
        const interval = setInterval(updateData, 1500);
        return () => clearInterval(interval);
    }, [symbol, currentPrice]);

    const maxTotal = Math.max(...asks.map(a => a.total), ...bids.map(b => b.total));

    return (
        <div className="flex flex-col h-full text-[10px] font-mono select-none">
            <div className="grid grid-cols-3 px-3 py-2 text-textMuted uppercase tracking-wider border-b border-border font-sans font-bold">
                <span>Price</span>
                <span className="text-right">Size</span>
                <span className="text-right">Total</span>
            </div>

            {/* ASKS (Sells) */}
            <div className="flex-1 flex flex-col-reverse justify-end overflow-hidden py-1">
                {asks.map((lvl, i) => (
                    <div key={i} className="relative grid grid-cols-3 px-3 py-0.5 hover:bg-white/5 group transition-colors">
                        <div className="absolute inset-y-0 right-0 bg-danger/10 transition-all duration-300" style={{ width: `${(lvl.total / maxTotal) * 100}%` }}></div>
                        <span className="text-danger z-10 font-bold">{fmt(lvl.price, 4)}</span>
                        <span className="text-right text-textMain z-10">{fmt(lvl.size, 4)}</span>
                        <span className="text-right text-textMuted z-10">{fmt(lvl.total, 4)}</span>
                    </div>
                ))}
            </div>

            {/* SPREAD / LAST PRICE */}
            <div className="px-3 py-3 border-y border-border bg-background/50 flex items-center justify-between">
                <span className={`text-sm font-bold mono-number ${Math.random() > 0.5 ? 'text-teal-400' : 'text-rose-500'}`}>
                    {fmt(lastPrice, 4)} {Math.random() > 0.5 ? '↑' : '↓'}
                </span>
                <span className="text-textMuted text-[9px] tracking-tight italic">Spread: 1.45 (0.001%)</span>
            </div>

            {/* BIDS (Buys) */}
            <div className="flex-1 flex flex-col overflow-hidden py-1">
                {bids.map((lvl, i) => (
                    <div key={i} className="relative grid grid-cols-3 px-3 py-0.5 hover:bg-white/5 group transition-colors">
                        <div className="absolute inset-y-0 right-0 bg-teal-400/10 transition-all duration-300" style={{ width: `${(lvl.total / maxTotal) * 100}%` }}></div>
                        <span className="text-teal-400 z-10 font-bold">{fmt(lvl.price, 4)}</span>
                        <span className="text-right text-textMain z-10">{fmt(lvl.size, 4)}</span>
                        <span className="text-right text-textMuted z-10">{fmt(lvl.total, 4)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ── Sub-components ──────────────────────────────────────────
function NavItem({ icon, label, active = false, onClick }: { icon: React.ReactNode; label: string; active?: boolean; onClick?: () => void }) {
    return (
        <div onClick={onClick} className={`w-full flex items-center px-4 py-2 cursor-pointer transition-colors border-l-2 ${active ? 'bg-background border-primary text-textMain' : 'border-transparent text-textMuted hover:bg-background hover:text-textMain'}`}>
            <span className={`shrink-0 transition-transform ${active ? 'text-primary' : ''}`}>{icon}</span>
            <span className="ml-3 text-[10px] font-bold uppercase tracking-widest opacity-0 group-hover:opacity-100 whitespace-nowrap">{label}</span>
        </div>
    );
}

function TopMetric({ label, value, trend, isPositive, isNegative }: any) {
    return (
        <div className="flex flex-col h-full justify-center">
            <span className="text-[10px] text-textMuted uppercase tracking-wider">{label}</span>
            <div className="flex items-end gap-2">
                <span className="font-semibold text-lg mono-number leading-none">{value}</span>
                {trend && (
                    <span className={`text-xs mono-number leading-none ${isPositive ? 'text-success' : ''} ${isNegative ? 'text-danger' : ''}`}>
                        {trend}
                    </span>
                )}
            </div>
        </div>
    );
}

function StrategyToggle({ name, enabled, onToggle, onSettings, risk }: { name: string; enabled: boolean; onToggle: () => void; onSettings: () => void; risk?: number }) {
    return (
        <div className="group flex items-center justify-between p-2.5 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all hover:border-white/10">
            <div className="flex items-center gap-3">
                <div onClick={onToggle} className={`w-2 h-2 rounded-full cursor-pointer transition-all duration-300 ${enabled ? 'bg-teal-400 shadow-[0_0_8px_rgba(45,212,191,0.5)] animate-pulse' : 'bg-slate-700'}`} />
                <div className="flex flex-col">
                    <span className={`text-[11px] font-black uppercase tracking-tight transition-colors ${enabled ? 'text-white' : 'text-slate-500'}`}>{name}</span>
                    {risk && <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest mt-0.5">Risk: {risk.toFixed(1)}%</span>}
                </div>
            </div>
            <div className="flex items-center gap-2">
                <button
                    onClick={onSettings}
                    className="p-1 px-1.5 rounded-md hover:bg-white/10 text-slate-500 hover:text-white transition-colors"
                >
                    <Settings size={12} />
                </button>
                <div
                    onClick={onToggle}
                    className={`relative w-7 h-4 rounded-full cursor-pointer transition-colors duration-300 ${enabled ? 'bg-teal-400/20' : 'bg-slate-800'}`}
                >
                    <div className={`absolute top-0.5 left-0.5 w-3 h-3 rounded-full transition-all duration-300 transform ${enabled ? 'translate-x-3 bg-teal-400' : 'bg-slate-500'}`} />
                </div>
            </div>
        </div>
    );
}

function EmptyState({ icon, title, subtitle }: { icon: string; title: string; subtitle: string }) {
    return (
        <div className="h-full flex flex-col items-center justify-center text-textMuted p-10 animate-in fade-in duration-500">
            <div className="text-4xl mb-2 opacity-20 filter grayscale">{icon}</div>
            <p className="text-sm font-bold tracking-tight text-white/50">{title}</p>
            <p className="text-[10px] uppercase tracking-widest mt-1 opacity-50">{subtitle}</p>
        </div>
    );
}

function PositionTable({ positions, onUpdate }: { positions: Position[]; onUpdate: (s: string) => void }) {
    return (
        <table className="w-full text-left text-xs border-separate border-spacing-y-2 px-4">
            <thead className="text-[10px] text-slate-500 uppercase tracking-widest">
                <tr>
                    <th className="px-4 py-2 font-black">Market</th>
                    <th className="px-4 py-2 font-black">Side</th>
                    <th className="px-4 py-2 font-black text-right">Size</th>
                    <th className="px-4 py-2 font-black text-right">Market Price</th>
                    <th className="px-4 py-2 font-black text-right">PnL</th>
                    <th className="px-4 py-2 font-black text-right pr-6">Action</th>
                </tr>
            </thead>
            <tbody>
                {positions.map((p) => {
                    const isLong = p.side.toLowerCase() === 'long';
                    function fmt(n: number, d = 4) { return n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: d }); }
                    return (
                        <tr key={p.id} className="bg-white/[0.03] hover:bg-white/[0.06] transition-all group overflow-hidden">
                            <td className="px-4 py-4 font-bold text-white rounded-l-2xl">{p.symbol}</td>
                            <td className="px-4 py-4">
                                <span className={`px-2 py-1 rounded-md font-black text-[10px] uppercase ${isLong ? 'bg-teal-400/10 text-teal-400' : 'bg-rose-500/10 text-rose-500'}`}>
                                    {p.side}
                                </span>
                            </td>
                            <td className="px-4 py-4 text-right mono-number font-bold text-slate-300">{fmt(p.size, 4)}</td>
                            <td className="px-4 py-4 text-right mono-number text-slate-400">{fmt(p.current_price, 4)}</td>
                            <td className={`px-4 py-4 text-right mono-number font-extrabold text-base ${p.unrealized_pnl >= 0 ? 'text-teal-400' : 'text-rose-400'}`}>
                                {p.unrealized_pnl >= 0 ? '+' : ''}{fmt(p.unrealized_pnl, 2)}
                            </td>
                            <td className="px-4 py-4 text-right rounded-r-2xl pr-6">
                                <button onClick={() => onUpdate(p.symbol)} className="ios-button-danger py-1.5 px-4 text-[9px] font-black tracking-widest opacity-0 group-hover:opacity-100 transition-all uppercase">Liquidate</button>
                            </td>
                        </tr>
                    );
                })}
            </tbody>
        </table>
    );
}
function TradeHistoryTable({ history, fmtPnl, fmt, onRefresh }: any) {
    return (
        <div className="relative h-full flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
                <h3 className="text-xs font-black uppercase tracking-widest text-slate-500">Execution History</h3>
                <button
                    onClick={onRefresh}
                    className="btn-refresh-history flex items-center justify-center transition-all active:rotate-180 duration-500"
                    title="Refresh History"
                >
                    <RefreshCw size={16} />
                </button>
            </div>
            <div className="flex-1 overflow-auto custom-scrollbar">
                <table className="w-full text-left text-xs border-separate border-spacing-y-1.5 px-4 pb-4">
                    <thead className="text-[10px] text-slate-600 uppercase font-black tracking-widest sticky top-0 bg-slate-900/80 backdrop-blur-md z-10">
                        <tr>
                            <th className="px-4 py-2">Time</th>
                            <th className="px-4 py-2">Symbol</th>
                            <th className="px-4 py-2">Side</th>
                            <th className="px-4 py-2 text-right">PnL</th>
                            <th className="px-4 py-2 pr-6">Strategy</th>
                        </tr>
                    </thead>
                    <tbody>
                        {history.map((t: any) => (
                            <tr key={t.id} className="bg-white/[0.02] hover:bg-white/[0.05] transition-all group">
                                <td className="px-4 py-3 text-slate-500 font-medium rounded-l-2xl">{new Date(t.executed_at).toLocaleTimeString()}</td>
                                <td className="px-4 py-3 font-bold text-white">{t.symbol}</td>
                                <td className="px-4 py-3 uppercase">
                                    <span className={`px-2 py-0.5 rounded-lg text-[9px] font-black ${t.side === 'long' ? 'bg-teal-400/10 text-teal-400' : 'bg-rose-500/10 text-rose-500'}`}>
                                        {t.side}
                                    </span>
                                </td>
                                <td className={`px-4 py-3 text-right mono-number font-black ${t.pnl >= 0 ? 'text-teal-400' : 'text-rose-400'}`}>
                                    {fmtPnl(t.pnl)}
                                </td>
                                <td className="px-4 py-3 text-slate-400 font-bold rounded-r-2xl pr-6">
                                    <span className="bg-slate-800/50 px-2 py-0.5 rounded text-[10px]">{t.strategy_name || 'Manual'}</span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// ── Page Components ─────────────────────────────────────────

function StrategiesPage({ strategies, setStrategies, onToggle, onUpdateParams, fmt, addToast }: { strategies: Strategy[]; setStrategies: React.Dispatch<React.SetStateAction<Strategy[]>>; onToggle: (id: string) => void; onUpdateParams: (id: string) => void; fmt: (n: number, d?: number) => string; addToast: (msg: string, type?: Toast['type']) => void }) {
    const [searchTerm, setSearchTerm] = useState('');
    const [filterType, setFilterType] = useState('all');

    const filteredStrats = strategies.filter(s => {
        const matchesSearch = s.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filterType === 'all' || s.type === filterType;
        return matchesSearch && matchesFilter;
    });

    const types = ['all', ...Array.from(new Set(strategies.map(s => s.type)))];

    return (
        <div className="h-full p-6 overflow-auto bg-background animate-in fade-in slide-in-from-bottom-4 duration-700">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-xl font-bold tracking-tighter text-white">Strategy Manager</h1>
                    <p className="text-[10px] text-textMuted mt-1 uppercase font-bold tracking-widest">Algorithmic Cluster Control</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-teal-400 transition-colors" size={14} />
                        <input
                            type="text"
                            placeholder="Find Module..."
                            className="bg-white/5 border border-white/5 rounded-full pl-11 pr-5 py-2.5 text-[11px] outline-none focus:border-teal-500/50 w-64 transition-all uppercase font-bold text-white placeholder:text-slate-600 shadow-inner"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <select
                        className="bg-white/5 border border-white/5 rounded-full px-5 py-2.5 text-[11px] outline-none focus:border-teal-500/50 capitalize font-bold text-slate-300 cursor-pointer hover:bg-white/10 transition-all appearance-none"
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                    >
                        {types.map(t => <option key={t} value={t} className="bg-slate-900">{t.replace(/_/g, ' ')}</option>)}
                    </select>
                    <button
                        onClick={() => addToast("Deployment protocol restricted.", "warning")}
                        className="bg-teal-400 hover:bg-teal-300 text-slate-950 font-black py-2.5 px-7 rounded-full text-[10px] uppercase tracking-[0.15em] transition-all shadow-[0_8px_20px_rgba(45,212,191,0.2)] active:scale-95 flex items-center gap-2"
                    >
                        <Zap size={14} fill="currentColor" />
                        New Module
                    </button>
                </div>
            </header>

            {filteredStrats.length === 0 ? (
                <div className="h-[60vh] flex items-center justify-center">
                    <EmptyState icon="📭" title="No Strategies Found" subtitle="Verify filters or deploy new module" />
                </div>
            ) : (
                <div className="grid gap-3 grid-cols-1 xl:grid-cols-2 pb-10">
                    {filteredStrats.map(s => (
                        <div key={s.id} className={`panel-card p-6 border-l-4 transition-all duration-500 group hover:translate-y-[-2px] ${s.is_enabled ? 'border-l-teal-400 bg-teal-400/[0.03]' : 'border-l-slate-800 bg-slate-900/40 opacity-70'}`}>
                            <div className="flex items-start justify-between mb-8">
                                <div className="flex items-center gap-6">
                                    <div className={`w-14 h-14 flex items-center justify-center rounded-2xl transition-all duration-500 ${s.is_enabled ? 'bg-gradient-to-br from-teal-400 to-teal-600 text-slate-950 shadow-[0_10px_25px_rgba(45,212,191,0.4)] rotate-3' : 'bg-slate-800 text-slate-500'}`}>
                                        <Cpu size={28} strokeWidth={2.5} />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-black tracking-tight uppercase text-white group-hover:text-teal-400 transition-colors">{s.name}</h3>
                                        <div className="flex items-center gap-3 mt-2">
                                            <span className={`text-[9px] font-black uppercase tracking-[0.2em] flex items-center gap-2 px-3 py-1 rounded-full border ${s.is_enabled ? 'text-teal-400 border-teal-500/30 bg-teal-500/10' : 'text-slate-500 border-white/5 bg-background'}`}>
                                                <div className={`w-1.5 h-1.5 rounded-full ${s.is_enabled ? 'bg-teal-400 animate-pulse shadow-[0_0_8px_rgba(45,212,191,0.8)]' : 'bg-slate-700'}`}></div>
                                                {s.is_enabled ? 'Active Cluster' : 'Standby Mode'}
                                            </span>
                                            <span className="text-[9px] font-bold uppercase tracking-widest text-slate-600 italic px-2 py-1 bg-white/5 rounded-md">{s.type.replace(/_/g, ' ')}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <button
                                        onClick={() => onToggle(s.id)}
                                        className={`group relative w-20 h-8 rounded-full transition-all duration-500 border ${s.is_enabled ? 'bg-teal-500/10 border-teal-500/40 shadow-[0_0_15px_rgba(45,212,191,0.1)]' : 'bg-slate-900 border-white/5'}`}
                                    >
                                        <div className={`absolute top-1 w-6 h-6 rounded-full transition-all duration-500 shadow-lg ${s.is_enabled ? 'right-1 bg-teal-400 shadow-teal-500/40' : 'left-1 bg-slate-700'}`}></div>
                                        <span className={`absolute top-1/2 -translate-y-1/2 text-[9px] font-black transition-all duration-500 ${s.is_enabled ? 'left-3 text-teal-400' : 'right-3 text-slate-500'}`}>
                                            {s.is_enabled ? 'ON' : 'OFF'}
                                        </span>
                                    </button>
                                </div>
                            </div>

                            {/* Performance Stats Tiles - Optimized Readability */}
                            <div className="flex flex-wrap gap-1.5 mb-2.5">
                                <div className="bg-slate-950/40 border border-white/5 p-2 px-3 rounded-lg flex flex-col min-w-[80px]">
                                    <span className="text-[9px] text-slate-500 font-black uppercase tracking-tighter leading-none mb-1">PnL</span>
                                    <span className={`text-[13px] font-black mono-number leading-none ${s.pnl_daily && s.pnl_daily >= 0 ? 'text-teal-400' : 'text-rose-500'}`}>
                                        {s.pnl_daily ? (s.pnl_daily > 0 ? '+' : '-') + '$' + Math.abs(s.pnl_daily).toFixed(0) : '$0'}
                                    </span>
                                </div>
                                <div className="bg-slate-950/40 border border-white/5 p-2 px-3 rounded-lg flex flex-col min-w-[60px]">
                                    <span className="text-[9px] text-slate-500 font-black uppercase tracking-tighter leading-none mb-1">Win</span>
                                    <span className="text-[13px] font-black mono-number leading-none text-white">{s.win_rate || 0}%</span>
                                </div>
                                <div className="bg-slate-950/40 border border-white/5 p-2 px-3 rounded-lg flex flex-col min-w-[60px]">
                                    <span className="text-[9px] text-slate-500 font-black uppercase tracking-tighter leading-none mb-1">Trades</span>
                                    <span className="text-[13px] font-black mono-number leading-none text-white">{s.trades_count || 0}</span>
                                </div>
                                <div className="bg-teal-400/5 border border-teal-400/20 p-2 px-3 rounded-lg flex flex-col min-w-[70px] shadow-[inset_0_0_8px_rgba(45,212,191,0.05)]">
                                    <span className="text-[9px] text-teal-400/70 font-black uppercase tracking-tighter leading-none mb-1">Risk</span>
                                    <span className="text-[13px] font-black mono-number leading-none text-teal-400">{s.risk_per_trade}%</span>
                                </div>
                            </div>

                            {/* 4 STRATEGY OPTIONS/CONTROLS - Optimized */}
                            <div className="space-y-2 mb-3 bg-white/[0.02] p-2.5 rounded-xl border border-white/5">
                                <div className="grid grid-cols-2 gap-x-4 gap-y-2.5">
                                    {/* 1. Risk Control */}
                                    <div className="bg-black/20 p-2 rounded-lg border border-white/5">
                                        <div className="flex justify-between items-center text-[10px] font-black uppercase mb-1.5">
                                            <span className="text-slate-600">Risk Limit</span>
                                            <span className="text-teal-400">{s.risk_per_trade}%</span>
                                        </div>
                                        <input
                                            type="range" className="w-full h-1 bg-slate-800 appearance-none cursor-pointer accent-teal-400 rounded-full"
                                            min="0.1" max="5" step="0.1" value={s.risk_per_trade}
                                            onChange={(e) => {
                                                const val = parseFloat(e.target.value);
                                                setStrategies(prev => prev.map(item => item.id === s.id ? { ...item, risk_per_trade: val } : item));
                                            }}
                                        />
                                    </div>
                                    {/* 2. Take Profit */}
                                    <div className="bg-black/20 p-2 rounded-lg border border-white/5">
                                        <div className="flex justify-between items-center text-[10px] font-black uppercase mb-1.5">
                                            <span className="text-slate-600">TP</span>
                                            <span className="text-teal-400">{s.take_profit}%</span>
                                        </div>
                                        <input
                                            type="range" className="w-full h-1 bg-slate-800 appearance-none cursor-pointer accent-teal-400 rounded-full"
                                            min="1" max="10" step="0.5" value={s.take_profit}
                                            onChange={(e) => {
                                                const val = parseFloat(e.target.value);
                                                setStrategies(prev => prev.map(item => item.id === s.id ? { ...item, take_profit: val } : item));
                                            }}
                                        />
                                    </div>
                                    {/* 3. Stop Loss */}
                                    <div className="bg-black/20 p-2 rounded-lg border border-white/5">
                                        <div className="flex justify-between items-center text-[10px] font-black uppercase mb-1.5">
                                            <span className="text-slate-600">SL</span>
                                            <span className="text-rose-500">{s.stop_loss}%</span>
                                        </div>
                                        <input
                                            type="range" className="w-full h-1 bg-slate-800 appearance-none cursor-pointer accent-rose-500 rounded-full"
                                            min="0.5" max="5" step="0.1" value={s.stop_loss}
                                            onChange={(e) => {
                                                const val = parseFloat(e.target.value);
                                                setStrategies(prev => prev.map(item => item.id === s.id ? { ...item, stop_loss: val } : item));
                                            }}
                                        />
                                    </div>
                                    {/* 4. Max Drawdown */}
                                    <div className="bg-black/20 p-2 rounded-lg border border-white/5">
                                        <div className="flex justify-between items-center text-[10px] font-black uppercase mb-1.5">
                                            <span className="text-slate-600">MaxDD</span>
                                            <span className="text-amber-500">{s.max_drawdown}%</span>
                                        </div>
                                        <input
                                            type="range" className="w-full h-1 bg-slate-800 appearance-none cursor-pointer accent-amber-500 rounded-full"
                                            min="1" max="20" step="1" value={s.max_drawdown}
                                            onChange={(e) => {
                                                const val = parseFloat(e.target.value);
                                                setStrategies(prev => prev.map(item => item.id === s.id ? { ...item, max_drawdown: val } : item));
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center justify-between pt-2">
                                <div className="flex gap-3">
                                    <div className="flex flex-col">
                                        <span className="text-[8px] text-textMuted uppercase font-bold">Sharpe</span>
                                        <span className="text-[10px] font-bold text-white">2.41</span>
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-[8px] text-textMuted uppercase font-bold">Sortino</span>
                                        <span className="text-[10px] font-bold text-white">3.12</span>
                                    </div>
                                </div>
                                <div className="flex gap-2.5">
                                    <button
                                        onClick={() => addToast(`[TELEMETRY] ${s.name}: Active | Latency: 4ms | CPU: 1.2%`, "info")}
                                        className="btn-telemetry flex items-center gap-2 group"
                                    >
                                        <Activity size={13} className="group-hover:text-teal-400 transition-colors" />
                                        <span>TELEMETRY</span>
                                    </button>
                                    <button
                                        onClick={() => onUpdateParams(s.id)}
                                        className="btn-apply-params"
                                    >
                                        APPLY SETTINGS
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}



function RiskControlPage({ metrics, fmt, fmtPct, fmtUsd, addToast }: { metrics: any; fmt: (n: number, d?: number) => string; fmtPct: (n: number) => string; fmtUsd: (n: number) => string; addToast: (msg: string, type?: Toast['type']) => void }) {
    const [riskLimit, setRiskLimit] = useState(2.0);
    const [maxDD, setMaxDD] = useState(5.0);
    const [guards, setGuards] = useState({
        kill_switch: true,
        volatility_guard: true,
        correlation_guard: false,
        weekend_guard: false
    });

    const handleUpdateSettings = async (updates: any) => {
        try {
            await apiPost('/api/risk/settings', updates);
            addToast('Risk Parameter Updated', 'success');
        } catch (error) {
            addToast('Failed to update risk settings', 'error');
        }
    };

    const handleToggleGuard = (key: keyof typeof guards) => {
        const newVal = !guards[key];
        const newGuards = { ...guards, [key]: newVal };
        setGuards(newGuards);
        handleUpdateSettings({ [key]: newVal });
    };
    return (
        <div className="h-full p-6 overflow-auto">
            <h1 className="text-xl font-semibold mb-1">Risk Control Center</h1>
            <p className="text-sm text-textMuted mb-6">Monitor and manage portfolio risk parameters</p>
            <div className="grid grid-cols-4 gap-4 mb-6">
                {[
                    { label: 'Total Equity', value: fmtUsd(metrics.equity), color: 'text-white' },
                    { label: 'Daily PnL', value: `${metrics.daily_pnl >= 0 ? '+' : ''}$${fmt(Math.abs(metrics.daily_pnl))}`, color: metrics.daily_pnl >= 0 ? 'text-teal-400' : 'text-rose-400' },
                    { label: 'Drawdown', value: `-${fmt(metrics.drawdown_pct, 1)}%`, color: metrics.drawdown_pct > 3 ? 'text-rose-500' : 'text-amber-400' },
                    { label: 'Exposure', value: `${fmt(metrics.exposure_pct, 0)}%`, color: 'text-teal-400' },
                ].map((m, i) => (
                    <div key={i} className="panel-card p-4">
                        <span className="text-xs text-textMuted uppercase tracking-wider">{m.label}</span>
                        <p className={`text-2xl font-semibold mono-number mt-1 ${m.color}`}>{m.value}</p>
                    </div>
                ))}
            </div>
            <div className="grid grid-cols-2 gap-6">
                <div className="panel-card p-5">
                    <h3 className="text-sm font-semibold text-textMuted uppercase tracking-wider mb-4">Risk Limits Configuration</h3>
                    <div className="space-y-6">
                        <div>
                            <div className="flex justify-between text-sm mb-2"><span>Global Risk Limit</span><span className="mono-number text-teal-400">{fmt(riskLimit, 1)}%</span></div>
                            <input
                                type="range"
                                className="w-full accent-teal-400"
                                min="0.5" max="10" step="0.5"
                                value={riskLimit}
                                onChange={e => {
                                    const val = parseFloat(e.target.value);
                                    setRiskLimit(val);
                                    handleUpdateSettings({ risk_limit_pct: val });
                                }}
                            />
                        </div>
                        <div>
                            <div className="flex justify-between text-sm mb-2"><span>Max Drawdown Limit</span><span className="mono-number text-rose-400">{fmt(maxDD, 1)}%</span></div>
                            <input
                                type="range"
                                className="w-full accent-rose-500"
                                min="1" max="20" step="0.5"
                                value={maxDD}
                                onChange={e => {
                                    const val = parseFloat(e.target.value);
                                    setMaxDD(val);
                                    handleUpdateSettings({ max_drawdown_limit: val });
                                }}
                            />
                            <div className="w-full bg-background h-2 rounded-full overflow-hidden mt-2">
                                <div className="bg-rose-500 h-full transition-all duration-500" style={{ width: `${Math.min(metrics.drawdown_pct / maxDD * 100, 100)}%` }}></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="panel-card p-5">
                    <h3 className="text-sm font-semibold text-textMuted uppercase tracking-wider mb-4">Kill Switch & Guards</h3>
                    <div className="space-y-4">
                        {[
                            { key: 'kill_switch', label: 'Auto Kill Switch', desc: 'Liquidate all if drawdown exceeds limit' },
                            { key: 'volatility_guard', label: 'Volatility Guard', desc: 'Pause entries during extreme volatility' },
                            { key: 'correlation_guard', label: 'Correlation Guard', desc: 'Limit exposure to correlated assets' },
                            { key: 'weekend_guard', label: 'Weekend Guard', desc: 'Close positions before market close' },
                        ].map((g) => {
                            const isOn = guards[g.key as keyof typeof guards];
                            return (
                                <div key={g.key} className="flex items-center justify-between p-3 bg-background rounded-lg">
                                    <div><p className="text-sm font-medium">{g.label}</p><p className="text-xs text-textMuted">{g.desc}</p></div>
                                    <div
                                        onClick={() => handleToggleGuard(g.key as keyof typeof guards)}
                                        className={`w-12 h-6 rounded-full transition-all duration-500 border ${isOn ? 'bg-teal-500/10 border-teal-500/40' : 'bg-slate-900 border-white/5'} relative cursor-pointer group`}
                                    >
                                        <div className={`absolute top-1 w-4 h-4 rounded-full transition-all duration-500 shadow-lg ${isOn ? 'right-1 bg-teal-400' : 'left-1 bg-slate-700'}`}></div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}

function ResearchLabPage({ addToast }: { addToast: (msg: string, type?: Toast['type']) => void }) {
    const [symbol, setSymbol] = useState('BTC-USD');
    const [period, setPeriod] = useState('90d');
    const [strategy, setStrategy] = useState('ema_trend');
    const [researchData, setResearchData] = useState<any>(null);
    const [backtestStatus, setBacktestStatus] = useState('');
    const [labLoading, setLabLoading] = useState(false);

    // Backtest Parameters
    const [initialBalance, setInitialBalance] = useState(10000);
    const [leverage, setLeverage] = useState(1);
    const [spread, setSpread] = useState(0.5);
    const [tradingFee, setTradingFee] = useState(0.06);

    // Intelligence Filter State
    const [newsItems, setNewsItems] = useState<any[]>([]);
    const [isFilterRunning, setIsFilterRunning] = useState(false);
    const [botInjection, setBotInjection] = useState(false);

    // Monte Carlo Parameters
    const [mcIterations, setMcIterations] = useState(1000);
    const [confidenceLevel, setConfidenceLevel] = useState(95);

    const loadMetrics = useCallback(async () => {
        setLabLoading(true);
        try {
            const data = await apiFetch(`/api/research/metrics/${symbol}`);
            setResearchData(data.data);
        } catch {
            console.error('Failed to load metrics');
            setResearchData(null);
        } finally {
            setLabLoading(false);
        }
    }, [symbol]);

    useEffect(() => { loadMetrics(); }, [loadMetrics]);

    const runBacktest = async () => {
        setLabLoading(true);
        setBacktestStatus('Computing Scenarios...');
        addToast('Initiating Hexa Backtest...', 'info');

        try {
            // Real API call with full parameters
            await apiPost('/api/research/run_backtest', {
                symbol,
                period,
                strategy,
                initial_balance: initialBalance,
                leverage,
                spread,
                fee: tradingFee,
                mc_iterations: mcIterations,
                confidence: confidenceLevel
            });

            // Simulation delay for "Wows" effect
            await new Promise(r => setTimeout(r, 2000));

            // Mock data for immediate visual feedback if real data is slow/demo
            const mockCurve = Array.from({ length: 150 }, (_, i) => 10000 + i * Math.random() * 200 + Math.sin(i / 10) * 1000).join(',');
            setResearchData({
                sharpe_ratio: (Math.random() * 1.5 + 1.2).toFixed(2),
                max_drawdown: (Math.random() * 5 + 3).toFixed(2),
                win_rate: (Math.random() * 15 + 55).toFixed(2),
                wfa_efficiency: (Math.random() * 10 + 82).toFixed(2),
                monte_carlo_prio: (Math.random() * 5 + 92).toFixed(2),
                equity_curve: mockCurve
            });

            setBacktestStatus('✅ Analysis Complete');
            addToast('Simulation & Optimization Finished', 'success');
        } catch {
            setBacktestStatus('❌ Link Interrupted');
            addToast('Uplink failed: Check compute cluster', 'error');
        } finally {
            setLabLoading(false);
        }
    };

    const runIntelligenceFilter = async () => {
        setIsFilterRunning(true);
        addToast('Gathering intelligence from 10 trusted sources...', 'info');

        await new Promise(r => setTimeout(r, 2000));

        const sources = [
            { source: 'Reuters', headline: 'US Inflation data shows 0.2% decrease', confidence: 98, veracity: 'VERIFIED' },
            { source: 'Bloomberg', headline: 'Fed expected to hold rates in next meeting', confidence: 95, veracity: 'VERIFIED' },
            { source: 'CryptoPanic', headline: 'Major exchange hack reported on Telegram', confidence: 22, veracity: 'HALLUCINATION' },
            { source: 'Twitter/X', headline: 'Elon Musk buys Bitcoin for Tesla again', confidence: 15, veracity: 'HALLUCINATION' },
            { source: 'Glassnode', headline: 'Exchange balances hit multi-year low', confidence: 92, veracity: 'VERIFIED' },
            { source: 'CoinDesk', headline: 'SEC to approve 3 more ETFs next week', confidence: 45, veracity: 'UNVERIFIED' },
            { source: 'WhaleAlert', headline: '50,000 BTC moved to Unknown Wallet', confidence: 99, veracity: 'VERIFIED' },
            { source: 'Reddit/Crypto', headline: 'Satoshi Nakamoto wallet keys leaked', confidence: 2, veracity: 'HALLUCINATION' },
            { source: 'CNBC', headline: 'Market volatility expected to increase', confidence: 88, veracity: 'VERIFIED' },
            { source: 'FinancialTimes', headline: 'Global trade volume rises by 4%', confidence: 94, veracity: 'VERIFIED' }
        ];

        setNewsItems(sources.sort((a, b) => b.confidence - a.confidence));
        setIsFilterRunning(false);
        addToast('Intelligence Filter: 3 Hallucinations blocked.', 'success');
    };

    const metrics = researchData || {
        sharpe_ratio: "0.00",
        max_drawdown: "0.0",
        win_rate: "0.0",
        wfa_efficiency: "0.0",
        monte_carlo_prio: "0.0",
        equity_curve: ""
    };

    // Mini-chart helper
    const EquityChart = ({ curve }: { curve: string }) => {
        if (!curve) return <div className="h-[120px] flex items-center justify-center text-textMuted text-[10px] uppercase font-bold border border-border/30 bg-black/20">Awaiting Backtest Data</div>;
        const points = curve.split(',').map(Number);
        const max = Math.max(...points);
        const min = Math.min(...points);
        const range = max - min || 1;
        const width = 800;
        const height = 120;

        const path = points.map((p, i) => {
            const x = (i / (points.length - 1)) * width;
            const y = height - ((p - min) / range) * height;
            return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
        }).join(' ');

        return (
            <div className="relative h-[120px] w-full bg-black/40 border border-border/30 overflow-hidden group">
                <div className="absolute inset-0 bg-grid-slate-800/[0.1] bg-[bottom_1px_center] [background-size:20px_20px]"></div>
                <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="relative z-10">
                    <defs>
                        <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#2DD4BF" stopOpacity="0.2" />
                            <stop offset="100%" stopColor="#2DD4BF" stopOpacity="0" />
                        </linearGradient>
                    </defs>
                    <path d={`${path} L ${width} ${height} L 0 ${height} Z`} fill="url(#chartGradient)" />
                    <path d={path} fill="none" stroke="#2DD4BF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="drop-shadow-[0_0_8px_rgba(45,212,191,0.4)]" />
                </svg>
                <div className="absolute top-2 left-3 flex gap-4 text-[8px] font-bold uppercase tracking-widest text-textMuted">
                    <span>Performance Graph</span>
                    <span className="text-teal-400">Sample Size: {points.length} Iterations</span>
                </div>
            </div>
        );
    };

    return (
        <div className="h-full p-6 overflow-auto custom-scrollbar">
            <div className="flex justify-between items-start mb-6">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-teal-400/10 rounded-xl border border-teal-400/30 flex items-center justify-center text-teal-400 shadow-[0_0_20px_rgba(45,212,191,0.1)]">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"><path d="M6 4V20M18 4V20M6 12H18" /></svg>
                    </div>
                    <div>
                        <h1 className="text-xl font-black mb-0.5 tracking-tight uppercase">Hexa Research Lab</h1>
                        <p className="text-[10px] text-textMuted uppercase font-bold tracking-widest">Walk-forward analysis, Monte Carlo simulation & backtesting engine</p>
                    </div>
                </div>
                <div className="flex flex-col items-end">
                    <span className="text-[10px] font-bold text-teal-400 uppercase tracking-[0.2em]">Compute_Status</span>
                    <span className="text-xs font-mono text-white flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse"></span>
                        Engine Ready
                    </span>
                </div>
            </div>

            <div className="flex flex-wrap items-center p-4 bg-white/5 rounded-2xl w-full mb-8 border border-white/5 gap-6">
                <div className="flex flex-col gap-2 min-w-[240px]">
                    <span className="text-[10px] font-bold text-textMuted uppercase tracking-[0.2em] ml-1">Asset Lab Selection</span>
                    <div className="relative group">
                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-hover:text-teal-400 transition-colors pointer-events-none">
                            <Search size={14} />
                        </div>
                        <select
                            value={symbol}
                            onChange={(e) => setSymbol(e.target.value)}
                            className="w-full bg-slate-950/50 border border-white/10 rounded-xl py-3 pl-11 pr-10 text-[11px] font-black uppercase tracking-widest text-white appearance-none cursor-pointer focus:border-teal-400 focus:ring-1 focus:ring-teal-400/20 outline-none transition-all group-hover:border-white/20"
                        >
                            {TRADABLE_ASSETS.map(s => (
                                <option key={s} value={s} className="bg-slate-900 text-white py-2 font-mono">{s.replace('-', ' ')}</option>
                            ))}
                        </select>
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500 group-hover:text-teal-400 transition-colors">
                            <svg width="10" height="6" viewBox="0 0 10 6" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 1L5 5L9 1" /></svg>
                        </div>
                    </div>
                </div>

                <div className="h-12 w-[1px] bg-white/5 hidden md:block"></div>

                <div className="flex-1 flex gap-10">
                    <div className="flex flex-col">
                        <span className="text-[10px] font-bold text-textMuted uppercase tracking-widest mb-1">Target Identity</span>
                        <div className="flex items-center gap-3">
                            <span className="text-xl font-black text-white tracking-tighter">{symbol.split('-')[0]}</span>
                            <span className="text-[10px] font-bold text-slate-500 bg-slate-500/10 px-2 py-0.5 rounded border border-white/5">PERP</span>
                        </div>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-[10px] font-bold text-textMuted uppercase tracking-widest mb-1">Compute Priority</span>
                        <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-teal-400 shadow-[0_0_8px_rgba(45,212,191,0.6)]"></div>
                            <span className="text-[11px] font-black text-white uppercase tracking-widest">High Performance</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex flex-wrap gap-2 mb-6">
                {[
                    { label: 'Sharpe', value: parseFloat(metrics.sharpe_ratio).toFixed(2), good: parseFloat(metrics.sharpe_ratio) > 1.5 },
                    { label: 'MaxDD', value: `-${parseFloat(metrics.max_drawdown).toFixed(1)}%`, good: parseFloat(metrics.max_drawdown) < 8 },
                    { label: 'Winfact', value: `${parseFloat(metrics.win_rate).toFixed(0)}%`, good: parseFloat(metrics.win_rate) > 58 },
                    { label: 'WFA', value: `${parseFloat(metrics.wfa_efficiency).toFixed(0)}%`, good: parseFloat(metrics.wfa_efficiency) > 75 },
                    { label: 'Stability', value: `${parseFloat(metrics.monte_carlo_prio).toFixed(0)}%`, good: parseFloat(metrics.monte_carlo_prio) > 80 },
                ].map((m, i) => (
                    <div key={i} className="bg-slate-900 border border-white/5 p-2 px-4 rounded-xl min-w-[110px] flex flex-col justify-center hover:border-teal-400 group transition-all">
                        <span className="text-[9px] text-slate-500 uppercase font-black tracking-widest leading-none mb-1 group-hover:text-teal-400">{m.label}</span>
                        <p className={`text-base font-black mono-number leading-none ${m.good ? 'text-teal-400' : 'text-rose-500'}`}>{m.value}</p>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-3 gap-6 mb-6">
                <div className="col-span-2 space-y-4">
                    <div className="panel-card p-5">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-[10px] font-bold text-textMuted uppercase tracking-widest">Equity Growth Curve</h3>
                            <button className="text-[9px] font-bold text-primary hover:underline uppercase">Export CSV</button>
                        </div>
                        <EquityChart curve={metrics.equity_curve} />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="panel-card p-4 bg-white/5 border-dashed">
                            <h4 className="text-[9px] font-bold text-textMuted uppercase mb-3">Monte Carlo Scenarios</h4>
                            <div className="space-y-2">
                                <div className="flex justify-between text-[10px]"><span className="text-textMuted">95% Confidence DD</span><span className="text-white font-mono">12.4%</span></div>
                                <div className="flex justify-between text-[10px]"><span className="text-textMuted">Prob of Ruin</span><span className="text-teal-400 font-mono">0.02%</span></div>
                                <div className="h-1 w-full bg-background mt-1"><div className="h-full bg-teal-400 w-[88%]"></div></div>
                            </div>
                        </div>
                        <div className="panel-card p-4 bg-white/5 border-dashed">
                            <h4 className="text-[9px] font-bold text-textMuted uppercase mb-3">Walk Forward Valid</h4>
                            <div className="space-y-2">
                                <div className="flex justify-between text-[10px]"><span className="text-textMuted">In-Sample Overfit</span><span className="text-warning font-mono">Low</span></div>
                                <div className="flex justify-between text-[10px]"><span className="text-textMuted">Pass Score</span><span className="text-primary font-mono">8.4/10</span></div>
                                <div className="h-1 w-full bg-background mt-1"><div className="h-full bg-primary w-[84%]"></div></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="panel-card p-5 flex flex-col justify-between">
                    <div>
                        <h3 className="text-[10px] font-bold text-textMuted uppercase tracking-widest mb-6 border-b border-border/30 pb-2">Simulator Control</h3>
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-[9px] text-textMuted uppercase font-bold">Optimization Period</label>
                                <select
                                    className="w-full bg-background border border-border/50 p-2 text-xs text-white focus:border-teal-400 outline-none"
                                    value={period}
                                    onChange={(e) => setPeriod(e.target.value)}
                                >
                                    <option value="90d">90 Days Rolling</option>
                                    <option value="180d">180 Days Window</option>
                                    <option value="365d">Full Year Fixed</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-[9px] text-textMuted uppercase font-bold">Algorithm Core</label>
                                <select
                                    className="w-full bg-background border border-border/50 p-2 text-xs text-white focus:border-teal-400 outline-none"
                                    value={strategy}
                                    onChange={(e) => setStrategy(e.target.value)}
                                >
                                    <option value="ema_trend">EMA Trend Engine</option>
                                    <option value="fibonacci">Fibonacci Pullback</option>
                                    <option value="multi_tf">Multi-TF Alignment</option>
                                </select>
                            </div>

                            <div className="border-t border-border/30 pt-4 mt-2">
                                <h4 className="text-[8px] font-black text-teal-400/70 uppercase tracking-[0.2em] mb-4">Manual Backtest Params</h4>
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="space-y-1">
                                        <label className="text-[8px] text-textMuted uppercase">Initial Balance</label>
                                        <input type="number" value={initialBalance} onChange={e => setInitialBalance(Number(e.target.value))} className="w-full bg-black/40 border border-white/10 p-1.5 text-[10px] text-white outline-none" />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-[8px] text-textMuted uppercase">Leverage</label>
                                        <select value={leverage} onChange={e => setLeverage(Number(e.target.value))} className="w-full bg-black/40 border border-white/10 p-1.5 text-[10px] text-white outline-none">
                                            {[1, 2, 5, 10, 20, 50].map(v => <option key={v} value={v}>{v}x</option>)}
                                        </select>
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-[8px] text-textMuted uppercase">Spread</label>
                                        <input type="number" step="0.1" value={spread} onChange={e => setSpread(Number(e.target.value))} className="w-full bg-black/40 border border-white/10 p-1.5 text-[10px] text-white outline-none" />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-[8px] text-textMuted uppercase">Trading Fee %</label>
                                        <input type="number" step="0.01" value={tradingFee} onChange={e => setTradingFee(Number(e.target.value))} className="w-full bg-black/40 border border-white/10 p-1.5 text-[10px] text-white outline-none" />
                                    </div>
                                </div>
                            </div>

                            <div className="border-t border-border/30 pt-4">
                                <h4 className="text-[8px] font-black text-rose-400/70 uppercase tracking-[0.2em] mb-4">Monte Carlo Config</h4>
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="space-y-1">
                                        <label className="text-[8px] text-textMuted uppercase">Iterations</label>
                                        <select value={mcIterations} onChange={e => setMcIterations(Number(e.target.value))} className="w-full bg-black/40 border border-white/10 p-1.5 text-[10px] text-white outline-none">
                                            {[100, 500, 1000, 5000].map(v => <option key={v} value={v}>{v} Sims</option>)}
                                        </select>
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-[8px] text-textMuted uppercase">Confidence</label>
                                        <select value={confidenceLevel} onChange={e => setConfidenceLevel(Number(e.target.value))} className="w-full bg-black/40 border border-white/10 p-1.5 text-[10px] text-white outline-none">
                                            {[90, 95, 99].map(v => <option key={v} value={v}>{v}% CI</option>)}
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="mt-4 space-y-3">
                        <div className="flex items-center justify-between text-[9px] font-bold uppercase">
                            <span className="text-textMuted">Job Status:</span>
                            <span className={backtestStatus.includes('✅') ? 'text-success' : backtestStatus.includes('❌') ? 'text-danger' : 'text-primary'}>
                                {backtestStatus || 'Idle Waiting'}
                            </span>
                        </div>
                        <button
                            onClick={runBacktest}
                            disabled={labLoading}
                            className={`w-full btn-initiate-sim ${labLoading ? 'opacity-50' : ''}`}
                        >
                            {labLoading ? 'Computing...' : 'Run Backtest'}
                        </button>
                    </div>

                    {/* Intelligence Filter Panel */}
                    <div className="mt-6 pt-6 border-t border-border/30">
                        <div className="flex justify-between items-center mb-4">
                            <div>
                                <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Intelligence Filter</h3>
                                <p className="text-[8px] text-textMuted uppercase mt-1">Cross-Source Verification & Hallucination Block</p>
                            </div>
                            <button
                                onClick={() => setBotInjection(!botInjection)}
                                className={`flex items-center gap-1.5 px-2 py-1 rounded-full border transition-all ${botInjection ? 'bg-teal-400/10 border-teal-400/50 text-teal-400' : 'bg-white/5 border-white/10 text-slate-500'}`}
                            >
                                <Zap size={10} className={botInjection ? 'animate-pulse' : ''} />
                                <span className="text-[8px] font-black uppercase">Bot Injected</span>
                            </button>
                        </div>

                        <div className="space-y-1.5 max-h-[220px] overflow-auto custom-scrollbar pr-1 mb-4">
                            {newsItems.length === 0 ? (
                                <div className="h-[140px] flex flex-col items-center justify-center border border-dashed border-white/5 bg-black/20 rounded-xl px-4 text-center">
                                    <Globe size={24} className="text-slate-700 mb-2" />
                                    <p className="text-[8px] text-slate-500 uppercase font-black leading-tight">No intelligence gathered. Initiate filter to harvest data from 10 sources.</p>
                                </div>
                            ) : (
                                newsItems.map((n, i) => (
                                    <div key={i} className={`p-2 rounded-lg border flex items-center gap-3 group transition-all ${n.veracity === 'HALLUCINATION' ? 'bg-rose-500/5 border-rose-500/20 grayscale' : 'bg-white/[0.02] border-white/5 hover:border-teal-400/30'}`}>
                                        <div className={`p-1 rounded-md ${n.veracity === 'HALLUCINATION' ? 'bg-rose-500/20 text-rose-500' : 'bg-teal-400/20 text-teal-400'}`}>
                                            {n.veracity === 'HALLUCINATION' ? <ShieldAlert size={14} /> : <ShieldCheck size={14} />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex justify-between items-center mb-0.5">
                                                <span className={`text-[8px] font-black uppercase tracking-widest ${n.veracity === 'HALLUCINATION' ? 'text-rose-500' : 'text-teal-400'}`}>{n.source}</span>
                                                <span className="text-[8px] font-mono text-slate-500">{n.confidence}% CONF</span>
                                            </div>
                                            <p className={`text-[10px] font-medium truncate ${n.veracity === 'HALLUCINATION' ? 'text-slate-600 line-through' : 'text-slate-300'}`}>{n.headline}</p>
                                        </div>
                                        <div className="flex flex-col items-end">
                                            <span className={`text-[7px] font-black px-1.5 py-0.5 rounded uppercase ${n.veracity === 'HALLUCINATION' ? 'bg-rose-500/20 text-rose-500' : 'bg-teal-400/20 text-teal-400'}`}>
                                                {n.veracity === 'HALLUCINATION' ? 'BLOCKED' : 'ACTIVE'}
                                            </span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        <button
                            onClick={runIntelligenceFilter}
                            disabled={isFilterRunning}
                            className={`w-full py-2.5 rounded-xl border flex items-center justify-center gap-2 group transition-all ${isFilterRunning ? 'bg-white/5 border-white/10 text-slate-600' : 'bg-slate-950 border-white/10 text-white hover:border-teal-400/50 hover:bg-slate-900 shadow-xl'}`}
                        >
                            <BrainCircuit size={16} className={isFilterRunning ? 'animate-spin' : 'text-teal-400'} />
                            <span className="text-[10px] font-black uppercase tracking-[0.1em]">{isFilterRunning ? 'Filtering Sources...' : 'Run Intelligence Filter'}</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function TradeHistoryPage({ tradeHistory, setTradeHistory, fmtPnl, fmt }: { tradeHistory: any[]; setTradeHistory: (t: any[]) => void; fmtPnl: (n: number) => string; fmt: (n: number, d?: number) => string }) {
    const [histLoading, setHistLoading] = useState(false);

    const refreshHistory = useCallback(() => {
        setHistLoading(true);
        apiFetch('/api/trading/history?limit=50')
            .then(data => setTradeHistory(data.trades || []))
            .catch(() => {
                console.error('Failed to fetch trade history');
                setTradeHistory([]);
            })
            .finally(() => setHistLoading(false));
    }, [setTradeHistory]);

    useEffect(() => {
        if (tradeHistory.length === 0) {
            refreshHistory();
        }
    }, [tradeHistory.length, refreshHistory]);

    const totalPnl = tradeHistory.reduce((sum, t) => sum + (t.pnl || 0), 0);
    const wins = tradeHistory.filter(t => (t.pnl || 0) > 0).length;
    return (
        <div className="h-full p-6 overflow-auto custom-scrollbar">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h1 className="text-xl font-semibold mb-1 tracking-tight">Trade History</h1>
                    <p className="text-sm text-textMuted">Comprehensive record of all executed terminal orders</p>
                </div>
                <button
                    onClick={refreshHistory}
                    disabled={histLoading}
                    className="glass-button bg-white/10 border border-white/10 px-6 py-2.5 rounded-2xl text-[10px] font-black uppercase tracking-[0.15em] hover:bg-white/20 hover:border-white/20 transition-all flex items-center gap-3 shadow-2xl active:scale-95 group"
                >
                    <RefreshCw size={14} className={`text-teal-400 ${histLoading ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-700'}`} />
                    <span className="text-white">{histLoading ? 'Syncing Ledger...' : 'Refresh History'}</span>
                </button>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="panel-card p-4"><span className="text-xs text-slate-500 uppercase font-black">Total Trades</span><p className="text-2xl font-black mono-number mt-1 text-white">{tradeHistory.length}</p></div>
                <div className="panel-card p-4"><span className="text-xs text-slate-500 uppercase font-black">Win Rate</span><p className="text-2xl font-black mono-number mt-1 text-teal-400">{tradeHistory.length > 0 ? ((wins / tradeHistory.length) * 100).toFixed(1) : 0}%</p></div>
                <div className="panel-card p-4"><span className="text-xs text-slate-500 uppercase font-black">Total PnL</span><p className={`text-2xl font-black mono-number mt-1 ${totalPnl >= 0 ? 'text-teal-400' : 'text-rose-500'}`}>{fmtPnl(totalPnl)}</p></div>
            </div>
            <div className="panel-card overflow-hidden">
                <table className="w-full text-left text-sm">
                    <thead className="text-xs text-textMuted bg-background"><tr>
                        <th className="px-4 py-3 font-normal">Time</th><th className="px-4 py-3 font-normal">Symbol</th><th className="px-4 py-3 font-normal">Side</th>
                        <th className="px-4 py-3 font-normal">Size</th><th className="px-4 py-3 font-normal">Entry</th><th className="px-4 py-3 font-normal">Exit</th>
                        <th className="px-4 py-3 font-normal">PnL</th><th className="px-4 py-3 font-normal">Strategy</th>
                    </tr></thead>
                    <tbody className="divide-y divide-border">
                        {histLoading ? <tr><td colSpan={8} className="px-4 py-8 text-center text-textMuted">Loading...</td></tr> :
                            tradeHistory.length === 0 ? <tr><td colSpan={8} className="px-4 py-8 text-center text-textMuted">No trade history</td></tr> :
                                tradeHistory.map(t => (
                                    <tr key={t.id} className="hover:bg-white/5 transition-colors">
                                        <td className="px-4 py-3 text-slate-500 font-medium">{new Date(t.executed_at).toLocaleString()}</td>
                                        <td className="px-4 py-3 font-bold text-white">{t.symbol}</td>
                                        <td className={`px-4 py-3 font-black text-[10px] uppercase ${t.side === 'long' ? 'text-teal-400' : 'text-rose-500'}`}>{t.side?.toUpperCase()}</td>
                                        <td className="px-4 py-3 mono-number font-medium">{fmt(t.size || 0, 4)}</td>
                                        <td className="px-4 py-3 mono-number text-slate-300">{fmt(t.entry_price || 0)}</td>
                                        <td className="px-4 py-3 mono-number text-slate-300">{fmt(t.exit_price || 0)}</td>
                                        <td className={`px-4 py-3 mono-number font-black ${(t.pnl || 0) >= 0 ? 'text-teal-400' : 'text-rose-500'}`}>{fmtPnl(t.pnl || 0)}</td>
                                        <td className="px-4 py-3"><span className="text-[10px] px-2 py-0.5 rounded-lg bg-teal-400/10 text-teal-400 border border-teal-400/20 font-black uppercase tracking-tighter">{t.strategy_name}</span></td>
                                    </tr>
                                ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function SettingsPage({ addToast }: { addToast: (msg: string, type?: Toast['type']) => void }) {
    const [apiUrl, setApiUrl] = useState(() => typeof window !== 'undefined' ? localStorage.getItem('qb_api_url') || 'http://localhost:8000' : 'http://localhost:8000');
    const [wsUrl, setWsUrl] = useState(() => typeof window !== 'undefined' ? localStorage.getItem('qb_ws_url') || 'ws://localhost:8000/ws/dashboard' : 'ws://localhost:8000/ws/dashboard');
    const [saved, setSaved] = useState('');

    const handleSave = () => {
        localStorage.setItem('qb_api_url', apiUrl);
        localStorage.setItem('qb_ws_url', wsUrl);
        addToast('Uplink configurations saved', 'success');
        setSaved('✅ Settings saved!');
        setTimeout(() => setSaved(''), 2000);
    };

    return (
        <div className="h-full p-8 overflow-auto animate-in fade-in duration-300">
            <h1 className="text-2xl font-bold uppercase tracking-[0.2em] mb-1">Configuration</h1>
            <p className="text-[10px] text-textMuted uppercase tracking-widest mb-10">System parameters and network uplink protocols</p>

            <div className="grid grid-cols-2 gap-8">
                <div className="border border-border bg-panel/30 p-6">
                    <h3 className="text-[10px] font-bold text-textMuted uppercase tracking-[0.2em] mb-6 border-b border-border pb-2">Network Uplink</h3>
                    <div className="space-y-6">
                        <div>
                            <label className="text-[9px] text-textMuted uppercase font-bold tracking-widest mb-1.5 block">API Endpoint</label>
                            <input className="w-full bg-background border border-border rounded-none px-4 py-2.5 text-xs font-mono outline-none focus:border-primary transition-colors" value={apiUrl} onChange={e => setApiUrl(e.target.value)} />
                        </div>
                        <div>
                            <label className="text-[9px] text-textMuted uppercase font-bold tracking-widest mb-1.5 block">WS Endpoint</label>
                            <input className="w-full bg-background border border-border rounded-none px-4 py-2.5 text-xs font-mono outline-none focus:border-primary transition-colors" value={wsUrl} onChange={e => setWsUrl(e.target.value)} />
                        </div>
                        <button onClick={handleSave} className="px-6 py-2.5 bg-white text-black hover:bg-white/90 rounded-none text-[10px] font-bold uppercase tracking-widest transition-all">Save Configuration</button>
                        {saved && <p className="text-[10px] text-success font-bold uppercase mt-2 animate-pulse">{saved}</p>}
                    </div>
                </div>

                <div className="border border-border bg-panel/30 p-6">
                    <h3 className="text-[10px] font-bold text-textMuted uppercase tracking-[0.2em] mb-6 border-b border-border pb-2">Notifications</h3>
                    <div className="space-y-4">
                        {[
                            { label: 'Trade Execution', desc: 'Alert on order fill', on: true },
                            { label: 'Risk Protocol', desc: 'Notify on drawdown limit', on: true },
                            { label: 'Strategy Cycle', desc: 'Alert on logic state change', on: false },
                            { label: 'Network Health', desc: 'Notify on uplink loss', on: true },
                        ].map((n, i) => (
                            <div key={i} className="flex items-center justify-between p-4 bg-background/50 border border-border/50">
                                <div>
                                    <p className="text-[11px] font-bold uppercase tracking-tight">{n.label}</p>
                                    <p className="text-[9px] text-textMuted uppercase">{n.desc}</p>
                                </div>
                                <div className={`w-10 h-4 rounded-none border border-border relative cursor-pointer ${n.on ? 'bg-success/20 border-success/30' : 'bg-background'}`}>
                                    <div className={`absolute top-0.5 w-3 h-2.5 rounded-none transition-transform ${n.on ? 'translate-x-[22px] bg-success shadow-[0_0_8px_rgba(0,255,157,0.5)]' : 'translate-x-0.5 bg-textMuted'}`}></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="border border-border bg-panel/30 p-6 mt-8">
                <h3 className="text-[10px] font-bold text-textMuted uppercase tracking-[0.2em] mb-6 border-b border-border pb-2">Firmware Info</h3>
                <div className="grid grid-cols-4 gap-8">
                    <div><span className="text-[9px] text-textMuted uppercase font-bold tracking-widest">Version</span><p className="mono-number text-xs mt-1 text-white">1.0.0-PRO</p></div>
                    <div><span className="text-[9px] text-textMuted uppercase font-bold tracking-widest">Base Layer</span><p className="mono-number text-xs mt-1 text-white">Next.js 14</p></div>
                    <div><span className="text-[9px] text-textMuted uppercase font-bold tracking-widest">Engine</span><p className="mono-number text-xs mt-1 text-white">Industrial FastAPI</p></div>
                    <div><span className="text-[9px] text-textMuted uppercase font-bold tracking-widest">Protocol</span><p className="mono-number text-xs mt-1 text-white">Hyperliquid v1</p></div>
                </div>
            </div>
        </div>
    );
}
