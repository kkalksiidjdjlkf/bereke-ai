// =============================================
// Easy Money.Bet — Slots Game Logic
// =============================================

class SlotsGame {
  constructor(tracker) {
    this.tracker = tracker;
    this.symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎', '7️⃣', '🎰'];
    this.payouts = {
      '💎💎💎': 50,
      '7️⃣7️⃣7️⃣': 30,
      '⭐⭐⭐': 20,
      '🍇🍇🍇': 10,
      '🍊🍊🍊': 8,
      '🍋🍋🍋': 6,
      '🍒🍒🍒': 4,
      '🎰🎰🎰': 100,
    };
    this.spinning = false;
  }

  spin(betAmount, currentBalance) {
    if (this.spinning) return null;
    this.spinning = true;

    this.tracker.logBet(betAmount, 'slots');

    // Генерируем результат с небольшим перевесом в пользу казино (RTP ~94%)
    const reels = this.generateReels();
    const winMultiplier = this.checkWin(reels);
    const winAmount = winMultiplier > 0 ? betAmount * winMultiplier : 0;
    const newBalance = currentBalance - betAmount + winAmount;

    this.tracker.logResult(winAmount > 0, winAmount > 0 ? winAmount : betAmount, newBalance);

    this.spinning = false;
    return {
      reels,
      winAmount,
      winMultiplier,
      newBalance,
      won: winAmount > 0,
    };
  }

  generateReels() {
    // Взвешенная вероятность — редкие символы реже
    const weights = [20, 18, 16, 12, 10, 8, 6, 4]; // чем выше индекс тем реже
    const reels = [];

    for (let i = 0; i < 3; i++) {
      const rand = Math.random() * weights.reduce((a, b) => a + b, 0);
      let cumWeight = 0;
      for (let j = 0; j < this.symbols.length; j++) {
        cumWeight += weights[j];
        if (rand < cumWeight) {
          reels.push(this.symbols[j]);
          break;
        }
      }
    }
    return reels;
  }

  checkWin(reels) {
    const key = reels.join('');
    if (this.payouts[key]) return this.payouts[key];
    // Два одинаковых — маленький выигрыш
    if (reels[0] === reels[1] || reels[1] === reels[2]) return 1.5;
    return 0;
  }
}

// =============================================
// Roulette Game Logic
// =============================================

class RouletteGame {
  constructor(tracker) {
    this.tracker = tracker;
    this.spinning = false;
  }

  spin(betType, betAmount, currentBalance) {
    if (this.spinning) return null;
    this.spinning = true;

    this.tracker.logBet(betAmount, 'roulette');

    const number = Math.floor(Math.random() * 37); // 0-36
    const result = this.evaluateBet(betType, number, betAmount);
    const newBalance = currentBalance - betAmount + result.winAmount;

    this.tracker.logResult(result.won, result.won ? result.winAmount : betAmount, newBalance);

    this.spinning = false;
    return { number, ...result, newBalance };
  }

  evaluateBet(betType, number, betAmount) {
    const red = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
    const isRed = red.includes(number);
    const isBlack = number > 0 && !isRed;
    const isEven = number > 0 && number % 2 === 0;
    const isOdd = number > 0 && number % 2 !== 0;

    let won = false;
    let multiplier = 0;

    switch (betType) {
      case 'red': won = isRed; multiplier = 2; break;
      case 'black': won = isBlack; multiplier = 2; break;
      case 'even': won = isEven; multiplier = 2; break;
      case 'odd': won = isOdd; multiplier = 2; break;
      case 'low': won = number >= 1 && number <= 18; multiplier = 2; break;
      case 'high': won = number >= 19 && number <= 36; multiplier = 2; break;
      case 'dozen1': won = number >= 1 && number <= 12; multiplier = 3; break;
      case 'dozen2': won = number >= 13 && number <= 24; multiplier = 3; break;
      case 'dozen3': won = number >= 25 && number <= 36; multiplier = 3; break;
      default:
        // Прямая ставка на число
        won = parseInt(betType) === number;
        multiplier = 36;
    }

    const winAmount = won ? betAmount * multiplier : 0;
    return { won, winAmount, multiplier };
  }

  getNumberColor(num) {
    if (num === 0) return 'green';
    const red = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
    return red.includes(num) ? 'red' : 'black';
  }
}

// =============================================
// Crash Game Logic
// =============================================

class CrashGame {
  constructor(tracker) {
    this.tracker = tracker;
    this.running = false;
    this.multiplier = 1.0;
    this.crashPoint = 0;
    this.interval = null;
  }

  start(betAmount, currentBalance, onTick, onCrash) {
    if (this.running) return;
    this.running = true;
    this.multiplier = 1.0;
    this.crashPoint = this.generateCrashPoint();

    this.tracker.logBet(betAmount, 'crash');

    this.interval = setInterval(() => {
      this.multiplier += 0.01 * this.multiplier;
      this.multiplier = parseFloat(this.multiplier.toFixed(2));

      onTick(this.multiplier);

      if (this.multiplier >= this.crashPoint) {
        this.running = false;
        clearInterval(this.interval);
        const newBalance = currentBalance - betAmount;
        this.tracker.logResult(false, betAmount, newBalance);
        onCrash(this.crashPoint, newBalance);
      }
    }, 50);

    return this.crashPoint;
  }

  cashout(betAmount, currentBalance) {
    if (!this.running) return null;
    this.running = false;
    clearInterval(this.interval);

    const winAmount = betAmount * this.multiplier;
    const newBalance = currentBalance - betAmount + winAmount;
    this.tracker.logResult(true, winAmount, newBalance);

    return { multiplier: this.multiplier, winAmount, newBalance };
  }

  generateCrashPoint() {
    // Казино имеет 5% преимущество
    const e = 2 ** 52;
    const h = Math.floor(Math.random() * e);
    if (h === 0) return 1.0;
    const crash = (e - h) / (h * 0.05) + 1;
    return parseFloat(Math.max(1.0, Math.min(crash, 100)).toFixed(2));
  }
}

window.SlotsGame = SlotsGame;
window.RouletteGame = RouletteGame;
window.CrashGame = CrashGame;
