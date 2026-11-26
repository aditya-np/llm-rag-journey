const tokenSelect = document.querySelector("#customer-select");
const money = new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR" });
let toastTimer;

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function showToast(message) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

async function api(path, options = {}, authenticated = true, trace = null) {
  const headers = new Headers(options.headers || {});
  if (options.body) headers.set("Content-Type", "application/json");
  if (authenticated) headers.set("Authorization", `Bearer ${tokenSelect.value}`);
  try {
    const response = await fetch(path, { ...options, headers });
    const payload = response.status === 204 ? null : await response.json().catch(() => null);
    if (trace) trace.push(`${options.method || "GET"} ${path} → ${response.status}`);
    if (!response.ok) {
      const detail = payload?.detail || `Request failed (${response.status})`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return payload;
  } catch (error) {
    if (trace && !trace.length) trace.push(`${options.method || "GET"} ${path} → network error`);
    throw error;
  }
}

function addChatMessage(text, { user = false, steps = [], action = null, containerId = "#chat-messages" } = {}) {
  const messages = document.querySelector(containerId);
  const message = el("div", `chat-message ${user ? "user-message" : "assistant-message"}`);
  message.append(el("div", "message-bubble", text));
  if (action) {
    const button = el("button", "chat-action", action.label);
    button.type = "button";
    button.addEventListener("click", action.onClick);
    message.lastChild.append(button);
  }
  if (steps.length) {
    const details = el("details", "step-details");
    details.append(el("summary", "", "Steps"));
    const list = el("ol");
    steps.forEach((step) => list.append(el("li", "", step)));
    details.append(list);
    message.append(details);
  }
  messages.append(message);
  messages.scrollTop = messages.scrollHeight;
}

function normalizedMessage(message) {
  return message.toLowerCase().replace(/[^a-z0-9€£$\s-]/g, " ").replace(/\s+/g, " ").trim();
}

async function answerChat(message) {
  const text = normalizedMessage(message);
  const trace = [];
  if (/\bcust-\d+\b/i.test(message)) {
    trace.push("Privacy rule matched: customer IDs cannot be used to look up another profile");
    return { text: "I can only access the demo customer selected in this session. I can’t look up information using another customer’s ID.", trace };
  }
  if (/^(hi|hello|hey|good morning|good afternoon|good evening|howdy)$/.test(text)) {
    trace.push("Greeting rule matched", "No backend call");
    return { text: "Hi! I can check your balance, loans, card eligibility and limit, recurring payments, and FAQs. What would you like to know?", trace };
  }
  if (/\b(my name|who am i|my profile)\b/.test(text)) {
    trace.push("Authenticated profile-name rule matched");
    const profile = await api("/v1/auth/me", {}, true, trace);
    return { text: `Your name is ${profile.name}.`, trace };
  }
  if (/\b(increase|raise|higher|upgrade)\b.*\b(limit|credit)\b|\b(limit|credit)\b.*\b(increase|raise|higher|upgrade)\b/.test(text)) {
    trace.push("Credit-limit request rule matched", "No request submitted; explicit request form required");
    return {
      text: "I can help you submit a credit-limit increase request. Open the request form to choose your card and requested new limit. The current limit won’t change automatically.",
      trace,
      action: {
        label: "Open limit request form",
        onClick: () => {
          document.querySelector("#limit-panel").scrollIntoView({ behavior: "smooth", block: "center" });
          document.querySelector("#limit-card").focus({ preventScroll: true });
          closeChatPanel();
        },
      },
    };
  }
  if (/\b(loan|loans)\b/.test(text) && /\b(eligible|eligibility|avail|available|get|apply|qualify|offer)\b/.test(text)) {
    trace.push("Loan eligibility rule matched");
    const result = await api("/v1/loans/eligibility", {}, true, trace);
    const amount = result.indicative_max_amount_cents ? ` Indicative demo amount: ${money.format(result.indicative_max_amount_cents / 100)}.` : "";
    return { text: `${result.eligible_for_demo_offer ? "Under the demo rule, you may be eligible." : "Under the demo rule, you are not eligible."}${amount} ${result.reason} ${result.disclaimer}`, trace };
  }
  if (/\b(loan|loans)\b/.test(text)) {
    trace.push("Existing-loans rule matched");
    const loans = await api("/v1/loans", {}, true, trace);
    return { text: loans.length ? `Your loan records: ${loans.map((loan) => `${loan.loan_type} loan, ${money.format(loan.outstanding_cents / 100)} outstanding, ${loan.status.replaceAll("_", " ")}`).join("; ")}.` : "There are no loans recorded for this demo profile.", trace };
  }
  if (/\b(card|cards|credit)\b/.test(text) && /\b(eligible|eligibility|avail|available|get|apply|qualify)\b/.test(text)) {
    trace.push("Card eligibility rule matched");
    const result = await api("/v1/cards/eligibility", {}, true, trace);
    return { text: `${result.eligible_for_demo_offer ? "Under the demo rule, you may be eligible for a card." : "Under the demo rule, you are not eligible for another card."} ${result.reason} ${result.disclaimer}`, trace };
  }
  if (/\b(card|cards|credit|limit)\b/.test(text) && /\b(limit|card|credit|available|current)\b/.test(text)) {
    trace.push("Card and credit-limit rule matched");
    const cards = await api("/v1/cards", {}, true, trace);
    const activeCards = cards.filter((card) => card.status === "active");
    if (!activeCards.length) return { text: "There is no active card recorded for this demo profile.", trace };
    const asksAvailableCredit = /\bavailable credit\b/.test(text);
    return {
      text: activeCards.map((card) => asksAvailableCredit
        ? `${card.card_type} card: available credit ${money.format(card.available_credit_cents / 100)}.`
        : `${card.card_type} card: current credit limit ${money.format(card.credit_limit_cents / 100)}.`).join(" "),
      trace,
    };
  }
  if (/\b(balance|balances|account|accounts|money)\b/.test(text)) {
    trace.push("Account-balance rule matched");
    const accounts = await api("/v1/accounts", {}, true, trace);
    return { text: accounts.length ? `Your account balances: ${accounts.map((account) => `${account.account_type}, ${money.format(account.balance_cents / 100)}`).join("; ")}.` : "There are no accounts recorded for this demo profile.", trace };
  }
  if (/\b(recurring|schedule|scheduled|subscription|subscriptions|autopay|automatic payment)\b/.test(text)) {
    trace.push("Recurring-payment rule matched");
    const payments = await api("/v1/recurring-payments", {}, true, trace);
    return { text: payments.length ? `Your recurring payments: ${payments.filter((payment) => payment.status === "active").map((payment) => `${payment.payee}, ${money.format(payment.amount_cents / 100)} ${payment.cadence}, next on ${payment.next_payment_date}`).join("; ")}.` : "There are no recurring payments recorded for this demo profile.", trace };
  }
  if (/\b(faq|faqs|help|lost|fraud|transfer|contact|support|payment|banking hours)\b/.test(text)) {
    trace.push("FAQ rule matched");
    const faqs = await api("/v1/faqs", {}, false, trace);
    const stopWords = new Set(["what", "when", "where", "how", "does", "do", "can", "the", "for", "my", "your", "are", "is", "i", "me", "a", "an", "to", "of", "in", "about", "please", "tell", "faq", "faqs", "help"]);
    const words = text.split(" ").filter((word) => word.length > 2 && !stopWords.has(word));
    const scored = faqs.map((faq) => {
      const haystack = `${faq.question} ${faq.answer} ${faq.category}`.toLowerCase();
      return { faq, score: words.filter((word) => haystack.includes(word)).length };
    }).filter((item) => item.score > 0).sort((a, b) => b.score - a.score).slice(0, 3);
    if (!words.length) return { text: `Here are the available FAQs: ${faqs.map((faq) => faq.question).join("; ")}.`, trace };
    return { text: scored.length ? scored.map(({ faq }) => `${faq.question} ${faq.answer}`).join("\n\n") : "I couldn’t find a matching FAQ. Try asking about a lost card, transfers, contact details, or suspected fraud.", trace };
  }
  trace.push("No supported intent matched", "No backend call");
  return { text: "That isn’t something I can help with. You can ask me about your balance, loans, card eligibility or limit, recurring payments, and banking FAQs.", trace };
}

async function answerWithQwen(message) {
  const trace = ["AI banking panel selected", "Authorization token taken from active profile selector"];
  const response = await api("/v1/learning/llm", {
    method: "POST",
    body: JSON.stringify({ message, mode: "banking_chat" }),
  }, true, trace);
  let action = null;
  if (response.action?.type === "limit_increase") {
    const proposal = response.action;
    action = {
      label: `Confirm request: ${money.format(proposal.requested_limit_cents / 100)}`,
      onClick: async (event) => {
        const button = event.currentTarget;
        button.disabled = true;
        button.textContent = "Submitting…";
        try {
          const submitted = await api("/v1/cards/limit-increase-requests", {
            method: "POST",
            body: JSON.stringify({ card_id: proposal.card_id, requested_limit_cents: proposal.requested_limit_cents }),
          });
          button.textContent = "Request submitted";
          addChatMessage(`${submitted.message} Current limit remains ${money.format(submitted.current_limit_cents / 100)}.`, {
            steps: ["Customer pressed confirmation", "POST /v1/cards/limit-increase-requests", `Request status: ${submitted.status}`],
            containerId: "#ai-chat-messages",
          });
        } catch (error) {
          button.disabled = false;
          button.textContent = action.label;
          addChatMessage(`The request was not submitted: ${error.message}`, { containerId: "#ai-chat-messages" });
        }
      },
    };
  }
  return { text: response.answer, trace: [...trace, ...response.steps], action };
}

function closeChatPanel() {
  document.querySelector("#chat-panel").classList.remove("open");
  document.querySelector("#ai-chat-panel").classList.remove("open");
  document.querySelector("#chat-backdrop").classList.remove("open");
  document.querySelector("#chat-toggle").setAttribute("aria-expanded", "false");
}

async function submitChat(message) {
  if (!message.trim()) return;
  addChatMessage(message.trim(), { user: true });
  const input = document.querySelector("#chat-input");
  const send = document.querySelector("#chat-form button");
  input.value = "";
  send.disabled = true;
  try {
    const answer = await answerChat(message.trim());
    addChatMessage(answer.text, { steps: answer.trace, action: answer.action });
  } catch (error) {
    addChatMessage(`I couldn’t complete that request: ${error.message}`, { steps: ["The matched backend request failed"] });
  } finally {
    send.disabled = false;
    input.focus();
  }
}

async function submitAiChat(message) {
  if (!message.trim()) return;
  addChatMessage(message.trim(), { user: true, containerId: "#ai-chat-messages" });
  const input = document.querySelector("#ai-chat-input");
  const send = document.querySelector("#ai-chat-form button");
  input.value = "";
  send.disabled = true;
  try {
    const answer = await answerWithQwen(message.trim());
    addChatMessage(answer.text, { steps: answer.trace, action: answer.action, containerId: "#ai-chat-messages" });
  } catch (error) {
    addChatMessage(`I couldn’t complete the AI request: ${error.message}`, {
      steps: ["POST /v1/learning/llm failed"],
      containerId: "#ai-chat-messages",
    });
  } finally {
    send.disabled = false;
    input.focus();
  }
}

function setEmpty(container, message) {
  container.replaceChildren(el("div", "empty", message));
}

function accountCard(account) {
  const row = el("div", "row-card");
  const left = el("div");
  left.append(el("div", "row-title", `${account.account_type[0].toUpperCase()}${account.account_type.slice(1)} account`));
  left.append(el("div", "row-sub", `•• ${account.id.slice(-4)} · ${account.id}`));
  const right = el("div", "row-value");
  right.append(el("div", "", money.format(account.balance_cents / 100)));
  const button = el("button", "text-button", "Transactions");
  button.type = "button";
  button.addEventListener("click", () => loadTransactions(account));
  right.append(button);
  row.append(left, right);
  return row;
}

async function loadTransactions(account) {
  const area = document.querySelector("#transactions-area");
  const list = document.querySelector("#transactions-list");
  area.hidden = false;
  list.replaceChildren(el("div", "empty", "Loading transactions…"));
  try {
    const rows = await api(`/v1/accounts/${encodeURIComponent(account.id)}/transactions`);
    list.replaceChildren();
    if (!rows.length) return setEmpty(list, "No transactions found for this account.");
    rows.forEach((transaction) => {
      const row = el("div", "transaction-row");
      const description = el("span", "", `${transaction.description} · ${new Date(transaction.posted_at).toLocaleDateString()}`);
      const amount = el("strong", transaction.amount_cents < 0 ? "negative" : "positive", money.format(transaction.amount_cents / 100));
      row.append(description, amount);
      list.append(row);
    });
  } catch (error) {
    setEmpty(list, error.message);
  }
}

function renderSimpleRows(container, rows, titleFor, subFor, valueFor) {
  container.replaceChildren();
  if (!rows.length) return setEmpty(container, "Nothing to show for this demo profile.");
  rows.forEach((item) => {
    const row = el("div", "row-card");
    const left = el("div");
    left.append(el("div", "row-title", titleFor(item)));
    left.append(el("div", "row-sub", subFor(item)));
    row.append(left, el("div", "row-value", valueFor(item)));
    container.append(row);
  });
}

function renderFaqs(rows) {
  const list = document.querySelector("#faqs-list");
  list.replaceChildren();
  if (!rows.length) return setEmpty(list, "No matching FAQs. Try another search.");
  rows.forEach((faq) => {
    const item = el("article", "faq-item");
    item.append(el("div", "faq-question", faq.question));
    item.append(el("p", "faq-answer", faq.answer));
    item.append(el("span", "faq-category", faq.category));
    list.append(item);
  });
}

function renderEligibility(node, result) {
  node.replaceChildren();
  const status = result.eligible_for_demo_offer ? "Eligible under the demo rule" : "Not eligible under the demo rule";
  const strong = el("strong", "", status);
  node.append(strong, document.createTextNode(` · ${result.reason} ${result.disclaimer}`));
}

async function loadDashboard() {
  document.querySelector("#connection-status").textContent = "Loading customer data…";
  try {
    const [profile, accounts, loans, loanEligibility, cards, cardEligibility, payments, demoProfiles] = await Promise.all([
      api("/v1/auth/me"),
      api("/v1/accounts"),
      api("/v1/loans"),
      api("/v1/loans/eligibility"),
      api("/v1/cards"),
      api("/v1/cards/eligibility"),
      api("/v1/recurring-payments"),
      api("/v1/auth/demo-profiles"),
    ]);

    const demoProfileNames = new Map(demoProfiles.map((item) => [item.id, item.name]));
    [...tokenSelect.options].forEach((option) => {
      if (option.value === "demo-token-alex") option.textContent = demoProfileNames.get("CUST-1001") || "Alex Morgan";
      else if (option.value === "demo-token-jamie") option.textContent = demoProfileNames.get("CUST-1002") || "Jamie Lee";
      else {
        const id = `CUST-${option.value.replace("demo-token-customer-", "")}`;
        option.textContent = demoProfileNames.get(id) || option.textContent;
      }
    });

    document.querySelector("#customer-name").textContent = profile.name.split(" ")[0];
    document.querySelector("#avatar").textContent = profile.name[0];
    document.querySelector("#connection-status").textContent = `Connected · ${profile.id}`;
    document.querySelector("#account-count").textContent = `${accounts.length} account${accounts.length === 1 ? "" : "s"} on file`;
    document.querySelector("#total-balance").textContent = money.format(accounts.reduce((sum, account) => sum + account.balance_cents, 0) / 100);
    document.querySelector("#active-loans").textContent = String(loans.filter((loan) => loan.status === "active").length);
    document.querySelector("#loan-note").textContent = loans.length ? `${loans.length} loan record${loans.length === 1 ? "" : "s"}` : "No loan records";
    document.querySelector("#available-credit").textContent = money.format(cards.reduce((sum, card) => sum + card.available_credit_cents, 0) / 100);
    document.querySelector("#card-note").textContent = `${cards.filter((card) => card.status === "active").length} active card${cards.filter((card) => card.status === "active").length === 1 ? "" : "s"}`;
    document.querySelector("#payment-count").textContent = String(payments.filter((payment) => payment.status === "active").length);

    const accountsList = document.querySelector("#accounts-list");
    accountsList.replaceChildren();
    if (accounts.length) accounts.forEach((account) => accountsList.append(accountCard(account)));
    else setEmpty(accountsList, "No accounts found for this demo profile.");

    renderSimpleRows(document.querySelector("#loans-list"), loans,
      (loan) => `${loan.loan_type[0].toUpperCase()}${loan.loan_type.slice(1)} loan`,
      (loan) => loan.status.replaceAll("_", " "),
      (loan) => money.format(loan.outstanding_cents / 100));
    renderEligibility(document.querySelector("#loan-eligibility"), loanEligibility);

    renderSimpleRows(document.querySelector("#cards-list"), cards,
      (card) => card.status === "active" ? `${card.card_type[0].toUpperCase()}${card.card_type.slice(1)} card` : "No active card",
      (card) => card.status.replaceAll("_", " "),
      (card) => card.status === "active" ? `Limit ${money.format(card.credit_limit_cents / 100)} · Available ${money.format(card.available_credit_cents / 100)}` : "—");
    renderEligibility(document.querySelector("#card-eligibility"), cardEligibility);

    renderSimpleRows(document.querySelector("#payments-list"), payments,
      (payment) => payment.payee,
      (payment) => `${payment.cadence} · next ${payment.next_payment_date}`,
      (payment) => money.format(payment.amount_cents / 100));

    const cardSelect = document.querySelector("#limit-card");
    cardSelect.replaceChildren(new Option("Choose a card", ""));
    cards.filter((card) => card.status === "active").forEach((card) => {
      cardSelect.add(new Option(`${card.card_type} · ${card.id} · ${money.format(card.credit_limit_cents / 100)}`, card.id));
    });
    renderFaqs(await api("/v1/faqs", {}, false));
  } catch (error) {
    document.querySelector("#connection-status").textContent = "Could not load local API";
    showToast(error.message);
  }
}

for (let number = 1003; number <= 1052; number += 1) {
  const suffix = String(number - 1000).padStart(3, "0");
  tokenSelect.add(new Option(`Demo Customer ${suffix}`, `demo-token-customer-${number}`));
}

document.querySelector("#customer-select").addEventListener("change", () => {
  document.querySelector("#transactions-area").hidden = true;
  document.querySelector("#limit-result").hidden = true;
  document.querySelector("#chat-messages").replaceChildren();
  addChatMessage(`Profile changed to ${tokenSelect.selectedOptions[0].textContent}. I’ll use this profile for banking lookups.`, {
    steps: ["Active profile changed", "Future API requests use its bearer token"],
  });
  document.querySelector("#ai-chat-messages").replaceChildren();
  addChatMessage(`Profile changed to ${tokenSelect.selectedOptions[0].textContent}. Ask a banking question to compare Qwen with the deterministic helper.`, {
    steps: ["Active profile changed", "AI endpoint validates its bearer token", "Banking tools will use only the resolved profile ID"],
    containerId: "#ai-chat-messages",
  });
  loadDashboard();
});

document.querySelector("#chat-toggle").addEventListener("click", () => {
  const panel = document.querySelector("#chat-panel");
  const open = !panel.classList.contains("open");
  panel.classList.toggle("open", open);
  document.querySelector("#ai-chat-panel").classList.toggle("open", open);
  document.querySelector("#chat-backdrop").classList.toggle("open", open);
  document.querySelector("#chat-toggle").setAttribute("aria-expanded", String(open));
});

document.querySelector("#chat-close").addEventListener("click", closeChatPanel);
document.querySelector("#ai-chat-close").addEventListener("click", closeChatPanel);
document.querySelector("#chat-backdrop").addEventListener("click", closeChatPanel);
document.querySelector("#chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  submitChat(document.querySelector("#chat-input").value);
});
document.querySelectorAll("#rule-quick-prompts button").forEach((button) => {
  button.addEventListener("click", () => submitChat(button.dataset.prompt));
});
document.querySelector("#ai-chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  submitAiChat(document.querySelector("#ai-chat-input").value);
});
document.querySelectorAll("#ai-quick-prompts button").forEach((button) => {
  button.addEventListener("click", () => submitAiChat(button.dataset.prompt));
});

