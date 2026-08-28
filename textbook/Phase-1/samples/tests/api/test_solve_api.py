"""作業単位 1-6: POST /api/v1/solve の契約。"""

from httpx import ASGITransport, AsyncClient
from tests.fixtures.optimization import build_route_problem, build_shift_problem

from app.main import app


async def test_solve_route_returns_verified_solution(api) -> None:
    client, _user = api
    problem = build_route_problem(forbidden=["e_bd"], required=["C"])
    resp = await client.post("/api/v1/solve", json={"problem": problem.model_dump(mode="json")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["solution"]["status"] == "valid"
    assert body["solution"]["assignments"]["path_node_ids"] == ["A", "B", "C", "E"]
    assert body["solution"]["metrics"]["total_weight"] == 9.0
    assert body["problem_id"] and body["solution_id"]


async def test_solve_persist_false_has_null_ids(api) -> None:
    client, _user = api
    resp = await client.post(
        "/api/v1/solve",
        json={
            "problem": build_route_problem().model_dump(mode="json"),
            "persist": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["problem_id"] is None and body["solution_id"] is None


async def test_solve_unsupported_problem_type_is_400(api) -> None:
    client, _user = api
    resp = await client.post(
        "/api/v1/solve",
        json={"problem": build_shift_problem().model_dump(mode="json")},
    )
    assert resp.status_code == 400
    assert "no algorithm" in resp.json()["detail"].lower()


async def test_solve_infeasible_problem_is_400(api) -> None:
    client, _user = api
    resp = await client.post(
        "/api/v1/solve",
        json={"problem": build_route_problem(forbidden=["e_ce", "e_de"]).model_dump(mode="json")},
    )
    assert resp.status_code == 400


async def test_solve_requires_authentication() -> None:
    # 認証ヘッダなしの素のクライアント
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as anon:
        resp = await anon.post(
            "/api/v1/solve",
            json={"problem": build_route_problem().model_dump(mode="json")},
        )
    assert resp.status_code == 401
