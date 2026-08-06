#!/usr/bin/env Rscript

if (nzchar(Sys.getenv("R_LIBS_USER"))) {
  .libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))
}

suppressPackageStartupMessages({
  library(jsonlite)
  library(car)
})

args <- commandArgs(trailingOnly = TRUE)
params_path <- args[1]
data_path <- args[2]
output_path <- args[3]

params <- fromJSON(params_path, simplifyVector = TRUE)
df <- read.csv(data_path, stringsAsFactors = FALSE, check.names = FALSE)
protocol_id <- params$protocol_id
method <- params$method
outcome <- params$outcome
group_col <- params$group
factor2_col <- params$factor2
paired_by_col <- params$paired_by
predictors <- unlist(params$predictors, use.names = FALSE)
alpha <- params$alpha
if (is.null(alpha) || is.na(alpha)) alpha <- 0.05

complete_case <- function(data, cols) {
  data[stats::complete.cases(data[, cols, drop = FALSE]), , drop = FALSE]
}

as_num <- function(x) {
  as.numeric(as.character(x))
}

sorted_labels <- function(x) {
  sort(unique(as.character(x)))
}

shapiro_checks <- function(groups, alpha) {
  checks <- list()
  for (label in names(groups)) {
    values <- groups[[label]]
    if (length(values) < 3) {
      checks[[length(checks) + 1L]] <- list(
        name = paste0("shapiro_wilk:", label),
        passed = NA,
        statistic = NA,
        p_value = NA,
        detail = "n<3, test not computed"
      )
    } else {
      test <- shapiro.test(values)
      checks[[length(checks) + 1L]] <- list(
        name = paste0("shapiro_wilk:", label),
        passed = test$p.value >= alpha,
        statistic = as.numeric(test$statistic),
        p_value = as.numeric(test$p.value),
        detail = ""
      )
    }
  }
  checks
}

levene_check <- function(groups, alpha) {
  if (length(groups) < 2) {
    return(list())
  }
  sizes <- lengths(groups)
  if (any(sizes < 3)) {
    return(list(list(
      name = "levene_equal_variance",
      passed = NA,
      statistic = NA,
      p_value = NA,
      detail = "requires at least 3 observations per group, test not computed"
    )))
  }
  values <- unlist(groups, use.names = FALSE)
  labels <- rep(names(groups), times = sizes)
  test <- car::leveneTest(values, factor(labels), center = median)
  p_value <- test$`Pr(>F)`[1]
  list(list(
    name = "levene_equal_variance",
    passed = p_value >= alpha,
    statistic = as.numeric(test$`F value`[1]),
    p_value = as.numeric(p_value),
    detail = ""
  ))
}

assumption_warnings <- function(checks, warnings) {
  for (check in checks) {
    if (isTRUE(check$passed == FALSE)) {
      p_text <- ifelse(is.na(check$p_value), "n/a",
                       sprintf("p=%.6g", check$p_value))
      warnings[[length(warnings) + 1L]] <- paste0(
        "Assumption check '", check$name, "' may be violated (", p_text, ")"
      )
    }
  }
  warnings
}

engine_info <- function() {
  list(
    name = "R",
    version = as.character(getRversion()),
    libraries = list(
      jsonlite = as.character(packageVersion("jsonlite")),
      car = as.character(packageVersion("car"))
    )
  )
}

run_descriptive <- function() {
  values <- as_num(df[[outcome]])
  values <- values[!is.na(values)]
  n <- length(values)
  if (n == 0) stop("Descriptive analysis needs at least 1 value")
  q <- as.numeric(quantile(values, probs = c(0.25, 0.75), names = FALSE))
  statistics <- list(
    n = n,
    mean = mean(values),
    median = median(values),
    std = sd(values),
    q1 = q[1],
    q3 = q[2],
    min = min(values),
    max = max(values)
  )
  warnings <- list()
  if (n >= 2) {
    sem <- sd(values) / sqrt(n)
    t_crit <- qt(1 - alpha / 2, df = n - 1)
    statistics$sem <- sem
    statistics$ci95_lower <- mean(values) - t_crit * sem
    statistics$ci95_upper <- mean(values) + t_crit * sem
  } else {
    warnings[[length(warnings) + 1L]] <-
      "Descriptive analysis with n=1 cannot compute SEM/CI"
  }
  list(
    protocol_id = protocol_id,
    method = method,
    engine = engine_info(),
    statistics = statistics,
    p_values = list(),
    effect_size = list(),
    assumptions = list(),
    warnings = warnings,
    parameters = list(alpha = alpha, missing_policy = "complete_case"),
    metadata = list(variable = outcome)
  )
}

