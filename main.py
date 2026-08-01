import pandas as pd
from src.game import find_name_stats, compare_stats
brawlers_data = "brawlers.csv"

df = pd.read_csv(brawlers_data, header = 0)

def find_result_cols(df, diff):
    corr = []
    wrong = []
    index = 2
    for stat in df.columns:
        if stat != "id" and stat != "Name":
            if diff[index] == 1:
                corr.append(stat)
            else:
                wrong.append(stat)
            index += 1
    return corr, wrong

answer_stats = df.sample().iloc[0]
while True:
    guess_stats = find_name_stats(df, input("Guess a brawler "))
    if guess_stats is None:
        print("invalid guess, guess again")
        continue
    diff = compare_stats(df, guess_stats, answer_stats)
    if diff[0] == 1:
        print("You got it! The correct brawler was ", answer_stats["Name"])
        break
    else:
        corr, wrong = find_result_cols(df, diff)
        print("You were correct about", corr)
        print("You were incorrect about", wrong)