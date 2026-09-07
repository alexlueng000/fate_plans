# 模拟付费 + 八字/六爻次数扣减

## Context

The platform has full quota infrastructure (`UserQuota`, `QuotaService.check_and_consume` / `add_quota`) and an Order/Payment/Product/Entitlement chain, but two gaps prevent the pricing page from actually working in dev:

1. **Real WeChat/Alipay aren't reachable** — the pricing page (`fate-frontend/app/pricing/page.tsx:120-186`) creates an order → calls `/payments/prepay` → polls for PAID, but no real payment ever lands. Need a "simulate payment" path so we can demo and test the full flow.
2. **Products grant only one quota type** — `Product.quota_amount` is a single int, and webhook handlers (`fate/app/routers/webhooks.py:142, 165, 218`) hardcode `"chat"` (i.e. Bazi). The advertised packages are bundles (`basic_combo` = 10 Bazi + 3 Liuyao; `premium_combo` = 50 Bazi + 15 Liuyao) — the schema can't represent them.

Goal: after clicking 立即购买, the user immediately gets both quotas added; thereafter `/api/chat/start` (Bazi) and `/api/liuyao/{id}/chat/start` (Liuyao) deduct from the right counter; when exhausted, the UI gracefully nudges them back to the pricing page.

The deduction side is already wired — keep the call sites, but adjust the 429 response payload (see §9b for `QUOTA_EXHAUSTED`):
- Bazi: `fate/app/routers/chat.py:71` calls `QuotaService.check_and_consume(db, user_id, "chat")`
- Bazi init: `fate/app/routers/chat.py:35` (same)
- Liuyao: `fate/app/routers/liuyao.py:429` calls `QuotaService.check_and_consume(db, user_id, "liuyao_chat")`

Free-tier behavior stays as-is: `QuotaService.DEFAULT_FREE_QUOTA = -1` (unlimited) — `add_quota` already handles the `-1 → finite` transition (`fate/app/services/quota.py:206-209`).

## Scope

- **Backend** (`fate/`): schema change, seed data, new service helper, new endpoint, fix existing webhook grants.
- **Web frontend** (`fate-frontend/`): rewire purchase button, show remaining quota, friendly 429 handling.
- **Out of scope**: WeChat mini program, real WeChat/Alipay flows (untouched).

## Priority breakdown

**P0 — must do (closes the loop):** §1–5, §7, §8 (refresh after purchase), §9 (friendly toast). Without these the demo can't run end-to-end.

**P1 — strongly recommended this iteration (avoids known pits):** §5b (env/admin gate on simulate), §9b (`QUOTA_EXHAUSTED` business code), §8b (`-1` unlimited rendering), §1b (`quota_amount` legacy comment). Skipping these works but creates traps: silent prod abuse of simulate, brittle frontend matching on HTTP-only signal, "0 / 无限制" UI confusion, future devs misusing legacy field.

**P2 — defer to later iterations:** see "Future work" section at bottom. Track as separate tasks; do **not** bundle into this PR.

---

## Backend changes

### 1. Extend `Product` model — multi-quota grants `[P0]`

**File:** `fate/app/models/product.py`

Add two columns alongside the existing `quota_amount`:

```python
bazi_quota: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="八字次数")
liuyao_quota: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="六爻次数")
```

### 1b. Mark `quota_amount` as legacy `[P1]`

Same file. Update the existing column's `comment=` to make the deprecation explicit so future devs don't misuse it:

```python
quota_amount: Mapped[int] = mapped_column(
    Integer, nullable=False,
    comment="【旧字段·仅兼容】legacy chat_5/chat_20/... 单一 chat 配额；新商品请用 bazi_quota / liuyao_quota",
)
```

Also add a one-line module docstring at the top of `product.py` pointing at the bundle convention.

### 2. Hand-written SQL migration `[P0]`

**New file:** `fate/migrations/006_add_product_multi_quota.sql` (this repo uses hand-written SQL, not Alembic — pattern matches files 001–005)

完整 SQL 内容(可直接粘到 mysql client 执行):