run_independent_t_test <- function() {
  required <- c(outcome, group_col)
  work <- complete_case(df, required)
  warnings <- list()
  dropped <- nrow(df) - nrow(work)
  if (dropped > 0) {
    warnings[[length(warnings) + 1L]] <- paste0(
      "complete_case removed ", dropped, " row(s)"
    )
  }
  labels <- sorted_labels(work[[group_col]])
  if (length(labels) != 2) {
    stop(paste0("Independent t-test requires exactly 2 groups; found ",
                length(labels), ": ", paste(labels, collapse = ",")))
  }
  groups <- list()
  for (label in labels) {
    values <- as_num(work[[outcome]][as.character(work[[group_col]]) == label])
    if (length(values) < 2) stop(paste0("Group '", label, "' needs at least 2 observations"))
    groups[[label]] <- values
  }
  a <- groups[[1]]
  b <- groups[[2]]
  equal_var <- identical(params$variance, "equal_variance")
  test <- t.test(a, b, alternative = "two.sided", var.equal = equal_var)
  n1 <- length(a)
  n2 <- length(b)
  m1 <- mean(a)
  m2 <- mean(b)
  s1 <- sd(a)
  s2 <- sd(b)
  if (equal_var) {
    dfree <- n1 + n2 - 2
    pooled_sd <- sqrt(((n1 - 1) * s1^2 + (n2 - 1) * s2^2) / dfree)
    cohens_d <- (m1 - m2) / pooled_sd
  } else {
    variance_numer <- s1^2 / n1 + s2^2 / n2
    dfree <- variance_numer^2 /
      ((s1^2 / n1)^2 / (n1 - 1) + (s2^2 / n2)^2 / (n2 - 1))
    cohens_d <- (m1 - m2) / sqrt((s1^2 + s2^2) / 2)
  }
  checks <- shapiro_checks(groups, alpha)
  if (equal_var) {
    checks <- c(checks, levene_check(groups, alpha))
  }
  warnings <- assumption_warnings(checks, warnings)
  list(
    protocol_id = protocol_id,
    method = method,
    engine = engine_info(),
    statistics = list(
      t = as.numeric(test$statistic),
      df = as.numeric(dfree),
      mean_difference = m1 - m2,
      mean_group1 = m1,
      mean_group2 = m2,
      sd_group1 = s1,
      sd_group2 = s2,
      n_group1 = n1,
      n_group2 = n2
    ),
    p_values = list(two_sided = as.numeric(test$p.value)),
    effect_size = list(cohens_d = cohens_d),
    assumptions = checks,
    warnings = warnings,
    parameters = list(alpha = alpha, missing_policy = "complete_case"),
    metadata = list(groups = labels)
  )
}

run_paired_t_test <- function() {
  required <- c(outcome, group_col, paired_by_col)
  work <- complete_case(df, required)
  warnings <- list()
  dropped <- nrow(df) - nrow(work)
  if (dropped > 0) {
    warnings[[length(warnings) + 1L]] <- paste0(
      "complete_case removed ", dropped, " row(s)"
    )
  }
  labels <- sorted_labels(work[[group_col]])
  if (length(labels) != 2) stop("Paired t-test requires exactly 2 groups")
  ids <- unique(work[[paired_by_col]])
  a <- numeric(0)
  b <- numeric(0)
  for (id in ids) {
    rows <- work[work[[paired_by_col]] == id, , drop = FALSE]
    a_val <- as_num(rows[[outcome]][as.character(rows[[group_col]]) == labels[1]])
    b_val <- as_num(rows[[outcome]][as.character(rows[[group_col]]) == labels[2]])
    if (length(a_val) == 1 && length(b_val) == 1 &&
        !is.na(a_val) && !is.na(b_val)) {
      a <- c(a, a_val)
      b <- c(b, b_val)
    }
  }
  if (length(a) < 2) stop("Paired analysis requires at least 2 complete pairs")
  test <- t.test(a, b, paired = TRUE)
  differences <- a - b
  cohens_d <- mean(differences) / sd(differences)
  checks <- shapiro_checks(list(paired_differences = differences), alpha)
  warnings <- assumption_warnings(checks, warnings)
  list(
    protocol_id = protocol_id,
    method = method,
    engine = engine_info(),
    statistics = list(
      t = as.numeric(test$statistic),
      df = as.numeric(test$parameter),
      mean_difference = mean(differences),
      sd_difference = sd(differences),
      n_pairs = length(a)
    ),
    p_values = list(two_sided = as.numeric(test$p.value)),
    effect_size = list(cohens_d = cohens_d),
    assumptions = checks,
    warnings = warnings,
    parameters = list(alpha = alpha, missing_policy = "complete_case"),
    metadata = list(groups = labels)
  )
}

