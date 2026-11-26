# Demo business rules

Every record and rule in this project is fictional and exists only to demonstrate backend structure.

- **Loan eligibility:** the demo marks a customer eligible for an indicative EUR 5,000 offer when no active loan exists. This is not a loan offer or credit decision.
- **Card eligibility:** the demo marks a customer eligible when no active card exists. This is not an application result or credit decision.
- **Limit increase:** requested limit must be greater than the current limit. The increase amount is `requested limit - current limit`.
- **Human follow-up:** when the increase amount is greater than `SELF_SERVICE_LIMIT_INCREASE_MAX`, the request is saved as `pending_human_review` and the response says a bank representative will call. Otherwise it is saved as `submitted_for_review`.
- **No automatic limit change:** neither status changes the card limit. This demo does not place a call, notify an employee, or provide a review queue.
- **AI confirmation:** the AI panel can prepare a limit-increase proposal, but cannot submit it. The customer must press the confirmation button. Requests above the configured threshold are stored as pending human review; the promised call is only demo response text.
- **AI task boundary:** the AI banking mode is limited to greetings, account/balance lookups, loans and demo eligibility, cards and demo eligibility, recurring payments, FAQs, and limit-increase proposals. Other topics receive a fixed out-of-scope response.
- **Money representation:** monetary values are stored as integer cents to avoid floating-point rounding errors.

The default cap is EUR 1,000. For example, if the current limit is EUR 3,000 and the customer requests EUR 4,200, the increase is EUR 1,200 and requires human follow-up.

