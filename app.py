from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from datetime import datetime, timedelta

app = Flask(__name__)

# --- 1) Load historical data and preprocess once ---
df_hist = pd.read_json('hackathon_2024/hackathon_data/transactions.json')
df_hist['ts'] = pd.to_datetime(df_hist['updated_timestamp'], errors='coerce')
df_hist = df_hist.sort_values(['owner_user_id','ts']).dropna(subset=['ts'])

# fill geolocation
for col in ('geolocation_latitude','geolocation_longitude'):
    df_hist[col] = pd.to_numeric(df_hist[col], errors='coerce')
    df_hist[col] = df_hist.groupby('owner_user_id')[col] \
                         .transform(lambda s: s.fillna(method='ffill')
                                           .fillna(method='bfill')
                                           .fillna(0))

# helper: haversine
def hav(lat1, lon1, lat2, lon2):
    if any(pd.isna([lat1,lon1,lat2,lon2])): return 0.0
    R = 6371.0
    dlat = np.radians(lat2-lat1)
    dlon = np.radians(lon2-lon1)
    a = (np.sin(dlat/2)**2 +
         np.cos(np.radians(lat1))*np.cos(np.radians(lat2))*np.sin(dlon/2)**2)
    return R*2*np.arctan2(np.sqrt(a), np.sqrt(1-a))

# 2) Define feature list
FEATURES = [
    'amount_z','hour','day_of_week',
    'dist_from_last','tx_count_last_hour','cat_freq'
]

# 3) Load your trained autoencoder
class AE(nn.Module):
    def __init__(self, D, H=3):
        super().__init__()
        self.enc = nn.Linear(D, H)
        self.dec = nn.Linear(H, D)
    def forward(self, x): return self.dec(self.enc(x))

model = AE(len(FEATURES), H=3)
model.load_state_dict(torch.load('autoencoder.pth', map_location='cpu'))
model.eval()

# 4) Precomputed thresholds (from training)
WARN_THRESHOLD = 0.30  # e.g. 97.5th percentile
FA_THRESHOLD   = 0.50  # e.g. 99.5th percentile

# 5) Reason mapping
reason_map = {
    'amount_z'          : 'unusual transaction size',
    'hour'              : 'atypical time of day',
    'day_of_week'       : 'odd day of week',
    'dist_from_last'    : 'unexpected location jump',
    'tx_count_last_hour': 'spike in transaction velocity',
    'cat_freq'          : 'rare merchant category'
}

# 6) Featurization helper
def featurize(txn):
    uid = txn.get('owner_user_id')
    # amount_z
    hist_amt = df_hist.loc[df_hist.owner_user_id==uid, 'amount'].dropna()
    if len(hist_amt)>1:
        mean, std = hist_amt.mean(), hist_amt.std()
        amt_z = (txn['amount'] - mean)/std if std else 0.0
    else:
        amt_z = 0.0

    # timestamp features
    ts = pd.to_datetime(txn.get('updated_timestamp'))
    hr = ts.hour if not pd.isna(ts) else 0
    dow= ts.dayofweek if not pd.isna(ts) else 0

    # distance from last
    user_hist = df_hist[df_hist.owner_user_id==uid]
    if not user_hist.empty:
        last = user_hist.iloc[-1]
        dist = hav(
            last.geolocation_latitude, last.geolocation_longitude,
            txn.get('geolocation_latitude',0), txn.get('geolocation_longitude',0)
        )
        # tx_count_last_hour
        window = user_hist[
            (user_hist.ts >= ts - timedelta(hours=1)) &
            (user_hist.ts < ts)
        ]
        vel = len(window)
        # cat_freq
        catf = len(user_hist[user_hist.merchant_category_code==txn.get('merchant_category_code')])
    else:
        dist, vel, catf = 0.0, 0, 0

    return np.array([amt_z, hr, dow, dist, vel, catf], dtype=np.float32)

# 7) Prediction endpoint
@app.route('/predict', methods=['POST'])
def predict():
    txn = request.get_json()

    # 1) featurize
    x = featurize(txn)
    x_tensor = torch.from_numpy(x).unsqueeze(0)  # shape [1,6]

    # 2) autoencoder inference
    with torch.no_grad():
        recon = model(x_tensor).cpu().numpy()[0]
    ae_error = float(np.mean((x - recon)**2))

    # 3) identify top 2 features
    feat_err = (x - recon)**2
    norm_err = feat_err / (feat_err.mean()+1e-6)
    idxs = np.argsort(norm_err)[-2:][::-1]
    top_feats = [FEATURES[i] for i in idxs]
    reasons  = "; ".join(reason_map[f] for f in top_feats)

    # 4) decide action
    if ae_error > FA_THRESHOLD:
        action = '2FA_required'
    elif ae_error > WARN_THRESHOLD:
        action = 'warn'
    else:
        action = 'none'

    # 5) return original txn + added columns
    out = txn.copy()
    out.update({
        'ae_error'       : ae_error,
        'ae_reasons'     : reasons,
        'ae_action'      : action
    })
    return jsonify(out)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
