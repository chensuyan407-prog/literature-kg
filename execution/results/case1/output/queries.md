# Executed graph queries

### q1: Which adsorbates were tested with which adsorbent, and what maximum capacity was reported (per paper)?

`predicate TESTED_ON,HAS_RESULT` → **ok** (28 nodes, 24 edges)

| subject | predicate | object | paper | ¶ | strength | conditions | quote |
|-|-|-|-|-|-|-|-|
| magnetically modified activated carbon reference | HAS_RESULT | magnetic AC qmax for lactic acid 74.6 mg/g | paper-A | p-0040 | direct |  | “its maximum adsorption capacity for lactic acid was substantially lower (q max = 74.6 mg/g)” |
| magnetically modified activated carbon reference | HAS_RESULT | magnetic AC specific surface area 40.38 m2/g | paper-A | p-0040 | direct |  | “parallel textural characterization was conducted on a magnetic activated carbon (AC) reference, which exhibited a slightly higher surface area (40.38 m2/g)” |
| magnetically modified graphene oxide composite | HAS_RESULT | MGO average pore radius 4.12 nm | paper-A | p-0039 | direct |  | “the average pore radius was found to be 4.12 nm” |
| magnetically modified graphene oxide composite | HAS_RESULT | MGO qmax for lactic acid 334.45 mg/g | paper-A | p-0055 | direct |  | “The maximum adsorption capacity of MGO for lactic acid (334.45 mg/g) is highly competitive” |
| magnetically modified graphene oxide composite | HAS_RESULT | MGO specific surface area 37.94 m2/g | paper-A | p-0039 | direct |  | “the specific surface area of the MGO was determined to be 37.94 m2/g” |
| magnetically modified graphene oxide composite | HAS_RESULT | PSO fit R2 > 0.99 for all acids | paper-A | p-0059 | direct ⚠ |  | “The experimental data for all acids exhibited an excellent fit with the PSO model (R 2 > 0.99)” |
| magnetically modified graphene oxide composite | HAS_RESULT | PSO k2 lactic 0.007, succinic 0.0023, citric 0.0019 g/mg·min | paper-A | p-0059 | direct ⚠ |  | “The rate constants (k 2) were determined as 0.007, 0.0023, and 0.0019 g/mg·min” |
| magnetically modified graphene oxide composite | HAS_RESULT | RL between 2.3 × 10–6 and 2.8 × 10–3 | paper-A | p-0063 | direct ⚠ |  | “R L values for all investigated acids on both adsorbents across the studied concentration range (10–100 g/L) were between 2.3 × 10–6 and 2.8 × 10–3” |
| magnetically modified graphene oxide composite | HAS_RESULT | below ~3 g/L lactic acid, AC adsorbs slightly more than MGO | paper-A | p-0051 | direct |  | “the activated carbon-based adsorbent exhibits a slightly higher adsorption capacity than the MGO composite” |
| magnetically modified graphene oxide composite | HAS_RESULT | capacity retention after 5 cycles: lactic 91.4%, succinic 87.8%, citric 84.2% | paper-A | p-0067 | direct |  | “The capacity retention rates after the fifth cycle were found to be 87.8% for succinic acid and 84.2% for citric acid.” |
| magnetically modified graphene oxide composite | HAS_RESULT | mean Qe citric acid: MGO 213 vs AC 73.7 mg/g | paper-A | p-0048 | direct |  | “the overall mean adsorption capacity was determined to be 213 mg/g for MGO-based and 73.7 mg/g for AC-based adsorbents” |
| magnetically modified graphene oxide composite | HAS_RESULT | mean Qe succinic acid: MGO 188.6 vs AC 67.8 mg/g | paper-A | p-0045 | direct |  | “the overall mean adsorption capacity (Q e) was determined as 188.6 mg/g for MGO-based and 67.8 mg/g for AC-based adsorbents” |
| magnetically modified graphene oxide composite | TESTED_ON | citric acid | paper-A | p-0010 | direct |  | “All adsorption experiments for lactic, succinic, and citric acids were conducted using a standardized protocol” |
| magnetically modified graphene oxide composite | TESTED_ON | lactic acid | paper-A | p-0010 | direct |  | “All adsorption experiments for lactic, succinic, and citric acids were conducted using a standardized protocol” |
| magnetically modified graphene oxide composite | TESTED_ON | succinic acid | paper-A | p-0010 | direct |  | “All adsorption experiments for lactic, succinic, and citric acids were conducted using a standardized protocol” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | paper-B | p-0094 | direct |  | “The maximum adsorption capacity calculated according to the Langmuir model was 7.10 mg/g for HA–rGO” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | O/C ratio: HA 0.77, rGO 0.36, HA-rGO 0.73 (mechanical mixture expected ~0.66) | paper-B | p-0037 | direct |  | “For the HA-rGO composite, the O/C ratio decreases to 0.73.” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | carbon content HA 47.34 → HA-rGO 55.61 wt.% | paper-B | p-0035 | direct |  | “The carbon content increases to 55.61 wt.%, whereas the oxygen content decreases to 40.79 wt.%.” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | oxygen content HA 48.31 → HA-rGO 40.79 wt.% | paper-B | p-0035 | direct |  | “The carbon content increases to 55.61 wt.%, whereas the oxygen content decreases to 40.79 wt.%.” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | residual mass at 1000 °C: HA 59.21%, HA-rGO 70.03%, rGO 84.23% | paper-B | p-0058 | direct |  | “The residual mass of the initial humic acid is 59.21%, whereas that of the HA-rGO composite increases to 70.03%.” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | Σ(COOH+OH) HA 5.00 → HA-rGO 5.47 mmol/g | paper-B | p-0038 | direct |  | “the HA-rGO composite shows an increase in Σ(COOH + OH) to 5.47 mmol/g compared with the initial humic acid (5.00 mmol/g)” |
| rGO sample (Sigma-Aldrich) | HAS_RESULT | rGO isotherm fit: Langmuir R2 0.9266 vs Freundlich 0.9299 (no clear winner) | paper-B | p-0093 | direct ⚠ |  | “For rGO, the Langmuir and Freundlich models showed comparable agreement with the experimental data” |
| rGO sample (Sigma-Aldrich) | HAS_RESULT | rGO kinetics: PFO R2 0.9973 vs PSO 0.9968 | paper-B | p-0099 | direct ⚠ |  | “The pseudo-first-order model exhibited a marginally higher R2 value of 0.9973 compared with 0.9968 for the pseudo-second-order model.” |
| humic acid/reduced graphene oxide composite | TESTED_ON | phenol | paper-B | p-0028 | direct |  | “Phenol adsorption was evaluated as a preliminary functional test of the synthesized HA-rGO composite.” |

