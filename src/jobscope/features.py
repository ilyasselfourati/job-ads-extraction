from dataclasses import dataclass

import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

MAX_FEATURES_CANDIDATES = [50, 100, 150, 200, 300, None]

def apply_cv_search_and_get_results(
    X: pd.Series,
    y: pd.Series,
    max_features_candidates: list[int|None] = MAX_FEATURES_CANDIDATES,
) -> dict[int|None, tuple[float,float]]:
    if y.isna().any():
        raise ValueError("Target variable contains NaN values. Please handle missing values before proceeding.")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_results = {}

    for max_features in max_features_candidates:
        pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(min_df=2, max_features=max_features)),
                ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        )
        scores = cross_val_score(pipeline, X, y, cv=cv, scoring="f1_macro")
        cv_results[max_features] = (scores.mean(), scores.std())
    return cv_results

def get_best_max_features(
    cv_results: dict[int|None, tuple[float,float]]
) -> int|None:
    best_mean, best_std = max(cv_results.values(), key=lambda ms: ms[0])
    threshold = best_mean - best_std

    eligible = [mf for mf, (mean, _) in cv_results.items() if mean >= threshold]
    best_max_features = min(eligible, key=lambda mf: mf if mf is not None else float("inf"))
    return best_max_features


def drop_rows_with_missing_values_on_target_series(
    X: pd.Series, 
    y: pd.Series
) -> tuple[pd.Series, pd.Series]:
    mask = y.notna()
    return X[mask], y[mask]

@dataclass
class TargetPreprocessingResult:
    preprocessed_df : pd.DataFrame
    description_vectorizer : TfidfVectorizer

def vectorize_train_data_and_get_trained_vectorizer(
    features_data:pd.DataFrame,
    targets_data:pd.DataFrame,
    target_columns: list[str],
    max_features_candidates: list[int|None] = MAX_FEATURES_CANDIDATES
) -> tuple[dict[str, TargetPreprocessingResult], TfidfVectorizer]:
    intitule_vectorizer = TfidfVectorizer(min_df=2)
    intitule_vectorizer.fit(features_data["intitule"])

    best_max_features_by_target: dict[str, int | None] = {}
    cleaned_description_by_target: dict[str, pd.Series] = {}

    for target in target_columns:
        description_clean, y_clean = drop_rows_with_missing_values_on_target_series(
            features_data["description"], targets_data[target]
        )
        cleaned_description_by_target[target] = description_clean
        cv_results = apply_cv_search_and_get_results(description_clean, y_clean, max_features_candidates)
        best_max_features_by_target[target] = get_best_max_features(cv_results)

    distinct_max_features = set(best_max_features_by_target.values())
    if len(distinct_max_features) == 1:
        shared_vectorizer = TfidfVectorizer(min_df=2, max_features=next(iter(distinct_max_features)))
        shared_vectorizer.fit(features_data["description"])
        description_vectorizer_by_target = {target: shared_vectorizer for target in target_columns}
    else:
        description_vectorizer_by_target = {}
        for target, max_features in best_max_features_by_target.items():
            vectorizer = TfidfVectorizer(min_df=2, max_features=max_features)
            vectorizer.fit(features_data["description"])
            description_vectorizer_by_target[target] = vectorizer

    results: dict[str, TargetPreprocessingResult] = {}
    for target in target_columns:
        description_clean = cleaned_description_by_target[target]
        description_vectorizer = description_vectorizer_by_target[target]

        intitule_features = intitule_vectorizer.transform(features_data.loc[description_clean.index, "intitule"])
        description_features = description_vectorizer.transform(description_clean)

        combined_features = hstack([intitule_features, description_features]).toarray()
        feature_names = [
            f"intitule__{name}" for name in intitule_vectorizer.get_feature_names_out()
        ] + [
            f"description__{name}" for name in description_vectorizer.get_feature_names_out()
        ]

        results[target] = TargetPreprocessingResult(
            preprocessed_df=pd.DataFrame(combined_features, index=description_clean.index, columns=feature_names),
            description_vectorizer=description_vectorizer,
        )

    return results, intitule_vectorizer