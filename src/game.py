import pandas as pd

brawlers_data = "brawlers.csv"

df = pd.read_csv(brawlers_data, header = 0)

def find_name_stats(df, guess):
    if guess not in df["Name"].values:
        return None
    return df[df["Name"] == guess].iloc[0]
shelly_stats = find_name_stats(df, "Shelly")
piper_stats = find_name_stats(df, "Piper")

def compare_stats(df, guess_stats, answer_stats):
    diff = []
    for stat in df.columns:
        if guess_stats[stat] == answer_stats[stat]:
            diff.append(1)
        else:
            diff.append(0)
    return diff

#print(compare_stats(df, piper_stats, shelly_stats))