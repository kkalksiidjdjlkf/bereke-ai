// =============================================
// Easy Money.Bet v3 — Advanced Behavior Tracker
// Full ML Pipeline: TF.js + Rule Engine + Session Memory
// Features: 14 fich, Martingale, Cross-session, Temporal
// =============================================

class BehaviorTracker {
  constructor() {
    this.sessionStart = Date.now();
    this.events = [];
    this.tfModel = null;
    this.modelReady = false;

    this.metrics = {
      sessionId: this.generateId(),
      sessionStart: new Date().toISOString(),
      hourOfDay: new Date().getHours(),
      dayOfWeek: new Date().getDay(),

      // === CORE COUNTERS ===
      totalBets: 0,
      totalDeposits: 0,
      totalLost: 0,
      totalWon: 0,
      betAmounts: [],
      betResults: [],       // 'win'/'loss' для каждой ставки
      betTimestamps: [],
      timeBetweenBets: [],
      depositsPerSession: 0,

      // === RISK SIGNALS ===
      accountDepleted: 0,
      chasingLossEvents: 0,
      betIncreaseAfterLoss: 0,
      rapidBetCount: 0,
      switchedGameCount: 0,
      failedDepositAttempts: 0,  // открыл депозит, но закрыл без пополнения

      // === ADVANCED SIGNALS ===
      lossStreakCurrent: 0,
      lossStreakMax: 0,
      winStreakCurrent: 0,
      martingaleEvents: 0,       // удвоение ставки после проигрыша
      reinvestmentEvents: 0,     // большая ставка сразу после выигрыша
      betEscalationRate: 0,      // ставки растут к концу сессии
      avgBetToBalanceRatio: 0,   // ставка / баланс
      highBetToBalanceCount: 0,  // ставок > 30% от баланса
      rapidSeriesCount: 0,       // серий из 3+ быстрых ставок подряд
      lossStreak5Plus: 0,        // серий из 5+ проигрышей подряд

      // === SESSION META ===
      nightSession: this.isNightTime(),
      sessionLengthMinutes: 0,
      lastGame: null,
      lastBetTime: null,
      lastBetResult: null,
      lastBetAmount: null,
      lastBalance: 500,

      // === SCORES ===
      riskScore: 0,
      mlRiskScore: 0,
      ruleRiskScore: 0,
      modelSource: 'rules',

      // === CROSS-SESSION ===
      crossSession: this.loadCrossSessionData(),
    };

    this.initTFModel();
    this.startTracking();
  }

  generateId() {
    return 'sess_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
  }

  isNightTime() {
    const h = new Date().getHours();
    return h >= 22 || h <= 6;
  }

  isHighRiskTime() {
    const h = new Date().getHours();
    return h >= 1 && h <= 5; // 1-5 утра = максимальный риск
  }

  // ============================================
  // CROSS-SESSION MEMORY (localStorage)
  // ============================================
  loadCrossSessionData() {
    try {
      const raw = localStorage.getItem('em_sessions');
      if (!raw) return this.defaultCrossSession();
      const sessions = JSON.parse(raw);
      return this.computeCrossSessionFeatures(sessions);
    } catch (e) {
      return this.defaultCrossSession();
    }
  }

  defaultCrossSession() {
    return {
      totalSessions: 0,
      daysPlayedLast7: 0,
      daysPlayedLast30: 0,
      consecutiveDays: 0,
      avgLossPerSession: 0,
      totalLostAllTime: 0,
      totalDepositsAllTime: 0,
      avgSessionLength: 0,
      sessionsWithHighRisk: 0,
      lossGrowthRate: 0,   // растут ли потери со временем
      sessionGrowthRate: 0, // растут ли сессии по длине
    };
  }

