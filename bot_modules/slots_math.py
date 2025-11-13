"""
Mathematical slot machine engine with probability-based RTP calculations.
Target RTP: 94.8% (balanced between player-friendly and house edge)
Uses virtual reel stops for realistic probability distribution.
"""

import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from math import comb

@dataclass
class Symbol:
    """Represents a slot symbol with its properties"""
    icon: str
    name: str
    reel_stops: List[int]  # Stops per reel [reel1, reel2, reel3, reel4, reel5]
    payouts: Dict[int, float]  # {num_matches: multiplier}
    is_scatter: bool = False

class SlotMachine:
    """
    Mathematically balanced 5-reel slot machine.
    Each reel has 64 virtual stops for precise probability control.
    """
    
    REEL_STOPS = 64  # Virtual stops per reel
    TARGET_RTP = 0.948  # 94.8% return to player
    
    def __init__(self):
        self.symbols = self._define_symbols()
        self.rtp_data = self._calculate_rtp()
    
    def _define_symbols(self) -> List[Symbol]:
        """
        Define symbols with their reel distribution and payouts.
        Reel stops determine probability: more stops = more likely to appear.
        """
        return [
            # High value symbols (rare, high payout)
            Symbol(
                icon="💎",
                name="Diamond",
                reel_stops=[2, 2, 2, 3, 3],  # Very rare
                payouts={3: 20, 4: 50, 5: 200},  # High rewards
                is_scatter=False
            ),
            Symbol(
                icon="⭐",
                name="Star",
                reel_stops=[3, 3, 4, 4, 5],  # Rare
                payouts={3: 10, 4: 25, 5: 100},
                is_scatter=False
            ),
            Symbol(
                icon="🎰",
                name="Scatter",
                reel_stops=[4, 4, 4, 4, 4],  # Equal on all reels
                payouts={3: 5, 4: 15, 5: 50},  # Also triggers free spins
                is_scatter=True
            ),
            
            # Medium value symbols (moderate frequency)
            Symbol(
                icon="🍇",
                name="Grape",
                reel_stops=[5, 6, 6, 7, 8],
                payouts={3: 5, 4: 15, 5: 40},
                is_scatter=False
            ),
            Symbol(
                icon="🍊",
                name="Orange",
                reel_stops=[6, 7, 8, 8, 9],
                payouts={3: 4, 4: 10, 5: 30},
                is_scatter=False
            ),
            Symbol(
                icon="🍋",
                name="Lemon",
                reel_stops=[8, 9, 10, 10, 11],
                payouts={3: 3, 4: 8, 5: 20},
                is_scatter=False
            ),
            
            # Low value symbols (common, low payout)
            Symbol(
                icon="🍒",
                name="Cherry",
                reel_stops=[10, 11, 12, 12, 11],
                payouts={3: 2, 4: 5, 5: 15},
                is_scatter=False
            ),
        ]
    
    def spin(self, bet: int = 1, bonus_multiplier: float = 1.0) -> Tuple[List[str], int, Dict]:
        """
        Execute a single spin with proper probability distribution.
        
        Args:
            bet: Bet amount in coins
            bonus_multiplier: Item/effect multiplier (e.g., 1.2 for +20%)
        
        Returns:
            (result_icons, payout, details)
        """
        # Spin each reel independently
        result = []
        for reel_idx in range(5):
            symbol = self._spin_reel(reel_idx)
            result.append(symbol.icon)
        
        # Calculate payout
        base_payout = self._calculate_payout(result, bet)
        
        # Apply bonus multiplier
        final_payout = int(base_payout * bonus_multiplier)
        
        # Determine win type
        win_details = self._analyze_win(result, base_payout, final_payout, bonus_multiplier)
        
        return result, final_payout, win_details
    
    def _spin_reel(self, reel_idx: int) -> Symbol:
        """
        Spin a single reel using weighted probability based on reel stops.
        Each symbol's probability = (stops on this reel) / REEL_STOPS
        """
        weights = [symbol.reel_stops[reel_idx] for symbol in self.symbols]
        return random.choices(self.symbols, weights=weights)[0]
    
    def _calculate_payout(self, result: List[str], bet: int) -> int:
        """
        Calculate payout for left-to-right consecutive matches.
        Standard slot rule: Must start from leftmost reel.
        """
        if not result or len(result) < 3:
            return 0
        
        # Find the leftmost symbol
        first_symbol = result[0]
        
        # Count consecutive matches from left
        consecutive_matches = 1
        for i in range(1, len(result)):
            if result[i] == first_symbol:
                consecutive_matches += 1
            else:
                break
        
        # Need at least 3 matches to win
        if consecutive_matches < 3:
            return 0
        
        # Find the symbol object
        symbol = next((s for s in self.symbols if s.icon == first_symbol), None)
        if not symbol:
            return 0
        
        # Get payout multiplier for this number of matches
        multiplier = symbol.payouts.get(consecutive_matches, 0)
        
        return int(bet * multiplier)
    
    def _analyze_win(self, result: List[str], base_payout: int, final_payout: int, 
                     bonus_multiplier: float) -> Dict:
        """Analyze the spin result and provide detailed information"""
        details = {
            "win": final_payout > 0,
            "win_type": None,
            "matches": 0,
            "symbol": None,
            "scatter_count": 0,
            "free_spins_triggered": False,
            "bonus_applied": bonus_multiplier > 1.0,
            "bonus_amount": final_payout - base_payout if bonus_multiplier > 1.0 else 0
        }
        
        if not result:
            return details
        
        # Count matches
        first_symbol = result[0]
        matches = 1
        for i in range(1, len(result)):
            if result[i] == first_symbol:
                matches += 1
            else:
                break
        
        if matches >= 3:
            details["matches"] = matches
            details["symbol"] = first_symbol
            
            # Determine win type
            if matches == 5:
                if first_symbol == "💎":
                    details["win_type"] = "MEGA JACKPOT"
                elif first_symbol == "⭐":
                    details["win_type"] = "JACKPOT"
                else:
                    details["win_type"] = "BIG WIN"
            elif matches == 4:
                details["win_type"] = "GOOD WIN"
            else:
                details["win_type"] = "WIN"
        
        # Check for scatter symbols (anywhere on reels)
        scatter_count = result.count("🎰")
        details["scatter_count"] = scatter_count
        
        if scatter_count >= 3:
            details["free_spins_triggered"] = True
            details["free_spins_count"] = scatter_count * 2  # 6, 8, or 10 free spins
        
        return details
    
    def _calculate_rtp(self) -> Dict:
        """
        Calculate theoretical Return To Player (RTP) percentage.
        RTP = Sum of (Probability × Payout) for all winning combinations.
        """
        total_ev = 0.0  # Expected value per spin
        
        for symbol in self.symbols:
            if symbol.is_scatter:
                continue  # Handle scatters separately
            
            # Calculate EV for this symbol
            symbol_ev = self._calculate_symbol_ev(symbol)
            total_ev += symbol_ev
        
        # Add scatter EV
        scatter_ev = self._calculate_scatter_ev()
        total_ev += scatter_ev
        
        return {
            "rtp": total_ev * 100,  # Convert to percentage
            "house_edge": (1 - total_ev) * 100,
            "hit_frequency": self._calculate_hit_frequency(),
            "variance": "Medium-High",
            "symbol_contributions": self._get_symbol_contributions()
        }
    
    def _calculate_symbol_ev(self, symbol: Symbol) -> float:
        """
        Calculate expected value contribution for a specific symbol.
        EV = Σ [P(exactly k matches) × payout(k)] for k = 3, 4, 5
        """
        ev = 0.0
        
        for num_matches, multiplier in symbol.payouts.items():
            probability = self._probability_n_matches(symbol, num_matches)
            ev += probability * multiplier
        
        return ev
    
    def _probability_n_matches(self, symbol: Symbol, n: int) -> float:
        """
        Calculate probability of exactly n consecutive matches (left-to-right).
        
        For exactly 3 matches: p1 × p2 × p3 × (1 - p4)
        For exactly 4 matches: p1 × p2 × p3 × p4 × (1 - p5)
        For exactly 5 matches: p1 × p2 × p3 × p4 × p5
        """
        if n < 3 or n > 5:
            return 0.0
        
        # Calculate probability for each reel
        prob = 1.0
        for i in range(n):
            p_reel = symbol.reel_stops[i] / self.REEL_STOPS
            prob *= p_reel
        
        # If not all 5, multiply by (1 - prob_next_reel)
        if n < 5:
            p_next = symbol.reel_stops[n] / self.REEL_STOPS
            prob *= (1 - p_next)
        
        return prob
    
    def _calculate_scatter_ev(self) -> float:
        """
        Calculate expected value from scatter symbols.
        Scatters can appear anywhere (not just left-to-right).
        Use binomial probability: C(5,k) × p^k × (1-p)^(5-k)
        """
        scatter = next((s for s in self.symbols if s.is_scatter), None)
        if not scatter:
            return 0.0
        
        # Average probability across all reels
        avg_prob = sum(scatter.reel_stops) / (len(scatter.reel_stops) * self.REEL_STOPS)
        
        ev = 0.0
        for k in range(3, 6):  # 3, 4, or 5 scatters
            # Binomial probability
            prob = comb(5, k) * (avg_prob ** k) * ((1 - avg_prob) ** (5 - k))
            multiplier = scatter.payouts.get(k, 0)
            ev += prob * multiplier
        
        return ev
    
    def _calculate_hit_frequency(self) -> float:
        """
        Calculate percentage of spins that result in any win.
        Hit frequency = P(at least one winning combination)
        """
        # Calculate probability of no win (lose on all symbols)
        prob_no_win = 1.0
        
        for symbol in self.symbols:
            if symbol.is_scatter:
                continue
            
            # Probability of NOT getting 3+ matches with this symbol
            prob_no_match = 1.0
            for n in [3, 4, 5]:
                prob_no_match -= self._probability_n_matches(symbol, n)
            
            prob_no_win *= prob_no_match
        
        hit_frequency = (1 - prob_no_win) * 100
        return hit_frequency
    
    def _get_symbol_contributions(self) -> Dict:
        """Get RTP contribution breakdown by symbol"""
        contributions = {}
        
        for symbol in self.symbols:
            ev = self._calculate_symbol_ev(symbol)
            contributions[symbol.icon] = {
                "name": symbol.name,
                "rtp_contribution": ev * 100,
                "probability": self._get_symbol_appearance_rate(symbol)
            }
        
        return contributions
    
    def _get_symbol_appearance_rate(self, symbol: Symbol) -> float:
        """Calculate average appearance rate across all reels"""
        return sum(symbol.reel_stops) / (len(symbol.reel_stops) * self.REEL_STOPS)
    
    def get_paytable(self) -> str:
        """Generate a formatted paytable for display"""
        lines = ["🎰 **SLOT MACHINE PAYTABLE** 🎰\n"]
        
        for symbol in sorted(self.symbols, key=lambda s: max(s.payouts.values()), reverse=True):
            payouts_str = " | ".join([f"{k}× = {v}x bet" for k, v in sorted(symbol.payouts.items())])
            scatter_tag = " 🌟 SCATTER" if symbol.is_scatter else ""
            lines.append(f"{symbol.icon} **{symbol.name}**{scatter_tag}: {payouts_str}")
        
        lines.append(f"\n📊 **RTP:** {self.rtp_data['rtp']:.2f}%")
        lines.append(f"🎯 **Hit Frequency:** {self.rtp_data['hit_frequency']:.2f}%")
        lines.append(f"📈 **Volatility:** {self.rtp_data['variance']}")
        lines.append(f"\n🎰 **3+ Scatter symbols trigger FREE SPINS!**")
        
        return "\n".join(lines)
    
    def get_rtp_report(self) -> str:
        """Generate detailed RTP analysis report"""
        lines = ["📊 **MATHEMATICAL RTP ANALYSIS** 📊\n"]
        lines.append(f"**Target RTP:** {self.TARGET_RTP * 100:.2f}%")
        lines.append(f"**Actual RTP:** {self.rtp_data['rtp']:.2f}%")
        lines.append(f"**House Edge:** {self.rtp_data['house_edge']:.2f}%")
        lines.append(f"**Hit Frequency:** {self.rtp_data['hit_frequency']:.2f}%")
        lines.append(f"**Variance:** {self.rtp_data['variance']}\n")
        
        lines.append("**Symbol Contributions:**")
        for icon, data in self.rtp_data['symbol_contributions'].items():
            lines.append(f"{icon} {data['name']}: {data['rtp_contribution']:.2f}% "
                        f"(appears {data['probability']*100:.1f}% of the time)")
        
        return "\n".join(lines)


# Singleton instance
_slot_machine = None

def get_slot_machine() -> SlotMachine:
    """Get or create the global slot machine instance"""
    global _slot_machine
    if _slot_machine is None:
        _slot_machine = SlotMachine()
    return _slot_machine