run_one_way_anova <- function() {
  required <- c(outcome, group_col)
  work <- complete_case(df, required)
  warnings <- list()
  dropped <- nrow(df) - nrow(work)
  if (dropped > 0) {
    warnings[[length(warnings) + 1L]] <- paste0(
      "complete_case removed ", dropped, " row(s)"
    )
  }
  labels <- sorted_labels(work[[group_col]])
  groups <- list()
  for (label in labels) {
    values <- as_num(work[[outcome]][as.character(work[[group_col]]) == label])
    if (length(values) < 2) stop(paste0("Group '", label, "' needs at least 2 observations"))
    groups[[label]] <- values
  }
  aov_data <- data.frame(
    value = unlist(groups, use.names = FALSE),
    group = rep(names(groups), times = lengths(groups))
  )
  model <- aov(value ~ group, data = aov_data)
  summary_table <- summary(model)[[1]]
  f_stat <- summary_table$`F value`[1]
  p_value <- summary_table$`Pr(>F)`[1]
  ss_between <- summary_table$`Sum Sq`[1]
  ss_within <- summary_table$`Sum Sq`[2]
  ss_total <- ss_between + ss_within
  df1 <- summary_table$Df[1]
  df2 <- summary_table$Df[2]
  eta_squared <- ss_between / ss_total

  tukey <- TukeyHSD(model, conf.level = 1 - alpha)
  tukey_table <- tukey[[1]]
  pairwise <- list()
  for (row_name in rownames(tukey_table)) {
    parts <- strsplit(row_name, "-", fixed = TRUE)[[1]]
    key_parts <- sort(parts)
    key <- paste(key_parts, collapse = "-")
    diff <- tukey_table[row_name, "diff"]
    pairwise[[key]] <- list(
      mean_difference = diff,
      p_value = tukey_table[row_name, "p adj"],
      ci_lower = tukey_table[row_name, "lwr"],
      ci_upper = tukey_table[row_name, "upr"]
    )
  }

  checks <- shapiro_checks(groups, alpha)
  checks <- c(checks, levene_check(groups, alpha))
  warnings <- assumption_warnings(checks, warnings)
  list(
    protocol_id = protocol_id,
    method = method,
    engine = engine_info(),
    statistics = list(
      F = as.numeric(f_stat),
      df1 = df1,
      df2 = df2,
      n_total = length(unlist(groups)),
      ss_between = ss_between,
      ss_within = ss_within,
      ss_total = ss_total,
      ms_between = ss_between / df1,
      ms_within = ss_within / df2
    ),
    p_values = list(
      overall = as.numeric(p_value),
      pairwise = pairwise
    ),
    effect_size = list(eta_squared = eta_squared),
    assumptions = checks,
    warnings = warnings,
    parameters = list(alpha = alpha, missing_policy = "complete_case"),
    metadata = list(groups = labels)
  )
}

