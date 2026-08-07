from itertools import combinations
import copy
import random

# Core game functions
def display_board(game_state):
    """Display the game board in a user-friendly format."""
    print("\n" + "="*50)
    print("           SHUT THE BOX - GAME BOARD")
    print("="*50)
    
    # Row 2 (double points) - displayed first, reversed order: 9 8 7 6 5 4 3 2 1
    row2_available = game_state.get(2, set())
    row2_display = "Row 2: "
    for num in [9, 8, 7, 6, 5, 4, 3, 2, 1]:
        if num in row2_available:
            row2_display += f"[{num}] "
        else:
            row2_display += "[X] "  # Show [X] for removed tiles
    print(row2_display.rstrip())
    
    # Row 1 (single points) - displayed below, normal order: 1 2 3 4 5 6 7 8 9
    row1_available = game_state.get(1, set())
    row1_display = "Row 1: "
    for num in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
        if num in row1_available:
            row1_display += f"[{num}] "
        else:
            row1_display += "[X] "  # Show [X] for removed tiles
    print(row1_display.rstrip())
    
    score = calculate_score(game_state)
    print(f"\nCurrent Score: {score} points")
    print("="*50 + "\n")

def display_valid_moves(valid_moves, target):
    """Display valid moves in a readable format."""
    if not valid_moves:
        return
    
    print(f"\nValid moves for total of {target}:")
    for i, move in enumerate(valid_moves, 1):
        move_str = " + ".join([f"Row{row}:{num}" for row, num in sorted(move)])
        total = sum(num for _, num in move)
        print(f"  {i}. {move_str} = {total}")

def flip_tile(row, num, game_state):
    if num in game_state[row]:
        game_state[row].remove(num)

def get_valid_combinations(total, game_state):
    all_tiles = []
    for row in [1, 2]:
        if row in game_state:
            for num in game_state[row]:
                all_tiles.append((row, num))

    valid_moves = []

    for r in range(1, len(all_tiles) + 1):
        for combo in combinations(all_tiles, r):
            if sum(num for row, num in combo) == total:
                valid = True
                combo_tiles = set(combo)  # For quick lookup

                for row, num in combo:
                    if row == 2 and 1 in game_state:
                        # Row 2: can only use if corresponding row 1 tile (10-num) is either:
                        # 1. Not available in game_state, OR
                        # 2. Also included in this same combo (can knock down both in same turn)
                        corresponding_row1 = 10 - num
                        if corresponding_row1 in game_state[1] and (1, corresponding_row1) not in combo_tiles:
                            valid = False
                            break
                if valid:
                    valid_moves.append(combo)

    return valid_moves

def check_win(curr_state):
    if calculate_score(curr_state) == 0:
        return True
    return False

def calculate_score(curr_state):
    score = 0
    for row, nums in curr_state.items():
        if row == 1:
            score += sum(nums)
        elif row == 2:
            score += sum(nums) * 2

    return score

def display_valid_moves_simple(valid_moves, target):
    """Display valid moves in a simple numbered list format."""
    if not valid_moves:
        return
    
    print(f"\nValid moves for total of {target}:")
    for i, move in enumerate(valid_moves, 1):
        move_list = sorted(move)
        move_str = " + ".join([f"R{row}:{num}" for row, num in move_list])
        total = sum(num for _, num in move)
        print(f"   {i}. {move_str} = {total}")

def check_game_total(game_state):
    total = 0
    for row in game_state:
        total += sum(game_state[row])
    return total

def check_valid_move(row, num, game_state):
    if row not in game_state:
        return False
    if num not in game_state[row]:
        return False
    return True

def roll_one_die():
    return random.randint(1, 6)

def roll_two_dice():
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    return die1, die2

def main():

    # Init game state
    game_state =  {1: {1, 2, 3, 4, 5, 6, 7, 8, 9},
                   2: {1, 2, 3, 4, 5, 6, 7, 8, 9}}

    print("\n" + "="*50)
    print("  Welcome to Shut the Box (Manual Player Mode)")
    print("="*50)
    print("\nInstructions:")
    print("  - Dice will be rolled automatically")
    print("  - You must select tiles that sum to the dice total")
    print("  - Enter moves as 'row, number' (e.g., '1, 3' or '2, 5')")
    print("  - Enter '0' at any time to exit")
    print("  - Goal: Flip all tiles to score 0 points")
    input("\nPress Enter to start the game...")
    
    turn = 1

    while True:
        display_board(game_state)
        print(f"--- Turn {turn} ---")

        input("\nPress Enter to roll the dice...")
        score = calculate_score(game_state)
        if score <= 6:
            d1 = roll_one_die()
            d2 = 0
            print(f"🎲 Rolled: {d1} (single die mode - score is {score})")
        else:
            d1, d2 = roll_two_dice()
            print(f"🎲 Rolled: {d1} + {d2} = {d1 + d2}")

        d_total = d1 + d2
        valid_moves = get_valid_combinations(d_total, game_state)

        if not valid_moves:
            print(f"\nNo valid moves available for total of {d_total}")
            print(f"Game Over. Final score: {calculate_score(game_state)} points")
            display_board(game_state)
            break
        
        display_valid_moves_simple(valid_moves, d_total)
        
        # Simple move selection by number
        while True:
            user_input = input(f"\nEnter move number (1-{len(valid_moves)}) or '0' to exit: ").strip()
            
            if user_input == '0':
                print("\nExiting the game.")
                return
            
            try:
                move_number = int(user_input)
                if move_number < 1 or move_number > len(valid_moves):
                    print(f"Invalid move. Please enter a number between 1 and {len(valid_moves)}.")
                    continue
                
                # Get the selected move
                selected_move = valid_moves[move_number - 1]
                
                # Verify all tiles in the move are still available
                move_valid = True
                for row, num in selected_move:
                    if not check_valid_move(row, num, game_state):
                        print(f"Invalid move. Some tiles in move #{move_number} are no longer available.")
                        move_valid = False
                        break
                
                if not move_valid:
                    continue
                
                # Apply the move
                move_display = " + ".join([f"R{row}:{num}" for row, num in sorted(selected_move)])
                print(f"\nSelected move #{move_number}: {move_display} = {d_total}")
                
                for row, num in selected_move:
                    flip_tile(row, num, game_state)
                
                break
                
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

        if check_win(game_state):
            print("\n" + "🎉"*25)
            print("BANG! You shut the box.")
            print("🎉"*25)
            display_board(game_state)
            break
        
        turn += 1
        input("\nPress Enter to continue to next turn...")

if __name__ == "__main__":
    main()