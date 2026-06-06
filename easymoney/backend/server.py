"""
Easy Money.Bet v3 — Python ML Backend
Models: Random Forest + Gradient Boosting + Ensemble
Features: 14 (extended from Auer & Griffiths 2022)
Run: python server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.calibration import CalibratedClassifierCV
import numpy as np

app = Flask(__name__)
CORS(app)

FEATURE_NAMES = [
    'depositsPerSession',       # 0 - ср. депозиты за сессию
    'accountDepleted',          # 1 - счёт опустошён
    'chasingLossEvents',        # 2 - погоня за потерями
    'rapidBetCount',            # 3 - быстрые ставки
    'sessionLengthMinutes',     # 4 - длина сессии
    'betIncreaseAfterLoss',     # 5 - увеличение ставок после проигрыша
    'nightSession',             # 6 - ночная игра
    'switchedGameCount',        # 7 - смена игр
    'martingaleEvents',         # 8 - мартингейл
    'reinvestmentEvents',       # 9 - реинвестирование выигрыша
    'betEscalationRate',        # 10 - эскалация ставок
    'avgBetToBalanceRatio',     # 11 - ставка/баланс
    'lossStreak5Plus',          # 12 - серии 5+ проигрышей
    'consecutiveDays',          # 13 - дней подряд (из cross-session)
]


def generate_training_data(n=5000):
    """
    Синтетические данные на основе паттернов из статьи.
    28% лудоманов (как в выборке Auer & Griffiths 2022).
    """
    np.random.seed(42)
    X, y = [], []

    for _ in range(n):
        is_pg = np.random.random() < 0.28

        if is_pg:
            row = [
                np.clip(np.random.gamma(2.8, 0.7), 0, 10),      # depositsPerSession
                np.clip(np.random.gamma(3.0, 0.8), 0, 10),      # accountDepleted
                np.clip(np.random.gamma(3.5, 1.2), 0, 15),      # chasingLossEvents
                np.clip(np.random.gamma(2.5, 3.0), 0, 30),      # rapidBetCount
                np.clip(np.random.gamma(3.0, 28), 0, 300),      # sessionLengthMinutes
                np.clip(np.random.gamma(2.8, 1.2), 0, 15),      # betIncreaseAfterLoss
                1 if np.random.random() < 0.45 else 0,          # nightSession
                np.clip(np.random.gamma(2.2, 1.5), 0, 12),      # switchedGameCount
                np.clip(np.random.gamma(2.5, 1.3), 0, 12),      # martingaleEvents
                np.clip(np.random.gamma(2.0, 1.2), 0, 10),      # reinvestmentEvents
                np.clip(np.random.normal(0.45, 0.3), -0.5, 2),  # betEscalationRate
                np.clip(np.random.beta(3, 4) * 0.8, 0, 1),      # avgBetToBalanceRatio
                np.clip(np.random.gamma(2, 1.2), 0, 8),         # lossStreak5Plus
                np.clip(np.random.gamma(3, 2.5), 0, 30),        # consecutiveDays
            ]
        else:
            row = [
                np.clip(np.random.gamma(1.1, 0.5), 0, 10),
                np.clip(np.random.gamma(1.0, 0.6), 0, 10),
                np.clip(np.random.gamma(0.8, 0.9), 0, 15),
                np.clip(np.random.gamma(1.0, 1.5), 0, 30),
                np.clip(np.random.gamma(2.0, 14), 0, 300),
                np.clip(np.random.gamma(0.9, 0.8), 0, 15),
                1 if np.random.random() < 0.18 else 0,
                np.clip(np.random.gamma(1.0, 0.8), 0, 12),
                np.clip(np.random.gamma(0.7, 0.8), 0, 12),
                np.clip(np.random.gamma(0.8, 0.7), 0, 10),
                np.clip(np.random.normal(0.05, 0.2), -0.5, 2),
                np.clip(np.random.beta(1.5, 8) * 0.5, 0, 1),
                np.clip(np.random.gamma(0.6, 0.8), 0, 8),
                np.clip(np.random.gamma(1.5, 1.2), 0, 30),
            ]

        X.append(row)
        y.append(1 if is_pg else 0)

    return np.array(X), np.array(y)


def extract_features(data):
    """Извлечь фичи из JSON объекта сессии."""
    cs = data.get('crossSession', {})
    return np.array([[
        float(data.get('depositsPerSession', 0)),
        float(data.get('accountDepleted', 0)),
        float(data.get('chasingLossEvents', 0)),
        float(data.get('rapidBetCount', 0)),
        float(data.get('sessionLengthMinutes', 0)),
        float(data.get('betIncreaseAfterLoss', 0)),
        1.0 if data.get('nightSession', False) else 0.0,
        float(data.get('switchedGameCount', 0)),
        float(data.get('martingaleEvents', 0)),
        float(data.get('reinvestmentEvents', 0)),
        float(data.get('betEscalationRate', 0)),
        float(data.get('avgBetToBalanceRatio', 0)),
        float(data.get('lossStreak5Plus', 0)),
        float(cs.get('consecutiveDays', 0)),
    ]])


# ============================================
# ОБУЧЕНИЕ
# ============================================
print("⏳ Генерация данных (5000 сессий)...")
X, y = generate_training_data(5000)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

print("⏳ Обучение Random Forest...")
rf_base = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    min_samples_split=4,
    min_samples_leaf=2,
    class_weight={0: 1, 1: 3},   # лудоманы весят в 3 раза больше
    random_state=42,
    n_jobs=-1
)
# Калибровка вероятностей (Platt scaling)
rf = CalibratedClassifierCV(rf_base, cv=3, method='sigmoid')
rf.fit(X_train_s, y_train)

print("⏳ Обучение Gradient Boosting...")
gb = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.04,
    max_depth=5,
    min_samples_split=5,
    subsample=0.8,
    random_state=42
)
gb.fit(X_train_s, y_train)

# Метрики
rf_auc  = roc_auc_score(y_test, rf.predict_proba(X_test_s)[:, 1])
gb_auc  = roc_auc_score(y_test, gb.predict_proba(X_test_s)[:, 1])
ens_proba = rf.predict_proba(X_test_s)[:, 1] * 0.6 + gb.predict_proba(X_test_s)[:, 1] * 0.4
ens_auc = roc_auc_score(y_test, ens_proba)

print(f"\n✅ Random Forest AUC:  {rf_auc:.4f}")
print(f"✅ Gradient Boost AUC: {gb_auc:.4f}")
print(f"✅ Ensemble AUC:       {ens_auc:.4f}")

# Feature importance только для RF base
rf_base.fit(X_train_s, y_train)
print(f"\n📊 Feature Importance:")
fi = sorted(zip(FEATURE_NAMES, rf_base.feature_importances_), key=lambda x: -x[1])
for name, imp in fi:
    bar = '█' * int(imp * 60)
    print(f"  {name:<28} {bar} {imp:.4f}")


# ============================================
# API
# ============================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'version': 'v3',
        'features': len(FEATURE_NAMES),
        'training_samples': 5000,
        'models': {
            'rf_auc':  round(rf_auc, 4),
            'gb_auc':  round(gb_auc, 4),
            'ens_auc': round(ens_auc, 4),
        }
    })


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        features = extract_features(data)
        features_s = scaler.transform(features)

        rf_score  = float(rf.predict_proba(features_s)[0][1])
        gb_score  = float(gb.predict_proba(features_s)[0][1])
        ens_score = rf_score * 0.6 + gb_score * 0.4

        risk_pct = round(ens_score * 100)
        level = 'HIGH' if risk_pct >= 70 else 'MEDIUM' if risk_pct >= 40 else 'LOW'

        # Топ-3 опасных фичи
        fv = features[0]
        normed = fv / (np.array([6,6,10,15,180,8,1,8,8,6,1,1,5,30]) + 1e-9)
        top_idx = np.argsort(normed)[::-1][:3]
        top_features = [FEATURE_NAMES[i] for i in top_idx]

        return jsonify({
            'riskScore':     risk_pct,
            'riskLevel':     level,
            'rfScore':       round(rf_score * 100),
            'gbScore':       round(gb_score * 100),
            'ensembleScore': round(ens_score * 100),
            'topRiskFactors': top_features,
            'model':         'RF+GB Calibrated Ensemble v3'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/feature_importance', methods=['GET'])
def feature_importance():
    return jsonify({
        name: round(float(imp), 4)
        for name, imp in zip(FEATURE_NAMES, rf_base.feature_importances_)
    })


@app.route('/batch_predict', methods=['POST'])
def batch_predict():
    try:
        sessions = request.json
        results = []
        for session in sessions:
            features_s = scaler.transform(extract_features(session))
            score = (
                float(rf.predict_proba(features_s)[0][1]) * 0.6 +
                float(gb.predict_proba(features_s)[0][1]) * 0.4
            )
            results.append({
                'sessionId': session.get('sessionId', 'unknown'),
                'riskScore': round(score * 100),
                'riskLevel': 'HIGH' if score >= 0.7 else 'MEDIUM' if score >= 0.4 else 'LOW'
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    print(f"\n🚀 Сервер запущен: http://localhost:5000")
    print(f"   GET  /health")
    print(f"   POST /predict")
    print(f"   POST /batch_predict")
    print(f"   GET  /feature_importance\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
