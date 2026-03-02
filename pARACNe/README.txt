Tyrosine kinase / substrate interaction networks created at the peptide and protein levels using pARACNe.
Suppl. Table 1 contains the peptide-level network, with phosphorylation sites indicated.
Suppl. Table 2 contains the protein-level network

Reference:
Bansal M, He J, Peyton M, Kustagi M, Iyer A, Comb M, White M, Minna JD,
Califano A. Elucidating synergistic dependencies in lung adenocarcinoma by
proteome-wide signaling-network analysis. PLoS One. 2019 Jan 7;14(1):e0208646.
doi: 10.1371/journal.pone.0208646. eCollection 2019. PubMed PMID: 30615629;
PubMed Central PMCID: PMC6322741.

The two data files described below are in tab-delimited format.


## Supplementary Table 1. pARACNe-inferred TK-peptides/substrate-peptides Interaction Network
File: S1_pARACNe_TK-peptides_substrate-peptides_network.txt
DOI: https://doi.org/10.1371/journal.pone.0208646.s002
(original filename pone.0208646.s002.xlsx)

Peptides are specified as a gene symbol with sites of phosphorylation in the protein given by a number, usually preceded by a dollar sign ($).  Multiple sites are separated by semicolons (;).

Column headers:
peptide1 - TK peptide 
peptide2 - Substrate peptide 
mutual_information - pARACNe mutual information between peptide1 and peptide2.



## Supplementary Table 2. pARACNe-inferred TK-Protein/Substrate Interaction Network.
File: S2_pARACNe_TK-Protein_Substrate_Network.txt
DOI: https://doi.org/10.1371/journal.pone.0208646.s003
(original filename pone.0208646.s003.xlsx)

Column headers:
kinase - TK protein
mutual_information - the maximum mutual information when aggregating the peptide network into the protein level network
substrate - substrate protein
