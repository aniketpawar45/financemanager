import httpx, io
from config.logger import log_error

async def generate_chart(totals):
    try:
        payload = {
            "backgroundColor": "#181818", 
            "chart": {
                "type": "doughnut", 
                "data": {
                    "labels": list(totals.keys()), 
                    "datasets": [{"data": list(totals.values()), "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]}]
                }
            }
        }
        async with httpx.AsyncClient() as c:
            r = await c.post("https://quickchart.io/chart", json=payload)
            if r.status_code == 200:
                return io.BytesIO(r.content)
            return None
    except Exception as e:
        log_error("Chart API failure", e)
        return None
