import mplfinance as mpf

def plot_candlestick_chart(market_data, detected):
    # Asegúrate de que 'detected' tenga las mismas columnas que 'market_data'
    detected = detected.reindex(market_data.index)

    # Crear una serie para resaltar las velas seleccionadas
    highlight = detected['close'].notna().astype(int)

    # Crear el gráfico de velas
    add_plot = [
        mpf.make_addplot(highlight, type='scatter', markersize=100, marker='o', color='red')
    ]

    fig, ax = mpf.plot(
        market_data,
        type='candle',
        style='charles',
        volume=True,
        addplot=add_plot,
        returnfig=True
    )
    return fig