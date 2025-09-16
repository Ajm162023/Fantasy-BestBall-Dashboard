import pandas as pd
import streamlit as st
from itertools import combinations

# ----------------------------
# Load Data
# ----------------------------
file_path = "Fantasy_BestBall_EntryPoolAndLineups.xlsx"
df = pd.read_excel(file_path)

try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    st.error(f"File not found at: {file_path}")
    st.stop()

# ----------------------------
# Normalize Owner Names
# ----------------------------
df["Team Owner"] = df["Team Owner"].astype(str).str.strip()
df["Team Owner Lower"] = df["Team Owner"].str.lower()

# ----------------------------
# Reshape Wide -> Long Format with NaN-safe Player Handling
# ----------------------------
cols = list(df.columns)
pairs = []
for i, col in enumerate(cols):
    if "Player" in col or "Alt" in col:
        salary_col = cols[i + 1]
        pairs.append((col, salary_col))

records = []
for _, row in df.iterrows():
    owner_lower = row["Team Owner Lower"]
    owner_display = row["Team Owner"]
    for slot, (pcol, scol) in enumerate(pairs, start=1):
        if pd.isna(row[pcol]):
            continue  # skip empty player slots
        player = str(row[pcol]).strip().lower()  # normalize player names
        salary = row[scol]
        lineup_type = "Main" if slot <= 6 else "Alternate"
        records.append([owner_lower, owner_display, player, salary, slot, lineup_type])

long_df = pd.DataFrame(records, columns=["OwnerLower", "Owner", "Player", "Salary", "Slot", "LineupType"])

# ----------------------------
# Helper Functions
# ----------------------------
def sort_lineup(owner_df):
    main_lineup = (
        owner_df[owner_df["LineupType"] == "Main"]
        .sort_values(by=["Salary", "Player"])
        .reset_index(drop=True)
    )
    alternate_lineup = (
        owner_df[owner_df["LineupType"] == "Alternate"]
        .sort_values(by=["Salary", "Player"])
        .reset_index(drop=True)
    )
    return main_lineup, alternate_lineup

def build_owner_overlap_table(long_df, max_shared_players=6):
    owner_players = {}
    for owner in long_df["OwnerLower"].unique():
        main_players = set(long_df[(long_df["OwnerLower"] == owner) & (long_df["LineupType"] == "Main")]["Player"])
        owner_players[owner] = main_players

    overlaps = []
    for o1, o2 in combinations(owner_players.keys(), 2):
        shared_players = owner_players[o1].intersection(owner_players[o2])
        if 1 <= len(shared_players) <= max_shared_players:
            owner1_display = long_df.loc[long_df["OwnerLower"] == o1, "Owner"].iloc[0]
            owner2_display = long_df.loc[long_df["OwnerLower"] == o2, "Owner"].iloc[0]
            overlaps.append({
                "Owner1": owner1_display,
                "Owner2": owner2_display,
                "SharedCount": len(shared_players),
                "SharedPlayers": ", ".join(sorted([p.title() for p in shared_players]))  # Title case
            })

    overlap_df = pd.DataFrame(overlaps)
    return overlap_df

# ----------------------------
# Streamlit App
# ----------------------------
st.set_page_config(page_title="Fantasy BestBall Leaderboards", layout="wide")
st.markdown(
    """
    <style>
    .stApp {background-color: #002D5B; color: white;}
    .stButton>button {background-color: #00B2D1; color: white;}
    .stSlider>div>div>div>div {color: white;}
    .stSelectbox>div>div>div>div {color: white;}
    .stDataFrame table th {background-color: #00B2D1; color: white;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🏈 Fantasy BestBall Leaderboards")

# ----------------------------
# Owner Selection
# ----------------------------
owner_choice = st.selectbox(
    "Choose a Team Owner to View Lineups:",
    long_df.groupby("OwnerLower")["Owner"].first().sort_values()
)
owner_choice_lower = owner_choice.lower()
owner_df = long_df[long_df["OwnerLower"] == owner_choice_lower]
main_lineup, alternate_lineup = sort_lineup(owner_df)

st.subheader("Main Lineup (Sorted by Salary then Name)")
st.dataframe(main_lineup.assign(Player=lambda x: x["Player"].str.title())[["Player", "Salary"]], use_container_width=True)

st.subheader("Alternates (Sorted by Salary then Name)")
st.dataframe(alternate_lineup.assign(Player=lambda x: x["Player"].str.title())[["Player", "Salary"]], use_container_width=True)

# ----------------------------
# Most Shared Players Between Owners
# ----------------------------
st.subheader("🔗 Owners Sharing Players with Selected Owner")
max_shared = st.slider("Maximum Number of Shared Players", min_value=1, max_value=6, value=6)

overlap_df = build_owner_overlap_table(long_df, max_shared_players=max_shared)

owner_overlap = overlap_df[
    overlap_df["Owner1"].str.lower().str.strip().eq(owner_choice_lower) |
    overlap_df["Owner2"].str.lower().str.strip().eq(owner_choice_lower)
]

if owner_overlap.empty:
    st.write(f"No owners share 1 to {max_shared} players with {owner_choice}.")
else:
    owner_overlap_sorted = owner_overlap.sort_values(by="SharedCount", ascending=False).reset_index(drop=True)
    
    # Gradient + highlight
    min_shared = owner_overlap_sorted["SharedCount"].min()
    max_shared_count = owner_overlap_sorted["SharedCount"].max()

    def color_gradient(row):
        owner1 = row["Owner1"].lower().strip()
        owner2 = row["Owner2"].lower().strip()
        shared_count = row["SharedCount"]
        ratio = (shared_count - min_shared) / max(1, (max_shared_count - min_shared))
        r1, g1, b1 = 0, 91, 153
        r2, g2, b2 = 0, 178, 209
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        gradient_color = f"background-color: rgb({r},{g},{b}); color: white;"
        highlight_color = "background-color: #FFDC00; color: black;"
        return [
            highlight_color if col_name in ["Owner1", "Owner2"] and (owner_choice_lower in [owner1, owner2]) else gradient_color
            for col_name in row.index
        ]

    st.dataframe(owner_overlap_sorted.style.apply(color_gradient, axis=1), use_container_width=True)

# ----------------------------
# Most Chosen Players (Main Lineups)
# ----------------------------
st.subheader("🏆 Most Chosen Players (Main Lineups)")
main_players_only = long_df[long_df["LineupType"] == "Main"]["Player"]
player_counts = main_players_only.value_counts().rename_axis("Player").reset_index(name="Count")
player_counts["Player"] = player_counts["Player"].str.title()
st.dataframe(player_counts.head(25), use_container_width=True)  # top 25 instead of top 10