```sql
-- ============================================
-- 商品多类型次数 - 数据库迁移脚本
-- 版本: 006
-- 日期: 2026-05-07
-- 描述: products 表新增 bazi_quota / liuyao_quota,
--       并写入 basic_combo / premium_combo 套餐种子数据。
--       quota_amount 字段保留作为兼容旧 chat_5/chat_20 等单类型商品。
-- ============================================

ALTER TABLE `products`
  ADD COLUMN `bazi_quota` INT NOT NULL DEFAULT 0 COMMENT '八字次数(quota_type=chat)' AFTER `quota_amount`,
  ADD COLUMN `liuyao_quota` INT NOT NULL DEFAULT 0 COMMENT '六爻次数(quota_type=liuyao_chat)' AFTER `bazi_quota`;

INSERT INTO `products`
  (`code`, `name`, `price_cents`, `currency`, `quota_amount`, `bazi_quota`, `liuyao_quota`, `description`, `active`)
VALUES
  ('basic_combo',   '基础套餐',  9900, 'CNY', 0, 10, 3,  '10次八字解读 + 3次六爻问卦',  TRUE),
  ('premium_combo', '高级套餐', 29900, 'CNY', 0, 50, 15, '50次八字解读 + 15次六爻问卦', TRUE)
ON DUPLICATE KEY UPDATE
  `name`         = VALUES(`name`),
  `price_cents`  = VALUES(`price_cents`),
  `bazi_quota`   = VALUES(`bazi_quota`),
  `liuyao_quota` = VALUES(`liuyao_quota`),
  `description`  = VALUES(`description`),
  `active`       = VALUES(`active`);
```

Plus a rollback file `006_rollback_product_multi_quota.sql`:

```sql
-- 回滚 006: 移除套餐数据 + 删除新增列
DELETE FROM `products` WHERE `code` IN ('basic_combo', 'premium_combo');

ALTER TABLE `products`
  DROP COLUMN `liuyao_quota`,
  DROP COLUMN `bazi_quota`;
```

Also mirror the seed in `fate/init_db.py` (`SEED_PRODUCTS`, around line 18) so fresh DBs come up correct (新建库时 `python init_db.py` 会自动建表 + 灌种子,无需手动跑 SQL)。

#### 执行步骤

> 数据库名约定为 `fate`(与 migrations/README.md 中既有迁移一致)。如本地用了别的库名,把命令里的 `fate` 替换成实际库名即可。

```bash
# 0) 进到后端目录(SQL 路径相对于此)
cd fate

# 1) 强制备份(必做!即使是开发环境也建议)
mysqldump -u root -p fate > backup_before_006_$(date +%Y%m%d_%H%M%S).sql

# 2) 执行迁移
mysql -u root -p fate < migrations/006_add_product_multi_quota.sql
```

#### 验证

```sql
-- 新列存在,类型正确
SHOW COLUMNS FROM products LIKE 'bazi_quota';
SHOW COLUMNS FROM products LIKE 'liuyao_quota';

-- 套餐种子已写入
SELECT code, name, price_cents, bazi_quota, liuyao_quota, active
FROM products
WHERE code IN ('basic_combo', 'premium_combo');
-- 期望:
-- basic_combo   | 基础套餐 |  9900 | 10 |  3 | 1
-- premium_combo | 高级套餐 | 29900 | 50 | 15 | 1

-- 旧商品兼容性:bazi_quota / liuyao_quota 默认 0,不影响现有逻辑
SELECT code, quota_amount, bazi_quota, liuyao_quota
FROM products
WHERE code IN ('REPORT_UNLOCK', 'VIP_30D', 'chat_5', 'chat_20');
```

#### 回滚

```bash
mysql -u root -p fate < migrations/006_rollback_product_multi_quota.sql
```

#### 已发放配额的清理(可选,仅测试时用)

模拟支付会向 `user_quotas` 累加 `total_quota`。如果想把测试用户重置回"无限制",可以:

```sql
-- 用 user_id 替换实际值
UPDATE user_quotas
SET total_quota = -1, used_quota = 0, source = 'free'
WHERE user_id = <USER_ID>
  AND quota_type IN ('chat', 'liuyao_chat');
```

### 3. New service helper — grant a product's full bundle `[P0]`

**File:** `fate/app/services/products.py` (this file already exists — add a function; do not create a new file)

```python
def grant_product_quota(db, user_id: int, product: Product, source: str = "purchase") -> dict:
    """Grant all quota types from a product. Returns granted breakdown."""
    granted = {}
    if product.bazi_quota > 0:
        QuotaService.add_quota(db, user_id, product.bazi_quota, "chat", source)
        granted["bazi"] = product.bazi_quota
    if product.liuyao_quota > 0:
        QuotaService.add_quota(db, user_id, product.liuyao_quota, "liuyao_chat", source)
        granted["liuyao"] = product.liuyao_quota
    # Fallback for legacy products that only have quota_amount
    if not granted and product.quota_amount > 0:
        QuotaService.add_quota(db, user_id, product.quota_amount, "chat", source)
        granted["bazi"] = product.quota_amount
    return granted
```

