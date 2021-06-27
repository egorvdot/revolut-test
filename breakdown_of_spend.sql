-- TASK DESCRIPTION
-- Given the transactions table and table containing exchange rates:

-- 1. Write down a query that gives us a breakdown of spend in GBP by each user.
-- Use the exchange rate with the largest timestamp.

WITH largest_ts AS (
    SELECT MAX(ts) AS ts, from_currency AS currency
    FROM exchange_rates
    GROUP BY from_currency
), last_gbp_rates AS (
    SELECT largest_ts.currency, exchange_rates.rate
    FROM largest_ts
    INNER JOIN exchange_rates
    ON largest_ts.currency=exchange_rates.from_currency
           AND largest_ts.ts=exchange_rates.ts
           AND exchange_rates.to_currency='GBP'
), transactions_in_gbp AS (
    SELECT user_id, amount*COALESCE(rate, 1) AS gbp_amount
    FROM transactions
    LEFT JOIN last_gbp_rates
    ON last_gbp_rates.currency=transactions.currency
)
SELECT user_id, SUM(gbp_amount) AS total_spent_gbp
FROM transactions_in_gbp
GROUP BY user_id
ORDER BY user_id;


-- 2. Write down the same query, but this time, use the latest exchange rate smaller or equal then the transaction timestamp.
-- The solution should have the two columns: user_id, total_spent_gbp, ordered by user_id

WITH transactions_with_less_or_equal_rates AS (
  SELECT t.ts, t.user_id, t.currency, exchange_rates.ts AS rate_ts, t.amount, rate
  FROM transactions AS t
  LEFT JOIN exchange_rates
  ON t.ts >= exchange_rates.ts
         AND t.currency=exchange_rates.from_currency
         AND exchange_rates.to_currency='GBP'
), transactions_in_gbp AS (
  SELECT DISTINCT ON (ts, currency) user_id, amount*COALESCE(rate, 1) AS gbp_amount
  FROM transactions_with_less_or_equal_rates
  ORDER BY ts, currency, rate_ts DESC
)
SELECT user_id, SUM(gbp_amount) AS total_spent_gbp
FROM transactions_in_gbp
GROUP BY user_id
ORDER BY user_id;