  computeCrossSessionFeatures(sessions) {
    if (!sessions || sessions.length === 0) return this.defaultCrossSession();

    const now = Date.now();
    const day = 86400000;
    const last7 = sessions.filter(s => now - s.timestamp < 7 * day);
    const last30 = sessions.filter(s => now - s.timestamp < 30 * day);

    // Дни подряд (streak)
    const dates = [...new Set(sessions.map(s =>
      new Date(s.timestamp).toDateString()
    ))].sort().reverse();
    let consecutive = 0;
    for (let i = 0; i < dates.length; i++) {
      const d = new Date(dates[i]);
      const prev = new Date(dates[i - 1] || dates[0]);
      if (i === 0) { consecutive = 1; continue; }
      if ((prev - d) / day <= 1.5) consecutive++;
      else break;
    }

    // Растут ли потери (линейная регрессия)
    const losses = sessions.slice(-10).map(s => s.totalLost || 0);
    const lossGrowth = losses.length > 2
      ? (losses[losses.length - 1] - losses[0]) / losses.length
      : 0;

    const sessionLengths = sessions.slice(-10).map(s => s.sessionLengthMinutes || 0);
    const sessionGrowth = sessionLengths.length > 2
      ? (sessionLengths[sessionLengths.length - 1] - sessionLengths[0]) / sessionLengths.length
      : 0;

    return {
      totalSessions: sessions.length,
      daysPlayedLast7: new Set(last7.map(s => new Date(s.timestamp).toDateString())).size,
      daysPlayedLast30: new Set(last30.map(s => new Date(s.timestamp).toDateString())).size,
      consecutiveDays: consecutive,
      avgLossPerSession: last7.reduce((a, b) => a + (b.totalLost || 0), 0) / Math.max(1, last7.length),
      totalLostAllTime: sessions.reduce((a, b) => a + (b.totalLost || 0), 0),
      totalDepositsAllTime: sessions.reduce((a, b) => a + (b.totalDeposits || 0), 0),
      avgSessionLength: last7.reduce((a, b) => a + (b.sessionLengthMinutes || 0), 0) / Math.max(1, last7.length),
      sessionsWithHighRisk: sessions.filter(s => (s.riskScore || 0) >= 70).length,
      lossGrowthRate: lossGrowth,
      sessionGrowthRate: sessionGrowth,
    };
  }

  saveCurrentSession() {
    try {
      const raw = localStorage.getItem('em_sessions');
      const sessions = raw ? JSON.parse(raw) : [];
      sessions.push({
        timestamp: Date.now(),
        sessionId: this.metrics.sessionId,
        totalLost: this.metrics.totalLost,
        totalWon: this.metrics.totalWon,
        totalDeposits: this.metrics.totalDeposits,
        sessionLengthMinutes: this.metrics.sessionLengthMinutes,
        riskScore: this.metrics.riskScore,
        depositsPerSession: this.metrics.depositsPerSession,
        chasingLossEvents: this.metrics.chasingLossEvents,
      });
      // Храним последние 60 сессий
      localStorage.setItem('em_sessions', JSON.stringify(sessions.slice(-60)));
    } catch (e) {
      console.warn('localStorage save failed:', e);
    }
  }

