from unittest.mock import patch

import pandas as pd
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

from jobscope.features import (
    apply_cv_search_and_get_results,
    drop_rows_with_missing_values_on_target_series,
    get_best_max_features,
    vectorize_train_data_and_get_trained_vectorizer,
)

# 5 exemples par classe pour satisfaire StratifiedKFold(n_splits=5), avec des mots
# repetes (min_df=2) pour que TfidfVectorizer ne se retrouve pas avec un vocabulaire vide.
FIXTURE_X = pd.Series(
    [
        "python developer java",
        "python developer sql",
        "python manager node",
        "python intern css",
        "python lead ruby",
        "marketing sales growth",
        "marketing sales plan",
        "marketing lead ads",
        "marketing growth hack",
        "marketing plan brand",
    ]
)
FIXTURE_Y = pd.Series(["a", "a", "a", "a", "a", "b", "b", "b", "b", "b"])


def test_apply_cv_search_and_get_results_returns_one_entry_per_candidate() -> None:
    candidates = [1, 2, None]

    results = apply_cv_search_and_get_results(FIXTURE_X, FIXTURE_Y, candidates)

    assert set(results.keys()) == set(candidates)


def test_apply_cv_search_and_get_results_values_are_mean_std_float_pairs() -> None:
    results = apply_cv_search_and_get_results(FIXTURE_X, FIXTURE_Y, [1, 2])

    for value in results.values():
        assert isinstance(value, tuple)
        assert len(value) == 2
        mean, std = value
        assert isinstance(mean, float)
        assert isinstance(std, float)


def test_apply_cv_search_and_get_results_raises_on_nan_target() -> None:
    y_with_nan = FIXTURE_Y.copy()
    y_with_nan.iloc[0] = None

    with pytest.raises(ValueError):
        apply_cv_search_and_get_results(FIXTURE_X, y_with_nan, [1, 2])


def test_get_best_max_features_returns_clear_winner_when_others_are_far_below() -> None:
    cv_results = {50: (0.5, 0.01), 100: (0.9, 0.01), None: (0.6, 0.01)}

    assert get_best_max_features(cv_results) == 100


def test_get_best_max_features_picks_smallest_among_statistically_tied_candidates() -> None:
    # Le meilleur score brut est 300 (0.85), mais son seuil (0.85 - 0.10 = 0.75) est
    # aussi depasse par 50 et 100 : la regle du 1-std doit retenir le plus simple, 50.
    cv_results: dict[int | None, tuple[float, float]] = {50: (0.80, 0.05), 100: (0.82, 0.05), 300: (0.85, 0.10)}

    assert get_best_max_features(cv_results) == 50


def test_get_best_max_features_prefers_smaller_int_over_none_when_both_eligible() -> None:
    # None (0.82) est le meilleur score brut, mais 50 reste eligible (seuil = 0.77).
    # None ne doit jamais etre prefere a un entier eligible plus simple.
    cv_results = {50: (0.80, 0.05), None: (0.82, 0.05)}

    assert get_best_max_features(cv_results) == 50


def test_get_best_max_features_returns_none_when_it_is_the_only_eligible_candidate() -> None:
    cv_results = {50: (0.10, 0.01), None: (0.90, 0.01)}

    assert get_best_max_features(cv_results) is None


def test_drop_rows_with_missing_values_on_target_series_keeps_x_and_y_aligned() -> None:
    y = pd.Series(["a", None, "b"])

    X_clean, y_clean = drop_rows_with_missing_values_on_target_series(FIXTURE_X.iloc[:3], y)

    assert list(X_clean.index) == list(y_clean.index) == [0, 2]


# 12 lignes (6 par classe) : StratifiedKFold(n_splits=5) exige au moins 5 exemples par
# classe, meme apres avoir retire la ligne home_office_policy manquante (6 "x" / 5 "y").
FIXTURE_DF = pd.DataFrame(
    {
        "intitule": ["developer informatique"] * 6 + ["chef marketing"] * 6,
        "description": [
            "python developer java",
            "python developer sql",
            "python manager node",
            "python intern css",
            "python lead ruby",
            "python architect go",
            "marketing sales growth",
            "marketing sales plan",
            "marketing lead ads",
            "marketing growth hack",
            "marketing plan brand",
            "marketing director brand",
        ],
        "seniority": ["a"] * 6 + ["b"] * 6,
        "home_office_policy": ["x"] * 6 + ["y"] * 5 + [None],
    }
)
TARGET_COLUMNS = ["seniority", "home_office_policy"]


def test_preprocess_data_returns_one_entry_per_target_with_consistent_feature_dimensions() -> None:
    results, intitule_vectorizer = vectorize_train_data_and_get_trained_vectorizer(FIXTURE_DF, FIXTURE_DF, TARGET_COLUMNS, [1, 2])

    assert set(results.keys()) == set(TARGET_COLUMNS)
    assert isinstance(intitule_vectorizer, TfidfVectorizer)

    assert results["seniority"].preprocessed_df.shape[0] == 12
    assert results["home_office_policy"].preprocessed_df.shape[0] == 11  # 1 ligne NaN retiree

    for target in TARGET_COLUMNS:
        expected_columns = len(intitule_vectorizer.get_feature_names_out()) + len(
            results[target].description_vectorizer.get_feature_names_out()
        )
        assert results[target].preprocessed_df.shape[1] == expected_columns


def test_preprocess_data_shares_one_vectorizer_when_targets_agree_on_max_features() -> None:
    with patch("jobscope.features.get_best_max_features", side_effect=[50, 50]):
        results, _ = vectorize_train_data_and_get_trained_vectorizer(FIXTURE_DF, FIXTURE_DF, TARGET_COLUMNS, [1, 2])

    assert results["seniority"].description_vectorizer is results["home_office_policy"].description_vectorizer


def test_preprocess_data_uses_separate_vectorizers_when_targets_disagree_on_max_features() -> None:
    with patch("jobscope.features.get_best_max_features", side_effect=[1, 2]):
        results, _ = vectorize_train_data_and_get_trained_vectorizer(FIXTURE_DF, FIXTURE_DF, TARGET_COLUMNS, [1, 2])

    assert results["seniority"].description_vectorizer is not results["home_office_policy"].description_vectorizer
    assert results["seniority"].description_vectorizer.max_features == 1
    assert results["home_office_policy"].description_vectorizer.max_features == 2
