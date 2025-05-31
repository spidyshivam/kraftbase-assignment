import httpx

delivery_agent_service_client = httpx.AsyncClient(base_url="http://delivery_agent_service:8002", timeout=5.0)

