"""
Password Policy Research Analysis
===================================
Produces all statistics, figures, and tables

Input: structured CSV produced by parse_password_policy.py
    - figures/        PNG plots (300 dpi, publication-ready)
    - tables/         CSV tables (paste into LaTeX or Word)
    - stats.txt       Summary of all findings
"""

import argparse
import os
import warnings
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
from scipy.stats import spearmanr, chi2_contingency, pointbiserialr
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore")

PALETTE   = ["#1a1a2e", "#16213e", "#0f3460", "#533483", "#e94560",
             "#f5a623", "#4ecdc4", "#a8e6cf", "#dcedc1", "#ffd3b6"]
ACCENT    = "#e94560"
DARK      = "#1a1a2e"
MID       = "#0f3460"
LIGHT_BG  = "#f8f9fc"

plt.rcParams.update({
    "figure.facecolor":  LIGHT_BG,
    "axes.facecolor":    "white",
    "axes.edgecolor":    "#cccccc",
    "axes.labelcolor":   DARK,
    "axes.titlesize":    13,
    "axes.labelsize":    11,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "xtick.color":       "#555555",
    "ytick.color":       "#555555",
    "grid.color":        "#e8e8e8",
    "grid.linewidth":    0.8,
    "font.family":       "DejaVu Sans",
    "legend.fontsize":   9,
    "legend.framealpha": 0.85,
    "figure.dpi":        150,
    "savefig.dpi":       300,
    "savefig.bbox":      "tight",
})

BINARY_COLS = [
    "Letter Required", "Uppercase Required", "Lowercase Required", "Number Required",
    "Special Char Required", "Special Chars Forbidden", "Check Common/Breached",
    "No Repeating Chars", "No Sequential Chars", "Strength Meter", #"Unique PW Recommended",
]

SHORT_LABELS = {
    "Letter Required":         "Letter req.",
    "Uppercase Required":      "Uppercase req.",
    "Lowercase Required":      "Lowercase req.",
    "Number Required":         "Number req.",
    "Special Char Required":   "SpChar req.",
    "Special Chars Forbidden": "Some SpChar forb.",
    "Check Common/Breached":   "Common/Breach chk.",
    "No Repeating Chars":      "Repeats Chk.",
    "No Sequential Chars":     "Sequences chk.",
    "Strength Meter":          "Show Strength",
    #"Unique PW Recommended":   "Unique PW",
}

NIST_MIN = 15


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in BINARY_COLS:
        df[col] = (df[col].str.strip().str.lower() == "yes").astype(int)
    df["Min Length"] = pd.to_numeric(df["Min Length"], errors="coerce")
    df["Max Length"] = pd.to_numeric(df["Max Length"], errors="coerce")
    df["sl"]         = pd.to_numeric(df["sl"],         errors="coerce")
    # Filter implausible lengths
    df.loc[df["Min Length"] > 200, "Min Length"] = np.nan
    df.loc[df["Max Length"] > 1000, "Max Length"] = np.nan
    return df


def strength_score(df: pd.DataFrame) -> pd.Series:
    """0–10 composite policy strength score."""
    s = pd.Series(0, index=df.index, dtype=float)
    for col in BINARY_COLS:
        if col != "Special Chars Forbidden":   # forbidden ≠ stronger
            s += df[col]
        else:
            s -= df[col]  # penalise forbidding special chars

    # Length contribution: scaled 0–2
    s += df["Min Length"].clip(0, 16).fillna(0) / 4
    return s


def savefig(fig, path):
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=LIGHT_BG)
    plt.close(fig)
    print(f"  Saved {path}")


def write_table(df_table, path, label=""):
    df_table.to_csv(path)
    print(f"  Saved {path}")


# ── Analysis functions ────────────────────────────────────────────────────────

def section(title, out):
    bar = "=" * 70
    out.append(f"\n{bar}\n{title}\n{bar}")

RANK_BAND_SIZE = 100_000  

