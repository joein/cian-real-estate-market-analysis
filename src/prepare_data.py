import os

import pandas as pd

from datetime import datetime as dt

data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data"
    )
USD = 75.0  # approximate course for converting USD TO RUB
TRANSPORT_TO_WALK_MULT = 5


def extract_time_to_undeground(x):
    if not x:
        return -1
    time_to = int(x.split()[0])
    if "транспорт" in x:
        time_to = time_to * TRANSPORT_TO_WALK_MULT
    return time_to


def extract_living_square(x):
    if not x:
        return 0.0
    value = float(x.split()[0].replace(",", "."))
    return value


def extract_room_number(x):
    if "свобод" in x.lower() or "студия" in x.lower():
        return "студия"
    else:
        return x.split("-")[0]


df = pd.read_csv(os.path.join(data_path, "raw_data.csv"), index_col=0, parse_dates=["offer_dt"])
print(f"Original shape: {df.shape}")

df.drop_duplicates(inplace=True)
print(f"Shape without duplicates: {df.shape}")


df.dropna(subset=["price"], inplace=True)
print(f"Shape without nan prices: {df.shape}")

df["Общая"] = df["Общая"].apply(
    lambda x: float(x.split()[0].replace(",", "."))
    if isinstance(x, str)  # here maybe already float values
    else x
)

usd_mask = df["price_currency"] == "USD"
df[usd_mask]["price"] *= USD

# dropping potential malicious offers
df.drop(df[df["agent_warning"] == True].index, inplace=True)

# these features being dropped because there too much gaps in their values
df.drop(
    columns=[
        "agent_warning",
        "price_currency",
        "Строительная серия",
        "Лифты",
        "Отопление",
        "Аварийность",
        "Ремонт",
        "Тип перекрытий",
        "Мусоропровод",
        "Подъезды",
        "Отделка",
        "Сдан",
        "Площадь комнат",
        "Кухня",
        "Газоснабжение",
        "Срок сдачи",
        "Планировка",
        "Тип дома",
    ],
    inplace=True,
)

df["Высота потолков"] = pd.to_numeric(
    df["Высота потолков"]
    .str.replace("м", "")
    .str.strip()
    .str.replace(",", ".")
)
df["Высота потолков"].fillna(df["Высота потолков"].median(), inplace=True)

# the order of following statements is important
df["Всего этажей"] = pd.to_numeric(
    df["Этаж"].apply(lambda x: x.replace("из", "").split()[1])
)
df["Этаж"] = pd.to_numeric(
    df["Этаж"].apply(lambda x: x.replace("из", "").split()[0])
)

df["Апартаменты"] = df["Тип жилья"].apply(lambda x: "апартамент" in x.lower())
df["Новостройка"] = df["Тип жилья"].apply(lambda x: "новостройка" in x.lower())
df.drop("Тип жилья", axis=1, inplace=True)

df["Вид из окон"].fillna("", inplace=True)
df["Окна во двор"] = df["Вид из окон"].apply(lambda x: "двор" in x.lower())
df["Окна на улицу"] = df["Вид из окон"].apply(lambda x: "улиц" in x.lower())
df.drop("Вид из окон", axis=1, inplace=True)

df["district"] = df["address"].apply(lambda x: x.split(",")[1].strip())


df["количество комнат"] = df["title"].apply(lambda x: extract_room_number(x))
df.drop("title", axis=1, inplace=True)

df["Санузел"].fillna(df["Санузел"].value_counts().index[0], inplace=True)
df["Количество санузлов"] = pd.to_numeric(
    df["Санузел"].apply(lambda x: x.split()[0])
)
df["Совмещенный санузел"] = df["Санузел"].apply(
    lambda x: "совмещен" in x.lower()
)
df.drop(columns=["Санузел"], inplace=True)

df["Парковка"].fillna("", inplace=True)
df["Парковка"] = df["Парковка"].apply(
    lambda x: "наземная" if "открыт" in x.lower() or not x else x.lower()
)
df["Балкон/лоджия"].fillna("", inplace=True)
df["балкон"] = df["Балкон/лоджия"].apply(
    lambda x: sum(map(lambda x: int(x) if x.isdigit() else 0, x.split()))
)
df.drop(columns=["Балкон/лоджия"], inplace=True)

df.loc[df["Построен"].isna(), "Построен"] = df["Год постройки"][
    df["Построен"].isna()
]
df["Построен"].ffill(inplace=True)
df.drop("Год постройки", axis=1, inplace=True)

living_square_mask = df["Жилая"].notna()
df["living_square_ratio"] = 0.0
df.loc[living_square_mask, "living_square_ratio"] = (
    pd.to_numeric(
        df["Жилая"][living_square_mask].apply(
            lambda x: extract_living_square(x)
        )
    )
    / df["Общая"][living_square_mask]
)
df.loc[df["living_square_ratio"] == 0.0, "living_square_ratio"] = df[
    "living_square_ratio"
].median()
df.drop("Жилая", axis=1, inplace=True)

today = dt.today()
df["placed_days_ago"] = df["offer_dt"].apply(
    lambda x: (today - x).round(freq="D").days
)

df.loc[df['description_len'] == 0, 'description_len'] = df['description_len'].median()

df.drop("distance_to_mkad", axis=1, inplace=True)
df.drop(df[df["time_to_underground"].isna() == True].index, inplace=True)
df.rename(
    columns={
        "Общая": "general_sq",
        "Этаж": "floor",
        "Построен": "built",
        "Высота потолков": "ceil",
        "Всего этажей": "total_floors",
        "Апартаменты": "apartments",
        "Новостройка": "new_building",
        "Окна во двор": "courtyard_view",
        "Окна на улицу": "road_view",
        "количество комнат": "rooms",
        "Количество санузлов": "wc_amount",
        "Совмещенный санузел": "joint_wc",
        "балкон": "balcony",
        "Парковка": "parking",
    },
    inplace=True,
)

# drop or correct outliers
df.loc[df["ceil"] > 20.0, "ceil"] = df["ceil"][df["ceil"] > 20.0] / 10
df.drop(df[df["ceil"] > 7.0].index, inplace=True)
df.drop(df[df["general_sq"] == 2.0].index, inplace=True)
df.drop(df[df['rooms'] == '5'].index, inplace=True)

print(df.info(), end="\n\n")
print(df.describe(), end="\n\n")


df.to_csv(os.path.join(data_path, "prepared_data.csv"))