run_two_way_anova <- function() {
  if (is.null(factor2_col) || is.na(factor2_col)) {
    stop("Two-way ANOVA requires factor2")
  }
  required <- c(outcome, group_col, factor2_col)
  work <- complete_case(df, required)
  warnings <- list()
  dropped <- nrow(df) - nrow(work)
  if (dropped > 0) {
    warnings[[length(warnings) + 1L]] <- paste0(
      "complete_case removed ", dropped, " row(s)"
    )
  }
  work[[outcome]] <- as_num(work[[outcome]])
  work[["_factor1"]] <- factor(as.character(work[[group_col]]))
  work[["_factor2"]] <- factor(as.character(work[[factor2_col]]))
  counts <- table(work[["_factor1"]], work[["_factor2"]])
  if (length(unique(as.numeric(counts))) > 1) {
    warnings[[length(warnings) + 1L]] <-
      "Unbalanced design detected; Type III sums of squares are reported"
  }
  if (nrow(work) < 4) stop("Two-way ANOVA needs at least 4 complete observations")

  options(contrasts = c(unordered = "contr.sum", ordered = "contr.poly"))
  anova_data <- data.frame(
    y = work[[outcome]],
    f1 = work[["_factor1"]],
    f2 = work[["_factor2"]]
  )
  model <- lm(y ~ f1 * f2, data = anova_data)
  anova_table <- Anova(model, type = 3)
  residual_ss <- anova_table["Residuals", "Sum Sq"]
  term_map <- c(
    "f1" = "factor1",
    "f2" = "factor2",
    "f1:f2" = "interaction"
  )
  statistics <- list(
    n = nrow(work),
    residual_df = anova_table["Residuals", "Df"],
    residual_ss = residual_ss
  )
  p_values <- list()
  effect_size <- list()
  for (term in names(term_map)) {
    label <- term_map[[term]]
    ss <- anova_table[term, "Sum Sq"]
    statistics[[paste0("F_", label)]] <- anova_table[term, "F value"]
    statistics[[paste0("df_", label)]] <- anova_table[term, "Df"]
    statistics[[paste0("ss_", label)]] <- ss
    p_values[[label]] <- anova_table[term, "Pr(>F)"]
    effect_size[[paste0("partial_eta_squared_", label)]] <-
      ss / (ss + residual_ss)
  }

  residuals <- residuals(model)
  checks <- shapiro_checks(list(residuals = residuals), alpha)
  interaction <- paste(work[["_factor1"]], work[["_factor2"]], sep = "_")
  lev_groups <- list()
  for (label in sorted_labels(interaction)) {
    lev_groups[[label]] <-
      as_num(work[[outcome]][interaction == label])
  }
  checks <- c(checks, levene_check(lev_groups, alpha))
  warnings <- assumption_warnings(checks, warnings)
  list(
    protocol_id = protocol_id,
    method = method,
    engine = engine_info(),
    statistics = statistics,
    p_values = p_values,
    effect_size = effect_size,
    assumptions = checks,
    warnings = warnings,
    parameters = list(
      alpha = alpha,
      missing_policy = "complete_case",
      type_iii_ss = TRUE
    ),
    metadata = list(factor1 = group_col, factor2 = factor2_col)
  )
}

run_mann_whitney_u <- function() {
  required <- c(outcome, group_col)
  work <- complete_case(df, required)
  warnings <- list()
  dropped <- nrow(df) - nrow(work)
  if (dropped > 0) {
    warnings[[length(warnings) + 1L]] <- paste0(
      "complete_case removed ", dropped, " row(s)"
    )
  }
  labels <- sorted_labels(work[[group_col]])
  if (length(labels) != 2) stop("Mann-Whitney U requires exactly 2 groups")
  groups <- list()
  for (label in labels) {
    groups[[label]] <-
      as_num(work[[outcome]][as.character(work[[group_col]]) == label])
  }
  a <- groups[[1]]
  b <- groups[[2]]
  n1 <- length(a)
  n2 <- length(b)
  combined <- c(a, b)
  ranks <- rank(combined)
  r1 <- sum(ranks[seq_along(a)])
  u_stat <- r1 - n1 * (n1 + 1) / 2
  n_total <- n1 + n2
  tie_counts <- table(combined)
  tie_term <- sum(tie_counts^3 - tie_counts)
  s <- sqrt(n1 * n2 / 12 * ((n_total + 1) - tie_term / (n_total * (n_total - 1))))
  numerator <- u_stat - n1 * n2 / 2
  if (numerator < 0) {
    numerator <- numerator + 0.5
  } else {
    numerator <- numerator - 0.5
  }
  z <- numerator / s
  p_value <- 2 * pnorm(-abs(z))
  rank_biserial <- 1 - (2 * u_stat) / (n1 * n2)
  list(
    protocol_id = protocol_id,
    method = method,
    engine = engine_info(),
    statistics = list(
      U = u_stat,
      n_group1 = n1,
      n_group2 = n2
    ),
    p_values = list(two_sided = p_value),
    effect_size = list(rank_biserial = rank_biserial),
    assumptions = list(),
    warnings = warnings,
    parameters = list(alpha = alpha, missing_policy = "complete_case"),
    metadata = list(groups = labels)
  )
}