def fig0_overview_by_rank_band(df, fig_dir, out):

    section("0. OVERVIEW BY RANK BAND", out)

    df = df.copy()
    df["score"] = strength_score(df)

    # ── Build rank bands ──────────────────────────────────────────────────────
    valid = df.dropna(subset=["sl"]).copy()
    valid = valid[valid["sl"] > 0]

    max_rank    = valid["sl"].max()
    band_edges  = np.arange(0, max_rank + RANK_BAND_SIZE, RANK_BAND_SIZE)
    band_labels = [
        f"{int(lo/1000)}k–{int((lo+RANK_BAND_SIZE)/1000)}k"
        for lo in band_edges[:-1]
    ]

    valid["band"] = pd.cut(
        valid["sl"],
        bins=band_edges,
        labels=band_labels,
        right=True,
        include_lowest=True,
    )

    # ── Aggregations ──────────────────────────────────────────────────────────
    band_counts = valid.groupby("band", observed=True).size().rename("n_sites")
    band_score  = valid.groupby("band", observed=True)["score"].mean()
    band_feats  = (
        valid.groupby("band", observed=True)[BINARY_COLS]
        .mean()
        .mul(100)
        .rename(columns=SHORT_LABELS)
    )

    n_bands = len(band_counts)
    # ── Figure layout ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(max(14, n_bands * 1.4), 17))
    gs  = fig.add_gridspec(3, 1, hspace=0.45)

    bar_colors = [PALETTE[i % len(PALETTE)] for i in range(n_bands)]
    x          = np.arange(n_bands)
    xlabels    = band_counts.index.astype(str)

  
    ax1 = fig.add_subplot(gs[0])
    bars = ax1.bar(x, band_counts.values, color=bar_colors,
                   edgecolor="white", linewidth=0.5, width=0.65)
    ax1.set_xticks(x)
    ax1.set_xticklabels(xlabels, rotation=45, ha="right", fontsize=8)
    ax1.set_ylabel("Number of Sites")
    ax1.set_title(f"A.  Total Sites per {RANK_BAND_SIZE//1000:,}k Rank Band", pad=10)
    ax1.grid(axis="y", linestyle="--")
    for bar in bars:
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(band_counts) * 0.01,
            f"{int(bar.get_height()):,}",
            ha="center", va="bottom", fontsize=7, color=DARK
        )

    ax2 = fig.add_subplot(gs[1])
    bars2 = ax2.bar(x, band_score.values, color=bar_colors,
                    edgecolor="white", linewidth=0.5, width=0.65, alpha=0.75)
    ax2.plot(x, band_score.values, "o-", color=ACCENT,
             linewidth=2, markersize=6, zorder=5, label="Mean score")
    ax2.set_xticks(x)
    ax2.set_xticklabels(xlabels, rotation=45, ha="right", fontsize=8)
    ax2.set_ylabel("Mean Policy Strength Score")
    ax2.set_title(f"B.  Mean Policy Strength Score per {RANK_BAND_SIZE//1000:,}k Rank Band", pad=10)
    ax2.grid(axis="y", linestyle="--")
    ax2.legend()
    for bar, val in zip(bars2, band_score.values):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            val + band_score.max() * 0.02,
            f"{val:.2f}",
            ha="center", va="bottom", fontsize=7, color=DARK
        )

    ax3 = fig.add_subplot(gs[2])
    feat_labels = list(SHORT_LABELS.values())
    heatmap_data = band_feats[feat_labels].T   # features as rows, bands as columns

    im = ax3.imshow(heatmap_data.values, aspect="auto", cmap="Blues",
                    vmin=0, vmax=100)
    ax3.set_xticks(x)
    ax3.set_xticklabels(xlabels, rotation=45, ha="right", fontsize=8)
    ax3.set_yticks(np.arange(len(feat_labels)))
    ax3.set_yticklabels(feat_labels, fontsize=9)
    ax3.set_title(f"C.  Feature Prevalence (%) per {RANK_BAND_SIZE//1000:,}k Rank Band", pad=10)

    # Annotate cells
    for r in range(len(feat_labels)):
        for c in range(n_bands):
            val = heatmap_data.values[r, c]
            text_color = "white" if val > 55 else DARK
            ax3.text(c, r, f"{val:.0f}%",
                     ha="center", va="center", fontsize=7, color=text_color)

    cbar = fig.colorbar(im, ax=ax3, orientation="vertical",
                        fraction=0.02, pad=0.01)
    cbar.set_label("% Sites Enforcing Feature", fontsize=9)

    fig.suptitle(
        f"Password Policy Overview — Every {RANK_BAND_SIZE//1000:,}k Sites by Popularity Rank",
        fontsize=14, y=0.995
    )
    savefig(fig, fig_dir / "fig0_overview_by_rank_band.png")

    # ── Stats log ─────────────────────────────────────────────────────────────
    out.append(f"  Rank band width: {RANK_BAND_SIZE:,}  ({RANK_BAND_SIZE//1000}k)")
    out.append(f"  Total bands:     {n_bands}")

    feat_labels_ordered = list(SHORT_LABELS.values())

    # Header
    out.append(f"\n  {'Band':<14} {'Sites':>8}  {'Mean Score':>11}    {'FEATURE PREVALENCE':<42}  {'FEATURE PREVALENCE (Length)'}")
    out.append("  " + "-" * 110)

    for band, n_sites, sc in zip(xlabels, band_counts.values, band_score.values):
        out.append(f"  {band:<14} {int(n_sites):>8,}  {sc:>11.3f}")

        # Features sorted by prevalence descending for this band
        band_row = band_feats.loc[band, feat_labels_ordered]
        sorted_feats = list(band_row.sort_values(ascending=False).items())

        # Min length value counts for this band, sorted by length value
        band_mask   = valid["band"] == band
        len_counts  = (
            valid.loc[band_mask, "Min Length"]
            .dropna()
            .astype(int)
            .value_counts()
            .sort_index()
        )
        len_total   = len_counts.sum()
        len_rows    = [
            (length, count, count / len_total * 100)
            for length, count in len_counts.items()
        ]  # list of (length_value, count, pct)


        n_rows = max(len(sorted_feats), len(len_rows))
        for i in range(n_rows):
            # Feature prevalence column
            if i < len(sorted_feats):
                feat, pct = sorted_feats[i]
                n_feat    = int(round(pct / 100 * int(n_sites)))
                feat_col  = f"{feat:<24} {pct:5.1f}%  ({n_feat:,} sites)"
            else:
                feat_col  = ""

            # Length prevalence column
            if i < len(len_rows):
                length, count, lpct = len_rows[i]
                len_col = f"{length:>2} - {lpct:4.1f}%  ({count:,} sites)"
            else:
                len_col = ""

            out.append(f"  {'':14} {'':>8}  {'':>11}   {feat_col:<42}  {len_col}")

        out.append("")  

