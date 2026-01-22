from sim_double_stb import (
    display_board, flip_tile, get_valid_combinations, 
    check_win, calculate_score
)
import copy
import random
from collections import defaultdict
from itertools import combinations

def get_all_possible_dice_rolls(score):
    """Get all possible dice roll outcomes given current score."""
    if score <= 6:
        # Single die mode
        return [(i, 0) for i in range(1, 7)]
    else:
        # Two dice mode
        return [(i, j) for i in range(1, 7) for j in range(1, 7)]

def evaluate_move_strategic(state_after_move, move):
    """Evaluate strategic value of a move beyond just score reduction.
    
    Args:
        state_after_move: Game state after the move has been applied
        move: The move that was made (for calculating value of removed tiles)
    """
    strategic_value = 0
    
    # Prefer removing high-value tiles (especially from row 2)
    for row, num in move:
        if row == 2:
            strategic_value += num * 3  # Row 2 tiles worth more
        else:
            strategic_value += num
    
    # Prefer moves that maintain flexibility (keep more tiles available)
    remaining_tiles = sum(len(state_after_move.get(row, set())) for row in [1, 2])
    strategic_value += remaining_tiles * 0.5
    
    # Check if we're leaving useful combinations
    all_remaining = []
    for row in [1, 2]:
        if row in state_after_move:
            all_remaining.extend([(row, n) for n in state_after_move[row]])
    
    # Reward keeping tiles that can form common totals (7, 8, 9, 10, 11, 12)
    common_totals = [7, 8, 9, 10, 11, 12]
    for total in common_totals:
        for r in range(1, len(all_remaining) + 1):
            for combo in combinations(all_remaining, r):
                if sum(n for _, n in combo) == total:
                    strategic_value += 2
                    break
    
    return strategic_value

