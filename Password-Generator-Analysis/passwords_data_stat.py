import os
import re
import csv
import statistics
from collections import Counter
from math import factorial, log2


TARGET_COMBINED_COVERAGE = 0.75
INPUT_FOLDER = "generated_passwords"
OUTPUT_FOLDER = "password_stats_summary"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def parse_range_tuple(range_str: str):
    if range_str == "N/A":
        return (0, 0)
    if "-" in range_str:
        parts = range_str.split("-")
        return (int(parts[0]), int(parts[1]))
    val = int(range_str)
    return (val, val)


def get_majority_range(bin_counter: Counter, total_passwords: int, threshold: float):
    if not bin_counter or total_passwords == 0:
        return "N/A", 0.0

    length_prob_pairs = [(count_val, freq / total_passwords) for count_val, freq in bin_counter.items()]
    length_prob_pairs.sort(key=lambda x: x[0])

    n = len(length_prob_pairs)
    best_range = None
    min_span = float('inf')
    max_coverage = -1.0

    for start in range(n):
        current_sum = 0.0
        for end in range(start, n):
            current_sum += length_prob_pairs[end][1]
            if current_sum >= threshold:
                span = length_prob_pairs[end][0] - length_prob_pairs[start][0] + 1
                if span < min_span or (span == min_span and current_sum > max_coverage):
                    min_span = span
                    best_range = (length_prob_pairs[start][0], length_prob_pairs[end][0])
                    max_coverage = current_sum
                break

    if best_range is None:
        return "N/A", 0.0

    range_str = f"{best_range[0]}-{best_range[1]}" if best_range[0] != best_range[1] else f"{best_range[0]}"
    return range_str, max_coverage


def evaluate_threshold(t_val, lowercase_bin, uppercase_bin, digit_bin, special_bin, 
                       password_count, lowercase_stats, uppercase_stats, digit_stats, special_stats):
    l_str, l_cov = get_majority_range(lowercase_bin, password_count, threshold=t_val)
    u_str, u_cov = get_majority_range(uppercase_bin, password_count, threshold=t_val)
    d_str, d_cov = get_majority_range(digit_bin, password_count, threshold=t_val)
    s_str, s_cov = get_majority_range(special_bin, password_count, threshold=t_val)

    l_rng = parse_range_tuple(l_str)
    u_rng = parse_range_tuple(u_str)
    d_rng = parse_range_tuple(d_str)
    s_rng = parse_range_tuple(s_str)

    fitting = 0
    for l, u, d, s in zip(lowercase_stats, uppercase_stats, digit_stats, special_stats):
        if (l_rng[0] <= l <= l_rng[1] and
            u_rng[0] <= u <= u_rng[1] and
            d_rng[0] <= d <= d_rng[1] and
            s_rng[0] <= s <= s_rng[1]):
            fitting += 1

    return fitting, (l_str, l_cov), (u_str, u_cov), (d_str, d_cov), (s_str, s_cov)


def find_threshold_for_target_coverage(target_pct, lowercase_bin, uppercase_bin, digit_bin, special_bin,
                                        password_count, lowercase_stats, uppercase_stats, digit_stats, special_stats):
    low, high = 0.01, 1.0
    best_t = 1.0
    best_eval = None

    for _ in range(25):
        mid = (low + high) / 2
        fitting, l_res, u_res, d_res, s_res = evaluate_threshold(
            mid, lowercase_bin, uppercase_bin, digit_bin, special_bin,
            password_count, lowercase_stats, uppercase_stats, digit_stats, special_stats
        )
        cov = fitting / password_count if password_count > 0 else 0.0

        if cov >= target_pct:
            best_t = mid
            best_eval = (fitting, l_res, u_res, d_res, s_res)
            high = mid
        else:
            low = mid

    if best_eval is None:
        best_eval = evaluate_threshold(
            best_t, lowercase_bin, uppercase_bin, digit_bin, special_bin,
            password_count, lowercase_stats, uppercase_stats, digit_stats, special_stats
        )

    return best_t, best_eval