def fig1_feature_prevalence(df, fig_dir, out):
    """Bar chart: % of sites enforcing each policy feature."""
    section("1. FEATURE PREVALENCE", out)
    counts = {SHORT_LABELS[c]: df[c].mean() * 100 for c in BINARY_COLS}
    counts = dict(sorted(counts.items(), key=lambda x: -x[1]))

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(list(counts.keys()), list(counts.values()),
                   color=[PALETTE[i % len(PALETTE)] for i in range(len(counts))],
                   edgecolor="white", linewidth=0.5, height=0.6)
    ax.set_xlabel("Sites Enforcing Feature (%)")
    ax.set_title("Password Policy Feature Prevalence Across 24,000+ Websites", pad=14)
    ax.set_xlim(0, max(counts.values()) * 1.18)
    ax.grid(axis="x", linestyle="--")
    ax.invert_yaxis()
    for bar, val in zip(bars, counts.values()):
        ax.text(val + 0.4, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=9, color=DARK)
    fig.tight_layout()
    savefig(fig, fig_dir / "fig1_feature_prevalence.png")

    for feat, pct in counts.items():
        n = int(pct / 100 * len(df))
        out.append(f"  {feat:<22} {pct:5.1f}%  ({n:,} sites)")

    # Min length value counts (overall)
    out.append("")
    out.append(f"  {'FEATURE PREVALENCE (Length)'}")
    out.append("  " + "-" * 40)

    len_counts = (
        df["Min Length"]
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
    )
    len_total = len_counts.sum()
    for length, count in len_counts.items():
        lpct = count / len_total * 100
        out.append(f"  {length:>2} - {lpct:4.1f}%  ({count:,} sites)")