Reuse `EntitlementService.grant(...)` if it exists in `fate/app/services/entitlements.py` (the file exists — confirm signature when implementing) to record an Entitlement row.

### 4. Replace hardcoded grants in webhooks `[P0]`

**File:** `fate/app/routers/webhooks.py`

Replace the three call sites — lines 142, 165, 218 — currently:
```python
QuotaService.add_quota(db, order.user_id, order.product.quota_amount, "chat", "purchase")
```
with:
```python
grant_product_quota(db, order.user_id, order.product, "purchase")
```
This makes the real WeChat/Alipay path correct for the new bundle products too — not just the simulate path.

### 5. New endpoint — `POST /api/payments/simulate` `[P0]`

**File:** `fate/app/routers/payments.py` (file already exists — add a route)

```python
@router.post("/simulate", response_model=SimulatePaymentOut)
def simulate_payment(
    body: SimulatePaymentIn,         # { product_code: str }
    db: Session = Depends(get_db_tx),
    current_user: User = Depends(get_current_user),   # required, not optional
):
    _ensure_simulate_allowed(current_user)            # see §5b

    product = db.query(Product).filter_by(code=body.product_code, active=True).first()
    if not product:
        raise HTTPException(404, "商品不存在")

    order = OrderService.create(db, user_id=current_user.id, product=product)
    pay_service.mark_success(db, order=order, transaction_id=f"sim_{order.id}", raw="simulate")
    granted = grant_product_quota(db, current_user.id, product, source="simulate")
    return SimulatePaymentOut(
        order_id=order.id,
        product_code=product.code,
        granted=granted,                          # {"bazi": 10, "liuyao": 3}
        quotas=QuotaService.get_user_stats(db, current_user.id)["quotas"],
    )
```

Schemas go in `fate/app/schemas/payment.py` (or wherever other payment schemas live — check before creating).

### 5b. Gate the simulate endpoint `[P1]`

The original answer was "any logged-in user", but leaving an unlimited free-quota grant open in production is too risky. Gate via `_ensure_simulate_allowed`:

```python
# fate/app/routers/payments.py
def _ensure_simulate_allowed(user: User) -> None:
    if settings.app_env == "production" and not user.is_admin:
        raise HTTPException(403, "Simulate payment is disabled in production")
```

Behavior:
- `APP_ENV != "production"` → any logged-in user can simulate (matches dev/test needs).
- `APP_ENV == "production"` → only `is_admin=True` can simulate (lets us still demo to investors / verify prod paths without exposing it to end users).

Add `app_env` to `Settings` in `fate/app/config.py` if it isn't already wired (the field is referenced in the existing CLAUDE.md but verify on implementation). Default to `"development"`.

### 6. Quota status endpoint `[P0]` (likely already exists, verify)

`fate/app/routers/quota.py` exists. Confirm there's a `GET /api/quota` (or similar) returning `QuotaService.get_user_stats(db, user.id)`. If not, add one — the frontend needs it to display "剩余 8 次八字 / 3 次六爻".

---

## Frontend changes

### 7. Rewire pricing buttons to simulate-pay `[P0]`

**File:** `fate-frontend/app/pricing/page.tsx`

Replace `handlePay()` (lines 120-154) and remove the `startPolling()`, `payChannel` selector, and pay-method modal — none are needed for a simulated one-shot purchase. Net effect: clicking 立即购买 → calls `/api/payments/simulate` → on success, shows a confirmation modal `已充值 10 次八字 + 3 次六爻` and links to `/panel`.

Replace the existing wechat/alipay icons in the modal with a single 模拟支付 confirmation button. Keep the modal shell (lines 324-395) — just simplify its body.

Add a small `(模拟支付 · 测试用)` badge near the price so it's visually clear this isn't real money.

### 8. Show remaining quota in the chat UI `[P0]`

**Files:**
- `fate-frontend/app/lib/api.ts` — add `getQuota()` helper
- `fate-frontend/app/chat/page.tsx` and `fate-frontend/app/panel/page.tsx` — fetch on mount, render small chip in the header: `剩余 8 次八字 · 3 次六爻`. Refresh after each successful purchase and after each chat send (chip read-only; the source of truth is the server).

### 8b. Render `-1` as 无限制 `[P1]`

