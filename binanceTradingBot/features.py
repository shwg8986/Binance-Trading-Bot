import talib

features = sorted([
    'EMA',
])


def calc_features(df):
    open = df['op']
    high = df['hi']
    low = df['lo']
    close = df['cl']
    volume = df['volume']

    orig_columns = df.columns
    hilo = (df['hi'] + df['lo']) / 2

    # MANAUSDT用の特徴量
    df['diff'] = (close - close.shift(1)) / close * 100
    df['ema_diff3'] = talib.EMA(df['diff'], timeperiod=10)
    df['sig3'] = df['ema_diff3'] - df['ema_diff3'].shift(16)

    return df