  // ============================================
  // BET TRACKING
  // ============================================
  logBet(amount, game, currentBalance) {
    const now = Date.now();

    // Время между ставками
    if (this.metrics.lastBetTime) {
      const gap = (now - this.metrics.lastBetTime) / 1000;
      this.metrics.timeBetweenBets.push(gap);
      if (gap < 10) this.metrics.rapidBetCount++;
    }

    // Смена игры
    if (this.metrics.lastGame && this.metrics.lastGame !== game) {
      this.metrics.switchedGameCount++;
    }

    // Ставка / Баланс ratio
    if (currentBalance > 0) {
      const ratio = amount / currentBalance;
      const ratios = this.metrics.betAmounts.map((b, i) => {
        const bal = this.metrics.lastBalance || currentBalance;
        return b / bal;
      });
      ratios.push(ratio);
      this.metrics.avgBetToBalanceRatio = ratios.reduce((a, b) => a + b, 0) / ratios.length;
      if (ratio > 0.3) this.metrics.highBetToBalanceCount++;
    }

    // Мартингейл: ставка удвоилась после проигрыша
    if (
      this.metrics.lastBetResult === 'loss' &&
      this.metrics.lastBetAmount &&
      amount >= this.metrics.lastBetAmount * 1.8
    ) {
      this.metrics.martingaleEvents++;
    }

    // Реинвестирование выигрыша: после победы ставит значительно больше
    if (
      this.metrics.lastBetResult === 'win' &&
      this.metrics.lastBetAmount &&
      amount >= this.metrics.lastBetAmount * 1.5
    ) {
      this.metrics.reinvestmentEvents++;
    }

    // Rapid series: 3+ ставки быстрее 8 сек подряд
    const recentTimes = this.metrics.timeBetweenBets.slice(-3);
    if (recentTimes.length === 3 && recentTimes.every(t => t < 8)) {
      this.metrics.rapidSeriesCount++;
    }

    this.metrics.lastGame = game;
    this.metrics.lastBetTime = now;
    this.metrics.lastBalance = currentBalance;
    this.metrics.totalBets++;
    this.metrics.betAmounts.push(amount);
    this.metrics.betTimestamps.push(now);

    this.logEvent('bet', { amount, game, balance: currentBalance, ts: now });
  }

  logResult(won, amount, newBalance) {
    const result = won ? 'win' : 'loss';
    this.metrics.betResults.push(result);

    // Chasing losses
    if (this.metrics.lastBetResult === 'loss' && !won) {
      this.metrics.chasingLossEvents++;
    }

    // Увеличение ставки после проигрыша
    const bets = this.metrics.betAmounts;
    if (this.metrics.lastBetResult === 'loss' && bets.length >= 2) {
      if (bets[bets.length - 1] > bets[bets.length - 2]) {
        this.metrics.betIncreaseAfterLoss++;
      }
    }

    // Loss streak
    if (!won) {
      this.metrics.lossStreakCurrent++;
      this.metrics.winStreakCurrent = 0;
      if (this.metrics.lossStreakCurrent > this.metrics.lossStreakMax) {
        this.metrics.lossStreakMax = this.metrics.lossStreakCurrent;
      }
      if (this.metrics.lossStreakCurrent >= 5) {
        this.metrics.lossStreak5Plus++;
      }
    } else {
      this.metrics.lossStreakCurrent = 0;
      this.metrics.winStreakCurrent++;
    }

    // Баланс опустошён
    if (newBalance < 5) this.metrics.accountDepleted++;

    // Ставки растут к концу сессии
    this.updateEscalationRate();

    if (won) this.metrics.totalWon += amount;
    else this.metrics.totalLost += amount;

    this.metrics.lastBetResult = result;
    this.metrics.lastBetAmount = bets[bets.length - 1];

    this.logEvent('result', { won, amount, newBalance });
  }

  logDeposit(amount) {
    this.metrics.totalDeposits += amount;
    this.metrics.depositsPerSession++;
    this.logEvent('deposit', { amount, ts: Date.now() });
  }

  logFailedDeposit() {
    this.metrics.failedDepositAttempts++;
  }

  logEvent(type, data) {
    this.events.push({ type, data, time: Date.now() });
  }

  // Эскалация ставок: сравниваем первую и вторую половину сессии
  updateEscalationRate() {
    const bets = this.metrics.betAmounts;
    if (bets.length < 6) return;
    const half = Math.floor(bets.length / 2);
    const firstHalf = bets.slice(0, half);
    const secondHalf = bets.slice(half);
    const avgFirst = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const avgSecond = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
    if (avgFirst > 0) {
      this.metrics.betEscalationRate = (avgSecond - avgFirst) / avgFirst;
    }
  }