The free baseline is `total_quota = -1` (`QuotaService.DEFAULT_FREE_QUOTA`). Without explicit handling the chip would show `-1 次` or `0 / -1` — confusing.

In `fate-frontend/app/lib/quota.ts` (new helper) or inline in the chip component:

```ts
function formatQuota(q: { total: number; used: number; remaining: number }): string {
  if (q.total === -1) return "无限制";
  return `剩余 ${q.remaining} 次`;
}
```

Apply in chat header chip, panel chip, and any pricing-page "your current balance" display.

### 9. Friendly 429 handling `[P0]`

**Files where chat is initiated:**
- `fate-frontend/app/lib/chat/sse.ts` — catch 429 and surface as a typed error
- `fate-frontend/app/chat/page.tsx` — when caught, replace assistant message with a friendly card: `次数已用完，前往充值 →` linking to `/pricing`

Same treatment for the Liuyao page (`fate-frontend/app/liuyao/page.tsx`) since it triggers `liuyao_chat` quota.

### 9b. Business error code `QUOTA_EXHAUSTED` `[P1]`

Today the deduction sites raise:
```python
raise HTTPException(status_code=429, detail=f"配额已用完：{msg}")
```
A bare 429 is fragile — any other rate limit (e.g. SMS, login throttle) returns the same status, and the frontend currently parses the `detail` string. Switch to a structured error so the frontend can branch deterministically:

```python
# fate/app/core/errors.py (or wherever shared errors live — check first)
class QuotaExhaustedError(HTTPException):
    def __init__(self, quota_type: str, remaining: int):
        super().__init__(
            status_code=429,
            detail={
                "code": "QUOTA_EXHAUSTED",
                "quota_type": quota_type,        # "chat" | "liuyao_chat"
                "remaining": remaining,
                "message": "配额已用完",
            },
        )
```

Update three call sites to raise `QuotaExhaustedError(quota_type, remaining)` instead of building the HTTPException inline:
- `fate/app/routers/chat.py:36-37`
- `fate/app/routers/chat.py:72-73`
- `fate/app/routers/liuyao.py:430-431`

Frontend (`fate-frontend/app/lib/chat/sse.ts`): typed error
```ts
type QuotaExhausted = { code: "QUOTA_EXHAUSTED"; quota_type: "chat" | "liuyao_chat"; remaining: number };
```
Branch on `code === "QUOTA_EXHAUSTED"` rather than HTTP status alone, and use `quota_type` to pick the right CTA copy ("八字次数已用完" vs "六爻次数已用完").

---

## Critical files to be modified

| Path | Change | Pri |
|---|---|---|
| `fate/app/models/product.py` | +2 columns (`bazi_quota`, `liuyao_quota`); legacy comment on `quota_amount` | P0 / P1 |
| `fate/migrations/006_product_multi_quota.sql` (new) + rollback | schema + seed | P0 |
| `fate/init_db.py` (~line 18 seed) | mirror seed data | P0 |
| `fate/app/services/products.py` | add `grant_product_quota()` | P0 |
| `fate/app/routers/webhooks.py` (lines 142, 165, 218) | swap to `grant_product_quota` | P0 |
| `fate/app/routers/payments.py` | add `POST /payments/simulate` + env/admin gate | P0 / P1 |
| `fate/app/schemas/payment.py` (or equivalent) | `SimulatePaymentIn`/`Out` | P0 |
| `fate/app/routers/quota.py` | confirm/add `GET /quota` for current user | P0 |
| `fate/app/core/errors.py` (or shared module) | `QuotaExhaustedError` class | P1 |
| `fate/app/routers/chat.py:36-37, 72-73` + `liuyao.py:430-431` | raise `QuotaExhaustedError` | P1 |
| `fate/app/config.py` | ensure `app_env` setting exists | P1 |
| `fate-frontend/app/pricing/page.tsx` | strip pay-channel modal; call simulate endpoint | P0 |
| `fate-frontend/app/lib/api.ts` | add `simulatePayment()`, `getQuota()` | P0 |
| `fate-frontend/app/lib/quota.ts` (new) | `formatQuota()` for `-1` → 无限制 | P1 |
| `fate-frontend/app/chat/page.tsx` | quota chip + 429 handling | P0 |
| `fate-frontend/app/liuyao/page.tsx` | quota chip + 429 handling | P0 |
| `fate-frontend/app/panel/page.tsx` | quota chip | P0 |
| `fate-frontend/app/lib/chat/sse.ts` | typed `QUOTA_EXHAUSTED` error | P0 / P1 |