def fig2_min_length_distribution(df, fig_dir, out):
    """Histogram of min length with NIST threshold marked."""
    section("2. MINIMUM LENGTH DISTRIBUTION", out)
    ml = df["Min Length"].dropna()
    ml = ml[ml <= 64]   # trim extreme outliers for display

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Histogram
    ax = axes[0]
    bins = np.arange(0, 33, 1)
    counts, edges, patches = ax.hist(ml, bins=bins, color=MID, edgecolor="white",
                                     linewidth=0.4, alpha=0.85)
    # Colour bars < NIST_MIN red
    for patch, left in zip(patches, edges[:-1]):
        if left < NIST_MIN:
            patch.set_facecolor(ACCENT)
    ax.axvline(NIST_MIN, color="#f5a623", linewidth=2, linestyle="--",
               label=f"NIST minimum ({NIST_MIN})")
    ax.set_xlabel("Minimum Password Length")
    ax.set_ylabel("Number of Sites")
    ax.set_title("Distribution of Minimum Password Length")
    ax.legend()
    ax.grid(axis="y", linestyle="--")

    # Cumulative
    ax2 = axes[1]
    sorted_ml = np.sort(ml)
    cdf = np.arange(1, len(sorted_ml) + 1) / len(sorted_ml) * 100
    ax2.plot(sorted_ml, cdf, color=MID, linewidth=2)
    ax2.axvline(NIST_MIN, color="#f5a623", linewidth=2, linestyle="--",
                label=f"NIST min ({NIST_MIN})")
    ax2.fill_betweenx([0, 100], 0, NIST_MIN, alpha=0.08, color=ACCENT,
                      label="Below NIST threshold")
    ax2.set_xlabel("Minimum Password Length")
    ax2.set_ylabel("Cumulative % of Sites")
    ax2.set_title("CDF of Minimum Password Length")
    ax2.set_xlim(0, 30)
    ax2.legend()
    ax2.grid(linestyle="--")

    fig.tight_layout()
    savefig(fig, fig_dir / "fig2_min_length_distribution.png")

    pct_has_min = ml.count() / len(df) * 100
    pct_below   = (ml < NIST_MIN).mean() * 100
    pct_meet    = (ml >= NIST_MIN).mean() * 100
    out.append(f"  Sites specifying min length:  {pct_has_min:.1f}%  ({ml.count():,})")
    out.append(f"  Below NIST min ({NIST_MIN}):        {pct_below:.1f}%  of those with explicit min")
    out.append(f"  Meet/exceed NIST min ({NIST_MIN}):  {pct_meet:.1f}%")
    out.append(f"  Mean min length:  {ml.mean():.2f}  Median: {ml.median():.0f}  Std: {ml.std():.2f}")
    mc = ml.mode()[0]
    out.append(f"  Most common min length: {mc:.0f}  ({(ml==mc).sum():,} sites)")


def fig3_strength_score(df, fig_dir, out):
    """Distribution of composite strength scores."""
    section("3. POLICY STRENGTH SCORE DISTRIBUTION", out)
    df = df.copy()
    df["score"] = strength_score(df)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax = axes[0]
    ax.hist(df["score"].dropna(), bins=30, color=MID, edgecolor="white",
            linewidth=0.4, alpha=0.85)
    ax.axvline(df["score"].mean(), color=ACCENT, linewidth=2, linestyle="--",
               label=f"Mean = {df['score'].mean():.2f}")
    ax.set_xlabel("Policy Strength Score (0–10)")
    ax.set_ylabel("Number of Sites")
    ax.set_title("Distribution of Password Policy Strength Scores")
    ax.legend()
    ax.grid(axis="y", linestyle="--")

    # Score by rank decile
    ax2 = axes[1]
    df2 = df.dropna(subset=["sl", "score"])
    df2 = df2[df2["sl"] > 0]
    df2["rank_decile"] = pd.qcut(df2["sl"], 10,
                                  labels=[f"D{i}" for i in range(1, 11)])
    means = df2.groupby("rank_decile", observed=True)["score"].mean()
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(means))]
    bars = ax2.bar(means.index.astype(str), means.values, color=colors,
                   edgecolor="white", linewidth=0.5)
    ax2.set_xlabel("Rank Decile (D1 = most popular)")
    ax2.set_ylabel("Mean Policy Strength Score")
    ax2.set_title("Policy Strength by Website Popularity Decile")
    ax2.grid(axis="y", linestyle="--")
    for bar in bars:
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                 f"{bar.get_height():.2f}", ha="center", fontsize=8)

    fig.tight_layout()
    savefig(fig, fig_dir / "fig3_strength_score.png")

    out.append(f"  Mean score:   {df['score'].mean():.3f}")
    out.append(f"  Median score: {df['score'].median():.3f}")
    out.append(f"  Std dev:      {df['score'].std():.3f}")
    out.append(f"  Score = 0 (no policy info): {(df['score'] == 0).sum():,} sites  "
               f"({(df['score'] == 0).mean()*100:.1f}%)")


