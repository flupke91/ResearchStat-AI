# ResearchStat AI Open Source Reuse Map

Updated: 2026-08-06  
Status: research baseline, to be re-validated before each dependency is pinned

## 1. Why This Map Exists

ResearchStat AI must not reinvent mature statistical or plotting infrastructure. The
project reuses established open source libraries for numerical methods and figure
rendering, and builds its own value on top of them:

- statistical protocol standardization
- reproducible analysis records
- cross-engine validation
- AI planning constrained by the protocol registry
- professional-grade publication figures driven by a reproducible spec

All reuse must respect licenses, keep provenance, and never reverse-engineer
commercial software internals.

## 2. Python Stack

| Component | Candidate | Why | License |
| - | - | - | - |
| Base plotting | `matplotlib` | mature vector output, precise layout control | PSF-based |
| Statistical plots | `seaborn` | box, violin, scatter, regression and distribution plots | BSD-3-Clause |
| Significance annotation | `statannotations` | stars and p-value annotations with smart stacking | MIT |
| Journal styles | `SciencePlots` | Nature/IEEE/science styles, colorblind-safe cycles | MIT |
| Journal-ready toolkit | `cnsplots` | multi-panel, survival, forest, SVG with editable text | BSD-3-Clause |
| Statistics | `scipy`, `statsmodels`, `pingouin`, `scikit-posthocs` | core tests, ANOVA, regression, effect sizes, post-hoc tests | BSD-3-Clause / MIT |

## 3. R Stack

| Component | Candidate | Why | License |
| - | - | - | - |
| Base plotting | `ggplot2` | grammar of graphics, reproducible plot objects | MIT |
| Publication-ready plots | `ggpubr` | statistical annotations and publication themes | GPL-2/GPL-3 |
| Prism-like visual theme | `ggprism` | public theme and p-value conventions inspired by Prism | GPL-3 |
| Panel composition | `patchwork` | multi-panel figures | MIT |
| Editable vector output | `svglite` | SVG with text preserved as text objects | GPL-2/GPL-3 |

## 4. Workflow References

The following projects are studied as workflow and UX references, not copied:

- JASP: free open source frequentist and Bayesian statistics software.
- jamovi: free open source statistics GUI built around R.
- ggpubr / statannotations: how statistical results are annotated directly on plots.
- cnsplots: how journal-level styling, multi-panel layouts, and SVG editability are
  packaged into a simple API.

Detailed project-level lessons from AStats, cross-tool-statistical-verification,
rmcp, AutoML Stat MCP, MedStat, JASP and jamovi are maintained in
`docs/RESEARCH_LESSONS.md`.

## 5. Professional Figure Baseline

V1 figure output must meet the following capability baseline:

1. Vector output: SVG and PDF with text preserved as editable text objects.
2. Raster output: TIFF at 300 DPI minimum, configurable up to 600 DPI.
3. Journal-ready themes: controlled font size, axes, margins, and panel spacing.
4. Colorblind-safe palettes and accessible contrast.
5. Multi-panel layouts with automatic panel labels.
6. Statistical annotations: stars, p values, adjusted p values, group comparisons.
7. Error bars: SD, SEM, or CI, explicitly labeled.
8. Point overlays: scatter, jitter, and individual points on box/violin plots.
9. Fit lines and confidence bands for correlation and regression plots.
10. Reproducible figure spec: every output has `figure_spec.json` describing data,
    statistics, theme, and rendering parameters.

## 6. Decisions and Risks

- Use matplotlib + seaborn as the primary renderer; do not write a custom plotting
  engine.
- Use statannotations for significance annotations instead of hand-rolling layout
  logic.
- Use SciencePlots or a derived internal theme as the default journal style; avoid
  requiring LaTeX in V1 by using the no-latex styles.
- Evaluate cnsplots before pinning it. It is promising but young, so it must pass
  golden-image and SVG-editing tests before becoming a core dependency.
- The R figure path is optional in V1. If ggprism or ggpubr is bundled into the
  delivered product, legal review is required because GPL constraints affect the
  overall distribution license.
- Visual regressions are guarded by golden-image tests, not by manual inspection
  alone.

## 7. Pinned Versions From Phase 3

The following versions were installed in the project virtual environment and
validated by the Phase 3 test suite:

A `requirements.lock` file is maintained at the repository root for reproducible
installs.

| Package | Version |
| - | - |
| Python | 3.14.3 |
| numpy | 2.5.1 |
| pandas | 3.0.5 |
| scipy | 1.18.0 |
| statsmodels | 0.14.6 |
| scikit-posthocs | 0.14.0 |
| matplotlib | 3.11.1 |
| seaborn | 0.13.2 |
| statannotations | 0.7.2 |
| SciencePlots | 2.2.2 |
| pydantic | 2.13.4 |
| PyYAML | 6.0.3 |
| mcp | 2.0.0 |

### R Runtime

| Package | Version |
| - | - |
| R | 4.6.1 |
| jsonlite | 2.0.0 |
| car | 3.1.5 |

The R engine uses base R `stats` for most methods. Dunn post-hoc p-values are
implemented in the R script with the Holm correction so the engine does not
depend on `dunn.test`.
