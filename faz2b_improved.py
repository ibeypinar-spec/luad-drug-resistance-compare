"""
Faz 2b — Geliştirilmiş Analiz
==============================
1. GDSC2 TAM TARAMA: tüm 286 ilaç × 9 kinaz (2574 test)
2. EGFR mutant subgroup KM (TCGA mutations dosyasından)
3. YES1 tertile survival (alt/üst 33%)
4. Kompozit KAS (PCA ile) vs OS
5. Kinaz ko-aktivasyon heatmap (9 kinaz arası korelasyon)
6. GDSC2: EGFR mutant vs WT IC50 karşılaştırması (biyoloji doğrulama)
"""

import os, sys, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, mannwhitneyu, pearsonr
from scipy.stats import kruskal
from statsmodels.stats.multitest import multipletests
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    from lifelines import KaplanMeierFitter, CoxPHFitter
    from lifelines.statistics import logrank_test
    LIFELINES = True
except ImportError:
    LIFELINES = False
    print("UYARI: lifelines bulunamadi — KM analizi atlanacak")

BASE    = os.path.dirname(os.path.abspath(__file__))
DEPMAP  = os.path.join(BASE, "DepMap")
CPTAC   = os.path.join(BASE, "CPTAC-LUAD")
TCGA    = os.path.join(BASE, "TCGA LUAD",
          "luad_tcga_pan_can_atlas_2018", "luad_tcga_pan_can_atlas_2018")
RESULTS = os.path.join(BASE, "results")
os.makedirs(RESULTS, exist_ok=True)

FOCUS = ['PTK2','MET','EGFR','SRC','LCK','YES1','FYN','LYN','DDR1']
COLORS = {
    'PTK2':'#E63946','MET':'#457B9D','EGFR':'#E9C46A',
    'SRC':'#2A9D8F','LCK':'#F4A261','YES1':'#264653',
    'FYN':'#A8DADC','LYN':'#6D6875','DDR1':'#B5838D',
}

def sec(t): print(f"\n{'='*55}\n  {t}\n{'='*55}")
def savefig(fig, n):
    p = os.path.join(RESULTS, n)
    fig.savefig(p, dpi=180, bbox_inches='tight')
    plt.close(fig)
    print(f"  Kaydedildi: results/{n}")


# ─── Ortak veri yükleme ────────────────────────────────────
sec("Veri Yükleme")

# GDSC2
gdsc = pd.read_excel(os.path.join(BASE, "GDSC2_fitted_dose_response_27Oct23.xlsx"))
luad_gdsc = gdsc[gdsc['TCGA_DESC']=='LUAD'].copy()

# DepMap
model = pd.read_csv(os.path.join(DEPMAP, "Model.csv"))
luad_model = model[model['OncotreeCode']=='LUAD'].copy()
sanger_to_ach = dict(zip(luad_model['SangerModelID'], luad_model['ModelID']))
ach_luad = set(luad_model['ModelID'])
luad_gdsc['ACH_ID'] = luad_gdsc['SANGER_MODEL_ID'].map(sanger_to_ach)
luad_gdsc = luad_gdsc.dropna(subset=['ACH_ID'])

# Expression — sadece odak kinazlar
depmap_kinase_cols = {}
header_line = open(os.path.join(DEPMAP, "OmicsExpressionProteinCodingGenesTPMLogp1.csv"),
                   encoding='utf-8').readline()
for k in FOCUS:
    for col in header_line.split(','):
        if col.strip().startswith(k+' ('):
            depmap_kinase_cols[k] = col.strip()
            break

usecols = ['Unnamed: 0'] + list(depmap_kinase_cols.values())
expr = pd.read_csv(os.path.join(DEPMAP, "OmicsExpressionProteinCodingGenesTPMLogp1.csv"),
                   usecols=usecols, index_col=0)
expr = expr[expr.index.isin(ach_luad)]
expr = expr.rename(columns={v:k for k,v in depmap_kinase_cols.items()})
print(f"DepMap expression LUAD: {expr.shape}")