dunn_pairwise <- function(groups) {
  values <- unlist(groups, use.names = FALSE)
  labels <- rep(names(groups), times = lengths(groups))
  ranks <- rank(values)
  mean_ranks <- tapply(ranks, labels, mean)
  n <- lengths(groups)
  n_total <- length(values)
  tie_counts <- table(values)
  tie_correction <- sum(tie_counts^3 - tie_counts) / 12

  pairs <- list()
  raw_p <- numeric(0)
  pair_names <- character(0)
  for (i in seq_along(names(groups))) {
    for (j in seq_along(names(groups))) {
      if (j <= i) next
      g1 <- names(groups)[i]
      g2 <- names(groups)[j]
      z <- (mean_ranks[[g1]] - mean_ranks[[g2]]) /
        sqrt((n_total * (n_total + 1) / 12 - tie_correction / (n_total - 1)) *
               (1 / n[g1] + 1 / n[g2]))
      raw_p <- c(raw_p, 2 * pnorm(-abs(z)))
      pair_names <- c(pair_names, paste(sort(c(g1, g2)), collapse = "-"))
    }
  }
  m <- length(raw_p)
  order_idx <- order(raw_p)
  adjusted <- pmin(1, raw_p[order_idx] * (m:1))
  adjusted <- cummax(adjusted)
  adj_p <- numeric(m)
  adj_p[order_idx] <- adjusted
  for (idx in seq_along(pair_names)) {
    pairs[[pair_names[idx]]] <- adj_p[idx]
  }
  pairs
}

run_kruskal_wallis <- function() {
  required <- c(outcome, group_col)
  work <- complete_case(df, required)
  warnings <- list()
  dropped <- nrow(df) - nrow(work)
  if (dropped > 0) {
    warnings[[length(warnings) + 1L]] <- paste0(
      "complete_case removed ", dropped, " row(s)"
    )
  }
  labels <- sorted_labels(work[[group_col]])
  groups <- list()
  for (label in labels) {
    groups[[label]] <-
      as_num(work[[outcome]][as.character(work[[group_col]]) == label])
  }
  test <- kruskal.test(groups)
  h_stat <- as.numeric(test$statistic)
  p_value <- as.numeric(test$p.value)
  n_total <- length(unlist(groups))
  epsilon_squared <- h_stat / (n_total - 1)
  pairwise <- dunn_pairwise(groups)
  list(
    protocol_id = protocol_id,
    method = method,
    engine = engine_info(),
    statistics = list(
      H = h_stat,
      df = length(groups) - 1,
      n_total = n_total
    ),
    p_values = list(
      overall = p_value,
      pairwise = pairwise
    ),
    effect_size = list(epsilon_squared = epsilon_squared),
    assumptions = list(),
    warnings = warnings,
    parameters = list(
      alpha = alpha,
      missing_policy = "complete_case",
      posthoc_adjustment = "holm"
    ),
    metadata = list(groups = labels)
  )
}

run_correlation <- function(kind) {
  if (length(predictors) != 1) {
    stop(paste0(kind, " correlation requires exactly one predictor variable"))
  }
  x_name <- predictors[1]
  work <- complete_case(df, c(outcome, x_name))
  warnings <- list()
  dropped <- nrow(df) - nrow(work)
  if (dropped > 0) {
    warnings[[length(warnings) + 1L]] <- paste0(
      "complete_case removed ", dropped, " row(s)"
    )
  }
  x <- as_num(work[[x_name]])
  y <- as_num(work[[outcome]])
  if (kind == "spearman") {
    test <- cor.test(x, y, method = "spearman", exact = FALSE)
  } else {
    test <- cor.test(x, y, method = kind)
  }
  statistic <- as.numeric(test$estimate)
  effect_key <- ifelse(kind == "pearson", "pearson_r", "spearman_rho")
  stat_key <- ifelse(kind == "pearson", "r", "rho")
  statistics <- list(statistic, length(x))
  names(statistics) <- c(stat_key, "n")
  effect_size <- list(statistic)
  names(effect_size) <- effect_key
  list(
    protocol_id = protocol_id,
    method = method,
    engine = engine_info(),
    statistics = statistics,
    p_values = list(two_sided = as.numeric(test$p.value)),
    effect_size = effect_size,
    assumptions = list(),
    warnings = warnings,
    parameters = list(alpha = alpha, missing_policy = "complete_case"),
    metadata = list(x = x_name, y = outcome)
  )
}

