import os
import requests
from datetime import date, timedelta
from collections import Counter

USERNAME = "tarunmavuri"
TOKEN = os.environ["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

QUERY = """
query($login: String!) {
  user(login: $login) {

    repositories(
      first: 100
      ownerAffiliations: OWNER
      privacy: PUBLIC
    ) {
      totalCount

      nodes {
        name
        stargazerCount

        languages(
          first: 10
          orderBy: {field: SIZE, direction: DESC}
        ) {
          edges {
            size
            node {
              name
            }
          }
        }
      }
    }

    pullRequests(first: 1) {
      totalCount
    }

    issues(first: 1) {
      totalCount
    }

    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalIssueContributions
      totalPullRequestContributions
      totalRepositoryContributions

      contributionCalendar {
        totalContributions

        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""

# ---------------------------------------------------------
# GET DATA FROM GITHUB
# ---------------------------------------------------------

response = requests.post(
    "https://api.github.com/graphql",
    json={
        "query": QUERY,
        "variables": {
            "login": USERNAME
        },
    },
    headers=HEADERS,
)

response.raise_for_status()

data = response.json()

if "errors" in data:
    raise RuntimeError(data["errors"])

user = data["data"]["user"]

repos = user["repositories"]["nodes"]
contributions = user["contributionsCollection"]
calendar = contributions["contributionCalendar"]

# ---------------------------------------------------------
# BASIC STATS
# ---------------------------------------------------------

stars = sum(
    repo["stargazerCount"]
    for repo in repos
)

commits = contributions["totalCommitContributions"]

prs = user["pullRequests"]["totalCount"]

issues = user["issues"]["totalCount"]

repositories = user["repositories"]["totalCount"]

total_contributions = calendar["totalContributions"]

# ---------------------------------------------------------
# CONTRIBUTION DAYS
# ---------------------------------------------------------

days = []

for week in calendar["weeks"]:

    for contribution_day in week["contributionDays"]:

        days.append({
            "date": contribution_day["date"],
            "count": contribution_day["contributionCount"],
        })

days.sort(
    key=lambda item: item["date"]
)

# ---------------------------------------------------------
# CURRENT + LONGEST STREAK
# ---------------------------------------------------------

longest_streak = 0
running_streak = 0
previous_date = None

for item in days:

    current_date = date.fromisoformat(
        item["date"]
    )

    if item["count"] > 0:

        if (
            previous_date is not None
            and current_date == previous_date + timedelta(days=1)
        ):
            running_streak += 1
        else:
            running_streak = 1

        longest_streak = max(
            longest_streak,
            running_streak
        )

        previous_date = current_date

    else:

        running_streak = 0
        previous_date = None


# Current streak
current_streak = 0

for item in reversed(days):

    if item["count"] > 0:
        current_streak += 1
    else:
        break

# ---------------------------------------------------------
# LANGUAGE STATISTICS
# ---------------------------------------------------------

language_sizes = Counter()

for repo in repos:

    for edge in repo["languages"]["edges"]:

        language = edge["node"]["name"]
        size = edge["size"]

        language_sizes[language] += size


top_languages = language_sizes.most_common(5)

total_language_size = sum(
    language_sizes.values()
)

language_percentages = []

for language, size in top_languages:

    if total_language_size:

        percentage = (
            size / total_language_size
        ) * 100

    else:

        percentage = 0

    language_percentages.append(
        (language, percentage)
    )

# ---------------------------------------------------------
# COLORS
# ---------------------------------------------------------

BG = "#07110D"
CARD = "#0B1712"
BORDER = "#123C2B"

GREEN = "#10B981"
GREEN_DARK = "#064E3B"

TEXT = "#F3F4F6"
MUTED = "#9CA3AF"

LANGUAGE_COLORS = [
    "#10B981",
    "#14B8A6",
    "#3B82F6",
    "#A855F7",
    "#F59E0B",
]

# ---------------------------------------------------------
# SVG HELPERS
# ---------------------------------------------------------

def escape(value):

    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def draw_text(
    x,
    y,
    value,
    size=14,
    fill=TEXT,
    weight="400",
    anchor="start"
):

    return f"""
    <text
        x="{x}"
        y="{y}"
        font-family="Inter, Segoe UI, Arial, sans-serif"
        font-size="{size}px"
        font-weight="{weight}"
        fill="{fill}"
        text-anchor="{anchor}">
        {escape(value)}
    </text>
    """


def draw_rect(
    x,
    y,
    width,
    height,
    radius=14,
    fill=CARD,
    stroke=BORDER
):

    return f"""
    <rect
        x="{x}"
        y="{y}"
        width="{width}"
        height="{height}"
        rx="{radius}"
        fill="{fill}"
        stroke="{stroke}"
        stroke-width="1"/>
    """

# ---------------------------------------------------------
# SVG SETTINGS
# ---------------------------------------------------------

WIDTH = 1100
HEIGHT = 1040

svg = f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}">

    <defs>

        <linearGradient
            id="greenGradient"
            x1="0%"
            y1="0%"
            x2="100%"
            y2="0%">

            <stop
                offset="0%"
                stop-color="#064E3B"/>

            <stop
                offset="100%"
                stop-color="#10B981"/>

        </linearGradient>

        <filter id="glow">

            <feGaussianBlur
                stdDeviation="4"
                result="coloredBlur"/>

            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>

        </filter>

    </defs>

    <rect
        width="100%"
        height="100%"
        fill="{BG}"/>
"""

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

svg += draw_text(
    WIDTH / 2,
    55,
    "📊 GitHub Stats",
    30,
    TEXT,
    "700",
    "middle"
)

svg += draw_text(
    WIDTH / 2,
    87,
    "Turning ideas into code. Shipping impact through consistent execution.",
    14,
    MUTED,
    "400",
    "middle"
)

svg += """
<line
    x1="440"
    y1="105"
    x2="660"
    y2="105"
    stroke="url(#greenGradient)"
    stroke-width="2"/>
"""

# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------

cards = [
    ("⭐", "Total Stars", stars),
    ("↗", "Total Commits", commits),
    ("⑂", "Pull Requests", prs),
    ("!", "Issues", issues),
    ("▣", "Repositories", repositories),
]

card_width = 195
card_height = 120
gap = 20
start_x = 35
card_y = 135

for index, (icon, label, value) in enumerate(cards):

    x = start_x + index * (
        card_width + gap
    )

    svg += draw_rect(
        x,
        card_y,
        card_width,
        card_height
    )

    svg += f"""
    <circle
        cx="{x + 42}"
        cy="{card_y + 45}"
        r="27"
        fill="{GREEN_DARK}"
        opacity="0.7"/>
    """

    svg += draw_text(
        x + 42,
        card_y + 53,
        icon,
        22,
        GREEN,
        "700",
        "middle"
    )

    svg += draw_text(
        x + 78,
        card_y + 38,
        label,
        13,
        MUTED,
        "500"
    )

    svg += draw_text(
        x + 78,
        card_y + 78,
        value,
        27,
        TEXT,
        "700"
    )

# ---------------------------------------------------------
# STREAK PANEL
# ---------------------------------------------------------

x = 35
y = 285
w = 525
h = 280

svg += draw_rect(
    x,
    y,
    w,
    h
)

svg += draw_text(
    x + 25,
    y + 38,
    "🔥 GitHub Streak",
    19,
    GREEN,
    "700"
)

cx = x + 145
cy = y + 135
radius = 70

circumference = 2 * 3.1415926535 * radius

if longest_streak > 0:

    progress = min(
        current_streak / longest_streak,
        1
    )

else:

    progress = 0

dash_offset = circumference * (
    1 - progress
)

svg += f"""
<circle
    cx="{cx}"
    cy="{cy}"
    r="{radius}"
    fill="none"
    stroke="{GREEN_DARK}"
    stroke-width="13"/>

<circle
    cx="{cx}"
    cy="{cy}"
    r="{radius}"
    fill="none"
    stroke="{GREEN}"
    stroke-width="13"
    stroke-linecap="round"
    stroke-dasharray="{circumference}"
    stroke-dashoffset="{dash_offset}"
    transform="rotate(-90 {cx} {cy})"
    filter="url(#glow)"/>
"""

svg += draw_text(
    cx,
    cy - 3,
    current_streak,
    30,
    TEXT,
    "700",
    "middle"
)

svg += draw_text(
    cx,
    cy + 23,
    "CURRENT STREAK",
    10,
    MUTED,
    "600",
    "middle"
)

streak_stats = [
    ("Current", current_streak),
    ("Longest", longest_streak),
    ("Contributions", total_contributions),
]

for index, (label, value) in enumerate(
    streak_stats
):

    sx = x + 285 + index * 75

    if index > 0:

        svg += f"""
        <line
            x1="{sx - 28}"
            y1="{y + 190}"
            x2="{sx - 28}"
            y2="{y + 240}"
            stroke="{BORDER}"/>
        """

    svg += draw_text(
        sx,
        y + 212,
        value,
        18,
        TEXT,
        "700",
        "middle"
    )

    svg += draw_text(
        sx,
        y + 232,
        label,
        9,
        MUTED,
        "500",
        "middle"
    )

# ---------------------------------------------------------
# LANGUAGE PANEL
# ---------------------------------------------------------

x = 585
y = 285
w = 480
h = 280

svg += draw_rect(
    x,
    y,
    w,
    h
)

svg += draw_text(
    x + 25,
    y + 38,
    "💻 Most Used Languages",
    19,
    GREEN,
    "700"
)

# Donut

cx = x + 130
cy = y + 145

radius = 75

circumference = (
    2 * 3.1415926535 * radius
)

offset = 0

for index, (
    language,
    percentage
) in enumerate(language_percentages):

    segment_length = (
        circumference
        * percentage
        / 100
    )

    color = LANGUAGE_COLORS[
        index % len(LANGUAGE_COLORS)
    ]

    svg += f"""
    <circle
        cx="{cx}"
        cy="{cy}"
        r="{radius}"
        fill="none"
        stroke="{color}"
        stroke-width="24"
        stroke-dasharray="{segment_length} {circumference - segment_length}"
        stroke-dashoffset="{-offset}"
        transform="rotate(-90 {cx} {cy})"/>
    """

    offset += segment_length

svg += f"""
<circle
    cx="{cx}"
    cy="{cy}"
    r="53"
    fill="{CARD}"/>
"""

for index, (
    language,
    percentage
) in enumerate(language_percentages):

    ly = y + 85 + index * 32

    color = LANGUAGE_COLORS[
        index % len(LANGUAGE_COLORS)
    ]

    svg += f"""
    <circle
        cx="{x + 250}"
        cy="{ly - 5}"
        r="6"
        fill="{color}"/>
    """

    svg += draw_text(
        x + 265,
        ly,
        language,
        13,
        TEXT,
        "500"
    )

    svg += draw_text(
        x + 430,
        ly,
        f"{percentage:.1f}%",
        12,
        GREEN,
        "600",
        "end"
    )

# ---------------------------------------------------------
# CONTRIBUTION ACTIVITY
# ---------------------------------------------------------

x = 35
y = 590
w = 1030
h = 350

svg += draw_rect(
    x,
    y,
    w,
    h
)

svg += draw_text(
    x + 25,
    y + 40,
    "📈 Contribution Activity",
    19,
    GREEN,
    "700"
)

svg += draw_text(
    x + 25,
    y + 65,
    "Daily contribution activity over the past year",
    12,
    MUTED
)

# ---------------------------------------------------------
# CONTRIBUTION HEATMAP
# ---------------------------------------------------------

heat_x = x + 30
heat_y = y + 95

cell_size = 11
cell_gap = 3

recent_days = days[-364:]

max_count = max(
    [item["count"] for item in recent_days],
    default=1
)

for index, item in enumerate(
    recent_days
):

    column = index // 7
    row = index % 7

    count = item["count"]

    if count == 0:
        opacity = 0.08

    elif count <= max_count * 0.25:
        opacity = 0.25

    elif count <= max_count * 0.50:
        opacity = 0.45

    elif count <= max_count * 0.75:
        opacity = 0.70

    else:
        opacity = 1

    svg += f"""
    <rect
        x="{heat_x + column * (cell_size + cell_gap)}"
        y="{heat_y + row * (cell_size + cell_gap)}"
        width="{cell_size}"
        height="{cell_size}"
        rx="2"
        fill="{GREEN}"
        opacity="{opacity}"/>
    """

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

svg += draw_text(
    WIDTH / 2,
    985,
    "Consistency compounds. Code. Learn. Improve. Repeat.",
    15,
    GREEN,
    "500",
    "middle"
)

svg += "</svg>"

# ---------------------------------------------------------
# SAVE SVG
# ---------------------------------------------------------

os.makedirs(
    "assets",
    exist_ok=True
)

with open(
    "assets/github-stats.svg",
    "w",
    encoding="utf-8"
) as file:

    file.write(svg)

print(
    "GitHub stats dashboard generated successfully."
)
