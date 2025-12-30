import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns

class TechnicalIndicator:
    """Calculates various technical indicators for stock data."""

    def __init__(self):
        pass

    @staticmethod
    def sma(series, period):
        return series.rolling(window=period).mean()

    @staticmethod
    def ema(series, period):
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Use Wilders smoothing for more traditional RSI
        # However, simple rolling mean is often used for simplicity
        # Let's stick to standard Wilder's smoothing if possible
        # for more accuracy, but simple rolling is also fine.
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(series, fast=12, slow=26, signal=9):
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def stochastic(high, low, close, k_period=14, d_period=3, slow_period=3):
        low_min = low.rolling(window=k_period).min()
        high_max = high.rolling(window=k_period).max()
        k_line = 100 * (close - low_min) / (high_max - low_min)
        d_line = k_line.rolling(window=d_period).mean()
        slow_d_line = d_line.rolling(window=slow_period).mean()
        return k_line, d_line, slow_d_line

    @staticmethod
    def atr(high, low, close, period=14):
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def bollinger_bands(series, period=20, std_dev=2):
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower

    @staticmethod
    def donchian_channels(high, low, period=20):
        upper = high.rolling(window=period).max()
        lower = low.rolling(window=period).min()
        middle = (upper + lower) / 2
        return upper, middle, lower

    @staticmethod
    def obv(close, volume):
        direction = np.sign(close.diff().fillna(0))
        # direction is 0 if no change, 1 if up, -1 if down
        # fillna(0) ensures the first row is 0
        return (direction * volume).cumsum()

    @staticmethod
    def mfi(high, low, close, volume, period=14):
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        
        delta = typical_price.diff()
        pos_flow = money_flow.where(delta > 0, 0)
        neg_flow = money_flow.where(delta < 0, 0)
        
        pos_mf = pos_flow.rolling(window=period).sum()
        neg_mf = neg_flow.rolling(window=period).sum()
        
        mfr = pos_mf / neg_mf
        return 100 - (100 / (1 + mfr))

    @staticmethod
    def cmf(high, low, close, volume, period=20):
        # Money Flow Multiplier
        # Handle cases where high == low to avoid division by zero
        denom = high - low
        mf_multiplier = ((close - low) - (high - close)) / denom
        mf_multiplier = mf_multiplier.fillna(0)
        mf_multiplier.replace([np.inf, -np.inf], 0, inplace=True)
        
        money_flow_volume = mf_multiplier * volume
        cmf = money_flow_volume.rolling(window=period).sum() / volume.rolling(window=period).sum()
        return cmf

    @staticmethod
    def adx(high, low, close, period=14):
        plus_dm = high.diff()
        minus_dm = low.diff()
        
        # +DM: if current high - prev high > prev low - current low, and > 0, else 0
        # -DM: if prev low - current low > current high - prev high, and > 0, else 0
        p_dm = np.where((plus_dm > minus_dm.abs()) & (plus_dm > 0), plus_dm, 0)
        m_dm = np.where((minus_dm.abs() > plus_dm) & (minus_dm.abs() > 0), minus_dm.abs(), 0)
        
        p_dm = pd.Series(p_dm, index=high.index)
        m_dm = pd.Series(m_dm, index=low.index)
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        plus_di = 100 * (p_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (m_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di

    @staticmethod
    def aroon(high, low, period=14):
        # Aroon Up = 100 * (period - days since period high) / period
        # Aroon Down = 100 * (period - days since period low) / period
        aroon_up = high.rolling(window=period+1).apply(lambda x: 100 * (period - x[::-1].argmax()) / period, raw=False)
        aroon_down = low.rolling(window=period+1).apply(lambda x: 100 * (period - x[::-1].argmin()) / period, raw=False)
        return aroon_up, aroon_down

    def calculate_1mo_daily(self, df):
        """1) 1mo daily (short-term / tactical)"""
        df = df.copy()
        # SMA/EMA: 5, 10, 20
        for p in [5, 10, 20]:
            df[f'SMA_{p}'] = self.sma(df['Close'], p)
            df[f'EMA_{p}'] = self.ema(df['Close'], p)
        
        # RSI: 14, RSI-7
        df['RSI_14'] = self.rsi(df['Close'], 14)
        df['RSI_7'] = self.rsi(df['Close'], 7)
        
        # MACD: 12/26/9
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = self.macd(df['Close'])
        
        # Stoch: 14/3/3
        df['Stoch_K'], df['Stoch_D'], _ = self.stochastic(df['High'], df['Low'], df['Close'])
        
        # ATR: 14
        df['ATR_14'] = self.atr(df['High'], df['Low'], df['Close'], 14)
        
        # Bollinger: 20, 2σ
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = self.bollinger_bands(df['Close'], 20, 2)
        
        # Donchian: 10, 20
        for p in [10, 20]:
            df[f'Donchian_Upper_{p}'], df[f'Donchian_Middle_{p}'], df[f'Donchian_Lower_{p}'] = \
                self.donchian_channels(df['High'], df['Low'], p)
        
        # Volume: 10, 20 bar volume avg; OBV/MFI/CMF
        df['Vol_Avg_10'] = self.sma(df['Volume'], 10)
        df['Vol_Avg_20'] = self.sma(df['Volume'], 20)
        df['OBV'] = self.obv(df['Close'], df['Volume'])
        df['MFI_14'] = self.mfi(df['High'], df['Low'], df['Close'], df['Volume'], 14)
        df['CMF_20'] = self.cmf(df['High'], df['Low'], df['Close'], df['Volume'], 20)
        
        return df.round(4)

    def calculate_6m_weekly(self, df):
        """2) 6m weekly (swing / intermediate)"""
        df = df.copy()
        # SMA/EMA: 10, 20, 30
        for p in [10, 20, 30]:
            df[f'SMA_{p}'] = self.sma(df['Close'], p)
            df[f'EMA_{p}'] = self.ema(df['Close'], p)
        
        # RSI: 14
        df['RSI_14'] = self.rsi(df['Close'], 14)
        
        # MACD: 12/26/9
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = self.macd(df['Close'])
        
        # ATR: 14
        df['ATR_14'] = self.atr(df['High'], df['Low'], df['Close'], 14)
        
        # Bollinger: 20, 2σ
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = self.bollinger_bands(df['Close'], 20, 2)
        
        # Donchian: 20
        df['Donchian_Upper_20'], df['Donchian_Middle_20'], df['Donchian_Lower_20'] = \
            self.donchian_channels(df['High'], df['Low'], 20)
        
        # ADX/DMI: 14
        df['ADX_14'], df['DI_Plus_14'], df['DI_Minus_14'] = self.adx(df['High'], df['Low'], df['Close'], 14)
        
        # Volume: optional (weekly volume trends)
        df['Vol_Avg_10'] = self.sma(df['Volume'], 10)
        df['Vol_Avg_20'] = self.sma(df['Volume'], 20)
        
        return df.round(4)

    def calculate_2y_monthly(self, df):
        """3) 2y monthly (structural / long-term)"""
        df = df.copy()
        # SMA/EMA: 6, 12, 24
        for p in [6, 12, 24]:
            df[f'SMA_{p}'] = self.sma(df['Close'], p)
            df[f'EMA_{p}'] = self.ema(df['Close'], p)
        
        # RSI: 14
        df['RSI_14'] = self.rsi(df['Close'], 14)
        
        # MACD: 12/26/9
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = self.macd(df['Close'])
        
        # ATR: 14
        df['ATR_14'] = self.atr(df['High'], df['Low'], df['Close'], 14)
        
        # Bollinger: 12, 2σ
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = self.bollinger_bands(df['Close'], 12, 2)
        
        # Donchian: 12, 24
        for p in [12, 24]:
            df[f'Donchian_Upper_{p}'], df[f'Donchian_Middle_{p}'], df[f'Donchian_Lower_{p}'] = \
                self.donchian_channels(df['High'], df['Low'], p)
        
        # ADX/DMI / Aroon: 14
        df['ADX_14'], df['DI_Plus_14'], df['DI_Minus_14'] = self.adx(df['High'], df['Low'], df['Close'], 14)
        df['Aroon_Up_14'], df['Aroon_Down_14'] = self.aroon(df['High'], df['Low'], 14)
        
        return df.round(4)

    def plot_indicators(self, df, output_image, title="Technical Indicators"):
        """Creates a visualization of the technical indicators using seaborn."""
        df = df.copy()
        
        # Set theme
        sns.set_theme(style="darkgrid")
        
        # Ensure Date is datetime and index
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            
        # Create subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True, 
                                            gridspec_kw={'height_ratios': [3, 1, 1]})
        
        # 1. Price and Bollinger Bands / SMAs
        sns.lineplot(data=df, x=df.index, y='Close', ax=ax1, label='Close Price', color='black', linewidth=1.5)
        
        if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
            ax1.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], alpha=0.15, color='royalblue', label='Bollinger Bands')
        
        for p in [5, 10, 20, 30]:
            col = f'SMA_{p}'
            if col in df.columns:
                sns.lineplot(data=df, x=df.index, y=col, ax=ax1, label=f'SMA {p}', alpha=0.8)
        
        ax1.set_title(f"{title} - Price & Overlays", fontsize=16)
        ax1.set_ylabel("Price")
        ax1.legend(loc='upper left')
        
        # 2. RSI
        rsi_col = 'RSI_14'
        if rsi_col in df.columns:
            sns.lineplot(data=df, x=df.index, y=rsi_col, ax=ax2, label='RSI 14', color='mediumpurple')
            ax2.axhline(70, linestyle='--', alpha=0.6, color='tomato')
            ax2.axhline(30, linestyle='--', alpha=0.6, color='mediumseagreen')
            ax2.set_ylim(0, 100)
            ax2.set_ylabel("RSI")
            ax2.set_title("Relative Strength Index (RSI)", fontsize=14)
            ax2.legend(loc='upper left')

        # 3. MACD
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            sns.lineplot(data=df, x=df.index, y='MACD', ax=ax3, label='MACD', color='dodgerblue')
            sns.lineplot(data=df, x=df.index, y='MACD_Signal', ax=ax3, label='Signal', color='darkorange')
            
            if 'MACD_Hist' in df.columns:
                # For bar chart, we use matplotlib directly as it's easier for colored bars
                colors = ['green' if x > 0 else 'red' for x in df['MACD_Hist']]
                ax3.bar(df.index, df['MACD_Hist'], alpha=0.3, color=colors, label='Histogram', width=0.8)
                
            ax3.set_title("MACD (12, 26, 9)", fontsize=14)
            ax3.set_ylabel("Value")
            ax3.legend(loc='upper left')
            
        plt.tight_layout()
        plt.savefig(output_image)
        plt.close()
        print(f"Saved visualization to {output_image}")

    def process_files(self, daily_path, weekly_path, monthly_path):
        """Reads CSV files, calculates indicators, and saves results."""
        # Daily
        if os.path.exists(daily_path):
            df_daily = pd.read_csv(daily_path)
            df_daily_res = self.calculate_1mo_daily(df_daily)
            output_daily = daily_path.replace('.csv', '_indicators.csv')
            df_daily_res.to_csv(output_daily, index=False)
            print(f"Saved daily indicators to {output_daily}")
            
            # Save daily chart
            chart_daily = output_daily.replace('.csv', '.png')
            self.plot_indicators(df_daily_res, chart_daily, title="Daily Technical Indicators")
        
        # Weekly
        if os.path.exists(weekly_path):
            df_weekly = pd.read_csv(weekly_path)
            df_weekly_res = self.calculate_6m_weekly(df_weekly)
            output_weekly = weekly_path.replace('.csv', '_indicators.csv')
            df_weekly_res.to_csv(output_weekly, index=False)
            print(f"Saved weekly indicators to {output_weekly}")
            
            # Save weekly chart
            chart_weekly = output_weekly.replace('.csv', '.png')
            self.plot_indicators(df_weekly_res, chart_weekly, title="Weekly Technical Indicators")
            
        # Monthly
        if os.path.exists(monthly_path):
            df_monthly = pd.read_csv(monthly_path)
            df_monthly_res = self.calculate_2y_monthly(df_monthly)
            output_monthly = monthly_path.replace('.csv', '_indicators.csv')
            df_monthly_res.to_csv(output_monthly, index=False)
            print(f"Saved monthly indicators to {output_monthly}")

            # Save monthly chart
            chart_monthly = output_monthly.replace('.csv', '.png')
            self.plot_indicators(df_monthly_res, chart_monthly, title="Monthly Technical Indicators")

if __name__ == "__main__":
    ti = TechnicalIndicator()
    # Example usage with paths provided in user query
    # The actual paths might vary, but we use the provided ones for the runner.
    base_path = "collectors_all/data/processed/AAPL_20251226_174048/"
    ti.process_files(
        os.path.join(base_path, "yfinance_History1mo_d.csv"),
        os.path.join(base_path, "yfinance_History6m_1wk.csv"),
        os.path.join(base_path, "yfinance_History2y_1mo.csv")
    )
