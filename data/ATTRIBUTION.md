# Test data attribution

Both articles are open access under CC BY 4.0 and are redistributed unchanged (JATS XML as served by Europe PMC / NCBI PMC).
`src/make_case.py` converts them into a case shaped like the challenge description (paragraph JSON files, manifest, publisher XML).

| file | article | license |
|-|-|-|
| raw/PMC13613405.xml | Ekinci E., Uslu H., Bayazit Ş.S., Yetişen M. "Comparative Adsorption of Mono-, Di-, and Tricarboxylic Acids on Magnetically Modified Graphene Oxide: Influence of Molecular Structure on Adsorption Behavior." ACS Omega 2026, 11(37), 55950–55965. doi:10.1021/acsomega.6c05759 | CC BY 4.0 |
| raw/PMC13514153.xml | Zhakina A.K., Arnt O.V., Vassilets Y.P., Zhakin A.M., Muldakhmetov Z. "Structural, Thermal, and Phenol Adsorption Properties of a Humic Acid/Reduced Graphene Oxide Composite." Materials 2026. doi:10.3390/ma19163371 | CC BY 4.0 |

`case1_agent_work/` holds the extraction files written by the agent (Claude) after reading the ingested paragraphs, following
`submission/SKILL.md`. They are inputs to the reproduction, not outputs of a script, and are not official answers to any platform case.