# TCGA
mrna_raw = pd.read_csv(os.path.join(TCGA, "data_mrna_seq_v2_rsem.txt"), sep='\t')
mrna_raw = mrna_raw.dropna(subset=['Hugo_Symbol']).drop_duplicates('Hugo_Symbol')
mrna_raw = mrna_raw.set_index('Hugo_Symbol').drop(columns=['Entrez_Gene_Id'])
mrna_log = np.log2(mrna_raw + 1)
mrna_log.columns = ['-'.join(c.split('-')[:3]) for c in mrna_log.columns]

clin = pd.read_csv(os.path.join(TCGA, "data_clinical_patient.txt"), sep='\t', comment='#')
clin = clin.set_index('PATIENT_ID')
clin['os_event']  = clin['OS_STATUS'].str.startswith('1').fillna(False).astype(int)
clin['os_months'] = pd.to_numeric(clin['OS_MONTHS'], errors='coerce')
clin = clin[clin['os_months'].notna() & (clin['os_months'] > 0)]

common_ids = list(set(mrna_log.columns) & set(clin.index))
mrna_sub = mrna_log[common_ids].T
clin_sub  = clin.loc[common_ids]
merged = mrna_sub.join(clin_sub[['os_months','os_event']])
focus_present = [k for k in FOCUS if k in merged.columns]
print(f"TCGA mRNA+klinik ortak hasta: {len(merged)}")


# ══════════════════════════════════════════════════════════
# ADIM 1 — GDSC2 TAM 286-İlaç Taraması
# ══════════════════════════════════════════════════════════
sec("ADIM 1: GDSC2 Tam Tarama (286 ilaç × 9 kinaz)")

all_drugs = luad_gdsc['DRUG_NAME'].unique()
print(f"Test edilecek ilaç: {len(all_drugs)}  |  Kinaz: {len([k for k in FOCUS if k in expr.columns])}")

full_corr = []
for kinase in [k for k in FOCUS if k in expr.columns]:
    kinase_expr = expr[kinase]
    for drug in all_drugs:
        dd = luad_gdsc[luad_gdsc['DRUG_NAME']==drug][['ACH_ID','LN_IC50']].dropna()
        dd = dd.groupby('ACH_ID')['LN_IC50'].mean()
        common = kinase_expr.index.intersection(dd.index)
        if len(common) < 8:
            continue
        rho, pval = spearmanr(kinase_expr.loc[common], dd.loc[common])
        full_corr.append({'kinase':kinase,'drug':drug,'rho':rho,'pval':pval,'n':len(common)})

full_df = pd.DataFrame(full_corr)
_, full_df['fdr'], _, _ = multipletests(full_df['pval'], method='fdr_bh')
full_df = full_df.sort_values('fdr')

n05 = (full_df['fdr']<0.05).sum()
n25 = (full_df['fdr']<0.25).sum()
print(f"Toplam test: {len(full_df)}  |  FDR<0.05: {n05}  |  FDR<0.25: {n25}")
print("\nTop 20 kinaz-ilaç ilişkisi:")
print(full_df[['kinase','drug','rho','pval','fdr','n']].head(20).to_string(index=False))

# FIG: Full heatmap
if n25 > 0:
    top_pairs = full_df.nsmallest(40, 'fdr')
    top_drugs_full = top_pairs['drug'].unique()[:25]
    pivot = full_df.pivot_table(index='kinase', columns='drug', values='rho')
    pivot_sub = pivot.reindex(columns=[d for d in top_drugs_full if d in pivot.columns]).dropna(how='all')

    if not pivot_sub.empty:
        fig, ax = plt.subplots(figsize=(max(12, len(pivot_sub.columns)), max(5, len(pivot_sub)*0.7)))
        sns.heatmap(pivot_sub, cmap='RdBu_r', center=0, vmin=-0.7, vmax=0.7,
                    annot=True, fmt='.2f', linewidths=0.4, ax=ax, annot_kws={'size':7})
        ax.set_title('Full GDSC2 Scan: Kinaz Expression × İlaç LN_IC50 (Spearman ρ)\nTop-25 ilaç (FDR sırası)', fontsize=12)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        plt.tight_layout()
        savefig(fig, "fig6_full_gdsc2_heatmap.png")