Uncertain:
- R:b3fdf59987: needs_review, subject 'rGO sample (Sigma-Aldrich)' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:f4c2774b5a: needs_review, subject 'magnetically modified graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:2cfa5e2574: needs_review, subject 'rGO sample (Sigma-Aldrich)' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:40dcb0566e: needs_review, subject 'magnetically modified graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:47f2658b4f: needs_review, subject 'magnetically modified graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review

### q2: Which isotherm / kinetic models fit each paper's data, and which model won under which sample?

`predicate FITS,OUTPERFORMS,COMPARED_WITH` → **ok** (21 nodes, 22 edges)

| subject | predicate | object | paper | ¶ | strength | conditions | quote |
|-|-|-|-|-|-|-|-|
| lactic acid | COMPARED_WITH | citric acid | paper-A | p-0060 | direct |  | “The lowest k 2 value observed for citric acid (0.0019 g/mg·min) is quantitatively consistent with its bulky tricarboxylic structure” |
| magnetically modified graphene oxide composite | COMPARED_WITH | activated carbon | paper-A | p-0038 | direct |  | “Unlike activated carbon, graphene oxide possesses a layered graphitic framework rich in oxygen-containing functional groups” |
| Freundlich isotherm model | FITS | lactic acid on MGO R2 = 0.826 (reported for both Freundlich p-0054 and Temkin p-0056) | paper-A | p-0054 | direct |  | “Specifically, for lactic acid on MGO, the high correlation coefficient (R 2 = 0.826)” |
| Langmuir isotherm model | FITS | magnetically modified activated carbon reference | paper-A | p-0046 | direct |  | “Both AC- and graphene oxide-based samples exhibit good agreement with the Langmuir isotherm model.” |
| Langmuir isotherm model | FITS | magnetically modified graphene oxide composite | paper-A | p-0046 | direct | adsorbates=succinic, citric, lactic acid | “Both AC- and graphene oxide-based samples exhibit good agreement with the Langmuir isotherm model.” |
| Temkin isotherm model | FITS | Temkin R2 0.758–0.897 on MGO | paper-A | p-0056 | direct |  | “the Temkin model provided a satisfactory fit for all investigated organic acids” |
| Temkin isotherm model | FITS | lactic acid on MGO R2 = 0.826 (reported for both Freundlich p-0054 and Temkin p-0056) | paper-A | p-0056 | direct |  | “The high correlation with the Temkin model (R 2 = 0.826 for lactic acid)” |
| pseudo-second-order kinetic model | FITS | PSO fit R2 > 0.99 for all acids | paper-A | p-0059 | direct |  | “The experimental data for all acids exhibited an excellent fit with the PSO model (R 2 > 0.99)” |
| magnetically modified activated carbon reference | OUTPERFORMS | magnetically modified graphene oxide composite | paper-A | p-0051 | direct | adsorbate=lactic acid; range=below approximately 3 g/L; criterion=adsorption capacity | “specifically below approximately 3 g/L, the activated carbon-based adsorbent exhibits a slightly higher adsorption capacity than the MGO composite” |
| magnetically modified graphene oxide composite | OUTPERFORMS | magnetically modified activated carbon reference | paper-A | p-0045 | direct | adsorbate=succinic acid; criterion=mean Qe; range=10–100 g/L | “These results clearly establish that the MGO composite provides a vastly superior affinity and saturation capacity for succinic acid recovery compared to the AC” |
| magnetically modified graphene oxide composite | OUTPERFORMS | magnetically modified activated carbon reference | paper-A | p-0040 | direct | adsorbate=lactic acid; criterion=qmax (Langmuir) | “its maximum adsorption capacity for lactic acid was substantially lower (q max = 74.6 mg/g)” |
| Langmuir isotherm model | COMPARED_WITH | Freundlich isotherm model | paper-B | p-0093 | direct | sample=rGO; criterion=R2; adsorbate=phenol | “neither model can be considered unambiguously predominant for rGO within the investigated concentration range” |
| pseudo-first-order kinetic model | COMPARED_WITH | pseudo-second-order kinetic model | paper-B | p-0100 | direct | sample=rGO; criterion=R2 | “whereas both models provided a comparable fit for rGO” |
| reduced graphene oxide | COMPARED_WITH | graphene oxide | paper-B | p-0034 | direct |  | “These results indicate substantial removal of oxygen-containing groups compared with graphene oxide” |
| Freundlich isotherm model | FITS | HA isotherm fit: Freundlich R2 0.9092 vs Langmuir 0.8502 | paper-B | p-0092 | direct |  | “for which the coefficient of determination was R2 = 0.9092, compared with R2 = 0.8502 for the Langmuir model” |
| Langmuir isotherm model | FITS | HA–rGO isotherm fit: Langmuir R2 0.9804 vs Freundlich 0.9515 | paper-B | p-0094 | direct |  | “phenol adsorption on the HA–rGO composite was better described by the Langmuir model, with R2 = 0.9804” |
| pseudo-second-order kinetic model | FITS | HA–rGO kinetics: PSO R2 0.9939 vs PFO 0.9727 | paper-B | p-0098 | direct | C0=7.5 mg/dm3 | “The pseudo-second-order model also showed better agreement for the HA–rGO composite” |
| Freundlich isotherm model | OUTPERFORMS | Langmuir isotherm model | paper-B | p-0092 | direct | sample=initial humic acid; criterion=R2; adsorbate=phenol | “The adsorption of phenol on HA was better described by the Freundlich model” |
| Langmuir isotherm model | OUTPERFORMS | Freundlich isotherm model | paper-B | p-0094 | direct | sample=HA–rGO composite; criterion=R2; adsorbate=phenol | “phenol adsorption on the HA–rGO composite was better described by the Langmuir model, with R2 = 0.9804, whereas the Freundlich model gave R2 = 0.9515” |
| humic acid/reduced graphene oxide composite | OUTPERFORMS | initial humic acid sample (Shubarkol coal) | paper-B | p-0089 | direct | adsorbate=phenol; criterion=adsorption capacity; range=0.5–15 mg/dm3 | “the HA-rGO composite exhibited a higher adsorption capacity toward phenol than the initial humic acid and rGO” |
| humic acid/reduced graphene oxide composite | OUTPERFORMS | rGO sample (Sigma-Aldrich) | paper-B | p-0089 | direct ⚠ | adsorbate=phenol; criterion=adsorption capacity; range=0.5–15 mg/dm3 | “the HA-rGO composite exhibited a higher adsorption capacity toward phenol than the initial humic acid and rGO” |
| pseudo-second-order kinetic model | OUTPERFORMS | pseudo-first-order kinetic model | paper-B | p-0100 | direct | sample=HA–rGO composite and HA; criterion=R2 | “the kinetic data for HA and HA–rGO were better described by the pseudo-second-order model” |

Uncertain:
- R:7dbf743e4e: needs_review, object 'rGO sample (Sigma-Aldrich)' not named in the evidence paragraph (pronoun/inference?) -> needs_review