## Reused (don't reimplement)

- `QuotaService.add_quota` / `check_and_consume` — `fate/app/services/quota.py:53, 192`
- `pay_service.mark_success` — already used in `webhooks.py:139, 162, 217`
- `OrderService.create` — used by existing `POST /api/orders` (verify at `fate/app/services/orders.py`)
- `EntitlementService.grant` — `fate/app/services/entitlements.py` (verify signature)
- Existing deduction sites: `chat.py:35, 71`, `liuyao.py:429` (no edits needed)

---

## Verification

End-to-end smoke test (as a regular user):

1. **Migration** — `mysql ... < fate/migrations/006_product_multi_quota.sql`; verify with `SELECT code, bazi_quota, liuyao_quota FROM products WHERE code IN ('basic_combo','premium_combo');`
2. **Backend up** — `cd fate && uvicorn main:app --reload`
3. **Pre-purchase quota** — log in via web, open chat, confirm header shows `无限制` (free `-1` baseline). Send 1 Bazi message → completes; `SELECT used_quota, total_quota FROM user_quotas WHERE user_id=? AND quota_type='chat';` shows `used_quota=1, total_quota=-1`.
4. **Simulate basic_combo** — frontend pricing page → 立即购买 on basic. Confirmation modal shows `+10 八字, +3 六爻`. Header chip refreshes (10 granted; `add_quota` resets `used_quota` to 0 on the `-1 → finite` transition per `quota.py:206-209` — pre-purchase usage is wiped, matching "fresh package" intent).
5. **Bazi deduction** — start 10 fresh Bazi sessions; the 11th returns 429; UI shows `次数已用完, 前往充值 →`. Confirm no Liuyao quota was touched.
6. **Liuyao deduction** — open `/liuyao`, complete 3 hexagram interpretations; the 4th returns 429.
7. **Premium re-purchase** — buy `premium_combo` on top → quotas should be `+50 / +15` *added* to remainders, per `add_quota`'s accumulate branch (`quota.py:212`).
8. **Real-payment regression** — POST `{out_trade_no, transaction_id}` to `/webhooks/wechatpay` (dev mode) for an existing CREATED order → confirm bundle products now grant both quotas (this verifies the fix to webhook hardcoding from §4).
9. **DB audit** — `SELECT * FROM orders WHERE user_id=?;` shows two PAID rows with the simulated `transaction_id` like `sim_<order_id>`; entitlements table has matching grant rows.
10. **P1 — `-1` rendering** — log in as a fresh user with no purchases; chat header chip shows `无限制`, not `-1 次` or `0 / -1`.
11. **P1 — `QUOTA_EXHAUSTED`** — exhaust Bazi quota; capture the network response and confirm `detail.code === "QUOTA_EXHAUSTED"` and `detail.quota_type === "chat"`. Trigger Liuyao exhaustion separately and confirm `quota_type === "liuyao_chat"`.
12. **P1 — prod gate** — set `APP_ENV=production` and call `/api/payments/simulate` as a non-admin user → expect `403`. Same call as admin → succeeds.

---

## Future work (P2 — separate iterations, do not bundle)

- **`product_entitlements` table** — replace the per-quota-type columns on `Product` with a one-to-many entitlement spec (e.g. rows like `(product_id, kind="bazi_chat", amount=10)`). Cleaner than adding a column per new quota type. Migrate existing `bazi_quota` / `liuyao_quota` data into this table; keep `Product` columns as views or drop after migration. Touch points: `Product` model, `grant_product_quota`, seed migration.
- **Admin product entitlement editor** — admin page (`fate-frontend/app/admin/products/`) to CRUD product entitlements without SQL. Depends on the `product_entitlements` refactor above.
- **Restore real WeChat / Alipay** — re-enable `/payments/prepay` and the existing webhook signature/decrypt path; the simulate endpoint stays for admin/dev. Verify `grant_product_quota` (added in §3) handles real callbacks correctly, since §4 already routed real webhooks through it.
- **Unified audit page** — internal admin view joining `orders`, `payments`, `entitlements`, `user_quotas`, `usage_logs` per user/order to debug "why doesn't this user have X quota" support tickets.
- **充值记录 page** — user-facing order/recharge history at `fate-frontend/app/account/orders/`. Lists past purchases, granted quota, and remaining usage.
- **Failed-order auto-close** — background job (or on-read lazy check) to mark `CREATED` orders older than N hours as `CLOSED`/`EXPIRED`, so users can retry purchase without the old order lingering.