# Scatter: top 6 pair
top6 = full_df.nsmallest(6, 'fdr')[['kinase','drug','rho','fdr']].values
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
for ax, (kinase, drug, rho, fdr) in zip(axes.flat, top6):
    dd = luad_gdsc[luad_gdsc['DRUG_NAME']==drug][['ACH_ID','LN_IC50']].dropna()
    dd = dd.groupby('ACH_ID')['LN_IC50'].mean()
    common = expr[kinase].index.intersection(dd.index)
    x, y = expr[kinase].loc[common], dd.loc[common]
    ax.scatter(x, y, c=COLORS.get(kinase,'#555'), alpha=0.75, s=45, edgecolors='white', lw=0.5)
    m, b = np.polyfit(x, y, 1)
    xr = np.linspace(x.min(), x.max(), 50)
    ax.plot(xr, m*xr+b, 'k--', lw=1.5, alpha=0.8)
    pstr = "***" if fdr<0.001 else ("**" if fdr<0.01 else ("*" if fdr<0.05 else f"FDR={fdr:.3f}"))
    ax.set_xlabel(f'{kinase} log2 TPM', fontsize=9)
    ax.set_ylabel(f'{drug} LN_IC50', fontsize=9)
    ax.set_title(f'{kinase} × {drug}\nρ={rho:.3f}, {pstr}', fontsize=10)
plt.tight_layout()
savefig(fig, "fig6b_gdsc2_top_scatter.png")

# EGFR mutant vs WT IC50 (biyoloji doğrulama)
sec("ADIM 1b: GDSC2 EGFR Mutant vs WT IC50")

# TCGA mutations: EGFR mutant sample listesi
print("TCGA mutations yükleniyor (239 MB)...")
mut_cols = ['Tumor_Sample_Barcode','Hugo_Symbol','Variant_Classification']
maf = pd.read_csv(os.path.join(TCGA, "data_mutations.txt"), sep='\t',
                  usecols=mut_cols, low_memory=False)
egfr_mut_samples = maf[maf['Hugo_Symbol']=='EGFR']['Tumor_Sample_Barcode'].unique()
egfr_mut_patients = set(['-'.join(s.split('-')[:3]) for s in egfr_mut_samples])
print(f"EGFR mutant hasta (TCGA): {len(egfr_mut_patients)}")

# GDSC2: EGFR mutant vs WT cell lines
# DepMap mutations yok → GDSC2 kendi genomik verisi GDSC ANOVA'dan
anova = pd.read_csv(os.path.join(BASE, "LUAD_ANOVA_Sun Mar  1 09_17_41 2026.csv"))
egfr_anova = anova[anova['Feature Name'].str.upper().str.contains('EGFR', na=False)]
print(f"\nGDSC2 ANOVA - EGFR ilgili satır: {len(egfr_anova)}")
print("En anlamlı EGFR-ilaç ilişkileri (GDSC2 ANOVA):")
egfr_sig = egfr_anova.sort_values('fdr').head(15)
print(egfr_sig[['Drug name','Drug target','Feature Name','ic50_effect_size','fdr']].to_string(index=False))

# EGFR ilaçları için IC50 dağılımı — EGFR mutant vs WT (DepMap OmicsMutations varsa)
egfr_drugs = ['Erlotinib','Gefitinib','Osimertinib','Lapatinib','Afatinib']
egfr_drug_data = []
for drug in egfr_drugs:
    dd = luad_gdsc[luad_gdsc['DRUG_NAME'].str.lower()==drug.lower()][['CELL_LINE_NAME','LN_IC50']].dropna()
    if len(dd) > 5:
        egfr_drug_data.append((drug, dd))
        print(f"  {drug}: {len(dd)} hücre hattı, median LN_IC50={dd['LN_IC50'].median():.3f}")