run_linear_regression <- function() {
  if (length(predictors) == 0) {
    stop("Linear regression requires at least one predictor")
  }
  required <- c(outcome, predictors)
  work <- complete_case(df, required)
  warnings <- list()
  dropped <- nrow(df) - nrow(work)
  if (dropped > 0) {
    warnings[[length(warnings) + 1L]] <- paste0(
      "complete_case removed ", dropped, " row(s)"
    )
  }
  formula_text <- paste(outcome, "~", paste(predictors, collapse = " + "))
  model <- lm(as.formula(formula_text), data = work)
  summary_model <- summary(model)
  coef_table <- summary_model$coefficients
  ci <- confint(model, level = 1 - alpha)
  coefficients <- list()
  for (name in rownames(coef_table)) {
    key <- ifelse(name == "(Intercept)", "const", name)
    coefficients[[key]] <- list(
      estimate = coef_table[name, "Estimate"],
      std_error = coef_table[name, "Std. Error"],
      t = coef_table[name, "t value"],
      p_value = coef_table[name, "Pr(>|t|)"],
      ci_lower = ci[name, 1],
      ci_upper = ci[name, 2]
    )
  }
  residuals <- residuals(model)
  checks <- shapiro_checks(list(residuals = residuals), alpha)
  warnings <- assumption_warnings(checks, warnings)
  f_stat <- as.numeric(summary_model$fstatistic[1])
  f_p_value <- pf(f_stat, summary_model$fstatistic[2],
                  summary_model$fstatistic[3], lower.tail = FALSE)
  list(
    protocol_id = protocol_id,
    method = method,
    engine = engine_info(),
    statistics = list(
      n = nrow(work),
      k = nrow(coef_table),
      residual_df = model$df.residual,
      r_squared = summary_model$r.squared,
      adjusted_r_squared = summary_model$adj.r.squared,
      f_statistic = f_stat,
      residual_std_error = summary_model$sigma,
      coefficients = coefficients
    ),
    p_values = list(
      overall_f = f_p_value,
      coefficients = lapply(coefficients, function(x) x$p_value)
    ),
    effect_size = list(r_squared = summary_model$r.squared),
    assumptions = checks,
    warnings = warnings,
    parameters = list(
      alpha = alpha,
      missing_policy = "complete_case",
      include_intercept = TRUE
    ),
    metadata = list(predictors = predictors)
  )
}

result <- tryCatch(
  {
    if (method == "descriptive") {
      run_descriptive()
    } else if (method == "independent_t_test") {
      run_independent_t_test()
    } else if (method == "paired_t_test") {
      run_paired_t_test()
    } else if (method == "one_way_anova") {
      run_one_way_anova()
    } else if (method == "two_way_anova") {
      run_two_way_anova()
    } else if (method == "mann_whitney_u") {
      run_mann_whitney_u()
    } else if (method == "kruskal_wallis") {
      run_kruskal_wallis()
    } else if (method == "pearson_correlation") {
      run_correlation("pearson")
    } else if (method == "spearman_correlation") {
      run_correlation("spearman")
    } else if (method == "linear_regression") {
      run_linear_regression()
    } else {
      stop(paste0("No R handler for method: ", method))
    }
  },
  error = function(e) {
    writeLines(toJSON(list(error = conditionMessage(e)), auto_unbox = TRUE),
               output_path)
    quit(status = 1)
  }
)

writeLines(toJSON(result, auto_unbox = TRUE, digits = NA, na = "null",
                  null = "null"), output_path)
