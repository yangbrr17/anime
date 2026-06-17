"""
第二题原始代码 (含多处 bug, 仅用于诊断, 请勿直接使用)
来源: 实习生用 AI 生成的期货 CTA 策略回测代码
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class CTA_Backtester:
    def __init__(self, data_df, initial_capital=1_000_000):
        self.data = data_df  # columns: date, open, high, low, close, volume, contract
        self.capital = initial_capital
        self.position = 0
        self.trades = []
        self.daily_pnl = []

    def generate_signal(self, window=20):
        # 基于移动平均生成交易信号
        self.data['ma'] = self.data['close'].rolling(window=window).mean()
        self.data['signal'] = np.where(self.data['close'] > self.data['ma'], 1, -1)
        # 信号在当天收盘后生成, 第二天开盘执行
        self.data['signal'] = self.data['signal'].shift(-1)  # 前移, 确保及时执行
        return self.data

    def run_backtest(self):
        self.generate_signal()
        for i in range(len(self.data)):
            row = self.data.iloc[i]
            date = row['date']
            # 计算当日 PNL (基于收盘价)
            if self.position != 0:
                pnl = self.position * (row['close'] - self.prev_close) * 10  # 每点 10 元
                self.capital += pnl
                self.daily_pnl.append({'date': date, 'pnl': pnl, 'capital': self.capital})
            # 执行信号
            if row['signal'] == 1 and self.position <= 0:
                # 开多或平空开多
                self.position = 1
                self.trades.append({'date': date, 'action': 'buy', 'price': row['close']})
            elif row['signal'] == -1 and self.position >= 0:
                # 开空或平多开空
                self.position = -1
                self.trades.append({'date': date, 'action': 'sell', 'price': row['close']})
            self.prev_close = row['close']
        return self._calculate_metrics()

    def _calculate_metrics(self):
        pnl_series = pd.DataFrame(self.daily_pnl)['pnl']
        total_return = (self.capital - 1_000_000) / 1_000_000
        sharpe = pnl_series.mean() / pnl_series.std() * np.sqrt(252)
        max_drawdown = (pnl_series.cumsum().cummax() - pnl_series.cumsum()).max()
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'num_trades': len(self.trades),
            'final_capital': self.capital
        }


# 模拟数据生成 (含合约切换)
np.random.seed(42)
dates = pd.date_range('2026-01-01', '2026-04-30', freq='B')
# 模拟期货合约切换: 每季度切换
contracts = ['CU2603'] * 40 + ['CU2606'] * 40 + ['CU2609'] * 20
data = pd.DataFrame({
    'date': dates[:len(contracts)],
    'open': 70000 + np.random.randn(len(contracts)) * 500,
    'high': 70500 + np.random.randn(len(contracts)) * 500,
    'low': 69500 + np.random.randn(len(contracts)) * 500,
    'close': 70000 + np.random.randn(len(contracts)).cumsum() * 300,
    'volume': np.random.randint(10000, 50000, len(contracts)),
    'contract': contracts
})

bt = CTA_Backtester(data)
result = bt.run_backtest()
print(result)