# ══════════════════════════════════════════════════════════
# ADIM 2 — YES1 Tertile Survival + EGFR Subgroup
# ══════════════════════════════════════════════════════════
sec("ADIM 2: YES1 Derinlemesine Survival + EGFR Subgroup")

if LIFELINES:
    # YES1 tertile analysis
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 2a: YES1 tertile
    df_yes1 = merged[['YES1','os_months','os_event']].dropna()
    q33, q66 = df_yes1['YES1'].quantile([0.33, 0.66])
    df_yes1['group'] = pd.cut(df_yes1['YES1'], bins=[-np.inf, q33, q66, np.inf],
                               labels=['Low (≤33%)', 'Mid', 'High (≥67%)'])
    ax = axes[0]
    kmf = KaplanMeierFitter()
    colors_3 = ['#457B9D','#A8DADC','#E63946']
    for grp, col in zip(['Low (≤33%)','Mid','High (≥67%)'], colors_3):
        d = df_yes1[df_yes1['group']==grp]
        kmf.fit(d['os_months'], d['os_event'], label=f'{grp} (n={len(d)})')
        kmf.plot_survival_function(ax=ax, color=col, lw=2, ci_show=True, ci_alpha=0.1)

    # 3-group log-rank (pairwise high vs low)
    high = df_yes1[df_yes1['group']=='High (≥67%)']
    low  = df_yes1[df_yes1['group']=='Low (≤33%)']
    lr_yes1 = logrank_test(high['os_months'], low['os_months'],
                            high['os_event'], low['os_event'])
    ax.set_title(f'YES1 Expression — Overall Survival\nHigh vs Low log-rank p={lr_yes1.p_value:.4f}',
                 fontsize=12)
    ax.set_xlabel('Süre (Ay)'); ax.set_ylabel('Sağkalım Olasılığı')
    ax.set_ylim(0,1.05); ax.legend(fontsize=9)

    # 2b: EGFR mutant subgroup — YES1 etkisi
    egfr_mut_common = egfr_mut_patients & set(merged.index)
    df_egfr = merged.loc[list(egfr_mut_common)][['YES1','os_months','os_event']].dropna()
    print(f"EGFR mutant hasta (mRNA+klinik): {len(df_egfr)}")

    ax = axes[1]
    if len(df_egfr) >= 20:
        thr = df_egfr['YES1'].median()
        df_egfr['group'] = np.where(df_egfr['YES1'] >= thr, 'High', 'Low')
        for grp, col in [('High','#E63946'),('Low','#457B9D')]:
            d = df_egfr[df_egfr['group']==grp]
            kmf.fit(d['os_months'], d['os_event'], label=f'{grp} (n={len(d)})')
            kmf.plot_survival_function(ax=ax, color=col, lw=2, ci_show=True, ci_alpha=0.1)
        h_e = df_egfr[df_egfr['group']=='High']
        l_e = df_egfr[df_egfr['group']=='Low']
        lr_e = logrank_test(h_e['os_months'], l_e['os_months'],
                             h_e['os_event'], l_e['os_event'])
        ax.set_title(f'YES1 — EGFR Mutant Subgroup\nlog-rank p={lr_e.p_value:.4f}', fontsize=12)
    else:
        ax.text(0.5, 0.5, f'EGFR mutant n={len(df_egfr)}\n(yetersiz)', ha='center', transform=ax.transAxes)
        ax.set_title('EGFR Mutant Subgroup — Yetersiz hasta', fontsize=12)
    ax.set_xlabel('Süre (Ay)'); ax.set_ylabel('Sağkalım Olasılığı')
    ax.set_ylim(0,1.05); ax.legend(fontsize=9)

    plt.tight_layout()
    savefig(fig, "fig7_YES1_tertile_egfr_subgroup.png")

    # Tüm odak kinazlar için tertile KM
    km_tertile = {}
    for kinase in focus_present:
        df_k = merged[[kinase,'os_months','os_event']].dropna()
        q33_, q66_ = df_k[kinase].quantile([0.33,0.66])
        high_ = df_k[df_k[kinase] >= q66_]
        low_  = df_k[df_k[kinase] <= q33_]
        if len(high_) < 10 or len(low_) < 10:
            continue
        lr_ = logrank_test(high_['os_months'], low_['os_months'],
                            high_['os_event'], low_['os_event'])
        km_tertile[kinase] = {'p_tertile': lr_.p_value,
                               'n_high': len(high_), 'n_low': len(low_)}
    km_tertile_df = pd.DataFrame(km_tertile).T.sort_values('p_tertile')
    _, km_tertile_df['fdr'], _, _ = multipletests(km_tertile_df['p_tertile'], method='fdr_bh')
    print("\nTertile KM sonuçları (top vs bottom 33%):")
    print(km_tertile_df.to_string())