def fig4_rank_correlation(df, fig_dir, out):
    """Spearman correlation between site rank and policy score."""
    section("4. RANK vs POLICY STRENGTH (SPEARMAN CORRELATION)", out)
    df = df.copy()
    df["score"] = strength_score(df)
    valid = df.dropna(subset=["sl", "score"])
    valid = valid[valid["sl"] > 0]

    rho, pval = spearmanr(valid["sl"], valid["score"])

    # Scatter with trend 
    fig, ax = plt.subplots(figsize=(9, 5))
    valid["rank_bin"] = pd.qcut(valid["sl"], 100, labels=False)
    binned = valid.groupby("rank_bin")["score"].mean().reset_index()
    ax.scatter(valid["sl"], valid["score"], alpha=0.03, s=2,
               color=MID, rasterized=True)
    ax.plot(valid.groupby("rank_bin")["sl"].median().values,
            binned["score"].values,
            color=ACCENT, linewidth=2.5, label="Binned mean (100 bins)")
    ax.set_xlabel("Site Rank (lower = more popular)")
    ax.set_ylabel("Policy Strength Score")
    ax.set_title(f"Site Rank vs. Password Policy Strength\n"
                 f"Spearman ρ = {rho:.4f},  p = {pval:.4f}")
    ax.legend()
    ax.grid(linestyle="--")
    fig.tight_layout()
    savefig(fig, fig_dir / "fig4_rank_correlation.png")

    out.append(f"  Spearman ρ = {rho:.4f}")
    out.append(f"  p-value    = {pval:.6f}")
    interpretation = "significant negative" if (pval < 0.05 and rho < 0) else \
                     "significant positive" if (pval < 0.05 and rho > 0) else "not significant"
    out.append(f"  Interpretation: {interpretation} correlation  (α = 0.05)")
    out.append(f"  N = {len(valid):,}")


def fig5_cooccurrence(df, fig_dir, out):
    """Co-occurrence heatmap of binary features."""
    section("5. FEATURE CO-OCCURRENCE", out)
    labels = [SHORT_LABELS[c] for c in BINARY_COLS]
    mat = np.zeros((len(BINARY_COLS), len(BINARY_COLS)))
    for i, ci in enumerate(BINARY_COLS):
        for j, cj in enumerate(BINARY_COLS):
            both = ((df[ci] == 1) & (df[cj] == 1)).sum()
            either = ((df[ci] == 1) | (df[cj] == 1)).sum()
            mat[i, j] = both / either if either > 0 else 0

    fig, ax = plt.subplots(figsize=(9, 7.5))
    mask = np.eye(len(BINARY_COLS), dtype=bool)
    sns.heatmap(mat, xticklabels=labels, yticklabels=labels,
                annot=True, fmt=".2f", cmap="Blues",
                linewidths=0.4, linecolor="#eeeeee",
                mask=mask, ax=ax,
                cbar_kws={"label": "Jaccard Similarity"})
    ax.set_title("Feature Co-occurrence (Jaccard Similarity)", pad=14)
    plt.xticks(rotation=40, ha="right")
    plt.yticks(rotation=0)
    fig.tight_layout()
    savefig(fig, fig_dir / "fig5_cooccurrence.png")

    # Top pairs
    pairs = []
    for i in range(len(BINARY_COLS)):
        for j in range(i + 1, len(BINARY_COLS)):
            pairs.append((labels[i], labels[j], mat[i, j]))
    pairs.sort(key=lambda x: -x[2])
    out.append("  Top 5 co-occurring pairs (Jaccard):")
    for a, b, j in pairs[:5]:
        out.append(f"    {a} + {b}: {j:.3f}")


