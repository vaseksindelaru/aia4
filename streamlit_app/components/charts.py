import matplotlib.pyplot as plt
import mplfinance as mpf

def plot_candlestick_chart(market_data, detected, detection_agent):
    mc = mpf.make_marketcolors(up='g', down='r', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)
    fig, axlist = mpf.plot(market_data, type='candle', volume=True, style=s, returnfig=True)

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

    return fig