# A/B testing notes

The dashboard compares binary activation outcomes for independent control and treatment groups. The implementation uses `statsmodels.stats.proportion.proportions_ztest` for a two-sample normal z-test of proportions. The null hypothesis is equality of the two proportions; the module reports z-statistic, two-sided p-value, absolute lift, relative lift, and a 95% confidence interval for the difference in proportions.

The p-value is evidence against the null hypothesis under the test assumptions; it is not the probability that the hypothesis is true. Results should be interpreted with sample size, experiment design, guardrails, and pre-registered decision rules. For small samples or sparse outcomes, the readout should flag that the normal approximation may be weak.

References:

- https://www.statsmodels.org/devel/generated/statsmodels.stats.proportion.proportions_ztest.html
- https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing/python
