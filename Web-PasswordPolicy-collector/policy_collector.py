import pandas as pd
import os
from policy_agent import run_agent
def main(start=0, end=100, bs=100):

    START = start          
    END = end             
    batch_size = bs    

    INPUT_CSV = "tran_1M.csv"
    OUTPUT_FOLDER = "output"

    df = pd.read_csv(INPUT_CSV)
    df["policy"] = None


    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    total_rows = min(END, len(df))
    signup_count = 0

    # =====================
    # MAIN LOOP
    # =====================
    for idx in range(START, total_rows):
        domain = df.at[idx, "url"]
        signup_url = df.at[idx, "signup_url"]
        print(f"\nProcessing row {idx+1}/{total_rows}: {domain}")

        if signup_url == "NO_DIRECT_SIGNUP_URL":
            df.at[idx, "policy"] = "NO_SIGNUP_URL"
        else:
            try:
                result = run_agent(signup_url)
                df.at[idx, "policy"] = result

            except Exception as e:
                print(f"Failed for {domain}: {e}")
                df.at[idx, "policy"] = "ERROR"

        # =====================
        # BATCH SAVE
        # =====================
        processed = idx - START + 1
        is_batch_end = processed % batch_size == 0
        is_final = idx + 1 == total_rows

        if is_batch_end or is_final:
            batch_end = idx + 1
            batch_start = batch_end - batch_size + 1
            batch_start = max(batch_start, START + 1)

            filename = f"P_tran_{batch_start}_{batch_end}.csv"
            filepath = os.path.join(OUTPUT_FOLDER, filename)

            df.iloc[batch_start-1:batch_end].to_csv(filepath, index=False)
            #print(f"[INFO] Saved batch → {filename}","\n",f"Signup NOT found so far: {signup_count} / {processed}","\n",f"Login NOT found so far: {login_count} / {processed}")

    # =====================
    # FINAL SAVE
    # =====================
    final_path = os.path.join(OUTPUT_FOLDER, "P_tran_1M.csv")
    df.iloc[START:total_rows].to_csv(final_path, index=False)

    print("\nCrawl complete.")
    print(f"Final results saved to {final_path}")



main(17000, 20000, 1000)