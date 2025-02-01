import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from streamlit_app.utils.market_data import get_exchange  # or however you've exported your exchange

exchange = get_exchange()

def plot_candlestick_chart(market_data, detected, detection_agent):
    # Add VWAP to the addplot
    vwap = mpf.make_addplot(market_data['VWAP'], color='blue', width=1, label='VWAP')
    
    mc = mpf.make_marketcolors(up='g', down='r', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)
    
    # Add VWAP to the plot
    fig, axlist = mpf.plot(market_data, type='candle', 
                          volume=True, 
                          style=s, 
                          addplot=vwap,  # Add VWAP here
                          returnfig=True)

    ax = axlist[0]
    for idx, row in detected.iterrows():
        index_pos = market_data.index.get_loc(idx)

        # Detectar el primer rebote con al menos una vela intermedia
        rebote_index = detection_agent.detectar_rebotes_con_intermedias(market_data, index_pos)
        if rebote_index:
            promedio_intermedias = detection_agent.promedio_velas_intermedias(market_data, index_pos, rebote_index)
            if promedio_intermedias is not None:
                signo_intermedias = "+" if promedio_intermedias > market_data['close'].iloc[index_pos] else "-"
                ax.annotate(signo_intermedias,
                            xy=(rebote_index - 0.5, market_data['close'].iloc[rebote_index]),
                            color='black',
                            fontsize=10,
                            fontweight='bold',
                            ha='center', va='center',
                            bbox=dict(boxstyle='square,pad=0.2', fc='white', alpha=0.9))

                # Anotar la vela inicial detectada
                ax.annotate("V",
                            xy=(index_pos, market_data['high'].iloc[index_pos]),
                            xytext=(index_pos, market_data['high'].iloc[index_pos] + (market_data['high'].max() - market_data['low'].min()) * 0.05),
                            color='blue',
                            fontsize=8,
                            ha='center', va='center',
                            bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))

            # Conectar la vela de rebote con la vela inicial
            ax.plot([index_pos, rebote_index], [market_data['close'].iloc[index_pos], market_data['close'].iloc[rebote_index]], color='red', linestyle='-', linewidth=1)

            promedio_siguiente = detection_agent.promedio_dos_velas_siguientes(market_data, rebote_index)
            if promedio_siguiente is not None:
                ax.annotate(f"{promedio_siguiente:.2f}",
                            xy=(rebote_index + 2, promedio_siguiente),
                            color='purple',
                            fontsize=8,
                            fontweight='bold',
                            ha='center', va='center',
                            bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7))

                ax.plot([rebote_index, rebote_index + 2], [market_data['close'].iloc[rebote_index], promedio_siguiente], color='green', linestyle=':', linewidth=2)

                detection_agent.guardar_en_base_datos(market_data, index_pos, rebote_index, promedio_siguiente, signo_intermedias)

    print(market_data[['close', 'VWAP']].head())
    print(market_data['VWAP'].isnull().sum())  # Check for NaN values

    return fig

def plot_candlestick_chart_with_vwap(market_data):
    fig, ax = plt.subplots()

    # Plot candlestick chart first
    ax.plot(market_data.index, market_data['close'], label='Close Price', color='black')

    # Plot VWAP after the close price
    if 'VWAP' in market_data.columns:
        ax.plot(market_data.index, market_data['VWAP'], label='VWAP', color='orange', linewidth=2, linestyle='--')

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Add labels and legend
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.legend()

    # Adjust y-axis limits if necessary
    ax.set_ylim([market_data[['close', 'VWAP']].min().min(), market_data[['close', 'VWAP']].max().max()])

    plt.tight_layout()
    plt.show()

def fetch_market_data(symbol, timeframe, limit=1000):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # Calculate VWAP
    q = df['volume']
    p = (df['high'] + df['low'] + df['close']) / 3
    df['VWAP'] = (p * q).cumsum() / q.cumsum()

    print(df[['close', 'VWAP']].head())  # Print to verify VWAP values

    return df