def fig6_nist_compliance(df, fig_dir, out):
    """NIST compliance breakdown."""
    section("6. NIST SP 800-63B-4 COMPLIANCE", out)
    df = df.copy()

    has_min      = df["Min Length"].notna()
    meets_length = df["Min Length"].fillna(0) >= NIST_MIN
    checks_pwned = df["Check Common/Breached"] == 1
    # NIST discourages mandatory complexity rules
    no_complexity = ~((df["Uppercase Required"] == 1) |
                      (df["Lowercase Required"] == 1) |
                      (df["Number Required"] == 1) |
                      (df["Special Char Required"] == 1))

    df["nist_length"]     = meets_length.astype(int)
    df["nist_no_complex"] = no_complexity.astype(int)
    df["nist_breach"]     = checks_pwned.astype(int)
    df["nist_full"]       = (meets_length & no_complexity & checks_pwned).astype(int)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Pie of full compliance
    ax = axes[0]
    compliant = df["nist_full"].sum()
    non_comp  = len(df) - compliant
    wedges, texts, autotexts = ax.pie(
        [compliant, non_comp],
        labels=["Fully Compliant", "Non-Compliant"],
        colors=[MID, ACCENT],
        autopct="%1.1f%%", startangle=140,
        textprops={"fontsize": 11},
        wedgeprops={"edgecolor": "white", "linewidth": 2}
    )
    ax.set_title("Full NIST Compliance\n(length ≥ 15, no mandatory complexity, breach check)")

    # Stacked bar for individual criteria
    ax2 = axes[1]
    criteria = {
        "Min length ≥ 15":       df["nist_length"].mean() * 100,
        "No mandatory\ncomplexity": df["nist_no_complex"].mean() * 100,
        "Breach password\ncheck":   df["nist_breach"].mean() * 100,
        "All three\n(fully compliant)": df["nist_full"].mean() * 100,
    }
    bars = ax2.bar(criteria.keys(), criteria.values(),
                   color=[MID, MID, MID, ACCENT],
                   edgecolor="white", linewidth=0.5, width=0.55)
    ax2.set_ylabel("Sites Meeting Criterion (%)")
    ax2.set_title("NIST Compliance by Individual Criterion")
    ax2.set_ylim(0, 110)
    ax2.grid(axis="y", linestyle="--")
    for bar in bars:
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                 f"{bar.get_height():.1f}%", ha="center", fontsize=9, fontweight="bold")

    fig.tight_layout()
    savefig(fig, fig_dir / "fig6_nist_compliance.png")

    out.append(f"  Min length ≥ {NIST_MIN}:          {df['nist_length'].mean()*100:.1f}%")
    out.append(f"  No mandatory complexity:   {df['nist_no_complex'].mean()*100:.1f}%")
    out.append(f"  Breach password check:     {df['nist_breach'].mean()*100:.1f}%")
    out.append(f"  Fully compliant (all 3):   {df['nist_full'].mean()*100:.1f}%  ({compliant:,} sites)")