  // ============================================
  // TENSORFLOW.JS — 14 FEATURE NEURAL NETWORK
  // ============================================
  async initTFModel() {
    try {
      if (typeof tf === 'undefined') {
        setTimeout(() => this.initTFModel(), 2000);
        return;
      }

      this.tfModel = tf.sequential({
        layers: [
          tf.layers.dense({
            inputShape: [14], units: 64, activation: 'relu',
            kernelRegularizer: tf.regularizers.l2({ l2: 0.001 })
          }),
          tf.layers.batchNormalization(),
          tf.layers.dropout({ rate: 0.3 }),
          tf.layers.dense({ units: 32, activation: 'relu' }),
          tf.layers.dropout({ rate: 0.2 }),
          tf.layers.dense({ units: 16, activation: 'relu' }),
          tf.layers.dense({ units: 1, activation: 'sigmoid' })
        ]
      });

      this.tfModel.compile({
        optimizer: tf.train.adam(0.001),
        loss: 'binaryCrossentropy',
        metrics: ['accuracy']
      });

      await this.trainModel();
      this.modelReady = true;
      window.dispatchEvent(new CustomEvent('modelStatus', { detail: 'tfjs' }));
      console.log('✅ TF.js модель (14 фич) готова');
    } catch (e) {
      console.error('TF init error:', e);
    }
  }

  async trainModel() {
    const { X, y } = this.generateSyntheticData(3000);
    const xs = tf.tensor2d(X);
    const ys = tf.tensor2d(y, [y.length, 1]);

    await this.tfModel.fit(xs, ys, {
      epochs: 50,
      batchSize: 64,
      validationSplit: 0.15,
      shuffle: true,
      classWeight: { 0: 1, 1: 3 }, // Лудоманы весят больше
      verbose: 0
    });

    xs.dispose();
    ys.dispose();
  }

  // Синтетические данные — 14 фич, основаны на статье
  generateSyntheticData(n = 3000) {
    const X = [], y = [];
    for (let i = 0; i < n; i++) {
      const isPG = Math.random() < 0.28;
      if (isPG) {
        X.push([
          Math.min(1, (Math.random() * 3 + 1.5) / 6),    // depositsPerSession
          Math.min(1, (Math.random() * 3 + 1.5) / 6),    // accountDepleted
          Math.min(1, (Math.random() * 5 + 2) / 10),     // chasingLossEvents
          Math.min(1, (Math.random() * 8 + 3) / 15),     // rapidBetCount
          Math.min(1, (Math.random() * 90 + 40) / 180),  // sessionMinutes
          Math.min(1, (Math.random() * 4 + 2) / 8),      // betIncreaseAfterLoss
          Math.random() < 0.45 ? 1 : 0,                  // nightSession
          Math.min(1, (Math.random() * 4 + 1) / 8),      // switchedGame
          Math.min(1, (Math.random() * 4 + 2) / 8),      // martingaleEvents
          Math.min(1, (Math.random() * 3 + 1) / 6),      // reinvestmentEvents
          Math.min(1, Math.random() * 0.5 + 0.3),        // betEscalationRate
          Math.min(1, Math.random() * 0.6 + 0.2),        // avgBetToBalanceRatio
          Math.min(1, (Math.random() * 3 + 1) / 5),      // lossStreak5Plus
          Math.min(1, (Math.random() * 5 + 2) / 10),     // crossSession.consecutiveDays / 14
        ]);
      } else {
        X.push([
          Math.min(1, Math.random() * 1.2 / 6),
          Math.min(1, Math.random() * 1.0 / 6),
          Math.min(1, Math.random() * 1.5 / 10),
          Math.min(1, Math.random() * 3 / 15),
          Math.min(1, (Math.random() * 35 + 5) / 180),
          Math.min(1, Math.random() * 1.5 / 8),
          Math.random() < 0.18 ? 1 : 0,
          Math.min(1, Math.random() * 2 / 8),
          Math.min(1, Math.random() * 1.5 / 8),
          Math.min(1, Math.random() * 1 / 6),
          Math.min(1, Math.random() * 0.2),
          Math.min(1, Math.random() * 0.15),
          Math.min(1, Math.random() * 1 / 5),
          Math.min(1, Math.random() * 2 / 10),
        ]);
      }
      y.push(isPG ? 1 : 0);
    }
    return { X, y };
  }

