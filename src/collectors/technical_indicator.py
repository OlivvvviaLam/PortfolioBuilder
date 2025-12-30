import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid tkinter errors
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

    def plot_price_overlays(self, df, output_image, title="Technical Indicators"):
        """Chart 1: Price with overlays (SMAs, EMAs, Bollinger Bands, Donchian Channels)."""
        df = df.copy()
        
        # Set theme
        sns.set_theme(style="darkgrid")
        
        # Ensure Date is datetime and index
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            df.set_index('Date', inplace=True)
            
        # Create figure with larger size for better readability
        fig, ax = plt.subplots(figsize=(16, 9))
        
        # Plot close price with thicker line
        sns.lineplot(data=df, x=df.index, y='Close', ax=ax, label='Close Price', 
                     color='black', linewidth=3)
        
        # Bollinger Bands
        if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns and 'BB_Middle' in df.columns:
            if df['BB_Upper'].notna().any():
                ax.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], 
                               alpha=0.15, color='royalblue', label='Bollinger Bands (±2σ)')
                sns.lineplot(data=df, x=df.index, y='BB_Middle', ax=ax, 
                            label='BB Middle', color='blue', alpha=0.6, linestyle='--', linewidth=2)
        
        # SMAs with thicker lines
        for p in [5, 6, 10, 12, 20, 24, 30]:
            col = f'SMA_{p}'
            if col in df.columns and df[col].notna().any():
                sns.lineplot(data=df, x=df.index, y=col, ax=ax, label=f'SMA {p}', 
                           alpha=0.8, linewidth=2.5)
        
        # EMAs with thicker lines
        for p in [5, 6, 10, 12, 20, 24, 30]:
            col = f'EMA_{p}'
            if col in df.columns and df[col].notna().any():
                sns.lineplot(data=df, x=df.index, y=col, ax=ax, label=f'EMA {p}', 
                           alpha=0.8, linestyle='--', linewidth=2.5)
        
        # Donchian Channels (show one set to avoid clutter)
        donchian_period = 20 if 'Donchian_Upper_20' in df.columns else 10
        if f'Donchian_Upper_{donchian_period}' in df.columns:
            if df[f'Donchian_Upper_{donchian_period}'].notna().any():
                ax.fill_between(df.index, 
                              df[f'Donchian_Upper_{donchian_period}'], 
                              df[f'Donchian_Lower_{donchian_period}'],
                              alpha=0.12, color='green', label=f'Donchian ({donchian_period})')
        
        ax.set_title(f"{title} - Price & Overlays", fontsize=18, fontweight='bold')
        ax.set_ylabel("Price ($)", fontsize=14, fontweight='bold')
        ax.set_xlabel("Date", fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=11, ncol=2)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=12)
        
        plt.tight_layout()
        plt.savefig(output_image, dpi=100)
        plt.close()
        print(f"  Saved chart 1/3: {output_image}")
    
    def plot_momentum_indicators(self, df, output_image, title="Technical Indicators"):
        """Chart 2: Momentum indicators (RSI, Stochastic, MACD)."""
        df = df.copy()
        
        # Set theme
        sns.set_theme(style="darkgrid")
        
        # Ensure Date is datetime and index
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            df.set_index('Date', inplace=True)
        
        # Determine which indicators are available
        has_rsi = 'RSI_14' in df.columns and df['RSI_14'].notna().any()
        has_stoch = 'Stoch_K' in df.columns and 'Stoch_D' in df.columns and df['Stoch_K'].notna().any()
        has_macd = 'MACD' in df.columns and 'MACD_Signal' in df.columns and df['MACD'].notna().any()
        
        # Count available indicators
        num_indicators = sum([has_rsi, has_stoch, has_macd])
        
        if num_indicators == 0:
            print(f"  Skipped chart 2/3: No momentum indicators available")
            return
        
        # Create subplots dynamically based on available data
        fig, axes = plt.subplots(num_indicators, 1, figsize=(16, 5 * num_indicators), sharex=True)
        if num_indicators == 1:
            axes = [axes]  # Make it iterable
        
        current_ax = 0
        
        # 1. RSI
        if has_rsi:
            ax = axes[current_ax]
            sns.lineplot(data=df, x=df.index, y='RSI_14', ax=ax, label='RSI 14', 
                        color='mediumpurple', linewidth=2.5)
            if 'RSI_7' in df.columns and df['RSI_7'].notna().any():
                sns.lineplot(data=df, x=df.index, y='RSI_7', ax=ax, label='RSI 7', 
                            color='orchid', linewidth=2)
            ax.axhline(70, linestyle='--', alpha=0.7, color='tomato', label='Overbought (70)', linewidth=2)
            ax.axhline(30, linestyle='--', alpha=0.7, color='mediumseagreen', label='Oversold (30)', linewidth=2)
            ax.axhline(50, linestyle=':', alpha=0.5, color='gray', linewidth=1.5)
            ax.set_ylim(0, 100)
            ax.set_ylabel("RSI", fontsize=14, fontweight='bold')
            ax.set_title("Relative Strength Index (RSI)", fontsize=16, fontweight='bold')
            ax.legend(loc='upper left', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=12)
            current_ax += 1
        
        # 2. Stochastic Oscillator
        if has_stoch:
            ax = axes[current_ax]
            sns.lineplot(data=df, x=df.index, y='Stoch_K', ax=ax, label='%K', 
                        color='dodgerblue', linewidth=2.5)
            sns.lineplot(data=df, x=df.index, y='Stoch_D', ax=ax, label='%D', 
                        color='orange', linewidth=2.5)
            ax.axhline(80, linestyle='--', alpha=0.7, color='tomato', label='Overbought (80)', linewidth=2)
            ax.axhline(20, linestyle='--', alpha=0.7, color='mediumseagreen', label='Oversold (20)', linewidth=2)
            ax.set_ylim(0, 100)
            ax.set_ylabel("Stochastic", fontsize=14, fontweight='bold')
            ax.set_title("Stochastic Oscillator (14, 3, 3)", fontsize=16, fontweight='bold')
            ax.legend(loc='upper left', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=12)
            current_ax += 1
        
        # 3. MACD
        if has_macd:
            ax = axes[current_ax]
            sns.lineplot(data=df, x=df.index, y='MACD', ax=ax, label='MACD', 
                        color='dodgerblue', linewidth=2.5)
            sns.lineplot(data=df, x=df.index, y='MACD_Signal', ax=ax, label='Signal', 
                        color='darkorange', linewidth=2.5)
            
            if 'MACD_Hist' in df.columns and df['MACD_Hist'].notna().any():
                colors = ['green' if x > 0 else 'red' for x in df['MACD_Hist']]
                # Calculate dynamic bar width based on data points
                num_bars = len(df.index)
                bar_width = (df.index[-1] - df.index[0]).days / num_bars * 0.7
                ax.bar(df.index, df['MACD_Hist'], alpha=0.5, color=colors, 
                       label='Histogram', width=bar_width)
            
            ax.axhline(0, linestyle='-', alpha=0.5, color='black', linewidth=1.5)
            ax.set_title("MACD (12, 26, 9)", fontsize=16, fontweight='bold')
            ax.set_ylabel("MACD Value", fontsize=14, fontweight='bold')
            ax.set_xlabel("Date", fontsize=14, fontweight='bold')
            ax.legend(loc='upper left', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=12)
        
        plt.tight_layout()
        plt.savefig(output_image, dpi=100)
        plt.close()
        print(f"  Saved chart 2/3: {output_image}")
    
    def plot_volume_indicators(self, df, output_image, title="Technical Indicators"):
        """Chart 3: Volume analysis (Volume, OBV, MFI, CMF, ATR)."""
        df = df.copy()
        
        # Set theme
        sns.set_theme(style="darkgrid")
        
        # Ensure Date is datetime and index
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            df.set_index('Date', inplace=True)
        
        # Determine which indicators are available
        has_volume = 'Volume' in df.columns and df['Volume'].notna().any()
        has_obv = 'OBV' in df.columns and df['OBV'].notna().any()
        has_mfi = 'MFI_14' in df.columns and df['MFI_14'].notna().any()
        has_cmf = 'CMF_20' in df.columns and df['CMF_20'].notna().any()
        has_atr = 'ATR_14' in df.columns and df['ATR_14'].notna().any()
        
        # Count available indicators
        num_indicators = sum([has_volume, has_obv, has_mfi, has_cmf or has_atr])
        
        if num_indicators == 0:
            print(f"  Skipped chart 3/3: No volume indicators available")
            return
        
        # Create subplots dynamically based on available data
        fig, axes = plt.subplots(num_indicators, 1, figsize=(16, 5 * num_indicators), sharex=True)
        if num_indicators == 1:
            axes = [axes]  # Make it iterable
        
        current_ax = 0
        
        # 1. Volume bars with moving averages
        if has_volume:
            ax = axes[current_ax]
            colors = ['green' if (i > 0 and df['Close'].iloc[i] >= df['Close'].iloc[i-1]) else 'red' 
                     for i in range(len(df))]
            
            # Calculate dynamic bar width based on data points
            num_bars = len(df.index)
            bar_width = (df.index[-1] - df.index[0]).days / num_bars * 0.8
            ax.bar(df.index, df['Volume'], color=colors, alpha=0.7, label='Volume', width=bar_width)
            
            if 'Vol_Avg_10' in df.columns and df['Vol_Avg_10'].notna().any():
                sns.lineplot(data=df, x=df.index, y='Vol_Avg_10', ax=ax, 
                           label='Vol MA 10', color='blue', linewidth=2.5)
            if 'Vol_Avg_20' in df.columns and df['Vol_Avg_20'].notna().any():
                sns.lineplot(data=df, x=df.index, y='Vol_Avg_20', ax=ax, 
                           label='Vol MA 20', color='orange', linewidth=2.5)
            
            ax.set_ylabel("Volume", fontsize=14, fontweight='bold')
            ax.set_title("Trading Volume", fontsize=16, fontweight='bold')
            ax.legend(loc='upper left', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=12)
            current_ax += 1
        
        # 2. OBV (On-Balance Volume)
        if has_obv:
            ax = axes[current_ax]
            sns.lineplot(data=df, x=df.index, y='OBV', ax=ax, 
                        label='OBV', color='purple', linewidth=2.5)
            ax.set_ylabel("OBV", fontsize=14, fontweight='bold')
            ax.set_title("On-Balance Volume (OBV)", fontsize=16, fontweight='bold')
            ax.legend(loc='upper left', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=12)
            current_ax += 1
        
        # 3. MFI (Money Flow Index)
        if has_mfi:
            ax = axes[current_ax]
            sns.lineplot(data=df, x=df.index, y='MFI_14', ax=ax, 
                        label='MFI 14', color='teal', linewidth=2.5)
            ax.axhline(80, linestyle='--', alpha=0.7, color='tomato', label='Overbought (80)', linewidth=2)
            ax.axhline(20, linestyle='--', alpha=0.7, color='mediumseagreen', label='Oversold (20)', linewidth=2)
            ax.set_ylim(0, 100)
            ax.set_ylabel("MFI", fontsize=14, fontweight='bold')
            ax.set_title("Money Flow Index (MFI)", fontsize=16, fontweight='bold')
            ax.legend(loc='upper left', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=12)
            current_ax += 1
        
        # 4. CMF (Chaikin Money Flow) or ATR
        if has_cmf:
            ax = axes[current_ax]
            sns.lineplot(data=df, x=df.index, y='CMF_20', ax=ax, 
                        label='CMF 20', color='darkgreen', linewidth=2.5)
            ax.axhline(0, linestyle='-', alpha=0.5, color='black', linewidth=1.5)
            ax.axhline(0.1, linestyle='--', alpha=0.5, color='green', linewidth=1.5)
            ax.axhline(-0.1, linestyle='--', alpha=0.5, color='red', linewidth=1.5)
            ax.set_ylabel("CMF", fontsize=14, fontweight='bold')
            ax.set_title("Chaikin Money Flow (CMF)", fontsize=16, fontweight='bold')
            ax.legend(loc='upper left', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=12)
            ax.set_xlabel("Date", fontsize=14, fontweight='bold')
        elif has_atr:
            ax = axes[current_ax]
            sns.lineplot(data=df, x=df.index, y='ATR_14', ax=ax, 
                        label='ATR 14', color='crimson', linewidth=2.5)
            ax.set_ylabel("ATR", fontsize=14, fontweight='bold')
            ax.set_title("Average True Range (ATR)", fontsize=16, fontweight='bold')
            ax.legend(loc='upper left', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=12)
            ax.set_xlabel("Date", fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_image, dpi=100)
        plt.close()
        print(f"  Saved chart 3/3: {output_image}")

    def process_files(self, daily_path, weekly_path, monthly_path):
        """Reads CSV files, calculates indicators, and saves results."""
        # Daily
        if os.path.exists(daily_path):
            df_daily = pd.read_csv(daily_path)
            df_daily_res = self.calculate_1mo_daily(df_daily)
            output_daily = daily_path.replace('.csv', '_indicators.csv')
            df_daily_res.to_csv(output_daily, index=False)
            print(f"Saved daily indicators to {output_daily}")
            
            # Save 3 daily charts
            base_path = output_daily.replace('.csv', '')
            self.plot_price_overlays(df_daily_res, f"{base_path}_price_overlays.png", title="Daily")
            self.plot_momentum_indicators(df_daily_res, f"{base_path}_momentum.png", title="Daily")
            self.plot_volume_indicators(df_daily_res, f"{base_path}_volume.png", title="Daily")
        
        # Weekly
        if os.path.exists(weekly_path):
            df_weekly = pd.read_csv(weekly_path)
            df_weekly_res = self.calculate_6m_weekly(df_weekly)
            output_weekly = weekly_path.replace('.csv', '_indicators.csv')
            df_weekly_res.to_csv(output_weekly, index=False)
            print(f"Saved weekly indicators to {output_weekly}")
            
            # Save 3 weekly charts
            base_path = output_weekly.replace('.csv', '')
            self.plot_price_overlays(df_weekly_res, f"{base_path}_price_overlays.png", title="Weekly")
            self.plot_momentum_indicators(df_weekly_res, f"{base_path}_momentum.png", title="Weekly")
            self.plot_volume_indicators(df_weekly_res, f"{base_path}_volume.png", title="Weekly")
            
        # Monthly
        if os.path.exists(monthly_path):
            df_monthly = pd.read_csv(monthly_path)
            df_monthly_res = self.calculate_2y_monthly(df_monthly)
            output_monthly = monthly_path.replace('.csv', '_indicators.csv')
            df_monthly_res.to_csv(output_monthly, index=False)
            print(f"Saved monthly indicators to {output_monthly}")

            # Save 3 monthly charts
            base_path = output_monthly.replace('.csv', '')
            self.plot_price_overlays(df_monthly_res, f"{base_path}_price_overlays.png", title="Monthly")
            self.plot_momentum_indicators(df_monthly_res, f"{base_path}_momentum.png", title="Monthly")
            self.plot_volume_indicators(df_monthly_res, f"{base_path}_volume.png", title="Monthly")

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
