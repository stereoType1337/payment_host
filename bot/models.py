import datetime
from decimal import Decimal
from bot.db import get_pool


# ── Servers ──────────────────────────────────────────────

async def add_server(
    hoster: str,
    server_name: str,
    payment_day: int,
    payment_type: str,
    monthly_cost: Decimal | None,
    currency: str,
    count: int = 1,
) -> dict:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO servers (hoster, server_name, payment_day, payment_type, monthly_cost, currency, count)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        hoster, server_name, payment_day, payment_type, monthly_cost, currency, count,
    )
    return dict(row)


async def get_server(server_id: int) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow("SELECT * FROM servers WHERE id = $1", server_id)
    return dict(row) if row else None


async def list_servers(active_only: bool = True) -> list[dict]:
    pool = get_pool()
    if active_only:
        rows = await pool.fetch(
            "SELECT * FROM servers WHERE is_active = TRUE ORDER BY hoster, server_name"
        )
    else:
        rows = await pool.fetch("SELECT * FROM servers ORDER BY hoster, server_name")
    return [dict(r) for r in rows]


async def list_hosters() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT hoster, COUNT(*) AS count
        FROM servers
        WHERE is_active = TRUE
        GROUP BY hoster
        ORDER BY hoster
        """
    )
    return [{"hoster": r["hoster"], "count": r["count"]} for r in rows]


async def list_servers_by_hoster(hoster: str) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT * FROM servers WHERE hoster = $1 AND is_active = TRUE ORDER BY server_name",
        hoster,
    )
    return [dict(r) for r in rows]


async def delete_server(server_id: int) -> bool:
    pool = get_pool()
    result = await pool.execute("DELETE FROM servers WHERE id = $1", server_id)
    return result == "DELETE 1"


async def update_server(server_id: int, **fields) -> dict | None:
    if not fields:
        return await get_server(server_id)
    pool = get_pool()
    set_parts = []
    values = []
    for i, (key, val) in enumerate(fields.items(), start=1):
        set_parts.append(f"{key} = ${i}")
        values.append(val)
    values.append(server_id)
    query = f"UPDATE servers SET {', '.join(set_parts)} WHERE id = ${len(values)} RETURNING *"
    row = await pool.fetchrow(query, *values)
    return dict(row) if row else None


# ── Payments ─────────────────────────────────────────────

async def ensure_payment(server_id: int, due_date: datetime.date) -> dict:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO payments (server_id, due_date)
        VALUES ($1, $2)
        ON CONFLICT (server_id, due_date) DO NOTHING
        RETURNING *
        """,
        server_id, due_date,
    )
    if row is None:
        row = await pool.fetchrow(
            "SELECT * FROM payments WHERE server_id = $1 AND due_date = $2",
            server_id, due_date,
        )
    return dict(row)


async def get_payment(payment_id: int) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow("SELECT * FROM payments WHERE id = $1", payment_id)
    return dict(row) if row else None


async def mark_payment(payment_id: int, status: str) -> dict | None:
    pool = get_pool()
    paid_at = datetime.datetime.now() if status in ("paid", "confirmed") else None
    row = await pool.fetchrow(
        """
        UPDATE payments SET status = $1, paid_at = $2
        WHERE id = $3 RETURNING *
        """,
        status, paid_at, payment_id,
    )
    return dict(row) if row else None


async def set_notified(payment_id: int, days: int) -> None:
    pool = get_pool()
    col = "notified_3d" if days == 3 else "notified_1d"
    await pool.execute(
        f"UPDATE payments SET {col} = TRUE WHERE id = $1", payment_id
    )


async def get_upcoming_payments(days_ahead: int = 14) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT p.*, s.hoster, s.server_name, s.monthly_cost, s.currency, s.payment_type, s.count
        FROM payments p
        JOIN servers s ON s.id = p.server_id
        WHERE p.due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + $1::integer
          AND p.status = 'pending'
          AND s.is_active = TRUE
        ORDER BY p.due_date
        """,
        days_ahead,
    )
    return [dict(r) for r in rows]


async def get_pending_notifications() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT p.*, s.hoster, s.server_name, s.monthly_cost, s.currency, s.payment_type, s.count
        FROM payments p
        JOIN servers s ON s.id = p.server_id
        WHERE p.status = 'pending'
          AND s.is_active = TRUE
          AND p.due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + 3
        ORDER BY p.due_date
        """
    )
    return [dict(r) for r in rows]


# ── Settings ─────────────────────────────────────────────

async def get_setting(key: str) -> str | None:
    pool = get_pool()
    row = await pool.fetchrow("SELECT value FROM settings WHERE key = $1", key)
    return row["value"] if row else None


async def set_setting(key: str, value: str) -> None:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO settings (key, value) VALUES ($1, $2)
        ON CONFLICT (key) DO UPDATE SET value = $2
        """,
        key, value,
    )
