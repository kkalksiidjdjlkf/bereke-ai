# Easy Money.Bet v3 — Casino Simulation + Full ML

## Что нового в v3

### Новые фичи (14 вместо 8)
| Новая фича | Описание |
|---|---|
| `martingaleEvents` | Удвоение ставки после проигрыша |
| `reinvestmentEvents` | Большая ставка сразу после выигрыша |
| `betEscalationRate` | Насколько выросли ставки к концу сессии |
| `avgBetToBalanceRatio` | Ставка относительно баланса |
| `lossStreak5Plus` | Серии из 5+ проигрышей подряд |
| `consecutiveDays` | Дней подряд (из localStorage) |

### Межсессионная память
- История 60 сессий в localStorage
- Считает: дней подряд, дней за 7 дней, рост потерь, сессий с высоким риском

### Улучшенные алерты (5 уровней приоритета)
- Мартингейл → специальное предупреждение
- Дни подряд → предупреждение о зависимости
- Эскалация ставок → новое предупреждение

### Улучшенная ML модель
- TF.js: 8→64→32→16→1 + BatchNorm + Dropout
- Python RF: калиброванные вероятности (Platt scaling)
- class_weight: лудоманы весят в 3× больше
- AUC ~0.76+

---

## Запуск

### Быстро (только браузер)
Двойной клик на `index.html`

### С Python backend (точнее)
```bash
cd backend
pip install -r requirements.txt
python server.py
```

---

## Структура
```
easymoney/
├── index.html           ← UI (без изменений)
├── tracker/
│   └── behavior.js      ← 14 фич + localStorage + TF.js
├── games/
│   └── logic.js         ← Игровая логика
└── backend/
    ├── server.py        ← Flask + RF + GB + Calibration
    └── requirements.txt
```
