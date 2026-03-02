"""
LUAD Drug Resistance Study — Faz 2: Birincil Analiz Pipeline
=============================================================
Modüller:
  1. pARACNe S2 Hub Kinaz Analizi
  2. GDSC2 x DepMap Expression Korelasyon (Kinaz-İlaç)
  3. TCGA-LUAD Survival Analizi (KM + Cox)
  4. CPTAC Kinaz Aktivasyon Skoru (KAS) + Doğrulama

Çıktılar: results/ klasörü altında PNG figürler + LUAD_Faz2_Results.xlsx
"""

import os, sys, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy.stats import spearmanr, mannwhitneyu
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
PARACNE  = os.path.join(BASE, "pARACNe")
DEPMAP   = os.path.join(BASE, "DepMap")
CPTAC    = os.path.join(BASE, "CPTAC-LUAD")
TCGA     = os.path.join(BASE, "TCGA LUAD",
           "luad_tcga_pan_can_atlas_2018", "luad_tcga_pan_can_atlas_2018")
RESULTS  = os.path.join(BASE, "results")
os.makedirs(RESULTS, exist_ok=True)

# ─────────────────────────────────────────────
# FOCUS KINASES + COLORS
# ─────────────────────────────────────────────
FOCUS = ['PTK2','MET','EGFR','SRC','LCK','YES1','FYN','LYN','DDR1']
COLORS = {
    'PTK2':'#E63946','MET':'#457B9D','EGFR':'#E9C46A',
    'SRC':'#2A9D8F','LCK':'#F4A261','YES1':'#264653',
    'FYN':'#A8DADC','LYN':'#6D6875','DDR1':'#B5838D',
}

def sec(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)

def savefig(fig, name):
    path = os.path.join(RESULTS, name)
    fig.savefig(path, dpi=180, bbox_inches='tight')
    plt.close(fig)
    print(f"  Kaydedildi: results/{name}")


# ══════════════════════════════════════════════════════════
# MODÜL 1  —  pARACNe S2 Hub Kinaz Analizi
# ══════════════════════════════════════════════════════════
sec("MODÜL 1: pARACNe Hub Kinaz Analizi")

s2 = pd.read_csv(
    os.path.join(PARACNE, "S2_pARACNe_TK-Protein_Substrate_Network.txt"),
    sep='\t'
)
print(f"S2 boyutu: {s2.shape}  (kinaz-substrat çiftleri)")

hub = s2.groupby('kinase')['substrate'].count().sort_values(ascending=False)
print(f"Toplam kinaz: {len(hub)}")
print("Top 15 Hub Kinaz:")
for k, n in hub.head(15).items():
    tag = " <-- ODAK" if k in FOCUS else ""
    print(f"  {k:10s}: {n:3d}{tag}")

# Substrat listeleri
kinase_substrates = {k: s2[s2['kinase']==k]['substrate'].tolist() for k in FOCUS if k in hub.index}

# FIG 1: Hub kinaz barplot
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

top20 = hub.head(20)
bar_colors = ['#E63946' if k in FOCUS else '#ADB5BD' for k in top20.index]
axes[0].barh(top20.index[::-1], top20.values[::-1], color=bar_colors[::-1])
axes[0].set_xlabel('Substrat Sayısı', fontsize=12)
axes[0].set_title('pARACNe — Top 20 Hub Kinaz\n(kırmızı = odak kinazlar)', fontsize=12)
axes[0].axvline(100, ls='--', color='gray', alpha=0.5)
red_patch = mpatches.Patch(color='#E63946', label='Odak kinazlar')
axes[0].legend(handles=[red_patch], fontsize=10)