def count_pattern(l, u, d, s, length, l_size, u_size, d_size, s_size):
    arrangements = factorial(length) // (
        factorial(l) * factorial(u) * factorial(d) * factorial(s)
    )
    return arrangements * (
        (l_size ** l) * (u_size ** u) * (d_size ** d) * (s_size ** s)
    )


def count_restricted_space(l_range, u_range, d_range, s_range, length, l_size, u_size, d_size, s_size):
    total = 0
    for l in range(l_range[0], l_range[1] + 1):
        for u in range(u_range[0], u_range[1] + 1):
            for d in range(d_range[0], d_range[1] + 1):
                for s in range(s_range[0], s_range[1] + 1):
                    if l + u + d + s == length:
                        total += count_pattern(l, u, d, s, length, l_size, u_size, d_size, s_size)
    return total


def process_single_file(file_path: str):
    lowercase_bin, uppercase_bin, digit_bin, special_bin = Counter(), Counter(), Counter(), Counter()
    lowercase_stats, uppercase_stats, digit_stats, special_stats = [], [], [], []
    password_lengths = []
    password_count = 0

    unique_special_chars, unique_ascii_chars = set(), set()
    unique_lower_chars, unique_upper_chars, unique_digit_chars = set(), set(), set()

    with open(file_path, 'r', errors="ignore") as file:
        for line in file:
            password = line.strip()
            if not password:
                continue

            password_count += 1
            password_lengths.append(len(password))

            lower = sum(1 for char in password if char.islower())
            upper = sum(1 for char in password if char.isupper())
            digits = sum(1 for char in password if char.isdigit())
            special = len(re.findall(r"[^a-zA-Z0-9]", password))

            lowercase_stats.append(lower)
            uppercase_stats.append(upper)
            digit_stats.append(digits)
            special_stats.append(special)

            unique_ascii_chars.update(password)
            for char in password:
                if char.islower():
                    unique_lower_chars.add(char)
                elif char.isupper():
                    unique_upper_chars.add(char)
                elif char.isdigit():
                    unique_digit_chars.add(char)
                else:
                    unique_special_chars.add(char)

    if password_count == 0:
        return None

    lowercase_bin.update(lowercase_stats)
    uppercase_bin.update(uppercase_stats)
    digit_bin.update(digit_stats)
    special_bin.update(special_stats)

    ascii_space_used = len(unique_ascii_chars)

    _, eval_results = find_threshold_for_target_coverage(
        TARGET_COMBINED_COVERAGE, lowercase_bin, uppercase_bin, digit_bin, special_bin,
        password_count, lowercase_stats, uppercase_stats, digit_stats, special_stats
    )

    passwords_fitting_threshold, (lower_range_str, _), (upper_range_str, _), (digit_range_str, _), (special_range_str, _) = eval_results

    L_RANGE = parse_range_tuple(lower_range_str)
    U_RANGE = parse_range_tuple(upper_range_str)
    D_RANGE = parse_range_tuple(digit_range_str)
    S_RANGE = parse_range_tuple(special_range_str)

    target_length = Counter(password_lengths).most_common(1)[0][0] if password_lengths else 0

    gen_l_size = len(unique_lower_chars) if unique_lower_chars else 26
    gen_u_size = len(unique_upper_chars) if unique_upper_chars else 26
    gen_d_size = len(unique_digit_chars) if unique_digit_chars else 10
    gen_s_size = len(unique_special_chars) if unique_special_chars else 32


    S_inside = count_restricted_space(L_RANGE, U_RANGE, D_RANGE, S_RANGE, target_length, gen_l_size, gen_u_size, gen_d_size, gen_s_size)
    S_full_95 = 95 ** target_length
    S_gen_specific = ascii_space_used ** target_length

    S_outside_95 = S_full_95 - S_inside
    S_outside_gen = S_gen_specific - S_inside

    h_restricted = log2(S_inside) if S_inside > 0 else 0
    h_baseline_95 = log2(S_full_95) if S_full_95 > 0 else 0
    h_baseline_gen = log2(S_gen_specific) if S_gen_specific > 0 else 0

    entropy_loss_vs_95 = h_baseline_95 - h_restricted
    entropy_loss_vs_gen = h_baseline_gen - h_restricted


    p_inside_actual = passwords_fitting_threshold / password_count
    p_outside_actual = (password_count - passwords_fitting_threshold) / password_count


    pct_expected_95 = (S_inside / S_full_95) * 100 if S_full_95 > 0 else 0
    p_inside_exp_95 = pct_expected_95 / 100
    p_outside_exp_95 = 1 - p_inside_exp_95

    lift_vs_95 = p_inside_actual / p_inside_exp_95 if p_inside_exp_95 > 0 else 0
    odds_exp_95 = p_inside_exp_95 / p_outside_exp_95 if p_outside_exp_95 > 0 else float('inf')
    odds_actual = p_inside_actual / p_outside_actual if p_outside_actual > 0 else float('inf')
    bias_mult_95 = odds_actual / odds_exp_95 if odds_exp_95 > 0 else float('inf')

    yield_inside = p_inside_actual / S_inside if S_inside > 0 else 0
    yield_out_95 = p_outside_actual / S_outside_95 if S_outside_95 > 0 else 0
    eff_adv_95 = yield_inside / yield_out_95 if yield_out_95 > 0 else float('inf')
    speedup_95 = S_full_95 / S_inside if S_inside > 0 else float('inf')


    pct_expected_gen = (S_inside / S_gen_specific) * 100 if S_gen_specific > 0 else 0
    p_inside_exp_gen = pct_expected_gen / 100
    p_outside_exp_gen = 1 - p_inside_exp_gen

    lift_vs_gen = p_inside_actual / p_inside_exp_gen if p_inside_exp_gen > 0 else 0
    odds_exp_gen = p_inside_exp_gen / p_outside_exp_gen if p_outside_exp_gen > 0 else float('inf')
    bias_mult_gen = odds_actual / odds_exp_gen if odds_exp_gen > 0 else float('inf')

    yield_out_gen = p_outside_actual / S_outside_gen if S_outside_gen > 0 else 0
    eff_adv_gen = yield_inside / yield_out_gen if yield_out_gen > 0 else float('inf')
    speedup_gen = S_gen_specific / S_inside if S_inside > 0 else float('inf')

    return {
        "generator_name": os.path.basename(file_path),
        "total_passwords": password_count,
        "ascii_used": ascii_space_used,
        "passwords_captured": passwords_fitting_threshold,
        "empirical_pass_rate": round(p_inside_actual * 100, 2),
        "odds_actual": round(odds_actual, 2),
        
        # 95 ASCII Metrics
        "entropy_loss_vs_95": round(entropy_loss_vs_95, 2),
        "expected_space_pct_95": round(pct_expected_95, 4),
        "lift_vs_95": round(lift_vs_95, 2),
        "odds_theoretical_95": round(odds_exp_95, 4),
        "bias_multiplier_95": round(bias_mult_95, 2),
        "efficiency_advantage_95": round(eff_adv_95, 2),
        "speedup_vs_95": round(speedup_95, 2),

        # Generator Specific Metrics
        "entropy_loss_vs_gen": round(entropy_loss_vs_gen, 2),
        "expected_space_pct_gen": round(pct_expected_gen, 2),
        "lift_vs_gen": round(lift_vs_gen, 2),
        "odds_theoretical_gen": round(odds_exp_gen, 2),
        "bias_multiplier_gen": round(bias_mult_gen, 2),
        "efficiency_advantage_gen": round(eff_adv_gen, 2),
        "speedup_vs_gen": round(speedup_gen, 2),
    }



