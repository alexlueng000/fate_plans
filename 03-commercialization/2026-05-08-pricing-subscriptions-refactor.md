# 定价模型重构 — 订阅 + 可扩展 Grants

## Context

The current pricing model has two structural problems:

1. **No subscription support.** `Product` only models one-time packages. There's no concept of billing period, expiry, or auto-renewal. `Order` is one-shot, `Entitlement` has no `expires_at`. Adding 月付 today is impossible without schema changes.
2. **Hard to extend for new paid features.** `Product` has hardcoded columns `bazi_quota` and `liuyao_quota` (`fate/app/models/product.py:72-87`). Adding 心镜灯 or any new metered feature requires another column on `products`, plus matching changes in `services/products.py:grant_product_quota` and the frontend. The chokepoint is ~30 lines but the coupling is total.

Goal: introduce a normalized `product_grants` table (1:N from products to quota grants) plus a `subscriptions` table, refactor `grant_product_quota` to read from grants, and drive the pricing page from a `/products` API. After this PR, adding a new paid feature is an INSERT, not a schema change. Adding a monthly plan is a row, not a sprint.

**Out of scope** (deferred):
- Real WeChat Pay 协议支付 (auto-charge contracts).
- Cron job for automatic renewals.
- Dropping legacy `bazi_quota`/`liuyao_quota` columns.
- Touching `Entitlement` (still dead code).
- Admin CRUD for products (still seed-only).
- `/account` subscription management UI (separate follow-up).

---

## Phase 1 — Migration 008

**Files**:
- `fate/migrations/008_pricing_subscriptions.sql`
- `fate/migrations/008_rollback_pricing_subscriptions.sql`

Migration body (in this order):

1. `ALTER TABLE products` add: `kind ENUM('one_time','subscription') NOT NULL DEFAULT 'one_time'`, `period ENUM('monthly','yearly') NULL`, `features JSON NULL`.
2. `CREATE TABLE product_grants (id BIGINT PK AUTO_INCREMENT, product_id BIGINT NOT NULL, quota_type VARCHAR(50) NOT NULL, amount INT NOT NULL, FOREIGN KEY product_id REFERENCES products(id) ON DELETE CASCADE, INDEX idx_product (product_id))`.
3. `CREATE TABLE subscriptions (id BIGINT PK, user_id BIGINT NOT NULL FK→users, product_id BIGINT NOT NULL FK→products, status ENUM('active','cancelled','expired') NOT NULL DEFAULT 'active', current_period_start DATETIME NOT NULL, current_period_end DATETIME NOT NULL, auto_renew BOOL NOT NULL DEFAULT TRUE, cancelled_at DATETIME NULL, created_at, updated_at, INDEX idx_user_status (user_id, status))`.
4. `ALTER TABLE orders ADD COLUMN subscription_id BIGINT NULL, ADD INDEX idx_subscription (subscription_id)`.
5. **Backfill** product_grants from legacy columns:
   ```sql
   INSERT INTO product_grants (product_id, quota_type, amount)
     SELECT id, 'chat',        bazi_quota    FROM products WHERE bazi_quota   > 0
   UNION ALL
     SELECT id, 'liuyao_chat', liuyao_quota  FROM products WHERE liuyao_quota > 0;
   ```
6. **Seed** new `pro_monthly` product (¥39/月) + its grants + features JSON. Same `INSERT ... ON DUPLICATE KEY UPDATE` pattern as migration 006.

Rollback drops the two new tables, the new orders column, the three new products columns. Leaves legacy `bazi_quota`/`liuyao_quota` and existing rows untouched.

**Bootability**: legacy columns still exist after migration; old code paths keep working until Phase 3 lands.

---

## Phase 2 — Models (no behavior change)

**New**:
- `fate/app/models/product_grant.py` — `ProductGrant` (id, product_id FK, quota_type, amount).
- `fate/app/models/subscription.py` — `Subscription` (status enum, period datetimes, auto_renew, cancelled_at).

**Modified**:
- `fate/app/models/product.py` — add `kind`, `period`, `features` columns; add `grants: Mapped[list[ProductGrant]] = relationship(cascade="all, delete-orphan", lazy="selectin")`. Leave `bazi_quota`/`liuyao_quota` as-is, mark deprecated in docstring.
- `fate/app/models/order.py` — add nullable `subscription_id`.
- `fate/app/models/__init__.py` — export both new classes.

System still bootable: tables exist, models load, no new code paths active.

---

## Phase 3 — Services

**`fate/app/services/products.py`** — rewrite `grant_product_quota` to iterate `product.grants` and call `QuotaService.add_quota(db, user_id, g.amount, g.quota_type, source)` for each. Keep legacy-column fallback (`if not product.grants`) with a `logger.warning` so post-backfill we can spot any product missed. Signature unchanged: `grant_product_quota(db, *, user_id, product, source="purchase")`. Returns `{quota_type: amount}` dict.

**`fate/app/services/subscriptions.py`** (new):
- `create_or_renew_for_payment(db, user, product, order) -> tuple[Subscription, bool]`:
  - `SELECT ... FOR UPDATE` the active subscription for `(user_id, product_id)`.
  - If found and not expired: extend `current_period_end` by `product.period` **from the existing end** (not from `now()`) — so an early renewal doesn't lose days. Re-set status to 'active' if it was 'cancelled' but not yet expired.
  - Else: create new with `current_period_start=now()`, `current_period_end=now()+period`, status='active'.
  - Sets `order.subscription_id`. Returns `(sub, was_renewal)`.