focus_present = [k for k in FOCUS if k in hub.index]
focus_vals = hub.reindex(focus_present).dropna().sort_values(ascending=False)
fc = [COLORS.get(k,'#6C757D') for k in focus_vals.index]
bars = axes[1].bar(focus_vals.index, focus_vals.values, color=fc, edgecolor='white', lw=0.5)
axes[1].set_ylabel('Substrat Sayısı', fontsize=12)
axes[1].set_title('Odak Kinazlar — pARACNe S2 Network', fontsize=12)
axes[1].tick_params(axis='x', rotation=30)
for bar, v in zip(bars, focus_vals.values):
    axes[1].text(bar.get_x() + bar.get_width()/2, v + 1, str(v),
                 ha='center', fontsize=9, fontweight='bold')

plt.tight_layout()
savefig(fig, "fig1_hub_kinases.png")


# ══════════════════════════════════════════════════════════
# MODÜL 2  —  GDSC2 × DepMap Expression Korelasyon
# ══════════════════════════════════════════════════════════
sec("MODÜL 2: GDSC2 × DepMap Expression Korelasyon")

# GDSC2 LUAD verisi
gdsc = pd.read_excel(os.path.join(BASE, "GDSC2_fitted_dose_response_27Oct23.xlsx"))
luad_gdsc = gdsc[gdsc['TCGA_DESC'] == 'LUAD'].copy()
print(f"GDSC2 LUAD satır: {len(luad_gdsc)} | Benzersiz ilaç: {luad_gdsc['DRUG_NAME'].nunique()} | Hücre: {luad_gdsc['SANGER_MODEL_ID'].nunique()}")

# DepMap LUAD hücre hatları
model = pd.read_csv(os.path.join(DEPMAP, "Model.csv"))
luad_model = model[model['OncotreeCode'] == 'LUAD'].copy()
sanger_to_ach = dict(zip(luad_model['SangerModelID'], luad_model['ModelID']))
print(f"DepMap LUAD: {len(luad_model)} hücre hattı")

# DepMap Expression — LUAD filtresi (bellek için sütun seçimi)
ach_luad = set(luad_model['ModelID'])
depmap_kinase_cols = {}
for k in focus_present:
    matching = [c for c in open(
        os.path.join(DEPMAP, "OmicsExpressionProteinCodingGenesTPMLogp1.csv")
    ).readline().split(',') if c.startswith(k+' (')]
    if matching:
        depmap_kinase_cols[k] = matching[0].strip()

print(f"DepMap kinaz kolon eşlemesi: {depmap_kinase_cols}")
usecols = ['Unnamed: 0'] + list(depmap_kinase_cols.values())
expr_luad = pd.read_csv(
    os.path.join(DEPMAP, "OmicsExpressionProteinCodingGenesTPMLogp1.csv"),
    usecols=usecols, index_col=0
)
expr_luad = expr_luad[expr_luad.index.isin(ach_luad)]
# Kolon adlarını sadeleştir: "PTK2 (5747)" → "PTK2"
col_rename = {v: k for k, v in depmap_kinase_cols.items()}
expr_luad = expr_luad.rename(columns=col_rename)
print(f"DepMap expression LUAD: {expr_luad.shape}")

# GDSC2 → ACH ID eşlemesi
luad_gdsc['ACH_ID'] = luad_gdsc['SANGER_MODEL_ID'].map(sanger_to_ach)
luad_gdsc = luad_gdsc.dropna(subset=['ACH_ID'])

# İlaç listesi: kinaz inhibitörü olanlar + EGFR/MET/SRC/FAK yolu
KI_KEYWORDS = ['EGFR','MET','SRC','FAK','PTK2','ALK','KIT','PDGFR','VEGFR',
               'erlotinib','gefitinib','osimertinib','crizotinib','dasatinib',
               'defactinib','saracatinib','bosutinib','lapatinib','afatinib']
ki_mask = luad_gdsc['DRUG_NAME'].str.upper().str.contains(
    '|'.join([k.upper() for k in KI_KEYWORDS]), na=False
) | luad_gdsc['PUTATIVE_TARGET'].str.upper().str.contains(
    '|'.join([k.upper() for k in ['EGFR','MET','SRC','PTK2','ALK','KIT']]), na=False
)
ki_drugs = luad_gdsc[ki_mask]['DRUG_NAME'].unique()
print(f"Kinaz inhibitörü ilaç sayısı: {len(ki_drugs)}")

