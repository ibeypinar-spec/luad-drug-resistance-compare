"""
generate_figures_publication.py
Creates 5 publication-quality multi-panel figures for LUAD manuscript.
Output: results/publication_figures/  at 300 DPI (PNG + PDF)
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import seaborn as sns

# ── Paths ────────────────────────────────────────────────────────────────────
WORK_DIR = "G:\\Drive'\u0131m\\\u00c7al\u0131\u015fma\\Aktif \u00c7al\u0131\u015fmalar\\9. A\u00e7\u0131k eri\u015fim veri \u00e7al\u0131\u015fmalar\u0131\\LUAD Drug Resistance Study"
RES      = os.path.join(WORK_DIR, "results")
PUB      = os.path.join(RES, "publication_figures")
os.makedirs(PUB, exist_ok=True)

XL2  = os.path.join(RES, "LUAD_Faz2_Results.xlsx")
XL2B = os.path.join(RES, "LUAD_Faz2b_Results.xlsx")

# ── Global style ─────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'font.size':          11,
    'axes.titlesize':     12,
    'axes.labelsize':     11,
    'xtick.labelsize':    10,
    'ytick.labelsize':    10,
    'legend.fontsize':    10,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'figure.dpi':         150,
    'savefig.dpi':        300,
    'savefig.bbox':       'tight',
    'savefig.facecolor':  'white',
})

# Kinase color palette (consistent across all figures)
KINASE_COLORS = {
    'PTK2': '#4C72B0', 'MET':  '#DD8452', 'EGFR': '#55A868',
    'DDR1': '#C44E52', 'LCK':  '#8172B3', 'YES1': '#937860',
    'FYN':  '#DA8BC3', 'LYN':  '#8C8C8C', 'SRC':  '#CCB974',
}
SRC_FAMILY = {'LCK', 'YES1', 'FYN', 'LYN', 'SRC'}

def panel_label(ax, letter, fontsize=14):
    ax.text(-0.10, 1.05, letter, transform=ax.transAxes,
            fontsize=fontsize, fontweight='bold', va='top', ha='right')

def img_panel(ax, path, label=None):
    if os.path.exists(path):
        img = mpimg.imread(path)
        ax.imshow(img, aspect='auto')
    else:
        ax.text(0.5, 0.5, f'[{os.path.basename(path)}\nnot found]',
                ha='center', va='center', transform=ax.transAxes, color='grey')
    ax.axis('off')
    if label:
        ax.text(-0.02, 1.02, label, transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='bottom', ha='right')

def save_fig(fig, name):
    for ext in ['png', 'pdf']:
        out = os.path.join(PUB, f"{name}.{ext}")
        fig.savefig(out, dpi=300 if ext == 'png' else None,
                    bbox_inches='tight', facecolor='white')
    print(f"  Saved: {name}.png / .pdf")
    plt.close(fig)

# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 1 — pARACNe Hub Kinase Architecture
# Panel A: top-20 bar chart | Panel B: 9 focal kinases coloured by family
# ═══════════════════════════════════════════════════════════════════════════
def make_figure1():
    df = pd.read_excel(XL2, sheet_name='1_Hub_Kinazlar')
    # Expected columns: kinase / n_substrates (or similar)
    # Detect column names
    kin_col  = [c for c in df.columns if 'kinase' in c.lower() or 'kinaz' in c.lower()][0]
    sub_col  = [c for c in df.columns if 'sub' in c.lower() or 'n_' in c.lower()][0]
    df = df.sort_values(sub_col, ascending=False).reset_index(drop=True)

    top20 = df.head(20).copy()
    focal = df[df[sub_col] >= 100].copy().sort_values(sub_col, ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # ── Panel A: top-20 ──
    ax = axes[0]
    colors_a = ['#C44E52' if k in KINASE_COLORS else '#9db8d2'
                for k in top20[kin_col]]
    bars = ax.barh(range(len(top20)), top20[sub_col].values,
                   color=colors_a, edgecolor='white', linewidth=0.5)
    ax.set_yticks(range(len(top20)))
    ax.set_yticklabels(top20[kin_col].values, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel('Number of substrates', fontsize=11)
    ax.set_title('Top 20 hub kinases', fontsize=12, pad=8)
    ax.axvline(100, color='red', linewidth=1, linestyle='--', alpha=0.7,
               label='Focal threshold (n≥100)')
    ax.legend(fontsize=9, frameon=False)
    # Value labels
    for bar, val in zip(bars, top20[sub_col].values):
        ax.text(val + 2, bar.get_y() + bar.get_height()/2,
                str(int(val)), va='center', fontsize=9)
    panel_label(ax, 'A')

    # ── Panel B: 9 focal kinases coloured by family ──
    ax = axes[1]
    colors_b = ['#E8735A' if k in SRC_FAMILY else '#4C72B0'
                for k in focal[kin_col]]
    bars2 = ax.bar(range(len(focal)), focal[sub_col].values,
                   color=colors_b, edgecolor='white', linewidth=0.6, width=0.65)
    ax.set_xticks(range(len(focal)))
    ax.set_xticklabels(focal[kin_col].values, rotation=35, ha='right', fontsize=11)
    ax.set_ylabel('Number of substrates', fontsize=11)
    ax.set_title('Nine focal hub kinases (≥100 substrates)', fontsize=12, pad=8)
    # Value labels on bars
    for bar, val in zip(bars2, focal[sub_col].values):
        ax.text(bar.get_x() + bar.get_width()/2, val + 2,
                str(int(val)), ha='center', va='bottom', fontsize=10, fontweight='bold')
    # Legend
    legend_els = [
        mpatches.Patch(color='#E8735A', label='SRC family'),
        mpatches.Patch(color='#4C72B0', label='Other TK'),
    ]
    ax.legend(handles=legend_els, fontsize=10, frameon=False, loc='upper right')
    panel_label(ax, 'B')

    plt.tight_layout(w_pad=3)
    save_fig(fig, 'Figure1_HubKinases')

# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 2 — GDSC2 Kinase–Drug Associations
# Panel A: correlation heatmap | Panel B: top scatter plots (existing PNG)
# ═══════════════════════════════════════════════════════════════════════════
def make_figure2():
    df = pd.read_excel(XL2, sheet_name='2_GDSC2_Korelasyon')
    kin_col  = [c for c in df.columns if 'kinase' in c.lower() or 'kinaz' in c.lower()][0]
    drug_col = [c for c in df.columns if 'drug' in c.lower() or 'ilac' in c.lower() or 'ilaç' in c.lower()][0]
    rho_col  = [c for c in df.columns if 'rho' in c.lower()][0]
    p_col    = [c for c in df.columns if 'pval' in c.lower() or 'p_val' in c.lower() or c.lower()=='p'][0]

    # Take top 15 drugs (by lowest p-value) for heatmap readability
    top_drugs = df.nsmallest(20, p_col)[drug_col].unique()[:15]
    pivot = df[df[drug_col].isin(top_drugs)].pivot_table(
        index=kin_col, columns=drug_col, values=rho_col, aggfunc='mean')
    pivot = pivot.reindex(index=[k for k in
        ['PTK2','MET','EGFR','DDR1','LCK','YES1','FYN','LYN','SRC']
        if k in pivot.index])

    fig = plt.figure(figsize=(14, 9))
    gs  = gridspec.GridSpec(1, 2, width_ratios=[1.4, 1], wspace=0.35)

    # ── Panel A: Heatmap ──
    ax_a = fig.add_subplot(gs[0])
    mask = pivot.isnull()
    cmap = sns.diverging_palette(240, 10, as_cmap=True)
    sns.heatmap(pivot, ax=ax_a, cmap=cmap, center=0,
                vmin=-0.5, vmax=0.5, linewidths=0.4, linecolor='#cccccc',
                mask=mask, annot=True, fmt='.2f', annot_kws={'size': 9},
                cbar_kws={'label': 'Spearman ρ', 'shrink': 0.8})
    ax_a.set_title('Kinase expression vs. drug LN_IC50\n(GDSC2, 62 LUAD cell lines)', fontsize=12)
    ax_a.set_xlabel('Drug', fontsize=11)
    ax_a.set_ylabel('Kinase', fontsize=11)
    ax_a.tick_params(axis='x', rotation=40, labelsize=9)
    ax_a.tick_params(axis='y', rotation=0, labelsize=10)
    panel_label(ax_a, 'A')

    # ── Panel B: existing scatter PNG ──
    ax_b = fig.add_subplot(gs[1])
    img_panel(ax_b, os.path.join(RES, 'fig2b_top_scatter.png'), label='B')
    ax_b.set_title('Top kinase–drug pairs (scatter)', fontsize=12, pad=8)

    save_fig(fig, 'Figure2_GDSC2_Correlations')

# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 3 — YES1 as Independent Prognostic Factor
# Panel A: tertile KM (existing fig7) | Panel B: Cox forest (rebuilt)
# ═══════════════════════════════════════════════════════════════════════════
def make_figure3():
    # Cox regression data from Excel
    cox = pd.read_excel(XL2, sheet_name='4_Cox_Regression')
    # Detect column names robustly
    cov_col = cox.columns[0]  # covariate / kinase name
    hr_col  = [c for c in cox.columns if 'exp' in c.lower() and 'coef' in c.lower() and 'lower' not in c.lower() and 'upper' not in c.lower()][0]
    lo_col  = [c for c in cox.columns if 'lower' in c.lower()][0]
    hi_col  = [c for c in cox.columns if 'upper' in c.lower()][0]
    p_col   = [c for c in cox.columns if c.lower() == 'p' or 'pval' in c.lower() or (c.lower().startswith('p') and len(c) <= 2)][0]

    cox = cox[cox[cov_col] != 'AGE'].copy()  # exclude age covariate
    cox['sig'] = cox[p_col] < 0.05

    fig = plt.figure(figsize=(14, 6))
    gs  = gridspec.GridSpec(1, 2, width_ratios=[1.05, 1], wspace=0.3)

    # ── Panel A: Tertile KM (existing PNG) ──
    ax_a = fig.add_subplot(gs[0])
    img_panel(ax_a, os.path.join(RES, 'fig7_YES1_tertile_egfr_subgroup.png'), label='A')
    ax_a.set_title('Kaplan–Meier OS by expression tertile\n(TCGA-LUAD, n = 497)', fontsize=12, pad=6)

    # ── Panel B: Cox forest plot (rebuilt from data) ──
    ax_b = fig.add_subplot(gs[1])
    kinases = cox[cov_col].tolist()
    hrs     = cox[hr_col].values.astype(float)
    los     = cox[lo_col].values.astype(float)
    his     = cox[hi_col].values.astype(float)
    pvals   = cox[p_col].values.astype(float)
    y_pos   = np.arange(len(kinases))

    colors_forest = ['#C44E52' if s else '#4C72B0' for s in cox['sig']]
    for i, (k, hr, lo, hi, pv, col) in enumerate(zip(kinases, hrs, los, his, pvals, colors_forest)):
        ax_b.plot([lo, hi], [i, i], color=col, linewidth=2.2, solid_capstyle='round')
        ms = 10 if pv < 0.05 else 7
        ax_b.scatter(hr, i, color=col, s=ms**2, zorder=5)
        # p-value annotation
        p_str = f'p={pv:.3f}' if pv >= 0.001 else 'p<0.001'
        ax_b.text(max(his)*1.07, i, p_str, va='center', fontsize=9,
                  color='#C44E52' if pv < 0.05 else 'grey',
                  fontweight='bold' if pv < 0.05 else 'normal')

    ax_b.axvline(1.0, color='grey', linewidth=1.2, linestyle='--', alpha=0.7)
    ax_b.set_yticks(y_pos)
    ax_b.set_yticklabels(kinases, fontsize=11)
    ax_b.set_xlabel('Hazard Ratio (95% CI)', fontsize=11)
    ax_b.set_title('Multivariate Cox regression\n(n = 487, ridge λ = 0.1)', fontsize=12, pad=6)
    ax_b.invert_yaxis()
    ax_b.set_xlim(min(los)*0.85, max(his)*1.25)

    legend_els = [
        Line2D([0],[0], marker='o', color='w', markerfacecolor='#C44E52', markersize=10, label='p < 0.05'),
        Line2D([0],[0], marker='o', color='w', markerfacecolor='#4C72B0', markersize=8, label='p ≥ 0.05'),
    ]
    ax_b.legend(handles=legend_els, frameon=False, fontsize=10, loc='lower right')
    panel_label(ax_b, 'B')

    save_fig(fig, 'Figure3_YES1_Survival')

# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 4 — Composite Kinase Activation Score (KAS)
# A: violins | B: PCA loadings | C: PCA scatter | D: EGFR mut comparison
# ═══════════════════════════════════════════════════════════════════════════
def make_figure4():
    kas_df = pd.read_excel(XL2, sheet_name='5_CPTAC_KAS')
    pca_df = pd.read_excel(XL2B, sheet_name='4_KAS_PCA')

    # kas_df: rows = patients, columns include kinase KAS scores
    kinases = [k for k in ['PTK2','MET','EGFR','DDR1','LCK','YES1','FYN','LYN','SRC']
               if k in kas_df.columns]
    kas_long = kas_df[kinases].melt(var_name='Kinase', value_name='KAS')

    fig = plt.figure(figsize=(16, 11))
    gs  = gridspec.GridSpec(2, 2, hspace=0.45, wspace=0.35)

    # ── Panel A: Violin plots ──
    ax_a = fig.add_subplot(gs[0, :])  # full top row
    order = sorted(kinases, key=lambda k: kas_df[k].median(), reverse=True)
    pal   = [KINASE_COLORS.get(k, '#9db8d2') for k in order]
    vp = sns.violinplot(data=kas_long[kas_long['Kinase'].isin(order)],
                        x='Kinase', y='KAS', order=order,
                        palette=pal, inner='box', linewidth=1.2, ax=ax_a,
                        cut=0.5)
    ax_a.axhline(0, color='grey', linewidth=0.8, linestyle='--', alpha=0.5)
    ax_a.set_xlabel('', fontsize=11)
    ax_a.set_ylabel('Kinase Activation Score\n(mean log₂ phospho-ratio)', fontsize=11)
    ax_a.set_title('Substrate-based Kinase Activation Scores — CPTAC-LUAD (n = 110)', fontsize=12)
    # SRC family boxes
    for i, k in enumerate(order):
        if k in SRC_FAMILY:
            ax_a.axvspan(i-0.45, i+0.45, alpha=0.07, color='#E8735A', zorder=0)
    patch = mpatches.Patch(color='#E8735A', alpha=0.3, label='SRC family')
    ax_a.legend(handles=[patch], frameon=False, fontsize=10, loc='upper right')
    panel_label(ax_a, 'A')

    # ── Panel B: PCA loadings bar chart ──
    ax_b = fig.add_subplot(gs[1, 0])
    # Detect columns
    pc1_col = [c for c in pca_df.columns if 'pc1' in c.lower() or ('1' in c and 'load' in c.lower())][0]
    kin_col_pca = pca_df.columns[0]
    pca_sub = pca_df[pca_df[kin_col_pca].isin(kinases)].copy()
    pca_sub = pca_sub.sort_values(pc1_col, ascending=True)
    colors_pca = [KINASE_COLORS.get(k, '#9db8d2') for k in pca_sub[kin_col_pca]]
    ax_b.barh(range(len(pca_sub)), pca_sub[pc1_col].values,
              color=colors_pca, edgecolor='white', linewidth=0.5)
    ax_b.set_yticks(range(len(pca_sub)))
    ax_b.set_yticklabels(pca_sub[kin_col_pca].values, fontsize=11)
    ax_b.set_xlabel('PC1 loading', fontsize=11)
    ax_b.set_title('PC1 loadings\n(80.8% of KAS variance)', fontsize=12)
    ax_b.axvline(0, color='grey', linewidth=0.8)
    panel_label(ax_b, 'B')

    # ── Panel C: EGFR mutation KAS comparison (existing PNG) ──
    ax_c = fig.add_subplot(gs[1, 1])
    img_panel(ax_c, os.path.join(RES, 'fig5b_kas_egfr_mutation.png'), label='C')
    ax_c.set_title('KAS by EGFR mutation status\n(CPTAC-LUAD)', fontsize=12, pad=6)

    save_fig(fig, 'Figure4_KAS_CPTAC')

# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 5 — SRC Family Co-activation & pARACNe Validation
# A: co-activation heatmap | B: validation dot plot
# ═══════════════════════════════════════════════════════════════════════════
def make_figure5():
    coact_df = pd.read_excel(XL2B, sheet_name='5_CoActivation_CPTAC')
    val_df   = pd.read_excel(XL2, sheet_name='6_pARACNe_Validation')

    fig = plt.figure(figsize=(14, 6))
    gs  = gridspec.GridSpec(1, 2, width_ratios=[1, 1.1], wspace=0.4)

    # ── Panel A: Co-activation heatmap ──
    ax_a = fig.add_subplot(gs[0])
    # coact_df should be 9×9 correlation matrix
    # rows/cols might be kinase names as index
    if coact_df.index.dtype == object or coact_df.index.name:
        mat = coact_df
    else:
        mat = coact_df.set_index(coact_df.columns[0])

    # Keep only kinases of interest
    keep = [k for k in ['PTK2','MET','EGFR','DDR1','LCK','YES1','FYN','LYN','SRC']
            if k in mat.index]
    mat = mat.loc[keep, [c for c in keep if c in mat.columns]]

    mask = np.zeros_like(mat.values, dtype=bool)
    np.fill_diagonal(mask, True)  # mask diagonal

    cmap = sns.color_palette("coolwarm_r", as_cmap=True)
    sns.heatmap(mat.astype(float), ax=ax_a, cmap='coolwarm', center=0,
                vmin=-1, vmax=1, linewidths=0.6, linecolor='#eeeeee',
                mask=mask, annot=True, fmt='.2f', annot_kws={'size': 10},
                cbar_kws={'label': 'Spearman ρ', 'shrink': 0.85})
    ax_a.set_title('SRC-family co-activation\n(CPTAC phosphoproteomics, n = 110)', fontsize=12)
    ax_a.tick_params(axis='both', rotation=0, labelsize=11)

    # Highlight SRC-family sub-block
    src_idx = [i for i, k in enumerate(keep) if k in SRC_FAMILY]
    if src_idx:
        lo, hi = min(src_idx), max(src_idx) + 1
        for spine in ['bottom','top','left','right']:
            rect = plt.Rectangle((lo, lo), hi-lo, hi-lo,
                                   fill=False, edgecolor='#E8735A',
                                   linewidth=2.5, transform=ax_a.transData)
            ax_a.add_patch(rect)
    panel_label(ax_a, 'A')

    # ── Panel B: pARACNe validation dot plot ──
    ax_b = fig.add_subplot(gs[1])
    # val_df columns: kinase, substrate, site, rho, fdr
    kin_col  = [c for c in val_df.columns if 'kinase' in c.lower()][0]
    rho_col  = [c for c in val_df.columns if 'rho' in c.lower() or 'spearman' in c.lower()][0]
    fdr_col  = [c for c in val_df.columns if 'fdr' in c.lower()][0]

    val_sig = val_df[val_df[fdr_col] < 0.05].copy()

    # Count validated pairs per kinase
    cnt = val_sig[kin_col].value_counts().reset_index()
    cnt.columns = ['kinase', 'n_validated']
    cnt = cnt.sort_values('n_validated', ascending=True)

    colors_val = [KINASE_COLORS.get(k, '#9db8d2') for k in cnt['kinase']]
    ax_b.barh(range(len(cnt)), cnt['n_validated'],
              color=colors_val, edgecolor='white', linewidth=0.5)
    ax_b.set_yticks(range(len(cnt)))
    ax_b.set_yticklabels(cnt['kinase'], fontsize=11)
    ax_b.set_xlabel('Validated interactions (FDR < 0.05)', fontsize=11)
    ax_b.set_title(f'pARACNe predictions validated in\nCPTAC phosphoproteomics\n({len(val_sig)}/752 pairs, 4.9%)',
                   fontsize=12)
    for i, val in enumerate(cnt['n_validated']):
        ax_b.text(val + 0.1, i, str(int(val)), va='center', fontsize=10)

    # Top 5 validated pairs as text annotation
    top5 = val_sig.nsmallest(5, fdr_col)
    sub_col = [c for c in val_df.columns if 'sub' in c.lower()][0]
    site_col = [c for c in val_df.columns if 'site' in c.lower()][0]
    annotation = "Top validated pairs:\n"
    for _, row in top5.iterrows():
        site_short = str(row[site_col]).split(':')[-1] if ':' in str(row[site_col]) else row[site_col]
        annotation += f"  {row[kin_col]} → {row[sub_col]}:{site_short}  ρ={row[rho_col]:.2f}\n"
    ax_b.text(1.02, 0.5, annotation, transform=ax_b.transAxes,
              fontsize=8.5, va='center', ha='left', family='monospace',
              bbox=dict(boxstyle='round,pad=0.4', facecolor='#f8f8f8', alpha=0.8))

    panel_label(ax_b, 'B')

    save_fig(fig, 'Figure5_CoActivation_Validation')

# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 3 supplement: median KM grid (for supplementary figure)
# ═══════════════════════════════════════════════════════════════════════════
def make_supp_km():
    fig, ax = plt.subplots(figsize=(10, 8))
    img_panel(ax, os.path.join(RES, 'fig3_KM_grid.png'))
    ax.set_title('Kaplan–Meier OS: all 9 kinases, median stratification\n(TCGA-LUAD)',
                 fontsize=12, pad=8)
    save_fig(fig, 'FigureS1_KM_Median_Grid')

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
tasks = [
    ('Figure 1 — Hub Kinases',           make_figure1),
    ('Figure 2 — GDSC2 Correlations',    make_figure2),
    ('Figure 3 — YES1 Survival',         make_figure3),
    ('Figure 4 — KAS CPTAC',             make_figure4),
    ('Figure 5 — Co-Activation/Valid.',  make_figure5),
    ('Supp Figure S1 — KM median grid',  make_supp_km),
]

print(f"\nOutput directory: {PUB}\n{'='*55}")
for name, func in tasks:
    print(f"\n{name}")
    try:
        func()
    except Exception as e:
        import traceback
        print(f"  ERROR: {e}")
        traceback.print_exc()

print(f"\n{'='*55}")
print("Done. Files in:", PUB)
files = sorted(os.listdir(PUB))
for f in files:
    sz = os.path.getsize(os.path.join(PUB, f)) // 1024
    print(f"  {f}  ({sz} KB)")