if __name__ == "__main__":
    summary_data = []

    if os.path.exists(INPUT_FOLDER):
        for filename in sorted(os.listdir(INPUT_FOLDER)):
            if filename.endswith(".txt"):
                input_file_path = os.path.join(INPUT_FOLDER, filename)
                res = process_single_file(input_file_path)
                if res:
                    summary_data.append(res)

    if summary_data:
        summary_txt_path = os.path.join(OUTPUT_FOLDER, "SUMMARY_ALL_GENERATORS.txt")
        summary_csv_path = os.path.join(OUTPUT_FOLDER, "SUMMARY_ALL_GENERATORS.csv")

        avg_row = {
            "generator_name": "AVERAGE",
            "total_passwords": int(statistics.mean(item["total_passwords"] for item in summary_data)),
            "ascii_used": round(statistics.mean(item["ascii_used"] for item in summary_data), 2),
            "passwords_captured": int(statistics.mean(item["passwords_captured"] for item in summary_data)),
            "empirical_pass_rate": round(statistics.mean(item["empirical_pass_rate"] for item in summary_data), 2),
            "odds_actual": round(statistics.mean(item["odds_actual"] for item in summary_data), 2),

            # 95 ASCII Averages
            "entropy_loss_vs_95": round(statistics.mean(item["entropy_loss_vs_95"] for item in summary_data), 2),
            "expected_space_pct_95": round(statistics.mean(item["expected_space_pct_95"] for item in summary_data), 4),
            "lift_vs_95": round(statistics.mean(item["lift_vs_95"] for item in summary_data), 2),
            "odds_theoretical_95": round(statistics.mean(item["odds_theoretical_95"] for item in summary_data), 4),
            "bias_multiplier_95": round(statistics.mean(item["bias_multiplier_95"] for item in summary_data), 2),
            "efficiency_advantage_95": round(statistics.mean(item["efficiency_advantage_95"] for item in summary_data), 2),
            "speedup_vs_95": round(statistics.mean(item["speedup_vs_95"] for item in summary_data), 2),

            # Generator Specific Averages
            "entropy_loss_vs_gen": round(statistics.mean(item["entropy_loss_vs_gen"] for item in summary_data), 2),
            "expected_space_pct_gen": round(statistics.mean(item["expected_space_pct_gen"] for item in summary_data), 2),
            "lift_vs_gen": round(statistics.mean(item["lift_vs_gen"] for item in summary_data), 2),
            "odds_theoretical_gen": round(statistics.mean(item["odds_theoretical_gen"] for item in summary_data), 2),
            "bias_multiplier_gen": round(statistics.mean(item["bias_multiplier_gen"] for item in summary_data), 2),
            "efficiency_advantage_gen": round(statistics.mean(item["efficiency_advantage_gen"] for item in summary_data), 2),
            "speedup_vs_gen": round(statistics.mean(item["speedup_vs_gen"] for item in summary_data), 2),
        }


        with open(summary_txt_path, "w") as f:
            f.write("======================================================================================================================================================================\n")
            f.write("                                                   TABLE 1: METRICS COMPARISON VS. FULL 95 ASCII CHARACTER SPACE BASELINE                              \n")
            f.write("======================================================================================================================================================================\n\n")
            f.write(
                f"{'Generator File':<22} | {'R-Size':<6} | {'Pass Rate':<9} | {'H-Loss (95)':<11} | {'Exp Space (95)':<14} | {'Lift (95)':<9} | "
                f"{'Theo Odds (95)':<14} | {'Actual Odds':<11} | {'Bias Mult':<9} | {'Efficiency Advantage':<20} | {'Speedup (95)':<12}\n"
            )
            f.write("-" * 165 + "\n")

            for item in summary_data:
                theo_str = f"{item['odds_theoretical_95']:.4f}:1"
                actual_str = f"{item['odds_actual']:.2f}:1"
                eff_str = f"{item['efficiency_advantage_95']:,.2f}x more"

                f.write(
                    f"{item['generator_name']:<22} | "
                    f"{item['ascii_used']:<6} | "
                    f"{item['empirical_pass_rate']:>8.2f}% | "
                    f"{item['entropy_loss_vs_95']:>8.2f} bits | "
                    f"{item['expected_space_pct_95']:>13.4f}% | "
                    f"{item['lift_vs_95']:>8.2f}x | "
                    f"{theo_str:>14} | "
                    f"{actual_str:>11} | "
                    f"{item['bias_multiplier_95']:>8.2f}x | "
                    f"{eff_str:>20} | "
                    f"{item['speedup_vs_95']:>11.2f}x\n"
                )

            f.write("-" * 165 + "\n")
            avg_theo_str = f"{avg_row['odds_theoretical_95']:.4f}:1"
            avg_actual_str = f"{avg_row['odds_actual']:.2f}:1"
            avg_eff_str = f"{avg_row['efficiency_advantage_95']:,.2f}x more"
            f.write(
                f"{avg_row['generator_name']:<22} | "
                f"{avg_row['ascii_used']:<6} | "
                f"{avg_row['empirical_pass_rate']:>8.2f}% | "
                f"{avg_row['entropy_loss_vs_95']:>8.2f} bits | "
                f"{avg_row['expected_space_pct_95']:>13.4f}% | "
                f"{avg_row['lift_vs_95']:>8.2f}x | "
                f"{avg_theo_str:>14} | "
                f"{avg_actual_str:>11} | "
                f"{avg_row['bias_multiplier_95']:>8.2f}x | "
                f"{avg_eff_str:>20} | "
                f"{avg_row['speedup_vs_95']:>11.2f}x\n"
            )

            f.write("\n\n")
            f.write("======================================================================================================================================================================\n")
            f.write("                                              TABLE 2: METRICS COMPARISON VS. GENERATOR-SPECIFIC CHARACTER SPACE BASELINE                             \n")
            f.write("======================================================================================================================================================================\n\n")
            f.write(
                f"{'Generator File':<22} | {'R-Size':<6} | {'Pass Rate':<9} | {'H-Loss (R)':<11} | {'Exp Space (R)':<13} | {'Lift (R)':<8} | "
                f"{'Theo Odds (R)':<13} | {'Actual Odds':<11} | {'Bias Mult':<9} | {'Efficiency Advantage':<20} | {'Speedup (R)':<11}\n"
            )
            f.write("-" * 165 + "\n")

            for item in summary_data:
                theo_str_gen = f"{item['odds_theoretical_gen']:.2f}:1"
                actual_str = f"{item['odds_actual']:.2f}:1"
                eff_str_gen = f"{item['efficiency_advantage_gen']:,.2f}x more"

                f.write(
                    f"{item['generator_name']:<22} | "
                    f"{item['ascii_used']:<6} | "
                    f"{item['empirical_pass_rate']:>8.2f}% | "
                    f"{item['entropy_loss_vs_gen']:>8.2f} bits | "
                    f"{item['expected_space_pct_gen']:>12.2f}% | "
                    f"{item['lift_vs_gen']:>7.2f}x | "
                    f"{theo_str_gen:>13} | "
                    f"{actual_str:>11} | "
                    f"{item['bias_multiplier_gen']:>8.2f}x | "
                    f"{eff_str_gen:>20} | "
                    f"{item['speedup_vs_gen']:>10.2f}x\n"
                )

            f.write("-" * 165 + "\n")
            avg_theo_str_gen = f"{avg_row['odds_theoretical_gen']:.2f}:1"
            avg_eff_str_gen = f"{avg_row['efficiency_advantage_gen']:,.2f}x more"
            f.write(
                f"{avg_row['generator_name']:<22} | "
                f"{avg_row['ascii_used']:<6} | "
                f"{avg_row['empirical_pass_rate']:>8.2f}% | "
                f"{avg_row['entropy_loss_vs_gen']:>8.2f} bits | "
                f"{avg_row['expected_space_pct_gen']:>12.2f}% | "
                f"{avg_row['lift_vs_gen']:>7.2f}x | "
                f"{avg_theo_str_gen:>13} | "
                f"{avg_actual_str:>11} | "
                f"{avg_row['bias_multiplier_gen']:>8.2f}x | "
                f"{avg_eff_str_gen:>20} | "
                f"{avg_row['speedup_vs_gen']:>10.2f}x\n"
            )


        csv_rows = summary_data + [avg_row]
        fieldnames = list(csv_rows[0].keys())
        with open(summary_csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        print(f"Summary files created successfully:\n  - {summary_txt_path}\n  - {summary_csv_path}")