# Korelasyon hesapla
corr_results = []
for kinase in focus_present:
    if kinase not in expr_luad.columns:
        continue
    kinase_expr = expr_luad[kinase]

    for drug_name in ki_drugs:
        drug_data = luad_gdsc[luad_gdsc['DRUG_NAME'] == drug_name][['ACH_ID','LN_IC50']].dropna()
        drug_data = drug_data.groupby('ACH_ID')['LN_IC50'].mean()  # tekrar ölçüm ortalaması

        common = kinase_expr.index.intersection(drug_data.index)
        if len(common) < 8:
            continue
        x = kinase_expr.loc[common]
        y = drug_data.loc[common]

        rho, pval = spearmanr(x, y)
        corr_results.append({
            'kinase': kinase, 'drug': drug_name,
            'rho': rho, 'pval': pval, 'n': len(common)
        })

corr_df = pd.DataFrame(corr_results)
if len(corr_df) > 0:
    _, corr_df['fdr'], _, _ = multipletests(corr_df['pval'], method='fdr_bh')
    corr_df = corr_df.sort_values('fdr')
    sig = corr_df[corr_df['fdr'] < 0.25]
    print(f"Toplam test: {len(corr_df)} | FDR<0.25: {len(sig)} | FDR<0.05: {len(corr_df[corr_df['fdr']<0.05])}")
    print("\nTop 15 Kinaz-İlaç İlişkisi:")
    print(corr_df[['kinase','drug','rho','pval','fdr','n']].head(15).to_string(index=False))

    # FIG 2: Heatmap (kinaz × ilaç)
    pivot = corr_df.pivot_table(index='kinase', columns='drug', values='rho')
    # En anlamlı ilişkiler
    top_drugs = corr_df.nsmallest(30, 'fdr')['drug'].unique()[:20]
    pivot_sub = pivot.reindex(columns=[d for d in top_drugs if d in pivot.columns])
    pivot_sub = pivot_sub.dropna(how='all')

    if not pivot_sub.empty:
        fig, ax = plt.subplots(figsize=(max(10, len(pivot_sub.columns)*0.9), max(5, len(pivot_sub)*0.7)))
        mask = pivot_sub.isna()
        sns.heatmap(pivot_sub, cmap='RdBu_r', center=0, vmin=-0.7, vmax=0.7,
                    annot=True, fmt='.2f', linewidths=0.5, mask=mask, ax=ax,
                    annot_kws={'size':8})
        ax.set_title('Kinaz Expression × İlaç LN_IC50 — Spearman ρ\n(GDSC2 LUAD × DepMap 23Q4)', fontsize=12)
        ax.set_xlabel('İlaç', fontsize=11)
        ax.set_ylabel('Kinaz', fontsize=11)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        plt.tight_layout()
        savefig(fig, "fig2_kinase_drug_heatmap.png")

    # Scatter plot: en anlamlı 4 çift
    top4 = corr_df.nsmallest(4, 'fdr')[['kinase','drug','rho','fdr']].values
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for ax, (kinase, drug, rho, fdr) in zip(axes.flat, top4):
        drug_data = luad_gdsc[luad_gdsc['DRUG_NAME'] == drug][['ACH_ID','LN_IC50']].dropna()
        drug_data = drug_data.groupby('ACH_ID')['LN_IC50'].mean()
        common = expr_luad[kinase].index.intersection(drug_data.index)
        x = expr_luad[kinase].loc[common]
        y = drug_data.loc[common]
        ax.scatter(x, y, c=COLORS.get(kinase,'#666'), alpha=0.7, s=40, edgecolor='white')
        m, b = np.polyfit(x, y, 1)
        xr = np.linspace(x.min(), x.max(), 50)
        ax.plot(xr, m*xr+b, 'k--', lw=1.5, alpha=0.7)
        ax.set_xlabel(f'{kinase} Expression (log2 TPM)', fontsize=10)
        ax.set_ylabel(f'{drug} LN_IC50', fontsize=10)
        ax.set_title(f'{kinase} × {drug}\nρ={rho:.3f}, FDR={fdr:.3f}', fontsize=11)
    plt.tight_layout()
    savefig(fig, "fig2b_top_scatter.png")