def calculate_expected_future_score(game_state, depth=1, samples=8):
    """Calculate expected future score using Monte Carlo simulation with lookahead.
    Optimized for performance with reduced depth and samples.
    """
    if depth == 0 or calculate_score(game_state) == 0:
        return calculate_score(game_state)
    
    current_score = calculate_score(game_state)
    if current_score == 0:
        return 0
    
    # Get all possible dice rolls
    possible_rolls = get_all_possible_dice_rolls(current_score)
    
    # Use fewer samples for performance
    num_samples = min(samples, len(possible_rolls))
    sampled_rolls = random.sample(possible_rolls, num_samples)
    
    total_expected = 0
    valid_rolls = 0
    
    for d1, d2 in sampled_rolls:
        target = d1 + d2
        valid_moves = get_valid_combinations(target, game_state)
        
        if not valid_moves:
            # No valid moves - game over, use current score
            total_expected += current_score
            valid_rolls += 1
            continue
        
        # For each roll, find the best move (greedy - just pick lowest immediate score)
        # Don't recurse to avoid exponential explosion
        best_future_score = float('inf')
        
        for move in valid_moves:
            temp_state = copy.deepcopy(game_state)
            for row, num in move:
                if row in temp_state and num in temp_state[row]:
                    temp_state[row].remove(num)
            
            # Only recurse if depth > 1, otherwise just use immediate score
            if depth > 1:
                future_score = calculate_expected_future_score(temp_state, depth - 1, max(3, samples // 2))
            else:
                future_score = calculate_score(temp_state)
            
            if future_score < best_future_score:
                best_future_score = future_score
        
        total_expected += best_future_score
        valid_rolls += 1
    
    if valid_rolls == 0:
        return current_score
    
    return total_expected / valid_rolls

def evaluate_move_comprehensive(game_state, move, depth=1, use_lookahead=True):
    """Comprehensive evaluation of a move considering multiple factors.
    
    Args:
        game_state: Current game state
        move: Move to evaluate
        depth: Lookahead depth (1 is usually sufficient for performance)
        use_lookahead: If False, skip expensive lookahead calculation
    """
    # Create temporary state after move
    temp_state = copy.deepcopy(game_state)
    for row, num in move:
        if row in temp_state and num in temp_state[row]:
            temp_state[row].remove(num)
    
    # Factor 1: Immediate score reduction (weight: 70% if no lookahead, 40% with lookahead)
    immediate_score = calculate_score(temp_state)
    score_reduction = calculate_score(game_state) - immediate_score
    weight1 = 0.4 if use_lookahead else 0.7
    score_factor = score_reduction * weight1
    
    # Factor 2: Expected future score with lookahead (weight: 40% if enabled)
    if use_lookahead:
        expected_future = calculate_expected_future_score(temp_state, depth=depth, samples=6)
        future_factor = (calculate_score(game_state) - expected_future) * 0.4
    else:
        future_factor = 0
    
    # Factor 3: Strategic value (weight: 20% if lookahead, 30% if no lookahead)
    weight3 = 0.2 if use_lookahead else 0.3
    strategic = evaluate_move_strategic(temp_state, move) * weight3
    
    # Combined evaluation (higher is better)
    total_value = score_factor + future_factor + strategic
    
    return total_value, immediate_score, expected_future if use_lookahead else immediate_score

def get_next_move(d1, d2, game_state):
    """
    Advanced algorithm to find the most optimal move using:
    1. Immediate score reduction
    2. Expected future score (Monte Carlo lookahead) - optimized for performance
    3. Strategic evaluation (tile values, flexibility, combinations)
    """
    target = d1 + d2
    possible_moves = get_valid_combinations(target, game_state)
    
    if not possible_moves:
        return None
    
    if len(possible_moves) == 1:
        return possible_moves[0]
    
    # For performance: if there are many moves, use lighter evaluation
    # Use lookahead only if there are fewer moves or game is getting close to end
    current_score = calculate_score(game_state)
    use_lookahead = len(possible_moves) <= 10 and current_score > 20
    
    # Evaluate all moves comprehensively
    move_evaluations = []
    
    for move in possible_moves:
        total_value, immediate_score, expected_future = evaluate_move_comprehensive(
            game_state, move, depth=1, use_lookahead=use_lookahead
        )
        move_evaluations.append({
            'move': move,
            'value': total_value,
            'immediate_score': immediate_score,
            'expected_future': expected_future if use_lookahead else immediate_score
        })
    
    # Sort by total value (descending - higher is better)
    move_evaluations.sort(key=lambda x: x['value'], reverse=True)
    
    # Return the best move
    best_move = move_evaluations[0]['move']
    
    return best_move


def main():

    # Init game state
    game_state = {1: {1, 2, 3, 4, 5, 6, 7, 8, 9},
                  2: {1, 2, 3, 4, 5, 6, 7, 8, 9}}

    print("\n" + "="*50)
    print("  Welcome to Shut the Box (AI Player Mode)")
    print("="*50)
    print("\nInstructions:")
    print("  - Enter two die values (1-6) each turn")
    print("  - The AI will find the best move automatically")
    print("  - Enter 0 for either die to exit at any time")
    print("  - Goal: Flip all tiles to score 0 points")
    input("\nPress Enter to start the game...")

    score = 135  # starting score
    turn = 1
    
    while True:
        display_board(game_state)
        
        print(f"--- Turn {turn} ---")
        score = calculate_score(game_state)
        
        # If score is 6 or less, only roll one die
        if score <= 6:
            while True:
                try:
                    d1_input = input("Enter die value (1-6, or 0 to exit) - single die mode: ").strip()
                    d1 = int(d1_input)
                    if d1 == 0:
                        print("\nExiting the game.")
                        return
                    if d1 < 1 or d1 > 6:
                        print("❌ Invalid! Please enter a value between 1 and 6.")
                        continue
                    break
                except ValueError:
                    print("❌ Invalid input! Please enter a number.")
            d2 = 0
            target = d1
            print(f"\n🎲 Rolled: {d1} (single die mode - score is {score})")
        else:
            while True:
                try:
                    d1_input = input("Enter first die value (1-6, or 0 to exit): ").strip()
                    d1 = int(d1_input)
                    if d1 == 0:
                        print("\nExiting the game.")
                        return
                    if d1 < 1 or d1 > 6:
                        print("❌ Invalid! Please enter a value between 1 and 6.")
                        continue
                    break
                except ValueError:
                    print("❌ Invalid input! Please enter a number.")
            
            while True:
                try:
                    d2_input = input("Enter second die value (1-6, or 0 to exit): ").strip()
                    d2 = int(d2_input)
                    if d2 == 0:
                        print("\nExiting the game.")
                        return
                    if d2 < 1 or d2 > 6:
                        print("❌ Invalid! Please enter a value between 1 and 6.")
                        continue
                    break
                except ValueError:
                    print("❌ Invalid input! Please enter a number.")

            target = d1 + d2
            print(f"\n🎲 Rolled: {d1} + {d2} = {target}")
        
        move = get_next_move(d1, d2, game_state)
        if move:
            move_display = " + ".join([f"Row{row}:{num}" for row, num in sorted(move)])
            print(f"✅ Best move: {move_display}")
            
            for row, num in move:
                flip_tile(row, num, game_state)
            
            score = calculate_score(game_state)
            print(f"📊 New score: {score} points")
        else:
            print(f"\n❌ No valid moves available!")
            print(f"🏁 Game Over! Final score: {score} points")
            display_board(game_state)
            break

        if check_win(game_state):
            print("\n" + "🎉"*25)
            print("🎉 CONGRATULATIONS! You shut the box! 🎉")
            print("🎉"*25)
            display_board(game_state)
            break
        
        turn += 1
        input("\nPress Enter to continue to next turn...")

if __name__ == "__main__":
    main()