  async predictWithTF(features) {
    if (!this.modelReady || !this.tfModel) return null;
    try {
      const input = tf.tensor2d([features]);
      const pred = this.tfModel.predict(input);
      const score = (await pred.data())[0];
      input.dispose(); pred.dispose();
      return Math.round(score * 100);
    } catch (e) {
      return null;
    }
  }

  async predictWithBackend(snapshot) {
    try {
      const res = await fetch('/api/easymoney/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(snapshot),
        signal: AbortSignal.timeout(800)
      });
      if (!res.ok) return null;
      const data = await res.json();
      return data;
    } catch { return null; }
  }

  // 14 фич нормализованных
  getFeatureVector() {
    const cs = this.metrics.crossSession;
    return [
      Math.min(1, this.metrics.depositsPerSession / 6),
      Math.min(1, this.metrics.accountDepleted / 6),
      Math.min(1, this.metrics.chasingLossEvents / 10),
      Math.min(1, this.metrics.rapidBetCount / 15),
      Math.min(1, this.metrics.sessionLengthMinutes / 180),
      Math.min(1, this.metrics.betIncreaseAfterLoss / 8),
      this.metrics.nightSession ? 1 : 0,
      Math.min(1, this.metrics.switchedGameCount / 8),
      Math.min(1, this.metrics.martingaleEvents / 8),
      Math.min(1, this.metrics.reinvestmentEvents / 6),
      Math.min(1, Math.max(0, this.metrics.betEscalationRate)),
      Math.min(1, this.metrics.avgBetToBalanceRatio),
      Math.min(1, this.metrics.lossStreak5Plus / 5),
      Math.min(1, (cs.consecutiveDays || 0) / 14),
    ];
  }

  // ============================================
  // RULE-BASED SCORE — расширенный
  // ============================================
  calculateRuleScore() {
    let score = 0;
    const m = this.metrics;
    const cs = m.crossSession;

    // --- СЕССИОННЫЕ СИГНАЛЫ ---
    if (this.isHighRiskTime()) score += 15;       // 1-5 утра
    else if (this.isNightTime()) score += 8;

    // Длина сессии
    if (m.sessionLengthMinutes > 30)  score += 5;
    if (m.sessionLengthMinutes > 60)  score += 10;
    if (m.sessionLengthMinutes > 120) score += 10;
    if (m.sessionLengthMinutes > 180) score += 5;

    // Депозиты
    if (m.depositsPerSession >= 2) score += 15;
    if (m.depositsPerSession >= 3) score += 15;
    if (m.depositsPerSession >= 5) score += 10;

    // Счёт опустошён
    if (m.accountDepleted >= 1) score += 10;
    if (m.accountDepleted >= 3) score += 15;

    // Погоня за потерями
    if (m.chasingLossEvents >= 2)  score += 15;
    if (m.chasingLossEvents >= 5)  score += 10;

    // Быстрые ставки
    if (m.rapidBetCount >= 5)  score += 8;
    if (m.rapidSeriesCount >= 2) score += 10;

    // --- НОВЫЕ СИГНАЛЫ ---
    // Мартингейл
    if (m.martingaleEvents >= 2) score += 20;
    if (m.martingaleEvents >= 4) score += 10;

    // Реинвестирование
    if (m.reinvestmentEvents >= 3) score += 10;

    // Ставка > 30% баланса
    if (m.highBetToBalanceCount >= 3) score += 10;
    if (m.avgBetToBalanceRatio > 0.3)  score += 10;

    // Эскалация ставок
    if (m.betEscalationRate > 0.3) score += 10;
    if (m.betEscalationRate > 0.7) score += 10;

    // Серии проигрышей
    if (m.lossStreakMax >= 5)  score += 10;
    if (m.lossStreak5Plus >= 2) score += 10;

    // Неудавшиеся депозиты
    if (m.failedDepositAttempts >= 2) score += 10;

    // --- МЕЖСЕССИОННЫЕ СИГНАЛЫ ---
    if (cs.consecutiveDays >= 5)  score += 15;
    if (cs.consecutiveDays >= 10) score += 10;
    if (cs.daysPlayedLast7 >= 5)  score += 10;
    if (cs.sessionsWithHighRisk >= 3) score += 15;
    if (cs.lossGrowthRate > 5)    score += 10;
    if (cs.totalSessions >= 20)   score += 5;

    return Math.min(100, score);
  }

  // ============================================
  // FINAL SCORE (ансамбль)
  // ============================================
  async calculateFinalScore() {
    const ruleScore = this.calculateRuleScore();
    this.metrics.ruleRiskScore = ruleScore;

    const snapshot = this.getSnapshot();

    // Попытка backend
    const backendResult = await this.predictWithBackend(snapshot);
    if (backendResult) {
      this.metrics.mlRiskScore = backendResult.riskScore;
      this.metrics.modelSource = 'backend';
      this.metrics.riskScore = Math.round(backendResult.riskScore * 0.65 + ruleScore * 0.35);
      window.dispatchEvent(new CustomEvent('modelStatus', { detail: 'backend' }));
      return;
    }

    // TF.js
    if (this.modelReady) {
      const fv = this.getFeatureVector();
      const tfScore = await this.predictWithTF(fv);
      if (tfScore !== null) {
        this.metrics.mlRiskScore = tfScore;
        this.metrics.modelSource = 'tfjs';
        this.metrics.riskScore = Math.round(tfScore * 0.65 + ruleScore * 0.35);
        return;
      }
    }

    // Fallback
    this.metrics.mlRiskScore = ruleScore;
    this.metrics.modelSource = 'rules';
    this.metrics.riskScore = ruleScore;
  }

  // ============================================
  // LOOP
  // ============================================
  startTracking() {
    setInterval(async () => {
      this.metrics.sessionLengthMinutes = Math.floor((Date.now() - this.sessionStart) / 60000);
      await this.calculateFinalScore();
      this.saveCurrentSession();
      this.updateDashboard();
    }, 4000);
  }

  getRiskLevel() {
    const s = this.metrics.riskScore;
    if (s >= 70) return { level: 'HIGH',   color: '#ff3333', emoji: '🔴' };
    if (s >= 40) return { level: 'MEDIUM', color: '#ff9900', emoji: '🟠' };
    return         { level: 'LOW',    color: '#00ff88', emoji: '🟢' };
  }

  updateDashboard() {
    window.dispatchEvent(new CustomEvent('behaviorUpdate', { detail: this.getSnapshot() }));
  }

  getSnapshot() {
    const bets = this.metrics.betAmounts;
    const avgBet = bets.length > 0 ? bets.reduce((a, b) => a + b, 0) / bets.length : 0;
    const variance = bets.length > 1
      ? bets.reduce((a, b) => a + Math.pow(b - avgBet, 2), 0) / bets.length : 0;
    const times = this.metrics.timeBetweenBets;
    const avgTime = times.length > 0 ? times.reduce((a, b) => a + b, 0) / times.length : 0;

    return {
      ...this.metrics,
      avgBetAmount: parseFloat(avgBet.toFixed(2)),
      stdBetAmount: parseFloat(Math.sqrt(variance).toFixed(2)),
      avgTimeBetweenBets: parseFloat(avgTime.toFixed(1)),
      riskLevel: this.getRiskLevel(),
      netBalance: parseFloat((this.metrics.totalWon - this.metrics.totalLost).toFixed(2)),
      featureVector: this.getFeatureVector(),
      featureNames: [
        'Депозиты/сессия','Счёт опустошён','Chasing losses','Быстрые ставки',
        'Длина сессии','Рост ставок','Ночная игра','Смена игр',
        'Мартингейл','Реинвест выигрыша','Эскалация','Ставка/баланс',
        'Серии 5+ потерь','Дни подряд'
      ],
    };
  }

  exportJSON() {
    return JSON.stringify(this.getSnapshot(), null, 2);
  }

  clearHistory() {
    localStorage.removeItem('em_sessions');
    location.reload();
  }
}

window.tracker = new BehaviorTracker();