### q3: What does each paper say about the pseudo-second-order kinetic model?

`neighbors pseudo-second-order model` → **ok** (8 nodes, 8 edges)

| subject | predicate | object | paper | ¶ | strength | conditions | quote |
|-|-|-|-|-|-|-|-|
| pseudo-second-order kinetic model | FITS | PSO fit R2 > 0.99 for all acids | paper-A | p-0059 | direct |  | “The experimental data for all acids exhibited an excellent fit with the PSO model (R 2 > 0.99)” |
| magnetically modified graphene oxide composite | HAS_RESULT | PSO fit R2 > 0.99 for all acids | paper-A | p-0059 | direct ⚠ |  | “The experimental data for all acids exhibited an excellent fit with the PSO model (R 2 > 0.99)” |
| PSO fit R2 > 0.99 for all acids | SUPPORTS | PSO fit confirms chemisorption-controlled adsorption (paper A) | paper-A | p-0059 | direct |  | “This confirms that the adsorption rate is governed by chemical interactions (chemisorption).” |
| pseudo-first-order kinetic model | COMPARED_WITH | pseudo-second-order kinetic model | paper-B | p-0100 | direct | sample=rGO; criterion=R2 | “whereas both models provided a comparable fit for rGO” |
| HA–rGO kinetics: PSO R2 0.9939 vs PFO 0.9727 | CONTRADICTS | PSO/PFO fits are empirical and do not establish the chemical nature of adsorption (paper B) | paper-B | p-0100 | direct |  | “These models should be regarded as empirical descriptions of the adsorption-rate data” |
| pseudo-second-order kinetic model | FITS | HA–rGO kinetics: PSO R2 0.9939 vs PFO 0.9727 | paper-B | p-0098 | direct | C0=7.5 mg/dm3 | “The pseudo-second-order model also showed better agreement for the HA–rGO composite” |
| pseudo-second-order kinetic model | OUTPERFORMS | pseudo-first-order kinetic model | paper-B | p-0100 | direct | sample=HA–rGO composite and HA; criterion=R2 | “the kinetic data for HA and HA–rGO were better described by the pseudo-second-order model” |
| HA–rGO kinetics: PSO R2 0.9939 vs PFO 0.9727 | UNDER_CONDITION | kinetics at initial phenol 7.5 mg/dm3 | paper-B | p-0031 | direct |  | “Kinetic experiments were performed at an initial phenol concentration of 7.5 mg/dm3.” |

Related alignment records:
- interpretation_conflict: ['pseudo-second-order kinetic model', 'chemisorption'] — paper-A reads a PSO fit as confirming chemisorption; paper-B states PSO/PFO fits do not establish the chemical nature of adsorption. Different systems; kept as two paper-scoped conclusions, not resolved. (both_kept_not_resolved)

Uncertain:
- R:f4c2774b5a: needs_review, subject 'magnetically modified graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review

### q4: Is there a connection between MGO (paper A) and the HA-rGO composite (paper B)?

`path MGO HA-rGO composite` → **ok** (3 nodes, 2 edges)

> a path through a shared concept node connects two papers' statements; it is navigation, not a combined finding

| subject | predicate | object | paper | ¶ | strength | conditions | quote |
|-|-|-|-|-|-|-|-|
| magnetically modified graphene oxide composite | CHARACTERIZED_BY | Fourier transform infrared spectroscopy | paper-A | p-0009 | direct |  | “Fourier transform infrared spectroscopy (FTIR; Bruker VERTEX 70, Germany), respectively” |
| humic acid/reduced graphene oxide composite | CHARACTERIZED_BY | Fourier transform infrared spectroscopy | paper-B | p-0042 | direct |  | “FTIR spectroscopy was used to study the functional composition of the initial humic acid, reduced graphene oxide, and synthesized HA-rGO composite.” |

### q5: Which mechanisms are invoked, and with what strength?

`type Mechanism` → **ok** (12 nodes, 11 edges)

| subject | predicate | object | paper | ¶ | strength | conditions | quote |
|-|-|-|-|-|-|-|-|
| MGO qmax for lactic acid 334.45 mg/g | ATTRIBUTED_TO | hydrogen bonding | paper-A | p-0065 | hedged |  | “which may facilitate supplementary hydrogen bonding interactions with the oxygen-functionalized graphene oxide surface” |
| PSO fit confirms chemisorption-controlled adsorption (paper A) | INVOLVES | chemisorption | paper-A | p-0001 | direct |  | “confirming a chemisorption-controlled mechanism for all investigated acids” |
| k2 decreases with molecular complexity due to steric hindrance (paper A) | INVOLVES | steric hindrance | paper-A | p-0060 | direct |  | “which causes significant steric hindrance during diffusion into the 4.12 nm mesoporous framework of the MGO” |
| magnetically modified graphene oxide composite | INVOLVES | hydrogen bonding | paper-A | p-0041 | direct |  | “which facilitate specific hydrogen bonding and π–π interactions that are absent in the purely physical framework of the AC reference” |
| magnetically modified graphene oxide composite | INVOLVES | π–π interactions | paper-A | p-0041 | direct |  | “which facilitate specific hydrogen bonding and π–π interactions that are absent in the purely physical framework of the AC reference” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | ATTRIBUTED_TO | hydrogen bonding | paper-B | p-0090 | hedged |  | “Carboxyl, phenolic, and hydroxyl groups present in humic acid may participate in hydrogen bonding with phenol molecules” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | ATTRIBUTED_TO | π–π interactions | paper-B | p-0090 | hedged |  | “the graphene-like aromatic domains of rGO may promote π–π interactions with the aromatic ring of phenol” |
| H-bonding and π–π contributions to phenol adsorption are plausible, not directly demonstrated (paper B) | INVOLVES | π–π interactions | paper-B | p-0104 | hedged |  | “Hydrogen bonding and π–π interactions are therefore considered plausible contributions” |
| HA–rGO composite forms mainly through non-covalent interactions (paper B) | INVOLVES | hydrogen bonding | paper-B | p-0087 | hedged |  | “including π–π stacking of aromatic structures and hydrogen bonding between the functional groups of the components” |
| HA–rGO composite forms mainly through non-covalent interactions (paper B) | INVOLVES | non-covalent interactions | paper-B | p-0081 | hedged |  | “This suggests that composite formation occurs mainly through non-covalent interactions between the components.” |
| HA–rGO composite forms mainly through non-covalent interactions (paper B) | INVOLVES | π–π interactions | paper-B | p-0087 | hedged |  | “including π–π stacking of aromatic structures and hydrogen bonding between the functional groups of the components” |

Uncertain:
- R:e745caf967: hedged
- R:6ef1c181b6: hedged
- R:3fab2701d7: hedged
- R:4fc67016ad: hedged
- R:665966f364: hedged
- R:34b3eca17d: hedged
- R:387b947927: hedged

