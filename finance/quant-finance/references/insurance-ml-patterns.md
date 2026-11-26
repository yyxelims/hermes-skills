# Insurance / Production ML Patterns

Lessons from building a bank insurance cross-sell prediction model (May 2026).

## Missing Value Strategy: Sentinels + Binary Indicators

**DO NOT** use median/mode imputation for tree-based models. It destroys the signal in missingness.

**DO**: Fill with sentinel values + add `_isnull` binary columns:

| Column type | Fill value | isnull col? |
|-------------|-----------|-------------|
| Asset/product numeric (基金_万, 理财_万…) | 0 (missing = doesn't own) | ✓ |
| Age | 0 | ✓ |
| Other numeric | -1 (sentinel) | ✓ |
| Categorical | "缺失" | ✓ |

Tree models naturally split on `-1` to separate missing vs present — this is a free feature.

### Winsorize protection

When winsorizing, exclude sentinel values (-1, 0 for asset columns) from quantile calculation AND from clipping. Otherwise sentinels get collapsed.

```python
# Exclude sentinels from quantile calc
valid = df[col][(df[col] != -1) & (df[col] != 0)]  # for asset cols
# Only clip non-sentinel values
mask = (df[col] != -1) & (df[col] != 0)
df.loc[mask, col] = df.loc[mask, col].clip(lower, upper)
```

## String Key Joining: Robust Cleaning

When joining tables on ID columns (e.g. customer manager ID), naive `astype(str)` fails on:
- Float→str: `12345.0` vs `12345`
- TS prefix: `TS12345` vs `12345`
- Whitespace, NaN→`"nan"`, None→`"None"`

**Use a robust _clean_key function**:

```python
def _clean_key(series):
    s = series.astype(str).str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)   # float artifact
    s = s.str.replace(r"^TS", "", regex=True)    # prefix
    s = s.replace(["nan", "None", "", "NaN"], pd.NA)
    return s
```

Create temporary `_clean` columns for the join, drop them after merge. Log match statistics to diagnose join failures immediately.

## Threshold Optimization: F-beta for Production

Kaggle optimizes for AUC; production optimizes for business goals.

**F-beta** lets you weight precision vs recall:

| beta | Meaning | Use case |
|------|---------|----------|
| 0.5 | Precision 2× Recall | "推一个中一个" — limited manager capacity |
| 1.0 | Equal (F1) | Balanced |
| 2.0 | Recall 2× Precision | "广撒网不漏买家" — abundant capacity |

```python
from sklearn.metrics import fbeta_score
# Search: F2 searches 0.05~0.65 (lower threshold = more positives)
# Search: F0.5 searches 0.15~0.85 (higher threshold = fewer but more accurate)
for t in threshold_range:
    fb = fbeta_score(y_true, y_prob > t, beta=beta)
```

Also: sort model comparison by the metric that matters (Precision or Recall), not AUC.

## Prediction-as-Feature (Kaggle Porto Seguro Technique)

Train a lightweight model (LightGBM) with 5-fold CV on all features. The OOF predictions become a new feature column. This captures non-linear interactions that individual models might miss.

```python
skf = StratifiedKFold(n_splits=5)
oof = np.zeros(len(df))
for train_idx, val_idx in skf.split(X, y):
    model = LGBMClassifier(max_depth=5, n_estimators=100)
    model.fit(X.iloc[train_idx], y.iloc[train_idx])
    oof[val_idx] = model.predict_proba(X.iloc[val_idx])[:, 1]
df["pred_lgb_oof"] = oof
```

No data leakage: each row's prediction comes from a fold where it was held out.

## NN as GBDT Complement

For tabular data with 100-500 features, sklearn's `MLPClassifier` (256→128→64) adds value:
- GBDT excels at sparse, discrete boundaries
- NN excels at smooth non-linear surfaces
- Stacking both almost always beats either alone

No TensorFlow needed — sklearn MLPClassifier + StandardScaler is sufficient.

## CSV Output for String IDs

To prevent Excel from auto-converting string IDs to numbers:
```python
import csv
df.to_csv("out.csv", quoting=csv.QUOTE_NONNUMERIC)
```

## Kaggle Reference Code Workflow

When researching how others solve a problem:
1. Search GitHub API: `https://api.github.com/search/repositories?q=kaggle+{topic}&sort=stars`
2. Clone top 3-5 repos with `git clone --depth 1`
3. Read README for techniques, then dive into key `.py` files
4. Extract reusable patterns (feature engineering, ensemble architecture, threshold tuning)