else:
    print("  Yeterli korelasyon verisi bulunamadi.")
    corr_df = pd.DataFrame()


# ══════════════════════════════════════════════════════════
# MODÜL 3  —  TCGA-LUAD Survival Analizi
# ══════════════════════════════════════════════════════════
sec("MODÜL 3: TCGA-LUAD Survival Analizi")

try:
    from lifelines import KaplanMeierFitter, CoxPHFitter
    from lifelines.statistics import logrank_test
    lifelines_ok = True
except ImportError:
    print("  lifelines yuklu degil — KM/Cox atlaniyor")
    lifelines_ok = False

if lifelines_ok:
    # mRNA yükle — Hugo_Symbol'ü index yap
    mrna_raw = pd.read_csv(os.path.join(TCGA, "data_mrna_seq_v2_rsem.txt"), sep='\t')
    mrna_raw = mrna_raw.dropna(subset=['Hugo_Symbol'])
    mrna_raw = mrna_raw.drop_duplicates(subset='Hugo_Symbol', keep='first')
    mrna_raw = mrna_raw.set_index('Hugo_Symbol').drop(columns=['Entrez_Gene_Id'])
    # Sütunlar: TCGA-XX-XXXX-01 → log2(RSEM+1)
    mrna_log = np.log2(mrna_raw + 1)
    print(f"TCGA mRNA: {mrna_log.shape}  (gen × hasta)")

    # Klinik yükle
    clin = pd.read_csv(os.path.join(TCGA, "data_clinical_patient.txt"), sep='\t', comment='#')
    clin = clin.set_index('PATIENT_ID')
    clin['os_event'] = clin['OS_STATUS'].str.startswith('1').fillna(False).astype(int)
    clin['os_months'] = pd.to_numeric(clin['OS_MONTHS'], errors='coerce')
    clin = clin.dropna(subset=['os_months','os_event'])
    clin = clin[clin['os_months'] > 0]
    print(f"TCGA klinik: {len(clin)} hasta  |  event oranı: {clin['os_event'].mean():.2f}")

    # Sample → Patient eşlemesi (TCGA-XX-XXXX-01 → TCGA-XX-XXXX)
    mrna_log.columns = ['-'.join(c.split('-')[:3]) for c in mrna_log.columns]
    # Ortak hastalar
    common_ids = list(set(mrna_log.columns) & set(clin.index))
    print(f"mRNA+klinik ortak: {len(common_ids)} hasta")

    mrna_sub = mrna_log[common_ids].T  # hasta × gen
    clin_sub = clin.loc[common_ids]
    merged = mrna_sub.join(clin_sub[['os_months','os_event']])

    # KM analizi — her odak kinaz
    km_results = {}
    fig, axes = plt.subplots(3, 3, figsize=(16, 14))
    for ax, kinase in zip(axes.flat, focus_present):
        if kinase not in merged.columns:
            ax.set_visible(False)
            continue
        df = merged[[kinase,'os_months','os_event']].dropna()
        threshold = df[kinase].median()
        df['group'] = np.where(df[kinase] >= threshold, 'High', 'Low')
        high = df[df['group']=='High']
        low  = df[df['group']=='Low']

        lr = logrank_test(high['os_months'], low['os_months'],
                          high['os_event'], low['os_event'])
        km_results[kinase] = lr.p_value

        kmf = KaplanMeierFitter()
        for grp, col, ls in [('High','#E63946','-'),('Low','#457B9D','--')]:
            d = df[df['group']==grp]
            kmf.fit(d['os_months'], d['os_event'], label=f'{grp} (n={len(d)})')
            kmf.plot_survival_function(ax=ax, color=col, linestyle=ls, lw=2,
                                        ci_show=True, ci_alpha=0.1)
        pstar = '*' if lr.p_value < 0.05 else ('†' if lr.p_value < 0.1 else '')
        ax.set_title(f'{kinase}  {pstar}\nlog-rank p={lr.p_value:.4f}', fontsize=11)
        ax.set_xlabel('Süre (Ay)', fontsize=9)
        ax.set_ylabel('Sağkalım Olasılığı', fontsize=9)
        ax.set_ylim(0,1.05)
        ax.legend(fontsize=8)

    plt.suptitle('TCGA-LUAD — Overall Survival by Kinase Expression (Median Split)',
                 fontsize=13, y=1.01)
    plt.tight_layout()
    savefig(fig, "fig3_KM_grid.png")

    # KM özet tablosu
    km_summary = pd.DataFrame.from_dict(km_results, orient='index', columns=['logrank_p'])
    km_summary['FDR'] = multipletests(km_summary['logrank_p'], method='fdr_bh')[1]
    km_summary = km_summary.sort_values('logrank_p')
    print("\nKM Özet:")
    print(km_summary.to_string())

    # Cox multivariable (log10 transform için odak kinazlar)
    cox_kinases = [k for k in focus_present if k in merged.columns]
    cox_df = merged[cox_kinases + ['os_months','os_event']].dropna()
    # Ekstra kovariyatlar (varsa)
    extra_covs = []
    for cov in ['AGE','SMOKING_PACK_YEARS']:
        if cov in clin.columns:
            cox_df[cov] = pd.to_numeric(clin.loc[cox_df.index, cov], errors='coerce')
            extra_covs.append(cov)

    cox_df = cox_df.dropna()
    print(f"\nCox regresyonu: {len(cox_df)} hasta, {len(cox_kinases)+len(extra_covs)} değişken")

    cph = CoxPHFitter(penalizer=0.1)
    cph.fit(cox_df, duration_col='os_months', event_col='os_event')

    fig, ax = plt.subplots(figsize=(9, 6))
    cph.plot(ax=ax)
    ax.set_title('Cox Multivariable — Hazard Ratio (95% CI)\nTCGA-LUAD Overall Survival', fontsize=12)
    ax.axvline(0, ls='--', color='gray', alpha=0.5)
    plt.tight_layout()
    savefig(fig, "fig4_cox_forest.png")
    print(cph.summary[['exp(coef)','exp(coef) lower 95%','exp(coef) upper 95%','p']].to_string())

