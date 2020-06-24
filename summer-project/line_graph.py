import matplotlib.pyplot as plt


def plot_weekly_statuses(activity):
    week = []
    statuses = []

    for item in activity:
        week.append(item["week"])
        statuses.append(item["statuses"])
    print(statuses)
    statuses = list(map(int, statuses)) # Necessary to convert to int from string.
    plt.plot(statuses)
    plt.ylabel("Statuses")
    plt.show()

