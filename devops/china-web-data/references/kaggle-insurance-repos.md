# Kaggle Insurance Prediction — Verified Repos (May 2026)

GitHub API search patterns and verified high-quality repos for insurance prediction competitions.

## Search Patterns

```bash
# Life insurance risk classification
curl "https://api.github.com/search/repositories?q=kaggle+prudential+life+insurance&sort=stars&order=desc&per_page=10"

# Insurance claim prediction (imbalanced binary classification)
curl "https://api.github.com/search/repositories?q=kaggle+porto+seguro+solution&sort=stars&order=desc&per_page=10"

# Cross-sell prediction (health → vehicle)
curl "https://api.github.com/search/repositories?q=health+insurance+cross+sell+kaggle&sort=stars&order=desc&per_page=10"

# Ensemble approaches
curl "https://api.github.com/search/repositories?q=insurance+claim+prediction+kaggle+catboost+lightgbm&sort=stars&order=desc&per_page=10"
```

## Verified High-Quality Repos

### Prudential Life Insurance Assessment
| Repo | Stars | Rank | Key Techniques |
|------|-------|------|----------------|
| `AntonUBC/Prudential-Life-Insurance-Assessment` | 39★ | Top 3% (65th) | Bumper features, 4-fold stacking, XGB+RF+ET ensemble, regression→ordinal offset mapping |
| `PedroMDuarte/kaggle-prudential-201512` | 6★ | Top 4% (94th) | Step-by-step notebooks (EDA→missing→interactions→modeling→ensemble) |
| `ningningliu/Prudential-Life-Insurance-Assessment` | 5★ | — | Chinese README, GBM+RF+ET pipeline |
| `ffyu/Kaggle-Prudential-Life-Insurance-Assesment` | 3★ | — | Methodology for completing Kaggle in 1 week |

### Porto Seguro Safe Driver Prediction (Insurance Claims)
| Repo | Stars | Rank | Key Techniques |
|------|-------|------|----------------|
| `xiaozhouwang/kaggle-porto-seguro` | 155★ | 🥈 2nd | Prediction-as-feature (fea_eng0.py), NN+GBDT ensemble, rank average |
| `lorenzoridolfi/reproduce_porto_winner_solution` | 10★ | Champion | Winner solution reverse engineering, denoising autoencoder |

### Health Insurance Cross-Sell
| Repo | Stars | Key Techniques |
|------|-------|----------------|
| `ntclai/Health-Insurance-Cross-Sell-Prediction` | 2★ | Full EDA→Modeling notebook, LR→RF→XGBoost comparison |
| `anthonykeys/Health-Insurance-Cross-Sell-Prediction` | 0★ | Alternative implementation |

## Technique Summary (for bank insurance purchase prediction)

1. **Missing indicators** — Create binary `col_isnull` features so the model learns missingness as a signal
2. **Prediction-as-feature** — Train a lightweight XGBoost on feature groups, use CV out-of-fold predictions as new input features
3. **Target encoding in CV** — Compute target encodings within each fold to prevent data leakage
4. **Rank Average fusion** — More robust than weighted average when model output scales differ
5. **NN + GBDT hybrid** — 3-layer Dense NN (256→128→64) + LightGBM/XGBoost, complementary strengths
6. **Ordinal offset mapping** — For multi-class ordinal targets: regressor predictions + quantile-based offset → class mapping