else:
    km_summary = pd.DataFrame()


# ══════════════════════════════════════════════════════════
# MODÜL 4  —  CPTAC Kinaz Aktivasyon Skoru (KAS)
# ══════════════════════════════════════════════════════════
sec("MODÜL 4: CPTAC Kinaz Aktivasyon Skoru")

# Proteom yükle
prot = pd.read_csv(
    os.path.join(CPTAC, "HS_CPTAC_LUAD_proteome_ratio_NArm_TUMOR.cct"),
    sep='\t', index_col=0
)
print(f"Proteom: {prot.shape}  (gen × hasta)")

# Fosforproteom yükle
phospho = pd.read_csv(
    os.path.join(CPTAC, "HS_CPTAC_LUAD_phosphoproteome_ratio_norm_NArm_TUMOR.cct"),
    sep='\t', index_col=0
)
print(f"Fosforproteom: {phospho.shape}  (site × hasta)")

# Fosfosite'den gen adını çıkar (format: GENE:NP_xxx:S123s veya GENE_S123)
phospho_genes = phospho.index.str.split(':').str[0]

# CPTAC klinik
cptac_clin = pd.read_csv(os.path.join(CPTAC, "HS_CPTAC_LUAD_cli.tsi"), sep='\t', index_col=0)
# Satır 1 = data_type, gerçek veri satır 2'den başlar
cptac_clin = cptac_clin.iloc[1:]
print(f"CPTAC klinik: {cptac_clin.shape}")
print(f"CPTAC klinik kolonları: {list(cptac_clin.columns)}")

