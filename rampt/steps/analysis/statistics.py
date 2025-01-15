#!/usr/bin/env python3

"""
Analyze the statistical significance of a population.
"""

# Imports
from scipy import stats
from statsmodels.sandbox.stats.multicomp import multipletests
from rampt.helpers.types import Array
from rampt.helpers.logging import *


def choose_test(X: Array, groups: Array = None, paired: bool = False) -> str:
	test_name = None
	# Check for normality
	X_normal = stats.shapiro(X).pvalue > 0.05
	if paired:
		if X_normal:
			test_name = "Paired-sample t-test"
		else:
			test_name = "Wilcoxon signed-rank test"
	else:
		if X_normal:
			test_name = "One-sample t-test"
		else:
			test_name = "Wilcoxon matched pairs test"

	return test_name


def execute_test(
	x: Array,
	y: Array = None,
	test: str = None,
	axis: int = 0,
	alternative_hypothesis: str = "two-sided",
	cutoff: float = 0.05,
	multiple_testing_correction: str = "bonferroni",
	*args,
) -> bool:
	match test:
		case "Paired-sample t-test":
			p_values = stats.ttest_rel(x, y, axis=axis, alternative=alternative_hypothesis, *args)
		case "Wilcoxon signed-rank test":
			p_values = stats.wilcoxon(x, y, axis=axis, alternative=alternative_hypothesis, *args)
		case "ttest_ind":
			p_values = stats.ttest_ind(
				x, y, equal_var=False, axis=axis, alternative=alternative_hypothesis, *args
			)
		case "One-sample t-test":
			if y:
				warn("Passed y vector for a one-sample test.", UserWarning)
			p_values = stats.ttest_1samp(x, axis=axis, alternative=alternative_hypothesis)
		case "Wilcoxon matched pairs test":
			if y:
				warn("Passed y vector for a one-sample test.", UserWarning)
			p_values = stats.wilcoxon(x, axis=axis, alternative=alternative_hypothesis, *args)

	if multiple_testing_correction:
		passed, p_values, *_ = multipletests(
			p_values, alpha=cutoff, method=multiple_testing_correction.lower()
		)

	return p_values


def p_val_to_star(p: float) -> str:
	"""
	Generate star notation from p-value.

	:param p: p-value
	:type p: float
	:return: Star notation of p-value
	:rtype: str
	"""
	if p < 1e-4:
		return "****"
	elif p < 1e-3:
		return "***"
	elif p < 1e-2:
		return "**"
	elif p < 5e-2:
		return "*"
	else:
		return "ns"
