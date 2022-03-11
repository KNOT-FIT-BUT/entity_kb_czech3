
def run():
    all = 0
    identified = 0
    data_list = [0, 0, 0, 0, 0, 0]


    with open("kb_en", "r", encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            split = line.split("\t")
            for i in range(6):
                all += 1
                if split[i + 2]:
                    identified += 1
                    data_list[i] += 1
    print(f"{identified}/{all}\t{round(identified*100/all, 2)}%\tall")
    print(f"{data_list[0]}/{round(all/6)}\t\t{round(data_list[0]*100/(all/6), 2)}%\tbirth dates")
    print(f"{data_list[1]}/{round(all/6)}\t\t{round(data_list[1]*100/(all/6), 2)}%\tbirth places")
    print(f"{data_list[2]}/{round(all/6)}\t\t{round(data_list[2]*100/(all/6), 2)}%\tdeath dates")
    print(f"{data_list[3]}/{round(all/6)}\t\t{round(data_list[3]*100/(all/6), 2)}%\tdeath places")
    print(f"{data_list[4]}/{round(all/6)}\t\t{round(data_list[4]*100/(all/6), 2)}%\tgenders")
    print(f"{data_list[5]}/{round(all/6)}\t\t{round(data_list[5]*100/(all/6), 2)}%\tnationalities")

if __name__ == "__main__":
    run()