# ══════════════════════════════════════════════════════════
# ADIM 3 — Kompozit KAS Skoru (PCA) vs Survival
# ══════════════════════════════════════════════════════════
sec("ADIM 3: Kompozit KAS (PCA) vs Overall Survival")

# CPTAC KAS
from faz2_analysis import *  # yeniden import etmek yerine direkt hesapla
s2 = pd.read_csv(os.path.join(BASE, "pARACNe",
    "S2_pARACNe_TK-Protein_Substrate_Network.txt"), sep='\t')
kin_subs = {k: s2[s2['kinase']==k]['substrate'].tolist() for k in FOCUS}

phospho = pd.read_csv(
    os.path.join(CPTAC, "HS_CPTAC_LUAD_phosphoproteome_ratio_norm_NArm_TUMOR.cct"),
    sep='\t', index_col=0)
phospho_genes = phospho.index.str.split(':').str[0]

kas_dict = {}
for k in FOCUS:
    mask = phospho_genes.isin(set(kin_subs.get(k,[])))
    if mask.sum() >= 5:
        kas_dict[k] = phospho.loc[mask].mean(axis=0)
kas_df = pd.DataFrame(kas_dict).dropna()

# PCA kompozit skor
scaler = StandardScaler()
kas_scaled = scaler.fit_transform(kas_df)
pca = PCA(n_components=2)
kas_pca = pca.fit_transform(kas_scaled)
kas_df['PC1'] = kas_pca[:,0]
kas_df['PC2'] = kas_pca[:,1]
ev = pca.explained_variance_ratio_
print(f"PCA PC1 explained variance: {ev[0]*100:.1f}%  |  PC2: {ev[1]*100:.1f}%")
print("PC1 loadings:")
loading_df = pd.Series(pca.components_[0], index=kas_df.columns[:-2]).sort_values()
print(loading_df.to_string())

# PCA loading plot
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
colors_pc = [COLORS.get(k,'#666') for k in loading_df.index]
axes[0].barh(loading_df.index, loading_df.values, color=colors_pc)
axes[0].axvline(0, ls='--', color='black', alpha=0.5)
axes[0].set_title(f'PC1 Loadings ({ev[0]*100:.1f}% variance)\nKomposite KAS Skoru', fontsize=12)
axes[0].set_xlabel('PC1 Loading')

# KAS scatter (PC1 vs PC2)
scatter = axes[1].scatter(kas_df['PC1'], kas_df['PC2'], c='#457B9D', alpha=0.6, s=30)
axes[1].set_xlabel(f'PC1 ({ev[0]*100:.1f}%)', fontsize=11)
axes[1].set_ylabel(f'PC2 ({ev[1]*100:.1f}%)', fontsize=11)
axes[1].set_title('CPTAC-LUAD: Kinaz Aktivasyon Uzayı (PCA)', fontsize=12)
plt.tight_layout()
savefig(fig, "fig8_kas_pca.png")