document.querySelector("#close-transactions").addEventListener("click", () => {
  document.querySelector("#transactions-area").hidden = true;
});

document.querySelector("#faq-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = document.querySelector("#faq-query").value.trim();
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  try {
    renderFaqs(await api(`/v1/faqs${params.size ? `?${params}` : ""}`, {}, false));
  } catch (error) {
    showToast(error.message);
  }
});

document.querySelector("#limit-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button[type=submit]");
  const result = document.querySelector("#limit-result");
  const requestedEuros = Number(document.querySelector("#requested-limit").value);
  if (!Number.isFinite(requestedEuros) || requestedEuros <= 0) return;
  button.disabled = true;
  button.textContent = "Submitting…";
  result.hidden = true;
  result.classList.remove("error");
  try {
    const response = await api("/v1/cards/limit-increase-requests", {
      method: "POST",
      body: JSON.stringify({
        card_id: document.querySelector("#limit-card").value,
        requested_limit_cents: Math.round(requestedEuros * 100),
      }),
    });
    result.textContent = `${response.message} Request ${response.request_id} · Current limit ${money.format(response.current_limit_cents / 100)}.`;
    result.hidden = false;
    document.querySelector("#requested-limit").value = "";
  } catch (error) {
    result.textContent = error.message;
    result.classList.add("error");
    result.hidden = false;
  } finally {
    button.disabled = false;
    button.textContent = "Submit request";
  }
});

loadDashboard();
