# Kinase Activation Signatures and Drug Resistance in LUAD

Reproducibility code for:
**"Hub Kinase Activation Signatures Predict Drug Resistance and Survival in Lung Adenocarcinoma"**
*(manuscript submitted)*

---

## Overview

This repository contains analysis code integrating multi-omics datasets to identify
tyrosine kinase activation signatures (KAS) associated with drug resistance and
overall survival in lung adenocarcinoma (LUAD).

**Key findings:**
- pARACNe TK network identifies 9 hub kinases (≥100 substrates): PTK2, MET, LCK, YES1, FYN, EGFR, LYN, DDR1, SRC
- YES1 expression independently predicts OS (HR = 1.28, 95% CI 1.03–1.60, Cox multivariable)
- LCK and YES1 high-expression tertiles associate with poor OS (FDR < 0.05, TCGA LUAD, n = 497)
- SRC-family co-activation confirmed by CPTAC phosphoproteomics (FYN × YES1 ρ = 0.999)
- pARACNe network validated against CPTAC data (4.9% FDR < 0.05 vs 1% null, p < 0.001)

---

## Repository Structure

```
├── LUAD_Drug_Resistance_Analysis.ipynb   # Main analysis notebook (Google Colab compatible)
├── faz2_analysis.py                      # Phase 2: GDSC2 × DepMap expression correlations
├── faz2b_improved.py                     # Phase 2b: CPTAC KAS, TCGA survival, validation
├── generate_figures_publication.py       # Publication-quality figures (5 main + 1 supplementary)
├── generate_manuscript_docx.py           # Manuscript assembly (DOCX)
├── check_data.py                         # Data integrity checks
├── final_check.py                        # Final result verification
├── requirements.txt                      # Python dependencies
└── pARACNe/
    ├── README.txt
    └── MANIFEST.txt
```

---

## Data Availability

Data files are **not included** in this repository due to size constraints.
Download from the following public sources before running the analysis:

| File | Source | Notes |
|------|--------|-------|
| `secondary-screen-replicate-collapsed-logfold-change.csv` | [PRISM Repurposing 19Q4](https://depmap.org/portal/download/) | 87 MB |
| `secondary-screen-replicate-collapsed-treatment-info.csv` | PRISM Repurposing 19Q4 | 3.6 MB |
| `secondary-screen-dose-response-curve-parameters.csv` | PRISM Repurposing 19Q4 | 252 MB |
| `GDSC2_fitted_dose_response_27Oct23.xlsx` | [GDSC2](https://www.cancerrxgene.org/downloads/bulk_download) | 20 MB |
| `OmicsExpressionProteinCodingGenesTPMLogp1.csv` | [DepMap 23Q4](https://depmap.org/portal/download/) | 429 MB |
| `Model.csv` | DepMap 23Q4 | 0.5 MB |
| `data_mrna_seq_v2_rsem.txt` | [TCGA LUAD PanCanAtlas 2018](https://www.cbioportal.org/study/summary?id=luad_tcga_pan_can_atlas_2018) | 70 MB |
| `data_clinical_patient.txt` | TCGA LUAD PanCanAtlas 2018 | — |
| `data_mutations.txt` | TCGA LUAD PanCanAtlas 2018 | 239 MB |
| `HS_CPTAC_LUAD_proteome_ratio_NArm_TUMOR.cct` | [LinkedOmics CPTAC-LUAD](http://linkedomics.org/data_download/CPTAC-LUAD/) | 7.9 MB |
| `HS_CPTAC_LUAD_phosphoproteome_ratio_norm_NArm_TUMOR.cct` | LinkedOmics CPTAC-LUAD | 27.9 MB |
| `HS_CPTAC_LUAD_cli.tsi` | LinkedOmics CPTAC-LUAD | — |
| `LUAD-Proteome_Signaling.zip` (S1, S2) | [Columbia pARACNe](https://doi.org/10.1016/j.celrep.2021.110173) | pARACNe network |

Place all files in the project root directory (or adjust paths in scripts).

---

## Installation

```bash
git clone https://github.com/ibeypinar-spec/luad-drug-resistance.git
cd luad-drug-resistance
pip install -r requirements.txt
```

Python 3.9+ recommended.

---

## Usage

### Interactive notebook (recommended)
Open `LUAD_Drug_Resistance_Analysis.ipynb` in Jupyter or Google Colab.
For Colab: mount your Google Drive and update the `BASE_DIR` variable.

### Scripts (batch mode)
```bash
# Phase 2: GDSC2 correlations
python faz2_analysis.py

# Phase 2b: KAS, survival, validation
python faz2b_improved.py

# Generate publication figures
python generate_figures_publication.py
```

Output figures are saved to `results/publication_figures/`.

---

## Citation

If you use this code, please cite:

> [Author et al. (2026). Title. *Journal of Thoracic Oncology*. doi:...]

---

## License

MIT License — see [LICENSE](LICENSE) for details.
