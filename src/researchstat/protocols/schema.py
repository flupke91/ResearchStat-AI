"""Pydantic schemas for statistical protocols."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class StatisticalMethod(str, Enum):
    DESCRIPTIVE = "descriptive"
    INDEPENDENT_T_TEST = "independent_t_test"
    PAIRED_T_TEST = "paired_t_test"
    ONE_WAY_ANOVA = "one_way_anova"
    TWO_WAY_ANOVA = "two_way_anova"
    MANN_WHITNEY_U = "mann_whitney_u"
    KRUSKAL_WALLIS = "kruskal_wallis"
    PEARSON_CORRELATION = "pearson_correlation"
    SPEARMAN_CORRELATION = "spearman_correlation"
    LINEAR_REGRESSION = "linear_regression"


class VarianceAssumption(str, Enum):
    EQUAL = "equal_variance"
    UNEQUAL = "unequal_variance"
    NOT_APPLICABLE = "not_applicable"


class PosthocMethod(str, Enum):
    NONE = "none"
    TUKEY_HSD = "tukey_hsd"
    DUNN = "dunn"


class MissingPolicy(str, Enum):
    COMPLETE_CASE = "complete_case"


class EffectSize(str, Enum):
    NONE = "none"
    COHENS_D = "cohens_d"
    ETA_SQUARED = "eta_squared"
    EPSILON_SQUARED = "epsilon_squared"
    PEARSON_R = "pearson_r"
    SPEARMAN_RHO = "spearman_rho"
    RANK_BISERIAL = "rank_biserial"
    R_SQUARED = "r_squared"


class Assumptions(BaseModel):
    observations_independent: bool = True
    normality_checked: bool = False
    variance: VarianceAssumption = VarianceAssumption.NOT_APPLICABLE


class Protocol(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$", min_length=1)
    version: int = Field(default=1, ge=1)
    method: StatisticalMethod
    assumptions: Assumptions
    posthoc: PosthocMethod = PosthocMethod.NONE
    alpha: float = Field(default=0.05, gt=0, lt=1)
    missing_policy: MissingPolicy = MissingPolicy.COMPLETE_CASE
    effect_size: EffectSize = EffectSize.NONE
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_method_specific_fields(self) -> "Protocol":
        method = self.method
        variance = self.assumptions.variance

        if method is StatisticalMethod.INDEPENDENT_T_TEST:
            if variance is VarianceAssumption.NOT_APPLICABLE:
                raise ValueError(
                    "independent_t_test requires equal_variance or unequal_variance"
                )
            if self.assumptions.normality_checked is not True:
                raise ValueError("independent_t_test requires normality_checked=True")

        if method is StatisticalMethod.PAIRED_T_TEST:
            if variance is not VarianceAssumption.NOT_APPLICABLE:
                raise ValueError("paired_t_test does not use a variance assumption")
            if self.assumptions.normality_checked is not True:
                raise ValueError("paired_t_test requires normality_checked=True")

        if method in {
            StatisticalMethod.DESCRIPTIVE,
            StatisticalMethod.MANN_WHITNEY_U,
            StatisticalMethod.PEARSON_CORRELATION,
            StatisticalMethod.SPEARMAN_CORRELATION,
            StatisticalMethod.LINEAR_REGRESSION,
        }:
            if variance is not VarianceAssumption.NOT_APPLICABLE:
                raise ValueError(f"{method.value} does not use a variance assumption")
            if self.posthoc is not PosthocMethod.NONE:
                raise ValueError(f"{method.value} must not define a posthoc method")

        if method is StatisticalMethod.ONE_WAY_ANOVA:
            if variance is not VarianceAssumption.EQUAL:
                raise ValueError("one_way_anova_tukey requires equal_variance")
            if self.assumptions.normality_checked is not True:
                raise ValueError("one_way_anova requires normality_checked=True")
            if self.posthoc is not PosthocMethod.TUKEY_HSD:
                raise ValueError("one_way_anova_v1 requires posthoc=tukey_hsd")

        if method is StatisticalMethod.TWO_WAY_ANOVA:
            if variance is not VarianceAssumption.EQUAL:
                raise ValueError("two_way_anova requires equal_variance")
            if self.assumptions.normality_checked is not True:
                raise ValueError("two_way_anova requires normality_checked=True")
            if self.posthoc is not PosthocMethod.NONE:
                raise ValueError("two_way_anova_v1 does not define a posthoc method")

        if method is StatisticalMethod.KRUSKAL_WALLIS:
            if self.posthoc is not PosthocMethod.DUNN:
                raise ValueError("kruskal_wallis_v1 requires posthoc=dunn")

        return self