# ══════════════════════════════════════════════════════════
# ADIM 4 — Kinaz Ko-Aktivasyon Ağı (CPTAC + TCGA)
# ══════════════════════════════════════════════════════════
sec("ADIM 4: Kinaz Ko-Aktivasyon Analizi")

# CPTAC KAS korelasyon matrisi
kas_corr = kas_df[FOCUS].corr(method='spearman')
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# CPTAC
mask = np.triu(np.ones_like(kas_corr, dtype=bool))
sns.heatmap(kas_corr, mask=mask, cmap='RdBu_r', center=0, vmin=-1, vmax=1,
            annot=True, fmt='.2f', linewidths=0.5, ax=axes[0],
            cbar_kws={'label':'Spearman ρ'})
axes[0].set_title('CPTAC-LUAD: Kinaz Ko-Aktivasyon\n(Substrat Fosforilasyon Korelasyonu)', fontsize=12)

# TCGA mRNA korelasyon
tcga_kin_expr = mrna_sub[[k for k in FOCUS if k in mrna_sub.columns]]
tcga_corr = tcga_kin_expr.corr(method='spearman')
mask2 = np.triu(np.ones_like(tcga_corr, dtype=bool))
sns.heatmap(tcga_corr, mask=mask2, cmap='RdBu_r', center=0, vmin=-1, vmax=1,
            annot=True, fmt='.2f', linewidths=0.5, ax=axes[1],
            cbar_kws={'label':'Spearman ρ'})
axes[1].set_title('TCGA-LUAD: Kinaz Ko-Ekspresyon\n(mRNA Level Korelasyon)', fontsize=12)
plt.tight_layout()
savefig(fig, "fig9_kinase_coactivation.png")

# SRC ailesi analizi
src_family = ['SRC','LCK','YES1','FYN','LYN']
print("\nSRC ailesi ko-aktivasyon (CPTAC):")
for k1 in src_family:
    for k2 in src_family:
        if k1 < k2 and k1 in kas_corr.index and k2 in kas_corr.columns:
            print(f"  {k1} × {k2}: ρ={kas_corr.loc[k1,k2]:.3f}")


# ══════════════════════════════════════════════════════════
# EXPORT + ÖZET
# ══════════════════════════════════════════════════════════
sec("DIŞA AKTAR")

excel_path = os.path.join(RESULTS, "LUAD_Faz2b_Results.xlsx")
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    full_df.to_excel(writer, sheet_name='1_GDSC2_Full_Scan', index=False)
    egfr_sig.to_excel(writer, sheet_name='2_EGFR_ANOVA', index=False)
    if LIFELINES:
        km_tertile_df.to_excel(writer, sheet_name='3_KM_Tertile')
    kas_df.to_excel(writer, sheet_name='4_KAS_PCA')
    kas_corr.to_excel(writer, sheet_name='5_CoActivation_CPTAC')
    tcga_corr.to_excel(writer, sheet_name='6_CoExpression_TCGA')

print(f"Excel kaydedildi: results/LUAD_Faz2b_Results.xlsx")

sec("FAZ 2b ÖZET")
print(f"GDSC2 tam tarama: {len(full_df)} test | FDR<0.05: {n05} | FDR<0.25: {n25}")
if LIFELINES and len(km_tertile_df):
    sig_t = km_tertile_df[km_tertile_df['p_tertile']<0.05]
    print(f"Anlamlı tertile KM (p<0.05): {list(sig_t.index)}")
print(f"PCA PC1 açıklanan varyans: {ev[0]*100:.1f}%")

results_new = [f for f in os.listdir(RESULTS) if 'fig6' in f or 'fig7' in f or 'fig8' in f or 'fig9' in f or 'Faz2b' in f]
print(f"Yeni çıktılar: {results_new}")
print("\nFaz 2b tamamlandı.")