### q6: Does any paper report BET surface area of the HA-rGO composite?

`neighbors HA-rGO composite` predicate=CHARACTERIZED_BY source=paper-B → **ok** (7 nodes, 6 edges)

| subject | predicate | object | paper | ¶ | strength | conditions | quote |
|-|-|-|-|-|-|-|-|
| humic acid/reduced graphene oxide composite | CHARACTERIZED_BY | Fourier transform infrared spectroscopy | paper-B | p-0042 | direct |  | “FTIR spectroscopy was used to study the functional composition of the initial humic acid, reduced graphene oxide, and synthesized HA-rGO composite.” |
| humic acid/reduced graphene oxide composite | CHARACTERIZED_BY | elemental analysis | paper-B | p-0018 | direct ⚠ |  | “The elemental composition of the samples was determined using an Elementar Unicube elemental analyzer” |
| humic acid/reduced graphene oxide composite | CHARACTERIZED_BY | energy-dispersive X-ray spectroscopy | paper-B | p-0070 | direct |  | “energy-dispersive X-ray spectroscopy with elemental mapping was performed” |
| humic acid/reduced graphene oxide composite | CHARACTERIZED_BY | functional-group titrimetric analysis | paper-B | p-0020 | direct ⚠ |  | “The content of oxygen-containing functional groups was determined by selective chemical binding followed by titrimetric analysis.” |
| humic acid/reduced graphene oxide composite | CHARACTERIZED_BY | scanning electron microscopy | paper-B | p-0062 | direct |  | “The morphological features of the initial humic acid, reduced graphene oxide, and HA-rGO composite were studied by scanning electron microscopy.” |
| humic acid/reduced graphene oxide composite | CHARACTERIZED_BY | thermogravimetric analysis | paper-B | p-0052 | direct |  | “The thermal stability of the initial humic acid, reduced graphene oxide, and HA-rGO composite was investigated by thermogravimetric analysis” |

Uncertain:
- R:d864fd647c: needs_review, subject 'humic acid/reduced graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:4e1ef8e791: needs_review, subject 'humic acid/reduced graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review

### q7: Find XPS in paper B

`find X-ray photoelectron spectroscopy` source=paper-B → **no_result** (0 nodes, 0 edges)

Reason: no node named or aliased 'X-ray photoelectron spectroscopy' in paper-B


### q_shared: Which concepts occur in more than one paper, and what does each paper say about them (kept separate)?

`shared ` → **ok** (25 nodes, 28 edges)

> shared = same general concept term; paper-scoped samples, conditions and values are listed per paper and are not combined

| subject | predicate | object | paper | ¶ | strength | conditions | quote |
|-|-|-|-|-|-|-|-|
| MGO qmax for lactic acid 334.45 mg/g | ATTRIBUTED_TO | hydrogen bonding | paper-A | p-0065 | hedged |  | “which may facilitate supplementary hydrogen bonding interactions with the oxygen-functionalized graphene oxide surface” |
| magnetically modified graphene oxide composite | CHARACTERIZED_BY | Fourier transform infrared spectroscopy | paper-A | p-0009 | direct |  | “Fourier transform infrared spectroscopy (FTIR; Bruker VERTEX 70, Germany), respectively” |
| Freundlich isotherm model | FITS | lactic acid on MGO R2 = 0.826 (reported for both Freundlich p-0054 and Temkin p-0056) | paper-A | p-0054 | direct |  | “Specifically, for lactic acid on MGO, the high correlation coefficient (R 2 = 0.826)” |
| Langmuir isotherm model | FITS | magnetically modified activated carbon reference | paper-A | p-0046 | direct |  | “Both AC- and graphene oxide-based samples exhibit good agreement with the Langmuir isotherm model.” |
| Langmuir isotherm model | FITS | magnetically modified graphene oxide composite | paper-A | p-0046 | direct | adsorbates=succinic, citric, lactic acid | “Both AC- and graphene oxide-based samples exhibit good agreement with the Langmuir isotherm model.” |
| pseudo-second-order kinetic model | FITS | PSO fit R2 > 0.99 for all acids | paper-A | p-0059 | direct |  | “The experimental data for all acids exhibited an excellent fit with the PSO model (R 2 > 0.99)” |
| magnetically modified graphene oxide composite | INVOLVES | hydrogen bonding | paper-A | p-0041 | direct |  | “which facilitate specific hydrogen bonding and π–π interactions that are absent in the purely physical framework of the AC reference” |
| magnetically modified graphene oxide composite | INVOLVES | π–π interactions | paper-A | p-0041 | direct |  | “which facilitate specific hydrogen bonding and π–π interactions that are absent in the purely physical framework of the AC reference” |
| MGO qmax for lactic acid 334.45 mg/g | MEASURED_BY | maximum adsorption capacity | paper-A | p-0001 | direct |  | “Lactic acid exhibited the highest maximum adsorption capacity (q max = 334.45 mg/g)” |
| magnetically modified graphene oxide composite | PREPARED_FROM | graphene oxide | paper-A | p-0007 | direct |  | “Briefly, 0.5 g of GO was dispersed in 60 mL of deionized water” |
| Langmuir isotherm model | SUPPORTS | Langmuir agreement suggests predominantly monolayer adsorption on homogeneous sites (paper A) | paper-A | p-0069 | hedged |  | “While the Langmuir model demonstrated excellent agreement (R 2 > 0.95), suggesting predominantly monolayer adsorption on a homogeneous distribution of active si” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | ATTRIBUTED_TO | hydrogen bonding | paper-B | p-0090 | hedged |  | “Carboxyl, phenolic, and hydroxyl groups present in humic acid may participate in hydrogen bonding with phenol molecules” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | ATTRIBUTED_TO | π–π interactions | paper-B | p-0090 | hedged |  | “the graphene-like aromatic domains of rGO may promote π–π interactions with the aromatic ring of phenol” |
| humic acid/reduced graphene oxide composite | CHARACTERIZED_BY | Fourier transform infrared spectroscopy | paper-B | p-0042 | direct |  | “FTIR spectroscopy was used to study the functional composition of the initial humic acid, reduced graphene oxide, and synthesized HA-rGO composite.” |
| Langmuir isotherm model | COMPARED_WITH | Freundlich isotherm model | paper-B | p-0093 | direct | sample=rGO; criterion=R2; adsorbate=phenol | “neither model can be considered unambiguously predominant for rGO within the investigated concentration range” |
| pseudo-first-order kinetic model | COMPARED_WITH | pseudo-second-order kinetic model | paper-B | p-0100 | direct | sample=rGO; criterion=R2 | “whereas both models provided a comparable fit for rGO” |
| reduced graphene oxide | COMPARED_WITH | graphene oxide | paper-B | p-0034 | direct |  | “These results indicate substantial removal of oxygen-containing groups compared with graphene oxide” |
| Freundlich isotherm model | FITS | HA isotherm fit: Freundlich R2 0.9092 vs Langmuir 0.8502 | paper-B | p-0092 | direct |  | “for which the coefficient of determination was R2 = 0.9092, compared with R2 = 0.8502 for the Langmuir model” |
| Langmuir isotherm model | FITS | HA–rGO isotherm fit: Langmuir R2 0.9804 vs Freundlich 0.9515 | paper-B | p-0094 | direct |  | “phenol adsorption on the HA–rGO composite was better described by the Langmuir model, with R2 = 0.9804” |
| pseudo-second-order kinetic model | FITS | HA–rGO kinetics: PSO R2 0.9939 vs PFO 0.9727 | paper-B | p-0098 | direct | C0=7.5 mg/dm3 | “The pseudo-second-order model also showed better agreement for the HA–rGO composite” |
| H-bonding and π–π contributions to phenol adsorption are plausible, not directly demonstrated (paper B) | INVOLVES | π–π interactions | paper-B | p-0104 | hedged |  | “Hydrogen bonding and π–π interactions are therefore considered plausible contributions” |
| HA–rGO composite forms mainly through non-covalent interactions (paper B) | INVOLVES | hydrogen bonding | paper-B | p-0087 | hedged |  | “including π–π stacking of aromatic structures and hydrogen bonding between the functional groups of the components” |
| HA–rGO composite forms mainly through non-covalent interactions (paper B) | INVOLVES | π–π interactions | paper-B | p-0087 | hedged |  | “including π–π stacking of aromatic structures and hydrogen bonding between the functional groups of the components” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | MEASURED_BY | maximum adsorption capacity | paper-B | p-0094 | direct |  | “The maximum adsorption capacity calculated according to the Langmuir model was 7.10 mg/g for HA–rGO” |
| Freundlich isotherm model | OUTPERFORMS | Langmuir isotherm model | paper-B | p-0092 | direct | sample=initial humic acid; criterion=R2; adsorbate=phenol | “The adsorption of phenol on HA was better described by the Freundlich model” |
| Langmuir isotherm model | OUTPERFORMS | Freundlich isotherm model | paper-B | p-0094 | direct | sample=HA–rGO composite; criterion=R2; adsorbate=phenol | “phenol adsorption on the HA–rGO composite was better described by the Langmuir model, with R2 = 0.9804, whereas the Freundlich model gave R2 = 0.9515” |
| pseudo-second-order kinetic model | OUTPERFORMS | pseudo-first-order kinetic model | paper-B | p-0100 | direct | sample=HA–rGO composite and HA; criterion=R2 | “the kinetic data for HA and HA–rGO were better described by the pseudo-second-order model” |
| humic acid/reduced graphene oxide composite | PREPARED_FROM | sodium hydroxide | paper-B | p-0016 | direct | pH=9 | “the pH of the medium was adjusted to 9 by adding sodium hydroxide solution” |