- `cancel(db, *, user_id, subscription_id)`: status='cancelled', `auto_renew=False`, `cancelled_at=now()`. Period unchanged — user keeps what they paid for.

---

## Phase 4 — Routers

**`fate/app/routers/payments.py:simulate_payment`** — branch after `mark_success` (still in same transaction):
```python
if product.kind == "subscription":
    sub, was_renewal = subscriptions.create_or_renew_for_payment(db, current_user, product, order)
    granted = grant_product_quota(db, user_id=..., product=product,
                                  source="subscription_renewal" if was_renewal else "subscription_purchase")
    sub_id = sub.id
else:
    granted = grant_product_quota(db, user_id=..., product=product, source="purchase")
    sub_id = None
return SimulatePaymentOut(..., subscription_id=sub_id)
```
Idempotency note: double-click creates two orders → two renewals (extends 60d). Acceptable for v1; document and revisit when real payment is wired.

**`fate/app/routers/products.py`** (new):
- `GET /products` — list active products with eager-loaded grants + features.
- `GET /products/{code}` — single.

**`fate/app/routers/subscriptions.py`** (new):
- `GET /subscriptions/me` — list current user's subscriptions.
- `POST /subscriptions/{id}/cancel` — cancel (ownership check, 404 otherwise).

Register both in `fate/main.py`.

---

## Phase 5 — Schemas

- `fate/app/schemas/product.py` (new or extend): `ProductGrantOut`, `ProductOut` (with `grants: list[ProductGrantOut]`, `features: list[str]`, `kind`, `period`).
- `fate/app/schemas/subscription.py` (new): `SubscriptionOut`.
- Update `SimulatePaymentOut` to add optional `subscription_id`.

---

## Phase 6 — Seed (`fate/init_db.py`)

After each product upsert: upsert its grants (delete-by-product_id then insert — idempotent across reruns). Add the `pro_monthly` definition to the seed list:
```python
{"code": "pro_monthly", "name": "尊享月付", "kind": "subscription",
 "period": "monthly", "price_cents": 3900,
 "grants": [("chat", 30), ("liuyao_chat", 5)],
 "features": ["每月 30 次八字解读", "每月 5 次六爻问卦", "随时取消"]}
```

---

## Phase 7 — Frontend

- `fate-frontend/app/lib/api.ts` — add `getProducts()`, `getMySubscriptions()`, `cancelSubscription(id)`.
- `fate-frontend/app/pricing/page.tsx` — replace the hardcoded `plans` constant with a `useEffect` fetch of `/products`. Render `features[]` as the bullet list. For `kind==='subscription'` append `/月` to the price. Loading state: show 2-card skeleton.

---

## Critical files

- `fate/migrations/008_pricing_subscriptions.sql` (new)
- `fate/migrations/008_rollback_pricing_subscriptions.sql` (new)
- `fate/app/models/product_grant.py` (new)
- `fate/app/models/subscription.py` (new)
- `fate/app/models/product.py` (edit)
- `fate/app/models/order.py` (edit)
- `fate/app/models/__init__.py` (edit)
- `fate/app/services/products.py` (refactor `grant_product_quota`)
- `fate/app/services/subscriptions.py` (new)
- `fate/app/routers/payments.py` (edit `simulate_payment`)
- `fate/app/routers/products.py` (new)
- `fate/app/routers/subscriptions.py` (new)
- `fate/main.py` (register routers)
- `fate/app/schemas/product.py` (new/edit)
- `fate/app/schemas/subscription.py` (new)
- `fate/init_db.py` (extend seed)
- `fate-frontend/app/lib/api.ts` (add helpers)
- `fate-frontend/app/pricing/page.tsx` (fetch from API)

---

## Verification

After applying migration 008 and starting the backend:

1. `SELECT * FROM product_grants` → backfilled rows for `basic_combo` (chat=10, liuyao_chat=3) and `premium_combo` (chat=50, liuyao_chat=15).
2. `SELECT * FROM products WHERE code='pro_monthly'` → seeded with kind='subscription', period='monthly', features JSON populated.
3. `curl /products` → returns array with grants + features.
4. `POST /payments/simulate {"product_code":"basic_combo"}` → order succeeds, quotas added via grants path, **no subscription row** created.
5. `POST /payments/simulate {"product_code":"pro_monthly"}` (user A) → subscription row created, `current_period_end ≈ now+30d`, order has `subscription_id`, quotas granted with `source='subscription_purchase'`.
6. Repeat #5 same user 5 days later → **same subscription row**, `current_period_end ≈ original_end + 30d` (≈ now + 55d), quotas added again, source='subscription_renewal'.
7. `POST /subscriptions/{id}/cancel` → status='cancelled', `auto_renew=false`, `cancelled_at` set, `current_period_end` unchanged.
8. Frontend: load `/pricing` → renders 3 cards from API (basic, premium, pro_monthly), `/月` suffix on pro_monthly, features bullets match seed.
9. Rollback drill on a scratch DB: `mysql < 008_rollback_pricing_subscriptions.sql` → product_grants and subscriptions dropped, orders.subscription_id removed, products columns reverted, legacy `grant_product_quota` fallback path keeps working.