# KAS hesapla
kas_dict = {}
for kinase in focus_present:
    substrates = set(kinase_substrates.get(kinase, []))
    if not substrates:
        continue
    mask = phospho_genes.isin(substrates)
    if mask.sum() < 5:
        print(f"  {kinase}: {mask.sum()} fosfosite (yeterli değil)")
        continue
    kas = phospho.loc[mask].mean(axis=0)
    kas_dict[kinase] = kas
    print(f"  {kinase}: {mask.sum()} fosfosite substrat → KAS hesaplandı ({kas.notna().sum()} hasta)")

kas_df = pd.DataFrame(kas_dict)
print(f"\nKAS matrisi: {kas_df.shape}  (hasta × kinaz)")

# FIG 5a: KAS dağılımı — violin plot
fig, ax = plt.subplots(figsize=(12, 5))
kas_melt = kas_df.melt(var_name='Kinaz', value_name='KAS')
pal = {k: COLORS.get(k,'#ADB5BD') for k in kas_df.columns}
sns.violinplot(data=kas_melt, x='Kinaz', y='KAS', palette=pal,
               inner='box', ax=ax, cut=0)
ax.axhline(0, ls='--', color='black', alpha=0.4)
ax.set_title('CPTAC-LUAD: Kinaz Aktivasyon Skoru (KAS) Dağılımı (n=110)', fontsize=12)
ax.set_ylabel('Ortalama Substrat Fosforilasyon (Log2 Ratio)', fontsize=11)
ax.set_xlabel('')
plt.tight_layout()
savefig(fig, "fig5_cptac_kas_violin.png")

# EGFR mutasyon durumuna göre KAS karşılaştırması (varsa)
if 'EGFR.mutation.status' in cptac_clin.columns and 'EGFR' in kas_df.columns:
    egfr_mut = cptac_clin['EGFR.mutation.status'].map({'1':'Mutant','0':'WT','1.0':'Mutant','0.0':'WT'})
    common_pts = kas_df.index.intersection(egfr_mut.index)
    egfr_s = egfr_mut.loc[common_pts].dropna()
    kas_common = kas_df.loc[egfr_s.index]

    fig, axes = plt.subplots(1, min(3, len(kas_df.columns)), figsize=(14, 5))
    if not hasattr(axes, '__iter__'):
        axes = [axes]
    for ax, kinase in zip(axes, list(kas_df.columns)[:3]):
        wt   = kas_common.loc[egfr_s=='WT',   kinase].dropna()
        mut  = kas_common.loc[egfr_s=='Mutant', kinase].dropna()
        if len(wt) < 3 or len(mut) < 3:
            continue
        stat, pval = mannwhitneyu(wt, mut, alternative='two-sided')
        data = pd.DataFrame({'KAS': pd.concat([wt, mut]),
                              'EGFR': ['WT']*len(wt)+['Mutant']*len(mut)})
        sns.boxplot(data=data, x='EGFR', y='KAS', palette={'WT':'#457B9D','Mutant':'#E63946'}, ax=ax)
        sns.stripplot(data=data, x='EGFR', y='KAS', color='black', alpha=0.4, size=3, ax=ax)
        ax.set_title(f'{kinase} KAS\nEGFR Mutant vs WT\np={pval:.4f}', fontsize=11)
        ax.set_ylabel('KAS' if ax == axes[0] else '')
    plt.suptitle('CPTAC-LUAD: KAS vs EGFR Mutasyon Durumu', fontsize=12, y=1.02)
    plt.tight_layout()
    savefig(fig, "fig5b_kas_egfr_mutation.png")