Not merged across papers:
- interpretation_conflict: ['pseudo-second-order kinetic model', 'chemisorption'] — paper-A reads a PSO fit as confirming chemisorption; paper-B states PSO/PFO fits do not establish the chemical nature of adsorption. Different systems; kept as two paper-scoped conclusions, not resolved.
- interpretation_conflict: ['Langmuir isotherm model', 'monolayer adsorption'] — paper-A takes Langmuir agreement as suggesting monolayer adsorption on homogeneous sites; paper-B says a Langmuir fit is not direct proof of that.
- similar_name_review: ['graphene oxide', 'reduced graphene oxide'] — similar but not equal names; may be broader/narrower or different objects (e.g. GO vs reduced GO)
- cross_paper_values_not_combined: None — same metric reported by different papers on different samples/conditions; compare only with each paper's conditions

Uncertain:
- R:6ef1c181b6: hedged
- R:665966f364: hedged
- R:387b947927: hedged
- R:b113e63e89: hedged
- R:e745caf967: hedged
- R:3fab2701d7: hedged
- R:4fc67016ad: hedged

### q_results: Which reported results (Measurement) exist per paper, with conditions and evidence?

`type Measurement` → **ok** (57 nodes, 55 edges)

| subject | predicate | object | paper | ¶ | strength | conditions | quote |
|-|-|-|-|-|-|-|-|
| MGO qmax for lactic acid 334.45 mg/g | ATTRIBUTED_TO | hydrogen bonding | paper-A | p-0065 | hedged |  | “which may facilitate supplementary hydrogen bonding interactions with the oxygen-functionalized graphene oxide surface” |
| below ~3 g/L lactic acid, AC adsorbs slightly more than MGO | CONTRADICTS | MGO outperforms magnetic AC across the entire concentration range (paper A) | paper-A | p-0051 | direct |  | “the activated carbon-based adsorbent exhibits a slightly higher adsorption capacity than the MGO composite” |
| Freundlich isotherm model | FITS | lactic acid on MGO R2 = 0.826 (reported for both Freundlich p-0054 and Temkin p-0056) | paper-A | p-0054 | direct |  | “Specifically, for lactic acid on MGO, the high correlation coefficient (R 2 = 0.826)” |
| Temkin isotherm model | FITS | Temkin R2 0.758–0.897 on MGO | paper-A | p-0056 | direct |  | “the Temkin model provided a satisfactory fit for all investigated organic acids” |
| Temkin isotherm model | FITS | lactic acid on MGO R2 = 0.826 (reported for both Freundlich p-0054 and Temkin p-0056) | paper-A | p-0056 | direct |  | “The high correlation with the Temkin model (R 2 = 0.826 for lactic acid)” |
| pseudo-second-order kinetic model | FITS | PSO fit R2 > 0.99 for all acids | paper-A | p-0059 | direct |  | “The experimental data for all acids exhibited an excellent fit with the PSO model (R 2 > 0.99)” |
| magnetically modified activated carbon reference | HAS_RESULT | magnetic AC qmax for lactic acid 74.6 mg/g | paper-A | p-0040 | direct |  | “its maximum adsorption capacity for lactic acid was substantially lower (q max = 74.6 mg/g)” |
| magnetically modified activated carbon reference | HAS_RESULT | magnetic AC specific surface area 40.38 m2/g | paper-A | p-0040 | direct |  | “parallel textural characterization was conducted on a magnetic activated carbon (AC) reference, which exhibited a slightly higher surface area (40.38 m2/g)” |
| magnetically modified graphene oxide composite | HAS_RESULT | MGO average pore radius 4.12 nm | paper-A | p-0039 | direct |  | “the average pore radius was found to be 4.12 nm” |
| magnetically modified graphene oxide composite | HAS_RESULT | MGO qmax for lactic acid 334.45 mg/g | paper-A | p-0055 | direct |  | “The maximum adsorption capacity of MGO for lactic acid (334.45 mg/g) is highly competitive” |
| magnetically modified graphene oxide composite | HAS_RESULT | MGO specific surface area 37.94 m2/g | paper-A | p-0039 | direct |  | “the specific surface area of the MGO was determined to be 37.94 m2/g” |
| magnetically modified graphene oxide composite | HAS_RESULT | PSO fit R2 > 0.99 for all acids | paper-A | p-0059 | direct ⚠ |  | “The experimental data for all acids exhibited an excellent fit with the PSO model (R 2 > 0.99)” |
| magnetically modified graphene oxide composite | HAS_RESULT | PSO k2 lactic 0.007, succinic 0.0023, citric 0.0019 g/mg·min | paper-A | p-0059 | direct ⚠ |  | “The rate constants (k 2) were determined as 0.007, 0.0023, and 0.0019 g/mg·min” |
| magnetically modified graphene oxide composite | HAS_RESULT | RL between 2.3 × 10–6 and 2.8 × 10–3 | paper-A | p-0063 | direct ⚠ |  | “R L values for all investigated acids on both adsorbents across the studied concentration range (10–100 g/L) were between 2.3 × 10–6 and 2.8 × 10–3” |
| magnetically modified graphene oxide composite | HAS_RESULT | below ~3 g/L lactic acid, AC adsorbs slightly more than MGO | paper-A | p-0051 | direct |  | “the activated carbon-based adsorbent exhibits a slightly higher adsorption capacity than the MGO composite” |
| magnetically modified graphene oxide composite | HAS_RESULT | capacity retention after 5 cycles: lactic 91.4%, succinic 87.8%, citric 84.2% | paper-A | p-0067 | direct |  | “The capacity retention rates after the fifth cycle were found to be 87.8% for succinic acid and 84.2% for citric acid.” |
| magnetically modified graphene oxide composite | HAS_RESULT | mean Qe citric acid: MGO 213 vs AC 73.7 mg/g | paper-A | p-0048 | direct |  | “the overall mean adsorption capacity was determined to be 213 mg/g for MGO-based and 73.7 mg/g for AC-based adsorbents” |
| magnetically modified graphene oxide composite | HAS_RESULT | mean Qe succinic acid: MGO 188.6 vs AC 67.8 mg/g | paper-A | p-0045 | direct |  | “the overall mean adsorption capacity (Q e) was determined as 188.6 mg/g for MGO-based and 67.8 mg/g for AC-based adsorbents” |
| MGO qmax for lactic acid 334.45 mg/g | MEASURED_BY | maximum adsorption capacity | paper-A | p-0001 | direct |  | “Lactic acid exhibited the highest maximum adsorption capacity (q max = 334.45 mg/g)” |
| MGO specific surface area 37.94 m2/g | MEASURED_BY | Brunauer–Emmett–Teller method | paper-A | p-0039 | direct |  | “According to BET analysis, the specific surface area of the MGO was determined to be 37.94 m2/g” |
| MGO specific surface area 37.94 m2/g | MEASURED_BY | specific surface area | paper-A | p-0039 | direct |  | “the specific surface area of the MGO was determined to be 37.94 m2/g” |
| PSO k2 lactic 0.007, succinic 0.0023, citric 0.0019 g/mg·min | MEASURED_BY | pseudo-second-order rate constant | paper-A | p-0059 | direct |  | “The rate constants (k 2) were determined as 0.007, 0.0023, and 0.0019 g/mg·min” |
| RL between 2.3 × 10–6 and 2.8 × 10–3 | MEASURED_BY | dimensionless separation factor | paper-A | p-0063 | direct |  | “the dimensionless separation factor (R L) was calculated for each acid–adsorbent system” |
| capacity retention after 5 cycles: lactic 91.4%, succinic 87.8%, citric 84.2% | MEASURED_BY | capacity retention rate | paper-A | p-0015 | direct |  | “The capacity retention rate was calculated by comparing the q e of each cycle to the initial adsorption capacity.” |
| mean Qe succinic acid: MGO 188.6 vs AC 67.8 mg/g | MEASURED_BY | two-sample t-test | paper-A | p-0045 | direct |  | “a two-sample t-test was conducted on the data set presented in Table” |
| MGO qmax for lactic acid 334.45 mg/g | SUPPORTS | adsorption governed by surface chemistry/pore accessibility rather than surface area alone (paper A) | paper-A | p-0040 | direct |  | “its exceptional adsorption capacity (q max = 334.45 mg/g for lactic acid) confirms that the adsorption performance is governed by the synergistic effect of pore” |
| PSO fit R2 > 0.99 for all acids | SUPPORTS | PSO fit confirms chemisorption-controlled adsorption (paper A) | paper-A | p-0059 | direct |  | “This confirms that the adsorption rate is governed by chemical interactions (chemisorption).” |
| PSO k2 lactic 0.007, succinic 0.0023, citric 0.0019 g/mg·min | SUPPORTS | k2 decreases with molecular complexity due to steric hindrance (paper A) | paper-A | p-0060 | direct |  | “A comparative analysis of the rate constants decreasing from lactic (0.007 g/mg·min) and succinic (0.0023 g/mg·min) to citric acid (0.0019 g/mg·min)” |
| magnetic AC qmax for lactic acid 74.6 mg/g | SUPPORTS | adsorption governed by surface chemistry/pore accessibility rather than surface area alone (paper A) | paper-A | p-0040 | direct |  | “which directly underscores that surface area is not the primary determinant of efficiency in these systems” |
| MGO qmax for lactic acid 334.45 mg/g | UNDER_CONDITION | batch adsorption at 25 °C, 10 mg adsorbent in 20 mL, 10–100 g/L, natural pH ~2.0–3.5 | paper-A | p-0010 | direct |  | “The experiments were performed at 25 °C with an agitation speed of 120 rpm, utilizing 10 mg of adsorbent in a 20 mL solution volume.” |
| capacity retention after 5 cycles: lactic 91.4%, succinic 87.8%, citric 84.2% | UNDER_CONDITION | batch adsorption at 25 °C, 10 mg adsorbent in 20 mL, 10–100 g/L, natural pH ~2.0–3.5 | paper-A | p-0015 | indirect |  | “The spent adsorbent was then treated with 0.1 M NaOH as a desorption agent” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | ATTRIBUTED_TO | hydrogen bonding | paper-B | p-0090 | hedged |  | “Carboxyl, phenolic, and hydroxyl groups present in humic acid may participate in hydrogen bonding with phenol molecules” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | ATTRIBUTED_TO | π–π interactions | paper-B | p-0090 | hedged |  | “the graphene-like aromatic domains of rGO may promote π–π interactions with the aromatic ring of phenol” |
| HA–rGO kinetics: PSO R2 0.9939 vs PFO 0.9727 | CONTRADICTS | PSO/PFO fits are empirical and do not establish the chemical nature of adsorption (paper B) | paper-B | p-0100 | direct |  | “These models should be regarded as empirical descriptions of the adsorption-rate data” |
| Freundlich isotherm model | FITS | HA isotherm fit: Freundlich R2 0.9092 vs Langmuir 0.8502 | paper-B | p-0092 | direct |  | “for which the coefficient of determination was R2 = 0.9092, compared with R2 = 0.8502 for the Langmuir model” |
| Langmuir isotherm model | FITS | HA–rGO isotherm fit: Langmuir R2 0.9804 vs Freundlich 0.9515 | paper-B | p-0094 | direct |  | “phenol adsorption on the HA–rGO composite was better described by the Langmuir model, with R2 = 0.9804” |
| pseudo-second-order kinetic model | FITS | HA–rGO kinetics: PSO R2 0.9939 vs PFO 0.9727 | paper-B | p-0098 | direct | C0=7.5 mg/dm3 | “The pseudo-second-order model also showed better agreement for the HA–rGO composite” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | paper-B | p-0094 | direct |  | “The maximum adsorption capacity calculated according to the Langmuir model was 7.10 mg/g for HA–rGO” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | O/C ratio: HA 0.77, rGO 0.36, HA-rGO 0.73 (mechanical mixture expected ~0.66) | paper-B | p-0037 | direct |  | “For the HA-rGO composite, the O/C ratio decreases to 0.73.” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | carbon content HA 47.34 → HA-rGO 55.61 wt.% | paper-B | p-0035 | direct |  | “The carbon content increases to 55.61 wt.%, whereas the oxygen content decreases to 40.79 wt.%.” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | oxygen content HA 48.31 → HA-rGO 40.79 wt.% | paper-B | p-0035 | direct |  | “The carbon content increases to 55.61 wt.%, whereas the oxygen content decreases to 40.79 wt.%.” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | residual mass at 1000 °C: HA 59.21%, HA-rGO 70.03%, rGO 84.23% | paper-B | p-0058 | direct |  | “The residual mass of the initial humic acid is 59.21%, whereas that of the HA-rGO composite increases to 70.03%.” |
| humic acid/reduced graphene oxide composite | HAS_RESULT | Σ(COOH+OH) HA 5.00 → HA-rGO 5.47 mmol/g | paper-B | p-0038 | direct |  | “the HA-rGO composite shows an increase in Σ(COOH + OH) to 5.47 mmol/g compared with the initial humic acid (5.00 mmol/g)” |
| rGO sample (Sigma-Aldrich) | HAS_RESULT | rGO isotherm fit: Langmuir R2 0.9266 vs Freundlich 0.9299 (no clear winner) | paper-B | p-0093 | direct ⚠ |  | “For rGO, the Langmuir and Freundlich models showed comparable agreement with the experimental data” |
| rGO sample (Sigma-Aldrich) | HAS_RESULT | rGO kinetics: PFO R2 0.9973 vs PSO 0.9968 | paper-B | p-0099 | direct ⚠ |  | “The pseudo-first-order model exhibited a marginally higher R2 value of 0.9973 compared with 0.9968 for the pseudo-second-order model.” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | MEASURED_BY | maximum adsorption capacity | paper-B | p-0094 | direct |  | “The maximum adsorption capacity calculated according to the Langmuir model was 7.10 mg/g for HA–rGO” |
| O/C ratio: HA 0.77, rGO 0.36, HA-rGO 0.73 (mechanical mixture expected ~0.66) | MEASURED_BY | atomic oxygen-to-carbon ratio | paper-B | p-0036 | direct |  | “The calculated atomic O/C ratio for the initial humic acid is 0.77” |
| carbon content HA 47.34 → HA-rGO 55.61 wt.% | MEASURED_BY | elemental analysis | paper-B | p-0018 | direct |  | “The contents of carbon, hydrogen, and oxygen were calculated according to the standard procedures provided by the instrument software.” |
| residual mass at 1000 °C: HA 59.21%, HA-rGO 70.03%, rGO 84.23% | MEASURED_BY | residual mass at 1000 °C | paper-B | p-0058 | direct |  | “The residual mass of the initial humic acid is 59.21%” |
| residual mass at 1000 °C: HA 59.21%, HA-rGO 70.03%, rGO 84.23% | MEASURED_BY | thermogravimetric analysis | paper-B | p-0061 | direct |  | “an increase in residual mass at 1000 °C from 59.21 to 70.03%” |
| Σ(COOH+OH) HA 5.00 → HA-rGO 5.47 mmol/g | MEASURED_BY | functional-group titrimetric analysis | paper-B | p-0020 | direct |  | “the total content of carboxyl and phenolic hydroxyl groups was determined by treating the samples with barium hydroxide solution” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | SUPPORTS | results are a preliminary demonstration, not evidence of superiority over existing adsorbents (paper B) | paper-B | p-0103 | direct |  | “The adsorption capacity of HA–rGO is lower than the values reported for some highly porous graphene-based adsorbents [49].” |
| residual mass at 1000 °C: HA 59.21%, HA-rGO 70.03%, rGO 84.23% | SUPPORTS | rGO incorporation improves thermal stability of humic acid (paper B) | paper-B | p-0061 | direct |  | “as confirmed by lower mass losses at the main decomposition stages and an increase in residual mass at 1000 °C from 59.21 to 70.03%” |
| HA–rGO kinetics: PSO R2 0.9939 vs PFO 0.9727 | UNDER_CONDITION | kinetics at initial phenol 7.5 mg/dm3 | paper-B | p-0031 | direct |  | “Kinetic experiments were performed at an initial phenol concentration of 7.5 mg/dm3.” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | UNDER_CONDITION | static batch, 25 °C, phenol 0.5–15 mg/dm3, 0.1 g per 100 mL | paper-B | p-0028 | direct |  | “The experiments were performed under static batch conditions at 25 °C using freshly prepared aqueous phenol solutions with initial concentrations ranging from 0” |

