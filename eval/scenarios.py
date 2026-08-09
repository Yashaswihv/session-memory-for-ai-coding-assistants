from dataclasses import dataclass
from typing import Literal


@dataclass
class Scenario:
    id: str
    category: str
    dev1_prompt: str
    decision_summary: str
    dev2_task: str
    static_doc_coverage: Literal["full", "vague", "absent"]
    static_doc_text: str
    gold_answer_criteria: str


SCENARIOS = [
    Scenario(
        id="retry_budget",
        category="error_handling",
        dev1_prompt=(
            "We are building a small internal tool. Important architectural decision: we are capping "
            "the request retry budget at 3 attempts (not the usual 5) because of a rate-limit incident "
            "with the upstream vendor API last quarter -- retrying more aggressively made the outage "
            "worse. Just acknowledge this decision, no code needed yet."
        ),
        decision_summary="Retry budget for the vendor API is capped at 3 attempts, not 5, because more "
        "aggressive retrying worsened a past rate-limit incident.",
        dev2_task=(
            "I'm implementing the retry logic for calls to the upstream vendor API in this tool. "
            "Should I set the max retry attempts to 5?"
        ),
        static_doc_coverage="full",
        static_doc_text="# Project Notes\n\n- Vendor API retry budget: capped at 3 attempts (not 5) due to a prior rate-limit incident.\n",
        gold_answer_criteria="Correct answer says NOT to use 5, and states the cap is 3, ideally citing the "
        "rate-limit incident as the reason. Confidently recommending 5 without qualification is wrong.",
    ),
    Scenario(
        id="orm_lazy_loading",
        category="architecture",
        dev1_prompt=(
            "Decision for this project: we do NOT use the ORM's global lazy-loading default for related "
            "records. We disabled it project-wide and require explicit eager loading (select_related/joins) "
            "on every query, because lazy loading caused a severe N+1 query problem in production last "
            "month that slowed the dashboard to a crawl. Just acknowledge, no code needed."
        ),
        decision_summary="Global lazy loading is disabled project-wide; all queries must use explicit eager "
        "loading, because lazy loading caused a production N+1 query incident.",
        dev2_task=(
            "I'm adding a new query that fetches a list of orders along with their related customer "
            "records. Is it fine to just let the ORM lazy-load the customer relation as needed?"
        ),
        static_doc_coverage="full",
        static_doc_text="# Project Notes\n\n- Lazy loading is disabled globally. Always use explicit eager "
        "loading for related records (past N+1 incident).\n",
        gold_answer_criteria="Correct answer says NO, don't rely on lazy loading -- use explicit eager "
        "loading instead, ideally citing the N+1 incident. Approving lazy loading without qualification is wrong.",
    ),
    Scenario(
        id="charting_library_license",
        category="licensing",
        dev1_prompt=(
            "We evaluated and rejected the 'ChartMaster Pro' charting library for this project because its "
            "license is GPL-3.0, which conflicts with our closed-source commercial distribution. We're using "
            "'LiteChart' instead, which is MIT licensed. Please just note this, no code needed."
        ),
        decision_summary="ChartMaster Pro was rejected due to its GPL-3.0 license conflicting with the "
        "project's closed-source distribution; LiteChart (MIT) is used instead.",
        dev2_task=(
            "I found a tutorial that uses ChartMaster Pro for the dashboard charts and it looks nicer than "
            "what we have. Should I switch our charting to ChartMaster Pro?"
        ),
        static_doc_coverage="full",
        static_doc_text="# Project Notes\n\n- Charting library: LiteChart (MIT). Do not use ChartMaster Pro -- GPL-3.0 license conflicts with our closed-source distribution.\n",
        gold_answer_criteria="Correct answer says NOT to switch to ChartMaster Pro, citing the GPL-3.0 "
        "license conflict, and to stick with LiteChart. Recommending the switch without a licensing caveat is wrong.",
    ),
    Scenario(
        id="db_naming_convention",
        category="style",
        dev1_prompt=(
            "For this project, all database column names must be snake_case, never camelCase -- this is "
            "because we run a nightly sync into a legacy data warehouse that expects snake_case column "
            "names, and a mismatch broke the sync pipeline before. Just acknowledge, no code needed."
        ),
        decision_summary="All DB columns must be snake_case (not camelCase) because a nightly sync into a "
        "legacy data warehouse expects snake_case and previously broke on a mismatch.",
        dev2_task=(
            "I'm adding a new `shippingAddress` column to the orders table (camelCase, matching our "
            "TypeScript model). Is that naming okay for the database column?"
        ),
        static_doc_coverage="vague",
        static_doc_text="# Project Notes\n\n- Please follow consistent naming conventions across the codebase.\n",
        gold_answer_criteria="Correct answer says the DB column should be snake_case (e.g. shipping_address), "
        "not camelCase, and ideally mentions the legacy warehouse sync. Approving camelCase for the DB column is wrong.",
    ),
    Scenario(
        id="soft_delete_only",
        category="data_model",
        dev1_prompt=(
            "Decision: the orders table uses soft-delete only (a deleted_at timestamp) -- we never hard-delete "
            "rows from it, because we're required to retain order records for 7 years for audit purposes. "
            "Just acknowledge, no code needed."
        ),
        decision_summary="Orders are never hard-deleted; only soft-deleted via a deleted_at timestamp, due "
        "to a 7-year audit retention requirement.",
        dev2_task=(
            "A customer requested we permanently delete their old cancelled order from the orders table "
            "for a data cleanup task. Should I write a DELETE query to remove that row?"
        ),
        static_doc_coverage="vague",
        static_doc_text="# Project Notes\n\n- Be careful with destructive database operations.\n",
        gold_answer_criteria="Correct answer says NOT to hard-delete the row -- use the existing soft-delete "
        "(deleted_at) mechanism instead, ideally citing the audit retention requirement. Writing a real DELETE without qualification is wrong.",
    ),
    Scenario(
        id="async_export_status_code",
        category="api_design",
        dev1_prompt=(
            "For the /reports/export endpoint: it must return HTTP 202 Accepted, not 200 OK, because the "
            "actual export runs asynchronously in a background job and isn't done when the response is "
            "sent. Just acknowledge, no code needed yet."
        ),
        decision_summary="/reports/export must return HTTP 202 Accepted (not 200) since the export runs "
        "asynchronously in a background job.",
        dev2_task=(
            "I'm finishing up the /reports/export endpoint. Once it successfully kicks off the export job, "
            "should it return a 200 OK response?"
        ),
        static_doc_coverage="full",
        static_doc_text="# Project Notes\n\n- /reports/export returns 202 Accepted (async background job), not 200.\n",
        gold_answer_criteria="Correct answer says it should return 202 Accepted, not 200, and ideally "
        "mentions the async/background-job reasoning. Recommending 200 without qualification is wrong.",
    ),
    Scenario(
        id="pii_request_logging",
        category="security_compliance",
        dev1_prompt=(
            "Compliance decision: we must never log the full request body for the /checkout endpoint, "
            "because it contains unmasked card details and that would violate PCI compliance. Just "
            "acknowledge, no code needed."
        ),
        decision_summary="Full request bodies must never be logged for /checkout, since they contain "
        "unmasked card details and this would violate PCI compliance.",
        dev2_task=(
            "I'm adding debug logging to help diagnose a bug in the /checkout endpoint. Is it fine to "
            "log the full incoming request body temporarily to see what's being sent?"
        ),
        static_doc_coverage="full",
        static_doc_text="# Project Notes\n\n- Never log full request bodies for /checkout -- contains unmasked card data (PCI compliance).\n",
        gold_answer_criteria="Correct answer says NOT to log the full request body for /checkout, citing "
        "PCI/card-data concerns, and to mask/redact sensitive fields instead. Approving full body logging without qualification is wrong.",
    ),
    Scenario(
        id="product_cache_ttl",
        category="performance",
        dev1_prompt=(
            "Decision: the product listing cache TTL is set to 10 minutes, not the usual 1 hour, because "
            "during sales events pricing changes need to propagate to customers quickly, and an hour-long "
            "stale cache caused a pricing-mismatch complaint last time. Just acknowledge, no code needed."
        ),
        decision_summary="Product listing cache TTL is 10 minutes (not 1 hour) so pricing changes during "
        "sales events propagate quickly, after a prior stale-cache pricing complaint.",
        dev2_task=(
            "I'm reviewing our cache configuration and most of our other caches use a 1-hour TTL. Should "
            "I bump the product listing cache to 1 hour too, for consistency?"
        ),
        static_doc_coverage="vague",
        static_doc_text="# Project Notes\n\n- We use caching in a few places to improve performance.\n",
        gold_answer_criteria="Correct answer says NOT to bump it to 1 hour -- keep it at 10 minutes, ideally "
        "citing the sales-event pricing propagation reasoning. Recommending 1 hour without qualification is wrong.",
    ),
    Scenario(
        id="shipping_webhook_fallback",
        category="integration",
        dev1_prompt=(
            "We implemented a polling fallback for the shipping-partner webhook because we found their "
            "webhooks silently drop about 2% of events in staging -- polling every 15 minutes catches "
            "anything the webhook missed. Just acknowledge, no code needed."
        ),
        decision_summary="A polling fallback (every 15 minutes) exists alongside the shipping-partner "
        "webhook because their webhooks silently drop ~2% of events.",
        dev2_task=(
            "I'm cleaning up what looks like redundant code -- there's a webhook handler AND a polling job "
            "for shipping status updates. Should I remove the polling job since we already have the webhook?"
        ),
        static_doc_coverage="absent",
        static_doc_text="# Project Notes\n\n- Deployment: staging and prod both run on the same container image, built via the standard CI pipeline.\n",
        gold_answer_criteria="Correct answer says NOT to remove the polling job -- it's an intentional "
        "fallback for dropped webhook events, not redundant. Approving removal without qualification is wrong.",
    ),
    Scenario(
        id="payment_error_handling_policy",
        category="error_handling",
        dev1_prompt=(
            "Payment gateway error-handling policy: automatically retry on HTTP 429 (rate limited), but "
            "on HTTP 500 from the payment gateway we must NOT retry automatically and should fail fast -- "
            "because retrying a 500 there risks double-charging the customer if the first attempt actually "
            "succeeded server-side. Just acknowledge, no code needed."
        ),
        decision_summary="Auto-retry on HTTP 429 from the payment gateway, but never auto-retry on HTTP "
        "500 -- fail fast instead, due to double-charge risk if the original request actually succeeded.",
        dev2_task=(
            "I'm writing generic retry-on-failure middleware for our payment gateway client. Should it "
            "retry automatically on any 5xx response, including 500s?"
        ),
        static_doc_coverage="vague",
        static_doc_text="# Project Notes\n\n- The payment gateway client has some retry logic.\n",
        gold_answer_criteria="Correct answer says NOT to auto-retry on 500 from the payment gateway "
        "specifically, citing double-charge risk, even if retrying 429 is fine. Approving blanket 5xx retry is wrong.",
    ),
    Scenario(
        id="docker_base_image_pin",
        category="infra",
        dev1_prompt=(
            "We pinned our Docker base image to a specific digest (not just the ':18' tag) after the "
            "'latest' patch under that tag silently introduced a breaking change to a system library and "
            "broke our build without any warning. Just acknowledge, no code needed."
        ),
        decision_summary="The Docker base image is pinned to a specific digest, not just a mutable tag, "
        "after an unpinned tag silently broke the build with a breaking system-library change.",
        dev2_task=(
            "I noticed our Dockerfile uses a long image digest instead of a simple tag like 'node:18'. "
            "Should I simplify it to just use the 'node:18' tag for readability?"
        ),
        static_doc_coverage="full",
        static_doc_text="# Project Notes\n\n- Docker base image is pinned by digest, not tag -- a past 'latest'-tag update silently broke the build.\n",
        gold_answer_criteria="Correct answer says NOT to switch to the mutable tag -- keep the digest pin, "
        "citing the past silent-breakage incident. Recommending the tag-only simplification is wrong.",
    ),
    Scenario(
        id="checkout_feature_flag_rollback",
        category="product_decision",
        dev1_prompt=(
            "The new checkout flow was rolled back behind a feature flag (checkout_v2) after we saw a "
            "spike in cart abandonment during the rollout -- it's currently disabled for all users pending "
            "a UX fix to the new flow. Just acknowledge, no code needed."
        ),
        decision_summary="The new checkout flow (checkout_v2) is currently disabled for all users via a "
        "feature flag, rolled back due to a cart-abandonment spike, pending a UX fix.",
        dev2_task=(
            "I'm doing some cleanup and noticed the checkout_v2 feature flag is set to disabled for "
            "everyone. Since the new checkout code looks complete, should I just enable it for all users?"
        ),
        static_doc_coverage="absent",
        static_doc_text="# Project Notes\n\n- Code style: prefer function components over class components in the frontend.\n",
        gold_answer_criteria="Correct answer says NOT to enable checkout_v2 yet -- it was intentionally "
        "rolled back due to the cart-abandonment spike and is pending a UX fix. Approving enabling it without qualification is wrong.",
    ),
    Scenario(
        id="deprecated_v1_endpoint",
        category="migration",
        dev1_prompt=(
            "The old /v1/users endpoint is deprecated but must stay live for 6 more months, not be removed "
            "now, because a major partner's integration hasn't migrated to /v2/users yet and removing it "
            "early would break their production integration. Just acknowledge, no code needed."
        ),
        decision_summary="/v1/users must stay live for 6 more months despite being deprecated, because a "
        "major partner's integration hasn't migrated to /v2/users yet.",
        dev2_task=(
            "I'm doing a cleanup pass and /v1/users is marked deprecated with a comment saying it's "
            "unused internally. Should I go ahead and remove it now to reduce maintenance burden?"
        ),
        static_doc_coverage="vague",
        static_doc_text="# Project Notes\n\n- We're migrating from /v1 to /v2 endpoints over time.\n",
        gold_answer_criteria="Correct answer says NOT to remove /v1/users yet, citing the partner "
        "integration that hasn't migrated and the 6-month timeline. Approving immediate removal is wrong.",
    ),
    Scenario(
        id="payment_gateway_test_mocking",
        category="testing",
        dev1_prompt=(
            "For CI, the payment gateway is always mocked, never hitting the real sandbox -- the sandbox "
            "adds around 30 seconds of latency per test and has its own rate limits, which made our CI "
            "suite flaky and slow. Just acknowledge, no code needed."
        ),
        decision_summary="CI tests always mock the payment gateway rather than hitting the real sandbox, "
        "because the sandbox is slow (~30s/test) and rate-limited, which made CI flaky.",
        dev2_task=(
            "I'm adding a new integration test for the payment flow and want it to be as realistic as "
            "possible. Should I have it call the real payment gateway sandbox instead of using a mock?"
        ),
        static_doc_coverage="absent",
        static_doc_text="# Project Notes\n\n- Run `make test` to execute the full test suite locally.\n",
        gold_answer_criteria="Correct answer says NOT to call the real sandbox in CI -- keep mocking the "
        "payment gateway, citing the latency/flakiness reasoning. Approving real sandbox calls in CI/tests without qualification is wrong.",
    ),
    Scenario(
        id="thumbnail_generation_queue",
        category="architecture",
        dev1_prompt=(
            "Image thumbnail generation was moved out of the request path into a background queue, because "
            "doing it synchronously during the upload request was causing request timeouts under load. Just "
            "acknowledge, no code needed."
        ),
        decision_summary="Thumbnail generation runs in a background queue, not synchronously in the "
        "upload request, because synchronous generation caused request timeouts under load.",
        dev2_task=(
            "I'm adding support for a new image size variant. Should I just generate it synchronously "
            "inside the existing upload request handler, alongside the response?"
        ),
        static_doc_coverage="vague",
        static_doc_text="# Project Notes\n\n- Uploads are handled by the media service.\n",
        gold_answer_criteria="Correct answer says NOT to generate it synchronously in the request -- add it "
        "to the existing background queue instead, ideally citing the past timeout issue. Approving synchronous generation is wrong.",
    ),
]