def fig7_clustering(df, fig_dir, tables_dir, out):
    """K-means clustering to find policy archetypes."""
    section("7. POLICY ARCHETYPES (K-MEANS CLUSTERING)", out)
    features = BINARY_COLS + ["Min Length"]
    X = df[features].copy()
    X["Min Length"] = X["Min Length"].fillna(0).clip(0, 30) / 30  # normalise
    X = X.fillna(0)

    # Choose k via silhouette
    silhouettes = {}
    for k in range(2, 9):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        silhouettes[k] = silhouette_score(X, labels)

    best_k = max(silhouettes, key=silhouettes.get)

    km_final = KMeans(n_clusters=best_k, random_state=42, n_init=20)
    df = df.copy()
    df["cluster"] = km_final.fit_predict(X)

    # PCA for 2D visualisation
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X)
    df["pca1"], df["pca2"] = coords[:, 0], coords[:, 1]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Silhouette plot
    ax = axes[0]
    ax.plot(list(silhouettes.keys()), list(silhouettes.values()),
            "o-", color=MID, linewidth=2, markersize=7)
    ax.axvline(best_k, color=ACCENT, linewidth=2, linestyle="--",
               label=f"Best k = {best_k}")
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("Selecting Optimal k via Silhouette Score")
    ax.legend()
    ax.grid(linestyle="--")

    # PCA scatter
    ax2 = axes[1]
    cluster_colors = PALETTE[:best_k]
    for c in range(best_k):
        mask = df["cluster"] == c
        ax2.scatter(df.loc[mask, "pca1"], df.loc[mask, "pca2"],
                    alpha=0.15, s=4, color=cluster_colors[c],
                    label=f"Cluster {c + 1} (n={mask.sum():,})",
                    rasterized=True)
    ax2.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% var)")
    ax2.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% var)")
    ax2.set_title(f"Policy Archetypes — {best_k} Clusters (PCA projection)")
    ax2.legend(markerscale=4, loc="best")
    ax2.grid(linestyle="--")

    fig.tight_layout()
    savefig(fig, fig_dir / "fig7_clustering.png")

    # Cluster profiles
    profile_cols = [SHORT_LABELS[c] for c in BINARY_COLS] + ["Min Length"]
    feat_labels  = BINARY_COLS + ["Min Length"]
    cluster_profile = df.groupby("cluster")[feat_labels].mean()
    cluster_profile.index = [f"Cluster {i+1}" for i in cluster_profile.index]
    cluster_profile.columns = profile_cols
    cluster_profile["Size"] = df.groupby("cluster").size().values
    cluster_profile["Size %"] = (cluster_profile["Size"] / len(df) * 100).round(1)

    write_table(cluster_profile.round(3), tables_dir / "cluster_profiles.csv",
                label="Cluster profiles")

    # Heatmap of cluster profiles
    fig2, ax3 = plt.subplots(figsize=(12, 4))
    plot_data = cluster_profile[profile_cols[:-1]].T  # exclude Min Length for binary heatmap
    sns.heatmap(plot_data.astype(float), annot=True, fmt=".2f",
                cmap="YlOrRd", linewidths=0.4, linecolor="#eeeeee",
                vmin=0, vmax=1, ax=ax3,
                cbar_kws={"label": "Proportion enforcing"})
    ax3.set_title("Policy Archetype Profiles (Mean Feature Enforcement per Cluster)", pad=14)
    fig2.tight_layout()
    savefig(fig2, fig_dir / "fig7b_cluster_profiles.png")

    out.append(f"  Best k = {best_k}  (silhouette = {silhouettes[best_k]:.4f})")
    out.append(f"  PCA variance explained: PC1={pca.explained_variance_ratio_[0]*100:.1f}%  "
               f"PC2={pca.explained_variance_ratio_[1]*100:.1f}%")
    out.append("\n  Cluster sizes:")
    for i in range(best_k):
        n = (df["cluster"] == i).sum()
        out.append(f"    Cluster {i+1}: {n:,} sites  ({n/len(df)*100:.1f}%)")


def fig8_chi2_independence(df, fig_dir, tables_dir, out):
    """Chi-square test of independence between all feature pairs."""
    section("8. CHI-SQUARE INDEPENDENCE TESTS (FEATURE PAIRS)", out)
    n = len(BINARY_COLS)
    chi2_mat  = np.zeros((n, n))
    pval_mat  = np.ones((n, n))
    cramer_mat = np.zeros((n, n))

    results = []
    for i, ci in enumerate(BINARY_COLS):
        for j, cj in enumerate(BINARY_COLS):
            if i >= j:
                continue
            ct = pd.crosstab(df[ci], df[cj])
            chi2, p, dof, _ = chi2_contingency(ct)
            n_obs = ct.values.sum()
            cramer_v = np.sqrt(chi2 / (n_obs * (min(ct.shape) - 1)))
            chi2_mat[i, j]  = chi2_mat[j, i]  = chi2
            pval_mat[i, j]  = pval_mat[j, i]  = p
            cramer_mat[i, j] = cramer_mat[j, i] = cramer_v
            results.append({
                "Feature A":  SHORT_LABELS[ci],
                "Feature B":  SHORT_LABELS[cj],
                "Chi2":       round(chi2, 2),
                "p-value":    round(p, 6),
                "Cramér V":   round(cramer_v, 4),
                "Significant": "Yes" if p < 0.05 else "No",
            })

    res_df = pd.DataFrame(results).sort_values("Cramér V", ascending=False)
    write_table(res_df, tables_dir / "chi2_independence.csv")

    labels = [SHORT_LABELS[c] for c in BINARY_COLS]
    fig, ax = plt.subplots(figsize=(9, 7.5))
    mask = np.eye(n, dtype=bool)
    sns.heatmap(cramer_mat, xticklabels=labels, yticklabels=labels,
                annot=True, fmt=".2f", cmap="Purples",
                linewidths=0.4, linecolor="#eeeeee",
                mask=mask, ax=ax, vmin=0, vmax=0.6,
                cbar_kws={"label": "Cramér's V"})
    #ax.set_title("Feature Association Strength (Cramér's V)")
    plt.xticks(rotation=40, ha="right")
    plt.yticks(rotation=0)
    fig.tight_layout()
    savefig(fig, fig_dir / "fig8_cramer_v.png")

    out.append("  Top 5 strongest associations (Cramér's V):")
    for _, row in res_df.head(5).iterrows():
        out.append(f"    {row['Feature A']} ↔ {row['Feature B']}: V={row['Cramér V']:.3f}  p={row['p-value']:.4f}")