Uncertain:
- R:b3fdf59987: needs_review, subject 'rGO sample (Sigma-Aldrich)' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:f4c2774b5a: needs_review, subject 'magnetically modified graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:665966f364: hedged
- R:387b947927: hedged
- R:2cfa5e2574: needs_review, subject 'rGO sample (Sigma-Aldrich)' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:40dcb0566e: needs_review, subject 'magnetically modified graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:47f2658b4f: needs_review, subject 'magnetically modified graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:f533c77089: indirect
- R:4fc67016ad: hedged

### q_uncertain: Which relations are hedged, cited, flagged, rejected or in conflict?

`uncertain ` → **ok** (23 nodes, 20 edges)

| subject | predicate | object | paper | ¶ | strength | conditions | quote |
|-|-|-|-|-|-|-|-|
| MGO qmax for lactic acid 334.45 mg/g | ATTRIBUTED_TO | hydrogen bonding | paper-A | p-0065 | hedged |  | “which may facilitate supplementary hydrogen bonding interactions with the oxygen-functionalized graphene oxide surface” |
| magnetically modified graphene oxide composite | HAS_RESULT | PSO fit R2 > 0.99 for all acids | paper-A | p-0059 | direct ⚠ |  | “The experimental data for all acids exhibited an excellent fit with the PSO model (R 2 > 0.99)” |
| magnetically modified graphene oxide composite | HAS_RESULT | PSO k2 lactic 0.007, succinic 0.0023, citric 0.0019 g/mg·min | paper-A | p-0059 | direct ⚠ |  | “The rate constants (k 2) were determined as 0.007, 0.0023, and 0.0019 g/mg·min” |
| magnetically modified graphene oxide composite | HAS_RESULT | RL between 2.3 × 10–6 and 2.8 × 10–3 | paper-A | p-0063 | direct ⚠ |  | “R L values for all investigated acids on both adsorbents across the studied concentration range (10–100 g/L) were between 2.3 × 10–6 and 2.8 × 10–3” |
| Langmuir isotherm model | SUPPORTS | Langmuir agreement suggests predominantly monolayer adsorption on homogeneous sites (paper A) | paper-A | p-0069 | hedged |  | “While the Langmuir model demonstrated excellent agreement (R 2 > 0.95), suggesting predominantly monolayer adsorption on a homogeneous distribution of active si” |
| capacity retention after 5 cycles: lactic 91.4%, succinic 87.8%, citric 84.2% | UNDER_CONDITION | batch adsorption at 25 °C, 10 mg adsorbent in 20 mL, 10–100 g/L, natural pH ~2.0–3.5 | paper-A | p-0015 | indirect |  | “The spent adsorbent was then treated with 0.1 M NaOH as a desorption agent” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | ATTRIBUTED_TO | hydrogen bonding | paper-B | p-0090 | hedged |  | “Carboxyl, phenolic, and hydroxyl groups present in humic acid may participate in hydrogen bonding with phenol molecules” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | ATTRIBUTED_TO | π–π interactions | paper-B | p-0090 | hedged |  | “the graphene-like aromatic domains of rGO may promote π–π interactions with the aromatic ring of phenol” |
| humic acid/reduced graphene oxide composite | CHARACTERIZED_BY | elemental analysis | paper-B | p-0018 | direct ⚠ |  | “The elemental composition of the samples was determined using an Elementar Unicube elemental analyzer” |
| humic acid/reduced graphene oxide composite | CHARACTERIZED_BY | functional-group titrimetric analysis | paper-B | p-0020 | direct ⚠ |  | “The content of oxygen-containing functional groups was determined by selective chemical binding followed by titrimetric analysis.” |
| rGO sample (Sigma-Aldrich) | HAS_RESULT | rGO isotherm fit: Langmuir R2 0.9266 vs Freundlich 0.9299 (no clear winner) | paper-B | p-0093 | direct ⚠ |  | “For rGO, the Langmuir and Freundlich models showed comparable agreement with the experimental data” |
| rGO sample (Sigma-Aldrich) | HAS_RESULT | rGO kinetics: PFO R2 0.9973 vs PSO 0.9968 | paper-B | p-0099 | direct ⚠ |  | “The pseudo-first-order model exhibited a marginally higher R2 value of 0.9973 compared with 0.9968 for the pseudo-second-order model.” |
| H-bonding and π–π contributions to phenol adsorption are plausible, not directly demonstrated (paper B) | INVOLVES | π–π interactions | paper-B | p-0104 | hedged |  | “Hydrogen bonding and π–π interactions are therefore considered plausible contributions” |
| HA–rGO composite forms mainly through non-covalent interactions (paper B) | INVOLVES | hydrogen bonding | paper-B | p-0087 | hedged |  | “including π–π stacking of aromatic structures and hydrogen bonding between the functional groups of the components” |
| HA–rGO composite forms mainly through non-covalent interactions (paper B) | INVOLVES | non-covalent interactions | paper-B | p-0081 | hedged |  | “This suggests that composite formation occurs mainly through non-covalent interactions between the components.” |
| HA–rGO composite forms mainly through non-covalent interactions (paper B) | INVOLVES | π–π interactions | paper-B | p-0087 | hedged |  | “including π–π stacking of aromatic structures and hydrogen bonding between the functional groups of the components” |
| humic acid/reduced graphene oxide composite | OUTPERFORMS | rGO sample (Sigma-Aldrich) | paper-B | p-0089 | direct ⚠ | adsorbate=phenol; criterion=adsorption capacity; range=0.5–15 mg/dm3 | “the HA-rGO composite exhibited a higher adsorption capacity toward phenol than the initial humic acid and rGO” |
| humic acid/reduced graphene oxide composite | PREPARED_FROM | rGO sample (Sigma-Aldrich) | paper-B | p-0016 | direct ⚠ |  | “After stabilization of the system, reduced graphene oxide was introduced into the suspension.” |
| Langmuir qm phenol: HA–rGO 7.10, rGO 6.02, HA 4.65 mg/g | SUPPORTS | results are a preliminary demonstration, not evidence of superiority over existing adsorbents (paper B) | paper-B | p-0103 | direct |  | “The adsorption capacity of HA–rGO is lower than the values reported for some highly porous graphene-based adsorbents [49].” |
| humic acid/reduced graphene oxide composite | USES | ultrasonic treatment | paper-B | p-0015 | direct ⚠ |  | “The composite was synthesized by ultrasonic treatment in an aqueous medium.” |

Uncertain:
- R:b3fdf59987: needs_review, subject 'rGO sample (Sigma-Aldrich)' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:6ef1c181b6: hedged
- R:f4c2774b5a: needs_review, subject 'magnetically modified graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:665966f364: hedged
- R:47f2658b4f: needs_review, subject 'magnetically modified graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:34b3eca17d: hedged
- R:387b947927: hedged
- R:f533c77089: indirect
- R:e745caf967: hedged
- R:b113e63e89: hedged
- R:2cfa5e2574: needs_review, subject 'rGO sample (Sigma-Aldrich)' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:d864fd647c: needs_review, subject 'humic acid/reduced graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:05577cb609: needs_review, subject 'humic acid/reduced graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:b2e05b45a0: needs_review, object 'rGO sample (Sigma-Aldrich)' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:7dbf743e4e: needs_review, object 'rGO sample (Sigma-Aldrich)' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:4e1ef8e791: needs_review, subject 'humic acid/reduced graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:3fab2701d7: hedged
- R:40dcb0566e: needs_review, subject 'magnetically modified graphene oxide composite' not named in the evidence paragraph (pronoun/inference?) -> needs_review
- R:4fc67016ad: hedged