# pARACNe doğrulama: kinaz proteomik ~ substrat fosforilasyon korelasyonu
print("\npARACNe Doğrulama (CPTAC):")
val_results = []
for kinase in focus_present:
    if kinase not in prot.index:
        continue
    kinase_prot = prot.loc[kinase]
    substrates = kinase_substrates.get(kinase, [])[:15]  # ilk 15 substrat
    for sub in substrates:
        sub_mask = phospho_genes == sub
        if sub_mask.sum() == 0:
            continue
        for site in phospho.index[sub_mask]:
            sub_ph = phospho.loc[site]
            common = kinase_prot.index.intersection(sub_ph.index)
            x = kinase_prot[common].fillna(0)
            y = sub_ph[common].fillna(0)
            if len(common) < 10 or x.std() < 0.01:
                continue
            rho, pval = spearmanr(x, y)
            val_results.append({
                'kinase': kinase, 'substrate': sub, 'site': site,
                'rho': rho, 'pval': pval, 'n': len(common)
            })

if val_results:
    val_df = pd.DataFrame(val_results)
    _, val_df['fdr'], _, _ = multipletests(val_df['pval'], method='fdr_bh')
    sig_val = val_df[val_df['fdr'] < 0.05]
    total_val = len(val_df)
    print(f"  Test edilen çift: {total_val}")
    print(f"  Doğrulanan (FDR<0.05): {len(sig_val)} ({len(sig_val)/total_val*100:.1f}%)")
    print(f"  Top doğrulamalar:")
    print(val_df.nsmallest(10,'fdr')[['kinase','substrate','site','rho','fdr']].to_string(index=False))
else:
    print("  Yeterli doğrulama verisi yok.")
    val_df = pd.DataFrame()


# ══════════════════════════════════════════════════════════
# SONUÇLARI KAYDET
# ══════════════════════════════════════════════════════════
sec("SONUÇLARI DIŞA AKTAR")

excel_path = os.path.join(RESULTS, "LUAD_Faz2_Results.xlsx")
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    # S1: Hub kinazlar
    hub.reset_index().rename(columns={'kinase':'Kinaz','substrate':'Substrat_Sayisi'}) \
        .to_excel(writer, sheet_name='1_Hub_Kinazlar', index=False)

    # S2: GDSC2 korelasyon
    if len(corr_df) > 0:
        corr_df.to_excel(writer, sheet_name='2_GDSC2_Korelasyon', index=False)

    # S3: KM survival
    if len(km_summary) > 0:
        km_summary.to_excel(writer, sheet_name='3_KM_Survival')

    # S4: Cox özeti
    if lifelines_ok and 'cph' in dir():
        cph.summary[['exp(coef)','exp(coef) lower 95%','exp(coef) upper 95%','p']] \
            .to_excel(writer, sheet_name='4_Cox_Regression')

    # S5: KAS skorları
    if len(kas_df) > 0:
        kas_df.to_excel(writer, sheet_name='5_CPTAC_KAS')

    # S6: pARACNe doğrulama
    if len(val_df) > 0:
        val_df.to_excel(writer, sheet_name='6_pARACNe_Validation', index=False)

print(f"Excel kaydedildi: results/LUAD_Faz2_Results.xlsx")

# ─────────────────────────────────────────────
# ÖZET
# ─────────────────────────────────────────────
sec("FAZ 2 ÖZET")
results_files = [f for f in os.listdir(RESULTS) if f.endswith(('.png','.xlsx'))]
print(f"\nKaydedilen çıktılar ({len(results_files)} dosya):")
for f in sorted(results_files):
    fpath = os.path.join(RESULTS, f)
    size = os.path.getsize(fpath)/1024
    print(f"  {f}  ({size:.0f} KB)")

print(f"\npARACNe Hub: Top={hub.index[0]} ({hub.iloc[0]} substrat)")
if len(corr_df) > 0:
    top_pair = corr_df.iloc[0]
    print(f"Top GDSC2 korelasyon: {top_pair['kinase']} x {top_pair['drug']} (rho={top_pair['rho']:.3f}, FDR={top_pair['fdr']:.4f})")
if len(km_summary) > 0:
    sig_km = km_summary[km_summary['logrank_p'] < 0.05]
    print(f"Anlamlı KM kinaz (p<0.05): {list(sig_km.index)}")
if len(kas_df) > 0:
    print(f"CPTAC KAS hesaplanan kinaz: {list(kas_df.columns)}")

print("\nFaz 2 tamamlandı.")