def table_descriptive(df, tables_dir, out):
    """Descriptive statistics table."""
    section("9. DESCRIPTIVE STATISTICS TABLE", out)
    rows = []
    for col in BINARY_COLS:
        n_yes = df[col].sum()
        pct   = df[col].mean() * 100
        rows.append({
            "Feature":       SHORT_LABELS[col],
            "N (Yes)":       int(n_yes),
            "% Sites":       round(pct, 2),
            "95% CI lower":  round(pct - 1.96 * np.sqrt(pct*(100-pct)/len(df)), 2),
            "95% CI upper":  round(pct + 1.96 * np.sqrt(pct*(100-pct)/len(df)), 2),
        })
    desc_df = pd.DataFrame(rows)
    write_table(desc_df, tables_dir / "descriptive_stats.csv")

    ml = df["Min Length"].dropna()
    length_stats = {
        "Feature": "Min Length",
        "N (specified)": len(ml),
        "% Sites with min length": round(len(ml) / len(df) * 100, 2),
        "Mean":   round(ml.mean(), 2),
        "Median": ml.median(),
        "Std":    round(ml.std(), 2),
        "Min":    ml.min(),
        "Max":    ml.max(),
        "% below NIST (< 8)": round((ml < 8).mean() * 100, 2),
    }
    length_df = pd.DataFrame([length_stats])
    write_table(length_df, tables_dir / "length_stats.csv")
    out.append("  Tables written to tables/descriptive_stats.csv and tables/length_stats.csv")


def table_max_length(df, tables_dir, out):
    """Max length analysis — many sites have suspiciously low max lengths."""
    section("10. MAXIMUM LENGTH ANALYSIS", out)
    ml = df["Max Length"].dropna()
    ml = ml[ml > 0]
    out.append(f"  Sites with explicit max length: {len(ml):,}  ({len(ml)/len(df)*100:.1f}%)")
    out.append(f"  Mean max: {ml.mean():.1f}  Median: {ml.median():.0f}")
    low_max = (ml <= 20).sum()
    out.append(f"  Sites with max ≤ 20 chars: {low_max:,}  ({low_max/len(ml)*100:.1f}% of those with a max)")
    vc = ml.value_counts().head(10)
    out.append("  Most common max lengths:")
    for v, c in vc.items():
        out.append(f"    {int(v):>5} chars — {c:,} sites")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Analyse structured password policy CSV for research paper.")
    parser.add_argument("--input",  default="password_policies_structured.csv")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()

    out_path   = Path(args.outdir)
    fig_dir    = out_path / "figures"
    tables_dir = out_path / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.input} …")
    df = load_data(args.input)
    print(f"Loaded {len(df):,} rows\n")

    log = [
        "PASSWORD POLICY EMPIRICAL ANALYSIS — RESULTS SUMMARY",
        f"Dataset: {args.input}",
        f"N = {len(df):,} websites",
        "=" * 70,
    ]

    print("Running analyses …")
    fig0_overview_by_rank_band(df, fig_dir, log)
    fig1_feature_prevalence(df, fig_dir, log)
    fig2_min_length_distribution(df, fig_dir, log)
    fig3_strength_score(df, fig_dir, log)
    fig4_rank_correlation(df, fig_dir, log)
    fig5_cooccurrence(df, fig_dir, log)
    fig6_nist_compliance(df, fig_dir, log)
    fig7_clustering(df, fig_dir, tables_dir, log)
    fig8_chi2_independence(df, fig_dir, tables_dir, log)
    table_descriptive(df, tables_dir, log)
    table_max_length(df, tables_dir, log)

    stats_path = out_path / "stats.txt"
    stats_path.write_text("\n".join(log))
    print(f"\nDone! Results written to: {out_path}/")
    print(f"  {fig_dir}/      — {len(list(fig_dir.glob('*.png')))} figures")
    print(f"  {tables_dir}/   — {len(list(tables_dir.glob('*.csv')))} tables")
    print(f"  {stats_path}    — full stats log")


if __name__ == "__main__":
    main()
